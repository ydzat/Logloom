#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <time.h>
#include <pthread.h>
#include <sys/stat.h>
#include <errno.h>

#include "log.h"
#include "lang.h"

// 声明rotate.c中的函数
extern FILE* check_and_rotate_log_file(const char* log_file_path, FILE* log_file, size_t max_size);
extern FILE* rotate_log_file(const char* log_file_path, FILE* log_file);

// 日志系统配置
static struct {
    log_level_t level;         // 当前日志级别
    bool console_enabled;      // 是否输出到控制台
    FILE* log_file;            // 日志文件句柄
    char* log_file_path;       // 日志文件路径
    size_t max_file_size;      // 最大文件大小
    pthread_mutex_t lock;      // 线程锁
    bool initialized;          // 是否已初始化
} log_ctx = {
    .level = LOG_LEVEL_INFO,
    .console_enabled = true,
    .log_file = NULL,
    .log_file_path = NULL,
    .max_file_size = 10*1024*1024,  // 默认10MB
    .initialized = false
};

// 日志级别对应的名称
static const char* log_level_names[] = {
    "DEBUG", "INFO", "WARN", "ERROR"
};

// 日志级别对应的颜色代码（ANSI）
static const char* log_level_colors[] = {
    "\x1B[36m", "\x1B[32m", "\x1B[33m", "\x1B[31m"
};

// 重置颜色
static const char* reset_color = "\x1B[0m";

// 格式化时间字符串
static void format_time(char* buffer, size_t size) {
    time_t now = time(NULL);
    struct tm* tm_info = localtime(&now);
    strftime(buffer, size, "%Y-%m-%d %H:%M:%S", tm_info);
}

// 检查文件大小并轮转（如果需要）
static void check_and_rotate_log(void) {
    if (!log_ctx.log_file || !log_ctx.log_file_path || log_ctx.max_file_size <= 0) {
        return;
    }
    
    // 调用rotate.c中的函数执行日志轮转
    FILE* new_file = check_and_rotate_log_file(
        log_ctx.log_file_path, 
        log_ctx.log_file, 
        log_ctx.max_file_size
    );
    
    // 如果文件指针发生变化，更新上下文
    if (new_file != log_ctx.log_file) {
        log_ctx.log_file = new_file;
    }
}

int log_init(log_level_t level, bool console_enabled) {
    if (log_ctx.initialized) {
        // 已经初始化，忽略
        return 0;
    }
    
    log_ctx.level = level;
    log_ctx.console_enabled = console_enabled;
    
    // 初始化互斥锁
    if (pthread_mutex_init(&log_ctx.lock, NULL) != 0) {
        fprintf(stderr, "Failed to initialize log mutex\n");
        return -1;
    }
    
    log_ctx.initialized = true;
    return 0;
}

bool log_set_output_file(const char* filepath) {
    pthread_mutex_lock(&log_ctx.lock);
    
    // 如果已有打开的文件，先关闭
    if (log_ctx.log_file) {
        fclose(log_ctx.log_file);
        log_ctx.log_file = NULL;
    }
    
    // 如果之前有文件路径，释放内存
    if (log_ctx.log_file_path) {
        free(log_ctx.log_file_path);
        log_ctx.log_file_path = NULL;
    }
    
    // 如果filepath为NULL，则禁用文件输出
    if (!filepath) {
        pthread_mutex_unlock(&log_ctx.lock);
        return true;
    }
    
    // 保存新路径
    log_ctx.log_file_path = strdup(filepath);
    if (!log_ctx.log_file_path) {
        pthread_mutex_unlock(&log_ctx.lock);
        return false;
    }
    
    // 打开日志文件（追加模式）
    log_ctx.log_file = fopen(filepath, "a");
    if (!log_ctx.log_file) {
        free(log_ctx.log_file_path);
        log_ctx.log_file_path = NULL;
        pthread_mutex_unlock(&log_ctx.lock);
        return false;
    }
    
    pthread_mutex_unlock(&log_ctx.lock);
    return true;
}

void log_set_level(log_level_t level) {
    pthread_mutex_lock(&log_ctx.lock);
    log_ctx.level = level;
    pthread_mutex_unlock(&log_ctx.lock);
}

void log_set_output_console(bool enabled) {
    pthread_mutex_lock(&log_ctx.lock);
    log_ctx.console_enabled = enabled;
    pthread_mutex_unlock(&log_ctx.lock);
}

void log_set_max_file_size(size_t max_bytes) {
    pthread_mutex_lock(&log_ctx.lock);
    log_ctx.max_file_size = max_bytes;
    pthread_mutex_unlock(&log_ctx.lock);
}

size_t log_get_max_file_size(void) {
    return log_ctx.max_file_size;
}

// 设置最大历史日志文件数量
void log_set_max_backup_files(size_t count) {
    // 直接调用rotate.c中的函数，使用不同的符号名避免递归
    extern void log_set_max_backup_files_impl(size_t count);
    log_set_max_backup_files_impl(count);
}

// 获取最大历史日志文件数量
size_t log_get_max_backup_files(void) {
    // 直接调用rotate.c中的函数，使用不同的符号名避免递归
    extern size_t log_get_max_backup_files_impl(void);
    return log_get_max_backup_files_impl();
}

bool log_rotate_now(void) {
    bool success = false;
    
    pthread_mutex_lock(&log_ctx.lock);
    
    if (log_ctx.log_file && log_ctx.log_file_path) {
        FILE* new_file = rotate_log_file(log_ctx.log_file_path, log_ctx.log_file);
        if (new_file) {
            log_ctx.log_file = new_file;
            success = true;
        }
    }
    
    pthread_mutex_unlock(&log_ctx.lock);
    return success;
}

// 内部日志写入函数
static void log_write_internal(log_level_t level, const char* module, const char* message) {
    // 如果日志级别低于当前设置，忽略
    if (level < log_ctx.level) {
        return;
    }
    
    // 当前系统时间
    char time_str[32];
    format_time(time_str, sizeof(time_str));
    
    // 从对应的数组获取级别名称
    const char* level_name = log_level_names[level];
    
    // 消息前缀（时间、级别、模块）
    char prefix[256];
    snprintf(prefix, sizeof(prefix), "[%s] [%s] [%s] ", 
             time_str, level_name, module ? module : "SYSTEM");
    
    // 写入到控制台
    if (log_ctx.console_enabled) {
        // 使用ANSI颜色突出显示日志级别
        fprintf(stderr, "%s%s%s%s\n", 
                prefix, log_level_colors[level], message, reset_color);
    }
    
    // 写入到文件
    if (log_ctx.log_file) {
        // 首先检查是否需要轮转日志
        check_and_rotate_log();
        
        // 如果文件有效，才写入日志
        if (log_ctx.log_file) {
            // 写入日志（无颜色代码）
            fprintf(log_ctx.log_file, "%s%s\n", prefix, message);
            fflush(log_ctx.log_file);  // 立即刷新
        }
    }
}

// 可变参数的日志接口实现
#define IMPLEMENT_LOG_FUNC(name, level_value) \
    void log_##name(const char* module, const char* fmt, ...) { \
        if ((level_value) < log_ctx.level) return; \
        \
        va_list args; \
        va_start(args, fmt); \
        \
        char buffer[4096]; /* 足够大的缓冲区 */ \
        vsnprintf(buffer, sizeof(buffer), fmt, args); \
        \
        pthread_mutex_lock(&log_ctx.lock); \
        log_write_internal((level_value), module, buffer); \
        pthread_mutex_unlock(&log_ctx.lock); \
        \
        va_end(args); \
    }

IMPLEMENT_LOG_FUNC(debug, LOG_LEVEL_DEBUG)
IMPLEMENT_LOG_FUNC(info, LOG_LEVEL_INFO)
IMPLEMENT_LOG_FUNC(warn, LOG_LEVEL_WARN)
IMPLEMENT_LOG_FUNC(error, LOG_LEVEL_ERROR)

// 使用语言键的日志接口
void log_with_lang(log_level_t level, const char* module, const char* lang_key, ...) {
    if (level < log_ctx.level) return;
    
    // 获取语言字符串
    const char* template = lang_get(lang_key);
    if (!template) {
        // 如果语言键未找到，直接用键名作为消息
        pthread_mutex_lock(&log_ctx.lock);
        log_write_internal(level, module, lang_key);
        pthread_mutex_unlock(&log_ctx.lock);
        return;
    }
    
    // 格式化消息
    va_list args;
    va_start(args, lang_key);
    
    char buffer[4096];
    vsnprintf(buffer, sizeof(buffer), template, args);
    
    pthread_mutex_lock(&log_ctx.lock);
    log_write_internal(level, module, buffer);
    pthread_mutex_unlock(&log_ctx.lock);
    
    va_end(args);
}

log_level_t log_get_level(void) {
    return log_ctx.level;
}

bool log_is_console_enabled(void) {
    return log_ctx.console_enabled;
}

const char* log_get_file_path(void) {
    return log_ctx.log_file_path;
}

void log_cleanup(void) {
    pthread_mutex_lock(&log_ctx.lock);
    
    // 关闭日志文件
    if (log_ctx.log_file) {
        fclose(log_ctx.log_file);
        log_ctx.log_file = NULL;
    }
    
    // 释放路径
    if (log_ctx.log_file_path) {
        free(log_ctx.log_file_path);
        log_ctx.log_file_path = NULL;
    }
    
    log_ctx.initialized = false;
    
    pthread_mutex_unlock(&log_ctx.lock);
    pthread_mutex_destroy(&log_ctx.lock);
}

void log_lock(void) {
    pthread_mutex_lock(&log_ctx.lock);
}

void log_unlock(void) {
    pthread_mutex_unlock(&log_ctx.lock);
}
