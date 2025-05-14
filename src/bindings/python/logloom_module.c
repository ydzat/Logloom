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
static PyObject* logloom_lang_getf(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* key = NULL;
    PyObject* pos_args = NULL;
    
    // 先处理位置参数
    if (!PyArg_ParseTuple(args, "s|O", &key, &pos_args))
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
    
    PyObject* result = NULL;
    
    // 处理格式化逻辑：先看是否有位置参数
    if (pos_args && pos_args != Py_None) {
        // 确保是元组
        if (!PyTuple_Check(pos_args)) {
            pos_args = Py_BuildValue("(O)", pos_args);
            result = PyUnicode_Format(formatted, pos_args);
            Py_DECREF(pos_args);
        } else {
            result = PyUnicode_Format(formatted, pos_args);
        }
    } 
    // 处理关键字参数
    else if (kwargs && PyDict_Size(kwargs) > 0) {
        result = PyUnicode_Format(formatted, kwargs);
    } 
    // 没有格式参数，直接返回
    else {
        result = formatted;
        Py_INCREF(result); // 增加引用计数，因为后面会释放formatted
    }
    
    Py_DECREF(formatted);
    return result;
}

// 注册语言资源文件的包装函数
static PyObject* logloom_register_locale_file(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* file_path = NULL;
    const char* lang_code = NULL;
    static char* kwlist[] = {"file_path", "lang_code", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|s", kwlist, &file_path, &lang_code))
        return NULL;
    
    // 检查文件是否存在和可读
    if (access(file_path, R_OK) != 0) {
        PyErr_Format(PyExc_FileNotFoundError, "Language resource file does not exist or is not readable: %s", file_path);
        return NULL;
    }
    
    // 调用C API注册文件
    bool success = lang_register_file(file_path, lang_code);
    if (!success) {
        PyErr_Format(PyExc_RuntimeError, "Failed to register language resource file: %s", file_path);
        return NULL;
    }
    
    Py_RETURN_TRUE;
}

// 注册目录中所有匹配模式的语言资源文件的包装函数
static PyObject* logloom_register_locale_directory(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* dir_path = NULL;
    const char* pattern = "*.yaml";
    static char* kwlist[] = {"dir_path", "pattern", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|s", kwlist, &dir_path, &pattern))
        return NULL;
    
    // 检查目录是否存在
    struct stat st;
    if (stat(dir_path, &st) != 0 || !S_ISDIR(st.st_mode)) {
        PyErr_Format(PyExc_FileNotFoundError, "Directory does not exist: %s", dir_path);
        return NULL;
    }
    
    // 调用C API扫描目录
    int count = lang_scan_directory(dir_path, pattern);
    
    return PyLong_FromLong(count);
}

// 扫描使用glob模式的目录的包装函数
static PyObject* logloom_scan_directory_with_glob(PyObject* self, PyObject* args) {
    const char* glob_pattern;
    if (!PyArg_ParseTuple(args, "s", &glob_pattern))
        return NULL;
    
    // 调用C API扫描目录
    int count = lang_scan_directory_with_glob(glob_pattern);
    
    return PyLong_FromLong(count);
}

// 自动发现语言资源文件的包装函数
static PyObject* logloom_auto_discover_resources(PyObject* self, PyObject* Py_UNUSED(ignored)) {
    // 调用C API自动发现资源
    bool found = lang_auto_discover_resources();
    
    if (found)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

// 获取支持的语言列表的包装函数
static PyObject* logloom_get_supported_languages(PyObject* self, PyObject* Py_UNUSED(ignored)) {
    // 调用C API获取语言列表
    int count = 0;
    char** languages = lang_get_supported_languages(&count);
    
    if (!languages) {
        // 如果没有语言，返回空列表
        return PyList_New(0);
    }
    
    // 创建Python列表
    PyObject* lang_list = PyList_New(count);
    if (!lang_list) {
        // 释放C API分配的内存
        for (int i = 0; i < count; i++) {
            free(languages[i]);
        }
        free(languages);
        return NULL;
    }
    
    // 填充列表
    for (int i = 0; i < count; i++) {
        PyObject* lang_str = PyUnicode_FromString(languages[i]);
        if (!lang_str) {
            Py_DECREF(lang_list);
            // 释放C API分配的内存
            for (int j = 0; j < count; j++) {
                free(languages[j]);
            }
            free(languages);
            return NULL;
        }
        PyList_SET_ITEM(lang_list, i, lang_str); // 此函数窃取引用，无需DECREF
    }
    
    // 释放C API分配的内存
    for (int i = 0; i < count; i++) {
        free(languages[i]);
    }
    free(languages);
    
    return lang_list;
}

// 获取语言键列表的包装函数
static PyObject* logloom_get_language_keys(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* lang_code = NULL;
    static char* kwlist[] = {"lang_code", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|s", kwlist, &lang_code))
        return NULL;
    
    // 调用C API获取键列表
    int count = 0;
    char** keys = lang_get_language_keys(lang_code, &count);
    
    if (!keys) {
        // 如果没有键，返回空列表
        return PyList_New(0);
    }
    
    // 创建Python列表
    PyObject* key_list = PyList_New(count);
    if (!key_list) {
        // 释放C API分配的内存
        for (int i = 0; i < count; i++) {
            free(keys[i]);
        }
        free(keys);
        return NULL;
    }
    
    // 填充列表
    for (int i = 0; i < count; i++) {
        PyObject* key_str = PyUnicode_FromString(keys[i]);
        if (!key_str) {
            Py_DECREF(key_list);
            // 释放C API分配的内存
            for (int j = 0; j < count; j++) {
                free(keys[j]);
            }
            free(keys);
            return NULL;
        }
        PyList_SET_ITEM(key_list, i, key_str); // 此函数窃取引用，无需DECREF
    }
    
    // 释放C API分配的内存
    for (int i = 0; i < count; i++) {
        free(keys[i]);
    }
    free(keys);
    
    return key_list;
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
static PyObject* logloom_get_language(PyObject* self, PyObject* Py_UNUSED(ignored)) {
    const char* lang_code = lang_get_current();
    if (!lang_code) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to get current language");
        return NULL;
    }
    
    return PyUnicode_FromString(lang_code);
}

// 为保持API一致性，提供get_current_language别名
static PyObject* logloom_get_current_language(PyObject* self, PyObject* Py_UNUSED(ignored)) {
    return logloom_get_language(self, NULL);
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

// 设置控制台输出状态的包装函数
static PyObject* logloom_set_output_console(PyObject* self, PyObject* args) {
    int enabled;
    if (!PyArg_ParseTuple(args, "p", &enabled))
        return NULL;
    
    // 调用C API设置控制台输出状态
    log_set_console_enabled(enabled ? true : false);
    
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
static PyObject* logloom_cleanup(PyObject* self, PyObject* Py_UNUSED(ignored)) {
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
    {"format_text", (PyCFunction)logloom_lang_getf, METH_VARARGS | METH_KEYWORDS,
     "Format localized text with arguments"},
    {"set_log_level", logloom_set_log_level, METH_VARARGS,
     "Set the log level"},
    {"set_language", logloom_set_language, METH_VARARGS,
     "Set the current language"},
    {"get_language", logloom_get_language, METH_NOARGS,
     "Get the current language"},
    {"get_current_language", logloom_get_current_language, METH_NOARGS,
     "Get the current language (alias for get_language)"},
    {"set_log_file", logloom_set_log_file, METH_VARARGS,
     "Set the log file path"},
    {"set_log_max_size", logloom_set_log_max_size, METH_VARARGS,
     "Set the maximum log file size"},
    {"set_output_console", logloom_set_output_console, METH_VARARGS,
     "Enable or disable console output"},
    
    // 新增国际化扩展功能API
    {"register_locale_file", (PyCFunction)logloom_register_locale_file, METH_VARARGS | METH_KEYWORDS,
     "Register an additional language resource file"},
    {"register_locale_directory", (PyCFunction)logloom_register_locale_directory, METH_VARARGS | METH_KEYWORDS,
     "Register language resource files in a directory matching a pattern"},
    {"scan_directory_with_glob", logloom_scan_directory_with_glob, METH_VARARGS,
     "Scan directory using a glob pattern to find language resources"},
    {"auto_discover_resources", logloom_auto_discover_resources, METH_NOARGS,
     "Auto-discover language resource files in standard locations"},
    {"get_supported_languages", logloom_get_supported_languages, METH_NOARGS,
     "Get a list of all supported language codes"},
    {"get_language_keys", (PyCFunction)logloom_get_language_keys, METH_VARARGS | METH_KEYWORDS,
     "Get a list of all available translation keys for a language"},
    
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