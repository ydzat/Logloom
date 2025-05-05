#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <structmember.h>

#include "lang.h"
#include "log.h"
#include "config.h"

// 日志级别对应表
static const char* log_levels[] = {"DEBUG", "INFO", "WARN", "ERROR", "FATAL", NULL};

// 日志函数包装宏
#define LOG_WRAPPER(level) static PyObject* \
logloom_log_##level(PyObject* self, PyObject* args) { \
    const char* module; \
    const char* message; \
    if (!PyArg_ParseTuple(args, "ss", &module, &message)) \
        return NULL; \
    log_##level(module, "%s", message); \
    Py_RETURN_NONE; \
}

// 定义各日志级别的包装函数
LOG_WRAPPER(debug)
LOG_WRAPPER(info)
LOG_WRAPPER(warn)
LOG_WRAPPER(error)
LOG_WRAPPER(fatal)

// 获取语言字符串的包装函数
static PyObject* logloom_lang_get(PyObject* self, PyObject* args) {
    const char* key;
    if (!PyArg_ParseTuple(args, "s", &key))
        return NULL;
    
    const char* value = lang_get(key);
    if (!value) {
        PyErr_Format(PyExc_KeyError, "Language key not found: %s", key);
        return NULL;
    }
    
    return PyUnicode_FromString(value);
}

// 格式化语言字符串的包装函数
static PyObject* logloom_lang_getf(PyObject* self, PyObject* args) {
    const char* key;
    PyObject* format_args;
    
    if (!PyArg_ParseTuple(args, "sO", &key, &format_args))
        return NULL;
    
    // 获取模板字符串
    const char* template = lang_get(key);
    if (!template) {
        // 如果模板不存在，返回一个默认错误信息
        PyErr_Format(PyExc_KeyError, "Language key not found: %s", key);
        return NULL;
    }
    
    // 使用Python的字符串格式化
    PyObject* formatted = PyUnicode_FromString(template);
    if (!formatted)
        return NULL;
    
    PyObject* result;
    if (PyTuple_Check(format_args)) {
        // 使用位置参数格式化
        result = PyUnicode_Format(formatted, format_args);
    } else if (PyDict_Check(format_args)) {
        // 使用关键字参数格式化
        result = PyUnicode_Format(formatted, format_args);
    } else {
        PyErr_SetString(PyExc_TypeError, "Format arguments must be a tuple or a dict");
        Py_DECREF(formatted);
        return NULL;
    }
    
    Py_DECREF(formatted);
    return result;
}

// 设置日志级别的包装函数
static PyObject* logloom_set_log_level(PyObject* self, PyObject* args) {
    const char* level;
    if (!PyArg_ParseTuple(args, "s", &level))
        return NULL;
    
    // 验证日志级别的有效性
    bool valid_level = false;
    for (int i = 0; log_levels[i]; i++) {
        if (strcasecmp(level, log_levels[i]) == 0) {
            valid_level = true;
            break;
        }
    }
    
    if (!valid_level) {
        PyErr_Format(PyExc_ValueError, "Invalid log level: %s", level);
        return NULL;
    }
    
    log_set_level(level);
    Py_RETURN_NONE;
}

// 设置语言的包装函数
static PyObject* logloom_set_language(PyObject* self, PyObject* args) {
    const char* lang_code;
    if (!PyArg_ParseTuple(args, "s", &lang_code))
        return NULL;
    
    bool success = lang_set_language(lang_code);
    if (!success) {
        PyErr_Format(PyExc_ValueError, "Failed to set language: %s", lang_code);
        return NULL;
    }
    
    Py_RETURN_NONE;
}

// 获取当前语言代码的包装函数
static PyObject* logloom_get_language(PyObject* self, PyObject* args) {
    const char* lang_code = lang_get_current();
    if (!lang_code) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to get current language");
        return NULL;
    }
    
    return PyUnicode_FromString(lang_code);
}

// 设置日志文件的包装函数
static PyObject* logloom_set_log_file(PyObject* self, PyObject* args) {
    const char* file_path;
    if (!PyArg_ParseTuple(args, "s", &file_path))
        return NULL;
    
    // 使用正确的函数名设置日志文件
    log_set_file(file_path);
    
    // 尝试创建目录，并验证文件是否可写
    if (file_path && strlen(file_path) > 0) {
        // 创建目录路径
        char* dir_path = strdup(file_path);
        if (dir_path) {
            // 获取目录部分
            char* last_slash = strrchr(dir_path, '/');
            if (last_slash) {
                *last_slash = '\0';  // 截断，只保留目录部分
                
                // 创建目录（递归）
                char command[1024];
                snprintf(command, sizeof(command), "mkdir -p %s", dir_path);
                system(command);
            }
            free(dir_path);
        }
        
        // 验证文件是否可写
        FILE* test_file = fopen(file_path, "a");
        if (!test_file) {
            PyErr_Format(PyExc_IOError, "无法打开日志文件: %s", file_path);
            return NULL;
        }
        fclose(test_file);
    }
    
    Py_RETURN_TRUE;
}

// 设置日志文件最大大小的包装函数
static PyObject* logloom_set_log_max_size(PyObject* self, PyObject* args) {
    unsigned long max_size;
    if (!PyArg_ParseTuple(args, "k", &max_size))
        return NULL;
    
    log_set_max_file_size(max_size);
    Py_RETURN_NONE;
}

// 初始化Logloom的包装函数
static PyObject* logloom_initialize(PyObject* self, PyObject* args) {
    const char* config_path = NULL;
    
    // 解析可选的配置文件路径参数
    if (!PyArg_ParseTuple(args, "|s", &config_path))
        return NULL;
    
    // 初始化配置
    int config_result = config_init();
    if (config_result != 0) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to initialize configuration");
        return NULL;
    }
    
    // 加载配置文件（如果提供）
    if (config_path && strlen(config_path) > 0) {
        config_result = config_load_from_file(config_path);
        if (config_result != 0) {
            PyErr_Format(PyExc_FileNotFoundError, "Failed to load config file: %s", config_path);
            return NULL;
        }
        
        // 记录配置文件加载成功
        printf("[INFO] 加载配置文件: %s\n", config_path);
    }
    
    // 获取配置中的日志级别字符串
    const char* level_str = config_get_log_level();
    if (!level_str) {
        level_str = "INFO"; // 默认级别
    }
    
    // 获取配置中的日志文件路径
    const char* log_file = config_get_log_file();
    
    // 初始化语言模块
    int lang_result = lang_init(config_get_language());
    if (lang_result != 0) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to initialize language module");
        return NULL;
    }
    
    // 使用正确的参数类型初始化日志模块
    int log_result = log_init(level_str, log_file);
    if (log_result != 0) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to initialize log module");
        return NULL;
    }
    
    // 如果日志文件是动态创建的，确保目录存在
    if (log_file && strlen(log_file) > 0) {
        // 创建目录结构
        char* dir_path = strdup(log_file);
        if (dir_path) {
            // 获取目录部分
            char* last_slash = strrchr(dir_path, '/');
            if (last_slash) {
                *last_slash = '\0';  // 截断，只保留目录部分
                
                // 创建目录（递归）
                char command[1024];
                snprintf(command, sizeof(command), "mkdir -p %s", dir_path);
                system(command);
            }
            free(dir_path);
        }
    }
    
    // 返回True表示成功
    Py_RETURN_TRUE;
}

// 清理Logloom的包装函数
static PyObject* logloom_cleanup(PyObject* self, PyObject* args) {
    log_cleanup();
    lang_cleanup();
    config_cleanup();
    
    Py_RETURN_NONE;
}

// 模块方法定义
static PyMethodDef LogloomMethods[] = {
    {"initialize", logloom_initialize, METH_VARARGS,
     "Initialize Logloom with an optional config file path"},
    {"cleanup", logloom_cleanup, METH_NOARGS,
     "Clean up Logloom resources"},
    {"debug", logloom_log_debug, METH_VARARGS,
     "Log a debug message"},
    {"info", logloom_log_info, METH_VARARGS,
     "Log an info message"},
    {"warn", logloom_log_warn, METH_VARARGS,
     "Log a warning message"},
    {"error", logloom_log_error, METH_VARARGS,
     "Log an error message"},
    {"fatal", logloom_log_fatal, METH_VARARGS,
     "Log a fatal message"},
    {"get_text", logloom_lang_get, METH_VARARGS,
     "Get localized text by key"},
    {"format_text", logloom_lang_getf, METH_VARARGS,
     "Format localized text with arguments"},
    {"set_log_level", logloom_set_log_level, METH_VARARGS,
     "Set the log level"},
    {"set_language", logloom_set_language, METH_VARARGS,
     "Set the current language"},
    {"get_language", logloom_get_language, METH_NOARGS,
     "Get the current language"},
    {"set_log_file", logloom_set_log_file, METH_VARARGS,
     "Set the log file path"},
    {"set_log_max_size", logloom_set_log_max_size, METH_VARARGS,
     "Set the maximum log file size"},
    {NULL, NULL, 0, NULL} /* Sentinel */
};

// 模块定义结构
static struct PyModuleDef logloom_module = {
    PyModuleDef_HEAD_INIT,
    "logloom",
    "Python bindings for Logloom logging and internationalization library",
    -1,
    LogloomMethods
};

// 模块初始化函数
PyMODINIT_FUNC PyInit_logloom(void) {
    return PyModule_Create(&logloom_module);
}