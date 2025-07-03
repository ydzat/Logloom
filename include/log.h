#ifndef LOGLOOM_LOG_H
#define LOGLOOM_LOG_H

#include <stdbool.h>
#include <stddef.h>

// 日志级别定义
typedef enum {
    LOG_LEVEL_DEBUG = 0,
    LOG_LEVEL_INFO  = 1,
    LOG_LEVEL_WARN  = 2,
    LOG_LEVEL_ERROR = 3,
    LOG_LEVEL_FATAL = 4
} log_level_t;

// 日志条目结构
typedef struct {
    unsigned long timestamp;  // Unix 时间戳
    log_level_t level;        // 日志级别
    const char* module;       // 模块名称
    const char* message;      // 日志消息
    const char* lang_key;     // 对应的语言键（可选）
} log_entry_t;

/**
 * 初始化日志系统
 * @param level 初始日志级别字符串 ("DEBUG", "INFO", "WARN", "ERROR", "FATAL")
 * @param log_file 日志文件路径，NULL表示不输出到文件
 * @return 成功返回0，失败返回错误码
 */
int log_init(const char* level, const char* log_file);

/**
 * 设置日志输出文件
 * @param filepath 日志文件路径，NULL表示禁用文件输出
 * @return 成功返回true，失败返回false
 */
void log_set_file(const char* filepath);

/**
 * 设置日志级别
 * @param level 新的日志级别字符串 ("DEBUG", "INFO", "WARN", "ERROR", "FATAL")
 */
void log_set_level(const char* level);

/**
 * 从字符串获取日志级别枚举值
 * @param level 日志级别字符串
 * @return 对应的日志级别枚举值
 */
int log_level_from_string(const char* level);

/**
 * 将日志级别枚举值转换为字符串
 * @param level 日志级别枚举值
 * @return 对应的日志级别字符串
 */
const char* log_level_to_string(int level);

/**
 * 获取当前日志级别的字符串表示
 * @return 当前日志级别字符串
 */
const char* log_get_level_string(void);

/**
 * 开启/关闭控制台输出
 * @param enabled 是否启用控制台输出 (0=禁用, 1=启用)
 */
void log_set_console_enabled(int enabled);

/**
 * 设置最大日志文件大小（超过后自动轮转）
 * @param max_bytes 最大字节数
 */
void log_set_max_file_size(size_t max_bytes);

/**
 * 设置最大历史日志文件数量
 * @param count 最大历史文件数量
 */
void log_set_max_backup_files(size_t count);

/**
 * 获取最大历史日志文件数量
 * @return 最大历史文件数量
 */
size_t log_get_max_backup_files(void);

/**
 * 手动触发日志文件轮转
 * @return 成功返回true，失败返回false
 */
bool log_rotate_now(void);

/**
 * 调试级别日志
 * @param module 模块名称
 * @param format 格式字符串
 * @param ... 格式化参数
 */
void log_debug(const char* module, const char* format, ...);

/**
 * 信息级别日志
 * @param module 模块名称
 * @param format 格式字符串
 * @param ... 格式化参数
 */
void log_info(const char* module, const char* format, ...);

/**
 * 警告级别日志
 * @param module 模块名称
 * @param format 格式字符串
 * @param ... 格式化参数
 */
void log_warn(const char* module, const char* format, ...);

/**
 * 错误级别日志
 * @param module 模块名称
 * @param format 格式字符串
 * @param ... 格式化参数
 */
void log_error(const char* module, const char* format, ...);

/**
 * 严重错误级别日志
 * @param module 模块名称
 * @param format 格式字符串
 * @param ... 格式化参数
 */
void log_fatal(const char* module, const char* format, ...);

/**
 * 使用语言键输出日志（支持国际化）
 * @param level 日志级别
 * @param module 模块名称
 * @param lang_key 语言键
 * @param ... 格式化参数
 */
void log_with_lang(log_level_t level, const char* module, const char* lang_key, ...);

/**
 * 获取当前日志级别
 * @return 当前日志级别
 */
int log_get_level(void);

/**
 * 检查控制台输出是否启用
 * @return 如果启用返回true
 */
bool log_is_console_enabled(void);

/**
 * 获取当前日志文件路径
 * @return 日志文件路径，如果未设置则返回NULL
 */
const char* log_get_file_path(void);

/**
 * 获取最大日志文件大小
 * @return 最大日志文件大小（字节）
 */
size_t log_get_max_file_size(void);

/**
 * 清理日志系统资源
 */
void log_cleanup(void);

/**
 * 显式加锁日志系统（用于连续多条日志或事务）
 */
void log_lock(void);

/**
 * 解锁日志系统
 */
void log_unlock(void);

#endif // LOGLOOM_LOG_H
