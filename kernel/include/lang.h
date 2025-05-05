#ifndef LOGLOOM_KERNEL_LANG_H
#define LOGLOOM_KERNEL_LANG_H

#ifdef __KERNEL__
/* 内核环境 */
#include <linux/types.h>
#include <linux/string.h>
#include <linux/kernel.h>
typedef _Bool bool;
#define true 1
#define false 0
#else
/* 用户态环境 */
#include <stdbool.h>
#include <stdarg.h>
#endif

/**
 * 语言表项结构
 */
typedef struct {
    const char* key;   // 语言键
    const char* value; // 翻译文本
} lang_entry_t;

/**
 * 初始化语言模块
 * @param default_lang 默认语言代码，如 "en", "zh"
 * @return 成功返回0，失败返回错误码
 */
int lang_init(const char* default_lang);

/**
 * 设置当前语言
 * @param lang_code 语言代码，如 "en", "zh"
 * @return 成功返回true，失败返回false
 */
bool lang_set_language(const char* lang_code);

/**
 * 获取不带格式化的文本
 * @param key 语言键，如 "system.start_message"
 * @return 对应的语言文本，如果未找到则返回NULL
 */
const char* lang_get(const char* key);

/**
 * 获取格式化后的文本，类似printf
 * @param key 语言键
 * @param ... 格式化参数
 * @return 动态分配的格式化后字符串，使用后需调用释放
 */
char* lang_getf(const char* key, ...);

/**
 * 获取当前语言代码
 * @return 当前语言代码字符串
 */
const char* lang_get_current(void);

/**
 * 清理语言模块资源
 */
void lang_cleanup(void);

/**
 * 在语言表中查找指定键的值
 * @param table 语言表
 * @param key 查找的键
 * @return 找到的值，未找到则返回NULL
 */
const char* lang_find_in_table(const lang_entry_t* table, const char* key);

/**
 * 获取默认语言代码
 * @return 默认语言代码字符串
 */
const char* lang_get_default_code(void);

#endif /* LOGLOOM_KERNEL_LANG_H */