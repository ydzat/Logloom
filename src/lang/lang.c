#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include "lang.h"
#include "generated/lang_registry.h"

// 当前语言上下文
static const lang_entry_t* current_lang_table = NULL;
static const lang_entry_t* fallback_lang_table = NULL; // 默认语言表
static char current_lang_code[8] = "en";  // 当前语言代码
static const char* DEFAULT_LANG = "en";   // 默认语言代码

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
    
    return 0;
}

bool lang_set_language(const char* lang_code) {
    if (!lang_code || !*lang_code) return false;
    
    // 检查是否已经是当前语言
    if (strcmp(current_lang_code, lang_code) == 0) {
        return true; // 已经是请求的语言
    }
    
    // 尝试获取语言表
    const lang_entry_t* table = get_lang_table(lang_code);
    if (!table) {
        fprintf(stderr, "[ERROR] Failed to switch language to %s\n", lang_code);
        return false;
    }
    
    // 更新当前语言
    current_lang_table = table;
    strncpy(current_lang_code, lang_code, sizeof(current_lang_code) - 1);
    current_lang_code[sizeof(current_lang_code) - 1] = '\0';
    
    return true;
}

const char* lang_get(const char* key) {
    if (!key || !*key) return NULL;
    
    // 从当前语言查找
    const char* value = NULL;
    if (current_lang_table) {
        value = find_in_table(current_lang_table, key);
    }
    
    // 如果在当前语言找不到并且有默认语言，从默认语言查找
    if (!value && fallback_lang_table && current_lang_table != fallback_lang_table) {
        value = find_in_table(fallback_lang_table, key);
        if (value) {
            fprintf(stderr, "[WARN] Language key not found in '%s': %s, using default language\n", 
                    current_lang_code, key);
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
    // 在当前实现中无需清理资源
    // 所有语言表都是静态分配的
    current_lang_table = NULL;
    fallback_lang_table = NULL;
}
