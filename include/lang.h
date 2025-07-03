#ifndef LOGLOOM_LANG_H
#define LOGLOOM_LANG_H

#include <stdarg.h>  // 用于变参函数
#include <stdbool.h> // 用于布尔类型

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

/**
 * 注册额外的语言资源文件
 * @param file_path YAML语言资源文件的路径
 * @param lang_code 语言代码，如"en", "zh"，如果为NULL，则从文件名推断
 * @return 成功返回true，失败返回false
 */
bool lang_register_file(const char* file_path, const char* lang_code);

/**
 * 注册目录中所有匹配模式的语言资源文件
 * @param dir_path 包含语言资源文件的目录路径
 * @param pattern 文件匹配模式（如"*.yaml"）
 * @return 成功注册的文件数量
 */
int lang_scan_directory(const char* dir_path, const char* pattern);

/**
 * 扩展版的目录扫描函数，支持glob模式匹配
 * @param glob_pattern 路径glob模式（如"./locales/*.yaml"）
 * @return 成功注册的文件数量
 */
int lang_scan_directory_with_glob(const char* glob_pattern);

/**
 * 自动发现并加载语言资源文件
 * 会检查当前工作目录、配置指定路径和用户应用配置目录
 * @return 找到并加载资源返回true，否则返回false
 */
bool lang_auto_discover_resources(void);

/**
 * 获取当前支持的所有语言代码列表
 * @param count 输出参数，用于存储语言数量
 * @return 语言代码字符串数组，使用后需调用free()释放
 */
char** lang_get_supported_languages(int* count);

/**
 * 获取指定语言中所有可用的翻译键列表
 * @param lang_code 语言代码，如果为NULL则使用当前语言
 * @param count 输出参数，用于存储键数量
 * @return 翻译键字符串数组，使用后需调用free()释放
 */
char** lang_get_language_keys(const char* lang_code, int* count);

#endif // LOGLOOM_LANG_H
