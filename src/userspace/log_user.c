#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <time.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <unistd.h>
#include <pthread.h>
#include "log.h"
#include "config.h"
#include "../shared/platform.h"

/* 声明在log_core.c中定义的函数 */
extern int log_should_log(int level);
extern void log_format_message(char* buffer, size_t buffer_size, int level,
                              const char* module, const char* format, va_list args);

#define LOG_BUFFER_SIZE 4096
#define MAX_FILEPATH_LENGTH 256

/* 日志文件路径 */
static char g_log_file[MAX_FILEPATH_LENGTH] = {0};

/* 日志锁 */
static pthread_mutex_t log_mutex = PTHREAD_MUTEX_INITIALIZER;

/* 控制台输出标志 */
static int g_console_enabled = 1;

/* 日志文件句柄 */
static FILE* g_log_file_handle = NULL;

/* 日志文件最大大小（字节） */
static size_t g_max_file_size = 1048576; /* 默认 1MB */

/**
 * @brief 获取当前时间戳字符串
 * 
 * @param buffer 输出缓冲区
 * @param size 缓冲区大小
 */
static void get_timestamp(char* buffer, size_t size) {
    time_t now;
    struct tm* time_info;
    
    time(&now);
    time_info = localtime(&now);
    
    strftime(buffer, size, "%Y%m%d-%H%M%S", time_info);
}

/**
 * @brief 轮转日志文件
 * 当日志文件达到最大大小时，将其重命名为带时间戳的备份文件
 */
static void rotate_log_file(void) {
    if (!g_log_file[0] || !g_log_file_handle) {
        return;
    }
    
    // 关闭当前日志文件
    fclose(g_log_file_handle);
    g_log_file_handle = NULL;
    
    // 重命名为备份文件
    char backup_file[MAX_FILEPATH_LENGTH];
    char timestamp[32];
    get_timestamp(timestamp, sizeof(timestamp));
    
    // 使用更安全的方法构建备份文件名
    backup_file[0] = '\0'; // 确保是空字符串
    
    // 复制基本文件名，确保不超出缓冲区大小
    size_t max_base_len = sizeof(backup_file) - strlen(timestamp) - 2; // 为"."和结束符留出空间
    strncpy(backup_file, g_log_file, max_base_len);
    backup_file[max_base_len] = '\0'; // 确保字符串结束
    
    // 添加后缀
    strcat(backup_file, ".");
    strcat(backup_file, timestamp);
    
    rename(g_log_file, backup_file);
    
    // 重新打开日志文件
    g_log_file_handle = fopen(g_log_file, "w");
    if (!g_log_file_handle) {
        fprintf(stderr, "[ERROR] 无法重新打开日志文件: %s\n", g_log_file);
    }
}

/**
 * @brief 检查日志文件大小并进行轮转
 */
static void check_and_rotate(void) {
    if (!g_log_file[0] || !g_log_file_handle) {
        return;
    }
    
    // 获取文件大小
    struct stat st;
    if (stat(g_log_file, &st) == 0) {
        if ((size_t)st.st_size >= g_max_file_size) {
            rotate_log_file();
        }
    }
}

/**
 * @brief 写入日志到文件和/或控制台
 * 
 * @param msg 日志消息
 */
static void write_log(const char* msg) {
    // 输出到控制台
    if (g_console_enabled) {
        printf("%s\n", msg);
    }
    
    // 输出到文件
    if (g_log_file_handle) {
        check_and_rotate();
        fprintf(g_log_file_handle, "%s\n", msg);
        fflush(g_log_file_handle);
    }
}

int log_init(const char* level, const char* log_file) {
    log_set_level(level);
    
    pthread_mutex_lock(&log_mutex);
    
    // 配置日志文件
    if (log_file && *log_file) {
        strncpy(g_log_file, log_file, sizeof(g_log_file) - 1);
        g_log_file[sizeof(g_log_file) - 1] = '\0';
        
        g_log_file_handle = fopen(g_log_file, "a");
        if (!g_log_file_handle) {
            fprintf(stderr, "[ERROR] 无法打开日志文件: %s\n", g_log_file);
        }
    }
    
    // 从配置中获取控制台输出设置
    g_console_enabled = config_is_console_enabled();
    
    // 从配置中获取最大文件大小
    g_max_file_size = config_get_max_log_size();
    
    pthread_mutex_unlock(&log_mutex);
    
    return 0;
}

void log_cleanup(void) {
    pthread_mutex_lock(&log_mutex);
    
    if (g_log_file_handle) {
        fclose(g_log_file_handle);
        g_log_file_handle = NULL;
    }
    
    pthread_mutex_unlock(&log_mutex);
}

void log_set_file(const char* file_path) {
    pthread_mutex_lock(&log_mutex);
    
    if (g_log_file_handle) {
        fclose(g_log_file_handle);
        g_log_file_handle = NULL;
    }
    
    if (file_path && *file_path) {
        strncpy(g_log_file, file_path, sizeof(g_log_file) - 1);
        g_log_file[sizeof(g_log_file) - 1] = '\0';
        
        g_log_file_handle = fopen(g_log_file, "a");
        if (!g_log_file_handle) {
            fprintf(stderr, "[ERROR] 无法打开日志文件: %s\n", g_log_file);
        }
    } else {
        g_log_file[0] = '\0';
    }
    
    pthread_mutex_unlock(&log_mutex);
}

void log_set_max_file_size(size_t max_size) {
    pthread_mutex_lock(&log_mutex);
    g_max_file_size = max_size > 0 ? max_size : 1048576;
    pthread_mutex_unlock(&log_mutex);
}

void log_set_console_enabled(int enabled) {
    pthread_mutex_lock(&log_mutex);
    g_console_enabled = enabled;
    pthread_mutex_unlock(&log_mutex);
}

void log_lock(void) {
    pthread_mutex_lock(&log_mutex);
}

void log_unlock(void) {
    pthread_mutex_unlock(&log_mutex);
}

/**
 * @brief 通用日志记录函数
 */
static void log_message(int level, const char* module, const char* format, va_list args) {
    if (!log_should_log(level)) {
        return;
    }
    
    char buffer[LOG_BUFFER_SIZE];
    
    log_format_message(buffer, sizeof(buffer), level, module, format, args);
    
    pthread_mutex_lock(&log_mutex);
    write_log(buffer);
    pthread_mutex_unlock(&log_mutex);
}

void log_debug(const char* module, const char* format, ...) {
    va_list args;
    va_start(args, format);
    log_message(LOG_LEVEL_DEBUG, module, format, args);
    va_end(args);
}

void log_info(const char* module, const char* format, ...) {
    va_list args;
    va_start(args, format);
    log_message(LOG_LEVEL_INFO, module, format, args);
    va_end(args);
}

void log_warn(const char* module, const char* format, ...) {
    va_list args;
    va_start(args, format);
    log_message(LOG_LEVEL_WARN, module, format, args);
    va_end(args);
}

void log_error(const char* module, const char* format, ...) {
    va_list args;
    va_start(args, format);
    log_message(LOG_LEVEL_ERROR, module, format, args);
    va_end(args);
}

void log_fatal(const char* module, const char* format, ...) {
    va_list args;
    va_start(args, format);
    log_message(LOG_LEVEL_FATAL, module, format, args);
    va_end(args);
}