#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/spinlock.h>
#include <linux/slab.h>
#include <linux/string.h>
#include <linux/time.h>
#include <linux/rtc.h>
#include <linux/uaccess.h>
#include "log.h"
#include "config.h"
#include "../../src/shared/platform.h"

/* 声明在log_core.c中定义的函数 */
extern int log_should_log(int level);
extern void log_format_message(char* buffer, size_t buffer_size, int level,
                              const char* module, const char* format, va_list args);
extern const char* log_level_to_string(int level);
extern const char* log_get_level_string(void);
extern int log_level_from_string(const char* level);
extern void log_set_level(const char* level);
extern int log_get_level(void);

/* 内核日志相关配置 */
#define LOG_BUFFER_SIZE 4096
#define MAX_FILEPATH_LENGTH 256

/* 内核日志文件路径 */
static char g_log_file[MAX_FILEPATH_LENGTH] = {0};

/* 控制台输出标志 */
static int g_console_enabled = 1;

/* 内核同步锁 */
static DEFINE_SPINLOCK(log_spinlock);

/* 日志文件指针 */
static struct file* g_log_file_handle = NULL;

/* 日志文件最大大小（字节） */
static size_t g_max_file_size = 1048576; /* 默认 1MB */

/**
 * @brief 获取当前时间戳字符串
 * 
 * @param buffer 输出缓冲区
 * @param size 缓冲区大小
 */
static void get_timestamp(char* buffer, size_t size) {
    struct timespec64 ts;
    struct tm tm;
    
    ktime_get_real_ts64(&ts);
    time64_to_tm(ts.tv_sec, 0, &tm);
    
    snprintf(buffer, size, "%04ld%02d%02d-%02d%02d%02d",
             tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday,
             tm.tm_hour, tm.tm_min, tm.tm_sec);
}

/**
 * @brief 关闭内核日志文件并处理可能的错误
 */
static void close_log_file(void) {
    if (g_log_file_handle) {
        if (!IS_ERR(g_log_file_handle)) {
            filp_close(g_log_file_handle, NULL);
        }
        g_log_file_handle = NULL;
    }
}

/**
 * @brief 安全地打开日志文件
 * 
 * @param file_path 日志文件路径
 * @return 成功返回0，失败返回错误代码
 */
static int safe_open_log_file(const char* file_path) {
    // 关闭已有的日志文件
    close_log_file();
    
    if (!file_path || !*file_path) {
        return -EINVAL;
    }
    
    g_log_file_handle = filp_open(file_path, O_WRONLY | O_CREAT | O_APPEND, 0644);
    if (IS_ERR(g_log_file_handle)) {
        long err = PTR_ERR(g_log_file_handle);
        pr_err("无法打开日志文件: %s, 错误: %ld\n", file_path, err);
        g_log_file_handle = NULL;
        return err;
    }
    
    return 0;
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
    close_log_file();
    
    // 重命名为备份文件
    char backup_file[MAX_FILEPATH_LENGTH];
    char timestamp[32];
    get_timestamp(timestamp, sizeof(timestamp));
    
    snprintf(backup_file, sizeof(backup_file), "%s.%s", g_log_file, timestamp);
    
    // 在内核中使用vfs_rename进行文件重命名
    struct file* old_file = filp_open(g_log_file, O_RDONLY, 0);
    if (!IS_ERR(old_file)) {
        struct file* new_file = filp_open(backup_file, O_WRONLY | O_CREAT, 0644);
        if (!IS_ERR(new_file)) {
            // 使用堆分配缓冲区而不是栈分配，减少栈帧大小
            char *buffer = kmalloc(4096, GFP_KERNEL);
            if (buffer) {
                loff_t pos = 0;
                ssize_t bytes_read, bytes_written;
                
                while ((bytes_read = kernel_read(old_file, buffer, 4096, &pos)) > 0) {
                    loff_t write_pos = 0;
                    bytes_written = kernel_write(new_file, buffer, bytes_read, &write_pos);
                    if (bytes_written < bytes_read) {
                        pr_err("Failed to write all bytes during log rotation\n");
                        break;
                    }
                }
                
                kfree(buffer);
            } else {
                pr_err("Failed to allocate buffer for log rotation\n");
            }
            filp_close(new_file, NULL);
        }
        filp_close(old_file, NULL);
    }
    
    // 重新打开日志文件
    g_log_file_handle = filp_open(g_log_file, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (IS_ERR(g_log_file_handle)) {
        pr_err("无法重新打开日志文件: %s\n", g_log_file);
        g_log_file_handle = NULL;
    }
}

/**
 * @brief 检查日志文件大小并进行轮转
 */
static void check_and_rotate(void) {
    if (!g_log_file[0] || !g_log_file_handle) {
        return;
    }
    
    // 获取文件大小，使用内核提供的函数
    loff_t file_size;
    struct file *temp_file = filp_open(g_log_file, O_RDONLY, 0);
    
    if (!IS_ERR(temp_file)) {
        // 使用vfs_llseek获取文件大小
        file_size = vfs_llseek(temp_file, 0, SEEK_END);
        filp_close(temp_file, NULL);
        
        if (file_size >= g_max_file_size) {
            rotate_log_file();
        }
    }
}

/**
 * @brief 安全地写入日志到文件
 * 处理可能的错误并适当降级
 * 
 * @param msg 日志消息
 */
static void safe_write_to_file(const char* msg) {
    if (!g_log_file_handle || IS_ERR(g_log_file_handle) || !msg) {
        return;
    }
    
    // 检查文件是否仍然有效
    if (!g_log_file_handle->f_op || !g_log_file_handle->f_op->write) {
        pr_err("日志文件不再有效，关闭文件\n");
        close_log_file();
        return;
    }
    
    // 写入到文件
    loff_t pos = 0;
    vfs_llseek(g_log_file_handle, 0, SEEK_END);
    size_t len = strlen(msg);
    char *nl_msg = kmalloc(len + 2, GFP_KERNEL);
    if (nl_msg) {
        strcpy(nl_msg, msg);
        strcat(nl_msg, "\n");
        
        ssize_t written = kernel_write(g_log_file_handle, nl_msg, len + 1, &pos);
        if (written != len + 1) {
            pr_err("写入日志文件失败: 预期 %zu 字节, 实际写入 %zd 字节\n", 
                  len + 1, written);
        }
        
        kfree(nl_msg);
    } else {
        // 内存分配失败，尝试直接写入，不添加换行符
        kernel_write(g_log_file_handle, msg, len, &pos);
        pos = 0;
        kernel_write(g_log_file_handle, "\n", 1, &pos);
    }
}

/**
 * @brief 写入日志到文件和/或控制台
 * 添加错误恢复机制
 * 
 * @param msg 日志消息
 */
static void write_log(const char* msg) {
    // 输出到内核日志
    if (g_console_enabled) {
        printk("%s\n", msg);
    }
    
    // 输出到文件 - 如果文件打开失败，尝试重打开
    if (g_log_file[0]) {
        if (!g_log_file_handle || IS_ERR(g_log_file_handle)) {
            safe_open_log_file(g_log_file);
        }
        
        // 检查轮换
        if (g_log_file_handle && !IS_ERR(g_log_file_handle)) {
            check_and_rotate();
            safe_write_to_file(msg);
        }
    }
}

int log_init(const char* level, const char* log_file) {
    log_set_level(level);
    
    spin_lock(&log_spinlock);
    
    // 配置日志文件
    if (log_file && *log_file) {
        strncpy(g_log_file, log_file, sizeof(g_log_file) - 1);
        g_log_file[sizeof(g_log_file) - 1] = '\0';
        
        g_log_file_handle = filp_open(g_log_file, O_WRONLY | O_CREAT | O_APPEND, 0644);
        if (IS_ERR(g_log_file_handle)) {
            pr_err("无法打开日志文件: %s, 错误: %ld\n", g_log_file, PTR_ERR(g_log_file_handle));
            g_log_file_handle = NULL;
        }
    }
    
    // 从配置中获取控制台输出设置
    g_console_enabled = config_is_console_enabled();
    
    // 从配置中获取最大文件大小
    g_max_file_size = config_get_max_log_size();
    
    spin_unlock(&log_spinlock);
    
    return 0;
}

void log_cleanup(void) {
    spin_lock(&log_spinlock);
    close_log_file();
    spin_unlock(&log_spinlock);
}

void log_set_file(const char* file_path) {
    spin_lock(&log_spinlock);
    
    close_log_file();
    
    if (file_path && *file_path) {
        strncpy(g_log_file, file_path, sizeof(g_log_file) - 1);
        g_log_file[sizeof(g_log_file) - 1] = '\0';
        
        g_log_file_handle = filp_open(g_log_file, O_WRONLY | O_CREAT | O_APPEND, 0644);
        if (IS_ERR(g_log_file_handle)) {
            pr_err("无法打开日志文件: %s, 错误: %ld\n", g_log_file, PTR_ERR(g_log_file_handle));
            g_log_file_handle = NULL;
        }
    } else {
        g_log_file[0] = '\0';
    }
    
    spin_unlock(&log_spinlock);
}

void log_set_max_file_size(size_t max_size) {
    spin_lock(&log_spinlock);
    g_max_file_size = max_size > 0 ? max_size : 1048576;
    spin_unlock(&log_spinlock);
}

void log_set_console_enabled(int enabled) {
    spin_lock(&log_spinlock);
    g_console_enabled = enabled;
    spin_unlock(&log_spinlock);
}

void log_lock(void) {
    spin_lock(&log_spinlock);
}

void log_unlock(void) {
    spin_unlock(&log_spinlock);
}

/**
 * @brief 通用日志记录函数
 */
static void log_message(int level, const char* module, const char* format, va_list args) {
    if (!log_should_log(level)) {
        return;
    }
    
    char *buffer = kmalloc(LOG_BUFFER_SIZE, GFP_KERNEL);
    if (!buffer) {
        pr_err("Failed to allocate log buffer\n");
        return;
    }
    
    log_format_message(buffer, LOG_BUFFER_SIZE, level, module, format, args);
    
    spin_lock(&log_spinlock);
    write_log(buffer);
    spin_unlock(&log_spinlock);
    
    kfree(buffer);
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

// 导出这些符号，以便其他内核模块可以使用它们
EXPORT_SYMBOL(log_debug);
EXPORT_SYMBOL(log_info);
EXPORT_SYMBOL(log_warn);
EXPORT_SYMBOL(log_error);
EXPORT_SYMBOL(log_fatal);
EXPORT_SYMBOL(log_set_level);
EXPORT_SYMBOL(log_set_file);
EXPORT_SYMBOL(log_set_console_enabled);
EXPORT_SYMBOL(log_get_level_string);
EXPORT_SYMBOL(log_level_to_string);
EXPORT_SYMBOL(log_level_from_string);
EXPORT_SYMBOL(log_get_level);