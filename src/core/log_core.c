#include "log.h"
#include "../shared/platform.h"

#ifdef __KERNEL__
/* 内核环境 */
#include <linux/stdarg.h>
#include <linux/time.h>
#include <linux/timekeeping.h>
#else
/* 用户态环境 */
#include <stdarg.h>
#include <time.h>
#endif

// 日志级别枚举到字符串的映射
static const char* log_level_names[] = {
    "DEBUG", "INFO", "WARN", "ERROR", "FATAL"
};

// 全局日志级别，默认为INFO
static int g_log_level = LOG_LEVEL_INFO;

// 将字符串日志级别转换为枚举值
int log_level_from_string(const char* level) {
    if (!level) return LOG_LEVEL_INFO;
    
    for (int i = 0; i <= LOG_LEVEL_FATAL; i++) {
#ifdef __KERNEL__
        /* 在内核中使用strncasecmp替代strcasecmp */
        if (strncasecmp(level, log_level_names[i], strlen(log_level_names[i])) == 0) {
#else
        if (strcasecmp(level, log_level_names[i]) == 0) {
#endif
            return i;
        }
    }
    
    return LOG_LEVEL_INFO;  // 默认为INFO
}

// 获取当前日志级别名称
const char* log_level_to_string(int level) {
    if (level < LOG_LEVEL_DEBUG || level > LOG_LEVEL_FATAL) {
        return log_level_names[LOG_LEVEL_INFO];
    }
    return log_level_names[level];
}

// 获取当前日志级别的字符串表示
const char* log_get_level_string(void) {
    return log_level_to_string(g_log_level);
}

// 设置当前日志级别
void log_set_level(const char* level) {
    g_log_level = log_level_from_string(level);
}

// 获取当前日志级别
int log_get_level(void) {
    return g_log_level;
}

// 格式化日志消息（核心功能，被其他日志函数调用）
void log_format_message(char* buffer, size_t buffer_size, int level, 
                        const char* module, const char* format, va_list args) {
#ifdef __KERNEL__
    /* 内核环境下的时间处理 */
    struct timespec64 ts;
    struct tm tm;
    
    ktime_get_real_ts64(&ts);
    time64_to_tm(ts.tv_sec, 0, &tm);
    
    // 先写入时间和元数据
    int header_len = snprintf(buffer, buffer_size,
                             "[%04ld-%02d-%02d %02d:%02d:%02d][%s][%s] ",
                             tm.tm_year + 1900,
                             tm.tm_mon + 1,
                             tm.tm_mday,
                             tm.tm_hour,
                             tm.tm_min,
                             tm.tm_sec,
                             log_level_names[level],
                             module ? module : "SYSTEM");
#else
    /* 用户态环境下的时间处理 */
    time_t now = time(NULL);
    struct tm* time_info = localtime(&now);
    
    // 先写入时间和元数据
    int header_len = snprintf(buffer, buffer_size,
                             "[%04d-%02d-%02d %02d:%02d:%02d][%s][%s] ",
                             time_info->tm_year + 1900,
                             time_info->tm_mon + 1,
                             time_info->tm_mday,
                             time_info->tm_hour,
                             time_info->tm_min,
                             time_info->tm_sec,
                             log_level_names[level],
                             module ? module : "SYSTEM");
#endif
    
    // 检查是否有足够空间写入消息内容
    if (header_len < (int)buffer_size) {
        vsnprintf(buffer + header_len, buffer_size - header_len, format, args);
    }
}

// 检查日志级别是否应该被记录
int log_should_log(int level) {
    return level >= g_log_level;
}