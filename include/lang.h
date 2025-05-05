#ifndef LOGLOOM_LANG_H
#define LOGLOOM_LANG_H

#include <stdarg.h>  // 用于变参函数
#include <stdbool.h> // 用于布尔类型

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
 * @return 动态分配的格式化后字符串，使用后需调用 free() 释放
 */
char* lang_getf(const char* key, ...);

/**
 * 获取当前语言代码
 * @return 当前语言代码字符串
 */
const char* lang_get_current();

/**
 * 清理语言模块资源
 */
void lang_cleanup();

#endif // LOGLOOM_LANG_H
