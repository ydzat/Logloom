#ifndef LOGLOOM_LOG_H
#define LOGLOOM_LOG_H

#include <stdbool.h>
#include <stddef.h>

// 日志级别定义
typedef enum {
    LOG_LEVEL_DEBUG = 0,
    LOG_LEVEL_INFO  = 1,
    LOG_LEVEL_WARN  = 2,
    LOG_LEVEL_ERROR = 3
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
 * @param level 初始日志级别
 * @param console_enabled 是否启用控制台输出
 * @return 成功返回0，失败返回错误码
 */
int log_init(log_level_t level, bool console_enabled);

/**
 * 设置日志输出文件
 * @param filepath 日志文件路径，NULL表示禁用文件输出
 * @return 成功返回true，失败返回false
 */
bool log_set_output_file(const char* filepath);

/**
 * 设置日志级别
 * @param level 新的日志级别
 */
void log_set_level(log_level_t level);

/**
 * 开启/关闭控制台输出
 * @param enabled 是否启用控制台输出
 */
void log_set_output_console(bool enabled);

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
 * @param fmt 格式字符串
 * @param ... 格式化参数
 */
void log_debug(const char* module, const char* fmt, ...);

/**
 * 信息级别日志
 * @param module 模块名称
 * @param fmt 格式字符串
 * @param ... 格式化参数
 */
void log_info(const char* module, const char* fmt, ...);

/**
 * 警告级别日志
 * @param module 模块名称
 * @param fmt 格式字符串
 * @param ... 格式化参数
 */
void log_warn(const char* module, const char* fmt, ...);

/**
 * 错误级别日志
 * @param module 模块名称
 * @param fmt 格式字符串
 * @param ... 格式化参数
 */
void log_error(const char* module, const char* fmt, ...);

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
log_level_t log_get_level(void);

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
