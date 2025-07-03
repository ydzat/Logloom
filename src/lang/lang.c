#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <dirent.h> // 用于目录操作
#include <glob.h>   // 用于glob模式匹配
#include <unistd.h> // 用于access函数
#include <sys/stat.h> // 用于stat函数

#include "lang.h"
#include "generated/lang_registry.h"

// 我们将使用一个简单的哈希表来存储动态加载的语言资源
#define MAX_DYNAMIC_LANGS 32
#define MAX_ENTRIES_PER_LANG 1024

// 动态语言资源表结构
typedef struct {
    char lang_code[16];         // 语言代码
    int entry_count;            // 条目数量
    lang_entry_t entries[MAX_ENTRIES_PER_LANG]; // 实际条目
    char* keys_storage;         // 存储所有键的缓冲区
    char* values_storage;       // 存储所有值的缓冲区
} dynamic_lang_table_t;

// 全局变量
static dynamic_lang_table_t dynamic_langs[MAX_DYNAMIC_LANGS]; // 动态加载的语言资源
static int dynamic_lang_count = 0;                           // 动态语言资源数量

// 当前语言上下文
static const lang_entry_t* current_lang_table = NULL;
static const lang_entry_t* fallback_lang_table = NULL;  // 默认语言表
static char current_lang_code[16] = "en";               // 当前语言代码
static const char* DEFAULT_LANG = "en";                 // 默认语言代码
static int dynamic_table_for_current_lang = -1;         // 当前语言的动态表索引

// 查找语言表中的键
static const char* find_in_table(const lang_entry_t* table, const char* key) {
    if (!table || !key) return NULL;
    
    const lang_entry_t* entry = table;
    while (entry->key != NULL) {
        if (strcmp(entry->key, key) == 0) {
            return entry->value;
        }
        entry++;
    }
    
    return NULL;
}

// 查找动态语言资源表
static dynamic_lang_table_t* find_dynamic_lang(const char* lang_code) {
    for (int i = 0; i < dynamic_lang_count; i++) {
        if (strcmp(dynamic_langs[i].lang_code, lang_code) == 0) {
            return &dynamic_langs[i];
        }
    }
    return NULL;
}

// 查找动态语言表中的键
static const char* find_in_dynamic_table(dynamic_lang_table_t* table, const char* key) {
    if (!table || !key) return NULL;
    
    for (int i = 0; i < table->entry_count; i++) {
        if (strcmp(table->entries[i].key, key) == 0) {
            return table->entries[i].value;
        }
    }
    
    return NULL;
}

// 创建新的动态语言表
static dynamic_lang_table_t* create_dynamic_lang(const char* lang_code) {
    if (dynamic_lang_count >= MAX_DYNAMIC_LANGS) {
        fprintf(stderr, "[ERROR] Too many dynamic languages, limit is %d\n", MAX_DYNAMIC_LANGS);
        return NULL;
    }
    
    dynamic_lang_table_t* table = &dynamic_langs[dynamic_lang_count++];
    strncpy(table->lang_code, lang_code, sizeof(table->lang_code) - 1);
    table->lang_code[sizeof(table->lang_code) - 1] = '\0';
    table->entry_count = 0;
    table->keys_storage = NULL;
    table->values_storage = NULL;
    
    return table;
}

// 将键值对添加到动态语言表
static bool add_entry_to_dynamic_table(dynamic_lang_table_t* table, const char* key, const char* value) {
    if (table->entry_count >= MAX_ENTRIES_PER_LANG) {
        fprintf(stderr, "[ERROR] Too many entries for language %s, limit is %d\n", table->lang_code, MAX_ENTRIES_PER_LANG);
        return false;
    }
    
    // 分配和复制键值对
    size_t key_len = strlen(key);
    size_t value_len = strlen(value);
    
    char* new_keys = realloc(table->keys_storage, 
                            (table->keys_storage ? strlen(table->keys_storage) : 0) + key_len + 1);
    if (!new_keys) {
        fprintf(stderr, "[ERROR] Failed to allocate memory for keys\n");
        return false;
    }
    table->keys_storage = new_keys;
    
    char* new_values = realloc(table->values_storage,
                             (table->values_storage ? strlen(table->values_storage) : 0) + value_len + 1);
    if (!new_values) {
        fprintf(stderr, "[ERROR] Failed to allocate memory for values\n");
        return false;
    }
    table->values_storage = new_values;
    
    // 计算新键值位置
    char* key_pos = table->keys_storage;
    if (table->entry_count > 0) {
        key_pos += strlen(table->keys_storage);
    }
    
    char* value_pos = table->values_storage;
    if (table->entry_count > 0) {
        value_pos += strlen(table->values_storage);
    }
    
    // 复制键值
    strcpy(key_pos, key);
    strcpy(value_pos, value);
    
    // 更新条目
    table->entries[table->entry_count].key = key_pos;
    table->entries[table->entry_count].value = value_pos;
    table->entry_count++;
    
    return true;
}

// 解析YAML语言资源文件
static bool parse_yaml_lang_file(const char* file_path, dynamic_lang_table_t* table) {
    // 由于我们不想引入额外的YAML解析库依赖
    // 这里实现一个极其简单的YAML解析器，仅支持简单的键值对
    FILE* fp = fopen(file_path, "r");
    if (!fp) {
        fprintf(stderr, "[ERROR] Cannot open language file: %s\n", file_path);
        return false;
    }
    
    char line[1024];
    char current_section[256] = "";
    
    while (fgets(line, sizeof(line), fp)) {
        // 跳过空行和注释
        if (line[0] == '\n' || line[0] == '#') continue;
        
        // 检测缩进
        int indent = 0;
        while (line[indent] == ' ' || line[indent] == '\t') indent++;
        
        // 处理一级键（section）
        if (indent == 0) {
            char* colon = strchr(line, ':');
            if (colon) {
                *colon = '\0';
                strncpy(current_section, line, sizeof(current_section) - 1);
                current_section[sizeof(current_section) - 1] = '\0';
                
                // 移除可能的空格
                char* p = current_section;
                while (*p) {
                    if (*p == ' ' || *p == '\t') *p = '\0';
                    p++;
                }
            }
        }
        // 处理二级键（key-value）
        else if (indent > 0 && current_section[0] != '\0') {
            char* colon = strchr(line + indent, ':');
            if (colon) {
                *colon = '\0';
                
                char key[512];
                snprintf(key, sizeof(key), "%s.%s", current_section, line + indent);
                
                // 移除键中的空格
                char* p = key;
                while (*p) {
                    if (*p == ' ' || *p == '\t') *p = '\0';
                    p++;
                }
                
                // 提取值，跳过冒号和空格
                char* value = colon + 1;
                while (*value == ' ' || *value == '\t') value++;
                
                // 移除值末尾的换行符
                p = value;
                while (*p) {
                    if (*p == '\n') *p = '\0';
                    p++;
                }
                
                // 处理引号
                if (value[0] == '"' && value[strlen(value) - 1] == '"') {
                    value[strlen(value) - 1] = '\0';
                    value++;
                }
                
                // 添加到语言表
                add_entry_to_dynamic_table(table, key, value);
            }
        }
    }
    
    fclose(fp);
    return true;
}

// 从文件名推断语言代码
static void infer_lang_code_from_filename(const char* filename, char* lang_code, size_t max_len) {
    // 找到文件名部分（去除路径）
    const char* basename = strrchr(filename, '/');
    if (!basename) basename = filename;
    else basename++; // 跳过斜杠
    
    // 提取基本名称（去除扩展名）
    const char* dot = strchr(basename, '.');
    if (!dot) {
        strncpy(lang_code, basename, max_len - 1);
        lang_code[max_len - 1] = '\0';
        return;
    }
    
    size_t name_len = dot - basename;
    if (name_len >= max_len) name_len = max_len - 1;
    strncpy(lang_code, basename, name_len);
    lang_code[name_len] = '\0';
    
    // 处理以应用名称开头的情况（如"app_en.yaml"）
    char* underscore = strchr(lang_code, '_');
    if (underscore && *(underscore + 1)) {
        memmove(lang_code, underscore + 1, strlen(underscore));
    }
}

int lang_init(const char* default_lang) {
    if (!default_lang || !*default_lang) {
        default_lang = DEFAULT_LANG;
    }
    
    // 设置默认语言（fallback语言表）
    fallback_lang_table = get_lang_table(DEFAULT_LANG);
    if (!fallback_lang_table) {
        // 如果默认语言不可用，这是严重错误
        fprintf(stderr, "[ERROR] Cannot load default language: %s\n", DEFAULT_LANG);
        return -1;
    }
    
    // 尝试加载指定的默认语言
    const lang_entry_t* requested_lang_table = get_lang_table(default_lang);
    if (!requested_lang_table) {
        // 如果请求的语言不可用，使用内置默认语言
        fprintf(stderr, "[WARN] Requested language '%s' not available, using '%s'\n", 
                default_lang, DEFAULT_LANG);
        current_lang_table = fallback_lang_table;
        strcpy(current_lang_code, DEFAULT_LANG);
    } else {
        // 如果请求的语言可用，直接设置
        current_lang_table = requested_lang_table;
        strncpy(current_lang_code, default_lang, sizeof(current_lang_code) - 1);
        current_lang_code[sizeof(current_lang_code) - 1] = '\0';
    }
    
    // 执行自动发现
    lang_auto_discover_resources();
    
    return 0;
}

bool lang_set_language(const char* lang_code) {
    if (!lang_code || !*lang_code) return false;
    
    // 检查是否已经是当前语言
    if (strcmp(current_lang_code, lang_code) == 0) {
        return true; // 已经是请求的语言
    }
    
    // 首先尝试获取内置语言表
    const lang_entry_t* table = get_lang_table(lang_code);
    if (table) {
        // 更新当前语言
        current_lang_table = table;
        strncpy(current_lang_code, lang_code, sizeof(current_lang_code) - 1);
        current_lang_code[sizeof(current_lang_code) - 1] = '\0';
        dynamic_table_for_current_lang = -1; // 使用内置表，重置动态表索引
        return true;
    }
    
    // 如果内置表不存在，检查动态加载的表
    dynamic_lang_table_t* dynamic_table = find_dynamic_lang(lang_code);
    if (dynamic_table) {
        // 更新当前语言为动态表
        strncpy(current_lang_code, lang_code, sizeof(current_lang_code) - 1);
        current_lang_code[sizeof(current_lang_code) - 1] = '\0';
        current_lang_table = NULL; // 不使用内置表
        dynamic_table_for_current_lang = dynamic_table - dynamic_langs; // 计算表索引
        return true;
    }
    
    fprintf(stderr, "[ERROR] Failed to switch language to %s\n", lang_code);
    return false;
}

const char* lang_get(const char* key) {
    if (!key || !*key) return NULL;
    
    // 首先查找当前语言表
    const char* value = NULL;
    
    // 如果当前使用的是动态表
    if (dynamic_table_for_current_lang >= 0) {
        value = find_in_dynamic_table(&dynamic_langs[dynamic_table_for_current_lang], key);
    }
    // 否则使用内置表
    else if (current_lang_table) {
        value = find_in_table(current_lang_table, key);
    }
    
    // 如果当前语言找不到，检查是否有动态加载的表补充
    if (!value && current_lang_table) {
        dynamic_lang_table_t* dynamic_table = find_dynamic_lang(current_lang_code);
        if (dynamic_table) {
            value = find_in_dynamic_table(dynamic_table, key);
        }
    }
    
    // 如果在当前语言找不到并且有默认语言，从默认语言查找
    if (!value && fallback_lang_table && 
        (current_lang_table != fallback_lang_table || dynamic_table_for_current_lang >= 0)) {
        value = find_in_table(fallback_lang_table, key);
        if (value) {
            fprintf(stderr, "[WARN] Language key not found in '%s': %s, using default language\n", 
                    current_lang_code, key);
        } else {
            // 也尝试在默认语言的动态表中查找
            dynamic_lang_table_t* dynamic_table = find_dynamic_lang(DEFAULT_LANG);
            if (dynamic_table) {
                value = find_in_dynamic_table(dynamic_table, key);
            }
        }
    }
    
    // 如果在默认语言也找不到，返回错误信息
    if (!value) {
        fprintf(stderr, "[WARN] Language key not found: %s\n", key);
        return "Unknown Error";
    }
    
    return value;
}

char* lang_getf(const char* key, ...) {
    const char* template = lang_get(key);
    if (!template) return NULL;
    
    va_list args;
    va_start(args, key);
    
    // 计算所需缓冲区大小
    va_list args_copy;
    va_copy(args_copy, args);
    int size = vsnprintf(NULL, 0, template, args_copy) + 1;
    va_end(args_copy);
    
    if (size <= 0) {
        fprintf(stderr, "[WARN] Format failed for key: %s\n", key);
        va_end(args);
        return strdup("[FORMAT ERROR: Check argument count and types!]");
    }
    
    // 分配缓冲区
    char* buffer = (char*)malloc(size);
    if (!buffer) {
        va_end(args);
        return NULL;
    }
    
    // 执行格式化
    vsnprintf(buffer, size, template, args);
    va_end(args);
    
    return buffer;
}

const char* lang_get_current() {
    return current_lang_code;
}

void lang_cleanup() {
    // 释放动态分配的资源
    for (int i = 0; i < dynamic_lang_count; i++) {
        free(dynamic_langs[i].keys_storage);
        free(dynamic_langs[i].values_storage);
    }
    
    // 重置状态
    dynamic_lang_count = 0;
    current_lang_table = NULL;
    fallback_lang_table = NULL;
    dynamic_table_for_current_lang = -1;
}

bool lang_register_file(const char* file_path, const char* lang_code) {
    if (!file_path || !*file_path) {
        fprintf(stderr, "[ERROR] Invalid file path for language resource\n");
        return false;
    }
    
    // 检查文件是否存在
    if (access(file_path, R_OK) != 0) {
        fprintf(stderr, "[ERROR] Cannot access language file: %s\n", file_path);
        return false;
    }
    
    char inferred_lang_code[16] = {0};
    
    // 如果没有提供语言代码，从文件名推断
    if (!lang_code || !*lang_code) {
        infer_lang_code_from_filename(file_path, inferred_lang_code, sizeof(inferred_lang_code));
        lang_code = inferred_lang_code;
    }
    
    if (!lang_code || !*lang_code) {
        fprintf(stderr, "[ERROR] Cannot determine language code for file: %s\n", file_path);
        return false;
    }
    
    // 检查是否已存在该语言的动态表
    dynamic_lang_table_t* table = find_dynamic_lang(lang_code);
    if (!table) {
        // 创建新表
        table = create_dynamic_lang(lang_code);
        if (!table) return false;
    }
    
    // 解析并加载语言文件
    return parse_yaml_lang_file(file_path, table);
}

int lang_scan_directory(const char* dir_path, const char* pattern) {
    if (!dir_path || !*dir_path) {
        fprintf(stderr, "[ERROR] Invalid directory path for language resources\n");
        return 0;
    }
    
    DIR* dir = opendir(dir_path);
    if (!dir) {
        fprintf(stderr, "[WARN] Cannot open directory: %s\n", dir_path);
        return 0;
    }
    
    int count = 0;
    struct dirent* entry;
    
    while ((entry = readdir(dir)) != NULL) {
        // 跳过特殊目录
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0)
            continue;
        
        // 简单模式匹配
        if (pattern && *pattern) {
            // 极其简单的通配符匹配，仅支持*.yaml格式
            if (strstr(pattern, "*.") != NULL) {
                const char* ext = strrchr(pattern, '.');
                if (ext) {
                    ext++; // 跳过点
                    const char* file_ext = strrchr(entry->d_name, '.');
                    if (!file_ext || strcmp(file_ext + 1, ext) != 0)
                        continue;
                }
            }
        }
        
        // 构建完整路径
        char full_path[1024];
        snprintf(full_path, sizeof(full_path), "%s/%s", dir_path, entry->d_name);
        
        // 检查是否是普通文件
        struct stat st;
        if (stat(full_path, &st) == 0 && S_ISREG(st.st_mode)) {
            // 尝试注册语言文件
            if (lang_register_file(full_path, NULL)) {
                count++;
            }
        }
    }
    
    closedir(dir);
    return count;
}

int lang_scan_directory_with_glob(const char* glob_pattern) {
    if (!glob_pattern || !*glob_pattern) {
        fprintf(stderr, "[ERROR] Invalid glob pattern for language resources\n");
        return 0;
    }
    
    glob_t globbuf;
    int result = glob(glob_pattern, GLOB_TILDE, NULL, &globbuf);
    if (result != 0) {
        if (result == GLOB_NOMATCH) {
            return 0; // 没有匹配项，正常返回
        }
        fprintf(stderr, "[ERROR] Glob pattern matching failed: %s\n", glob_pattern);
        return 0;
    }
    
    int count = 0;
    for (size_t i = 0; i < globbuf.gl_pathc; i++) {
        // 检查是否是普通文件
        struct stat st;
        if (stat(globbuf.gl_pathv[i], &st) == 0 && S_ISREG(st.st_mode)) {
            // 尝试注册语言文件
            if (lang_register_file(globbuf.gl_pathv[i], NULL)) {
                count++;
            }
        }
    }
    
    globfree(&globbuf);
    return count;
}

bool lang_auto_discover_resources(void) {
    int found = 0;
    
    // 1. 检查当前工作目录/locales
    found += lang_scan_directory("./locales", "*.yaml");
    
    // 2. 检查配置中定义的路径 (这里需要从配置模块获取，暂时略过)
    // const char** paths = config_get_locale_paths();
    // if (paths) {
    //     for (int i = 0; paths[i]; i++) {
    //         found += lang_scan_directory_with_glob(paths[i]);
    //     }
    // }
    
    // 3. 检查系统应用配置目录 (简化实现)
    char app_config_path[1024] = {0};
    const char* home = getenv("HOME");
    if (home) {
        snprintf(app_config_path, sizeof(app_config_path), "%s/.config/logloom/locales", home);
        found += lang_scan_directory(app_config_path, "*.yaml");
    }
    
    return found > 0;
}

char** lang_get_supported_languages(int* count) {
    if (!count) return NULL;
    
    // 首先计算内置语言和动态语言的总数
    int builtin_count = get_language_count();
    int total_count = builtin_count + dynamic_lang_count;
    
    if (total_count == 0) {
        *count = 0;
        return NULL;
    }
    
    // 分配返回数组
    char** languages = (char**)malloc((total_count + 1) * sizeof(char*));
    if (!languages) {
        *count = 0;
        return NULL;
    }
    
    // 防止重复，使用简单的标记数组
    char used_langs[128][16] = {{0}};
    int unique_count = 0;
    
    // 添加内置语言
    for (int i = 0; i < builtin_count; i++) {
        const char* lang = get_language_code(i);
        if (lang) {
            // 检查是否已添加
            bool already_added = false;
            for (int j = 0; j < unique_count; j++) {
                if (strcmp(used_langs[j], lang) == 0) {
                    already_added = true;
                    break;
                }
            }
            
            if (!already_added && unique_count < 128) {
                strncpy(used_langs[unique_count], lang, 15);
                used_langs[unique_count][15] = '\0';
                languages[unique_count] = strdup(lang);
                unique_count++;
            }
        }
    }
    
    // 添加动态加载的语言
    for (int i = 0; i < dynamic_lang_count; i++) {
        const char* lang = dynamic_langs[i].lang_code;
        
        // 检查是否已添加
        bool already_added = false;
        for (int j = 0; j < unique_count; j++) {
            if (strcmp(used_langs[j], lang) == 0) {
                already_added = true;
                break;
            }
        }
        
        if (!already_added && unique_count < 128) {
            strncpy(used_langs[unique_count], lang, 15);
            used_langs[unique_count][15] = '\0';
            languages[unique_count] = strdup(lang);
            unique_count++;
        }
    }
    
    // 设置NULL结束符
    languages[unique_count] = NULL;
    *count = unique_count;
    
    return languages;
}

char** lang_get_language_keys(const char* lang_code, int* count) {
    if (!count) return NULL;
    
    // 如果没有提供语言代码，使用当前语言
    if (!lang_code || !*lang_code) {
        lang_code = current_lang_code;
    }
    
    // 先检查是否有内置表
    const lang_entry_t* builtin_table = get_lang_table(lang_code);
    
    // 检查是否有动态加载的表
    dynamic_lang_table_t* dynamic_table = find_dynamic_lang(lang_code);
    
    // 如果两者都没有，返回NULL
    if (!builtin_table && !dynamic_table) {
        *count = 0;
        return NULL;
    }
    
    // 计算键的总数
    int key_count = 0;
    if (builtin_table) {
        const lang_entry_t* entry = builtin_table;
        while (entry->key != NULL) {
            key_count++;
            entry++;
        }
    }
    
    if (dynamic_table) {
        key_count += dynamic_table->entry_count;
    }
    
    if (key_count == 0) {
        *count = 0;
        return NULL;
    }
    
    // 分配返回数组
    char** keys = (char**)malloc((key_count + 1) * sizeof(char*));
    if (!keys) {
        *count = 0;
        return NULL;
    }
    
    // 收集所有键，同时检查重复
    int unique_count = 0;
    char** used_keys = (char**)malloc(key_count * sizeof(char*));
    if (!used_keys) {
        free(keys);
        *count = 0;
        return NULL;
    }
    
    // 添加内置表的键
    if (builtin_table) {
        const lang_entry_t* entry = builtin_table;
        while (entry->key != NULL) {
            // 检查是否已添加
            bool already_added = false;
            for (int j = 0; j < unique_count; j++) {
                if (strcmp(used_keys[j], entry->key) == 0) {
                    already_added = true;
                    break;
                }
            }
            
            if (!already_added) {
                used_keys[unique_count] = (char*)entry->key;
                keys[unique_count] = strdup(entry->key);
                unique_count++;
            }
            
            entry++;
        }
    }
    
    // 添加动态表的键
    if (dynamic_table) {
        for (int i = 0; i < dynamic_table->entry_count; i++) {
            const char* key = dynamic_table->entries[i].key;
            
            // 检查是否已添加
            bool already_added = false;
            for (int j = 0; j < unique_count; j++) {
                if (strcmp(used_keys[j], key) == 0) {
                    already_added = true;
                    break;
                }
            }
            
            if (!already_added) {
                used_keys[unique_count] = (char*)key;
                keys[unique_count] = strdup(key);
                unique_count++;
            }
        }
    }
    
    // 设置NULL结束符
    keys[unique_count] = NULL;
    *count = unique_count;
    
    // 释放临时数组
    free(used_keys);
    
    return keys;
}
