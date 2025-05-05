#ifndef LOGLOOM_KERNEL_LOG_H
#define LOGLOOM_KERNEL_LOG_H

#ifdef __KERNEL__
/* 内核环境 */
#include <linux/types.h>
#include <linux/string.h>
#include <linux/kernel.h>
#include <linux/module.h>
typedef _Bool bool;
#define true 1
#define false 0
#else
/* 用户态环境 */
#include <stdbool.h>
#include <stddef.h>
#endif

// 日志级别定义
typedef enum {
    LOG_LEVEL_DEBUG = 0,
    LOG_LEVEL_INFO  = 1,
    LOG_LEVEL_WARN  = 2,
    LOG_LEVEL_ERROR = 3,
    LOG_LEVEL_FATAL = 4
} log_level_t;

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
 * 设置日志文件最大大小
 * @param max_size 日志文件最大大小（字节）
 */
void log_set_max_file_size(size_t max_size);

/**
 * 获取日志锁
 * 多线程环境下使用，确保日志操作的原子性
 */
void log_lock(void);

/**
 * 释放日志锁
 * 与log_lock配对使用
 */
void log_unlock(void);

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
 * 获取当前日志级别
 * @return 当前日志级别
 */
int log_get_level(void);

/**
 * 检查当前级别是否应该记录日志
 * @param level 要检查的日志级别
 * @return 如果需要记录返回非零，否则返回0
 */
int log_should_log(int level);

/**
 * 格式化日志消息
 * @param buffer 输出缓冲区
 * @param buffer_size 缓冲区大小
 * @param level 日志级别
 * @param module 模块名称
 * @param format 格式字符串
 * @param args 可变参数列表
 */
void log_format_message(char* buffer, size_t buffer_size, int level, 
                        const char* module, const char* format, va_list args);

/**
 * 清理日志系统资源
 */
void log_cleanup(void);

#endif /* LOGLOOM_KERNEL_LOG_H */