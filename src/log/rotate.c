#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>
#include <dirent.h>
#include <time.h>
#include <libgen.h>
#include <limits.h>

#include "log.h"

// 最大历史日志文件数量的默认值
#define DEFAULT_MAX_BACKUP_FILES 5

// 内部状态
static struct {
    size_t max_backup_files;  // 最大历史文件数量
} rotate_ctx = {
    .max_backup_files = DEFAULT_MAX_BACKUP_FILES
};

/**
 * 设置最大历史日志文件数量
 * @param count 最大历史文件数量
 */
void log_set_max_backup_files_impl(size_t count) {
    rotate_ctx.max_backup_files = count;
}

/**
 * 获取最大历史日志文件数量
 * @return 最大历史文件数量
 */
size_t log_get_max_backup_files_impl(void) {
    return rotate_ctx.max_backup_files;
}

/**
 * 查找指定路径的最大后缀编号
 * @param base_path 日志文件基础路径
 * @return 最大后缀编号，若无备份文件则返回0
 */
static int find_max_backup_index(const char* base_path) {
    DIR* dir;
    struct dirent* entry;
    int max_index = 0;
    
    // 获取目录路径
    char dir_path[PATH_MAX];
    strcpy(dir_path, base_path);
    dirname(dir_path);
    
    // 获取文件基础名称（不含路径）
    char base_name[PATH_MAX];
    strcpy(base_name, base_path);
    char* file_base = basename(base_name);
    size_t base_len = strlen(file_base);
    
    // 打开目录
    dir = opendir(*dir_path ? dir_path : ".");
    if (!dir) {
        return 0;
    }
    
    // 遍历目录内容
    while ((entry = readdir(dir)) != NULL) {
        if (strncmp(entry->d_name, file_base, base_len) == 0 && 
            entry->d_name[base_len] == '.') {
            
            // 尝试解析后缀为数字
            int index = atoi(entry->d_name + base_len + 1);
            if (index > max_index) {
                max_index = index;
            }
        }
    }
    
    closedir(dir);
    return max_index;
}

/**
 * 删除最旧的日志文件
 * @param base_path 日志文件基础路径
 * @return 成功返回0，失败返回错误码
 */
static int cleanup_old_logs(const char* base_path) {
    DIR* dir;
    struct dirent* entry;
    
    // 如果不限制备份文件数量，则不执行清理
    if (rotate_ctx.max_backup_files <= 0) {
        return 0;
    }
    
    // 获取目录路径
    char dir_path[PATH_MAX];
    strcpy(dir_path, base_path);
    dirname(dir_path);
    
    // 获取基础文件名
    char base_name[PATH_MAX];
    strcpy(base_name, base_path);
    char* file_base = basename(base_name);
    size_t base_len = strlen(file_base);
    
    // 收集所有备份文件信息
    typedef struct {
        char path[PATH_MAX];
        int index;
    } backup_file_t;
    
    backup_file_t* backup_files = NULL;
    int backup_count = 0;
    
    // 打开目录
    dir = opendir(*dir_path ? dir_path : ".");
    if (!dir) {
        return -1;
    }
    
    // 第一次遍历统计文件数量
    while ((entry = readdir(dir)) != NULL) {
        if (strncmp(entry->d_name, file_base, base_len) == 0 && 
            entry->d_name[base_len] == '.') {
            backup_count++;
        }
    }
    
    // 如果备份数量未超过限制，则不需要清理
    if (backup_count <= rotate_ctx.max_backup_files) {
        closedir(dir);
        return 0;
    }
    
    // 分配内存
    backup_files = (backup_file_t*)malloc(backup_count * sizeof(backup_file_t));
    if (!backup_files) {
        closedir(dir);
        return -2;
    }
    
    // 重置目录读取位置
    rewinddir(dir);
    
    // 第二次遍历收集文件信息
    int file_idx = 0;
    while ((entry = readdir(dir)) != NULL && file_idx < backup_count) {
        if (strncmp(entry->d_name, file_base, base_len) == 0 && 
            entry->d_name[base_len] == '.') {
            
            // 安全地构建完整路径
            if (*dir_path) {
                // 确保足够空间用于拼接
                size_t dir_len = strlen(dir_path);
                size_t name_len = strlen(entry->d_name);
                
                if (dir_len + name_len + 2 <= PATH_MAX) { // +2 for '/' and null
                    // 使用拷贝和连接，避免使用snprintf的格式化警告
                    strcpy(backup_files[file_idx].path, dir_path);
                    strcat(backup_files[file_idx].path, "/");
                    strcat(backup_files[file_idx].path, entry->d_name);
                } else {
                    // 路径太长，使用截断路径
                    strncpy(backup_files[file_idx].path, dir_path, PATH_MAX - 5);
                    backup_files[file_idx].path[PATH_MAX - 5] = '\0';
                    strcat(backup_files[file_idx].path, "/...");
                }
            } else {
                // 使用当前目录
                strncpy(backup_files[file_idx].path, entry->d_name, PATH_MAX - 1);
                backup_files[file_idx].path[PATH_MAX - 1] = '\0';
            }
            
            // 解析索引
            backup_files[file_idx].index = atoi(entry->d_name + base_len + 1);
            file_idx++;
        }
    }
    
    closedir(dir);
    
    // 删除多余的日志文件（从最低索引开始）
    int to_delete = backup_count - rotate_ctx.max_backup_files;
    
    // 简单的冒泡排序，按索引排序文件
    for (int i = 0; i < backup_count - 1; i++) {
        for (int j = 0; j < backup_count - i - 1; j++) {
            if (backup_files[j].index > backup_files[j+1].index) {
                backup_file_t temp = backup_files[j];
                backup_files[j] = backup_files[j+1];
                backup_files[j+1] = temp;
            }
        }
    }
    
    // 删除最旧的文件
    for (int i = 0; i < to_delete; i++) {
        remove(backup_files[i].path);
    }
    
    free(backup_files);
    return 0;
}

/**
 * 执行日志文件轮转
 * @param log_file_path 当前日志文件路径
 * @param log_file 日志文件指针（将被关闭并重新打开）
 * @return 新的日志文件指针，失败时返回NULL
 */
FILE* rotate_log_file(const char* log_file_path, FILE* log_file) {
    if (!log_file || !log_file_path) {
        return NULL;
    }
    
    // 关闭当前日志文件
    fclose(log_file);
    
    // 执行旧文件清理
    cleanup_old_logs(log_file_path);
    
    // 查找最大后缀编号
    int max_index = find_max_backup_index(log_file_path);
    
    // 创建新的备份文件名
    char backup_path[PATH_MAX];
    snprintf(backup_path, PATH_MAX, "%s.%d", log_file_path, max_index + 1);
    
    // 重命名当前日志文件为备份文件
    if (rename(log_file_path, backup_path) != 0) {
        // 如果重命名失败，记录错误，并尝试用时间戳作为备份
        char timestamp_path[PATH_MAX];
        time_t now = time(NULL);
        struct tm* tm_info = localtime(&now);
        
        // 修复strftime函数调用
        char time_str[32];
        strftime(time_str, sizeof(time_str), "%Y%m%d-%H%M%S", tm_info);
        snprintf(timestamp_path, PATH_MAX, "%s.%s", log_file_path, time_str);
        
        if (rename(log_file_path, timestamp_path) != 0) {
            // 重命名失败，尝试重新打开原文件（追加模式）
            FILE* f = fopen(log_file_path, "a");
            if (f) {
                fprintf(f, "[LOG ROTATE FAILED] Will continue appending to current log file. Error: %s\n", 
                        strerror(errno));
            }
            return f;
        }
    }
    
    // 创建新的日志文件
    FILE* new_file = fopen(log_file_path, "w");
    if (!new_file) {
        // 创建失败，记录错误
        FILE* f = fopen(backup_path, "a");
        if (f) {
            fprintf(f, "[LOG CREATE FAILED] Cannot create new log file: %s. Error: %s\n",
                    log_file_path, strerror(errno));
            return f;
        }
        return NULL;
    }
    
    // 在新日志文件中写入轮转信息
    fprintf(new_file, "[LOG ROTATE] Previous log rotated to %s\n", backup_path);
    fflush(new_file);
    
    return new_file;
}

/**
 * 检查日志文件大小并在需要时执行轮转
 * @param log_file_path 日志文件路径
 * @param log_file 日志文件指针
 * @param max_size 最大允许大小
 * @return 更新后的日志文件指针
 */
FILE* check_and_rotate_log_file(const char* log_file_path, FILE* log_file, size_t max_size) {
    if (!log_file || !log_file_path || max_size <= 0) {
        return log_file;
    }
    
    // 获取当前文件大小
    struct stat st;
    if (stat(log_file_path, &st) != 0) {
        return log_file;  // 无法获取文件信息
    }
    
    // 如果文件超过最大大小，执行轮转
    if (st.st_size >= max_size) {
        return rotate_log_file(log_file_path, log_file);
    }
    
    return log_file;
}