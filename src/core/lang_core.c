#ifdef __KERNEL__
/* 内核环境 */
#include <linux/string.h>
#include <linux/kernel.h>
#else
/* 用户态环境 */
#include <string.h>
#include <assert.h>
#endif

#include "lang.h"
#include "../shared/platform.h"

/**
 * 默认语言代码
 */
static const char* default_lang_code = "en";

/**
 * 获取默认语言代码
 * @return 默认语言代码字符串
 */
const char* lang_get_default_code(void) {
    return default_lang_code;
}

/**
 * 在语言表中查找指定键的值
 * @param table 语言表
 * @param key 查找的键
 * @return 找到的值，未找到则返回NULL
 */
const char* lang_find_in_table(const lang_entry_t* table, const char* key) {
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