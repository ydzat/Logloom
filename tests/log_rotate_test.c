#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <dirent.h>
#include <time.h>
#include "log.h"
#include "lang.h"

// 测试模块名称
#define TEST_MODULE "ROTATE"
#define LOG_TEST_FILE "rotate_test.log"

// 检查文件是否存在
static int file_exists(const char* filepath) {
    struct stat buffer;
    return (stat(filepath, &buffer) == 0);
}

// 获取指定目录中特定前缀的文件数量
static int count_files_with_prefix(const char* prefix) {
    DIR* dir;
    struct dirent* entry;
    int count = 0;
    
    dir = opendir(".");
    if (!dir) {
        return -1;
    }
    
    while ((entry = readdir(dir)) != NULL) {
        if (strncmp(entry->d_name, prefix, strlen(prefix)) == 0) {
            count++;
        }
    }
    
    closedir(dir);
    return count;
}

// 测试基本日志轮转
void test_basic_rotation() {
    printf("测试基本日志轮转功能...\n");
    
    // 设置小的日志文件大小以便于测试轮转
    log_set_max_file_size(1024); // 1KB
    
    // 生成足够的日志以触发轮转
    for (int i = 0; i < 30; i++) {
        log_info(TEST_MODULE, "这是测试轮转的日志 %d - 生成足够的数据以触发轮转, 添加一些额外的内容使其更长...", i);
    }
    
    // 检查是否有轮转文件生成
    printf("主日志文件是否存在: %s\n", file_exists(LOG_TEST_FILE) ? "是" : "否");
    
    // 计算轮转文件数量
    int rotate_count = count_files_with_prefix(LOG_TEST_FILE);
    printf("日志文件总数 (包括主文件与轮转文件): %d\n", rotate_count);
    
    if (rotate_count > 1) {
        printf("✅ 测试通过: 成功生成了轮转日志文件\n\n");
    } else {
        printf("❌ 测试失败: 未能生成轮转日志文件\n\n");
    }
}

// 测试最大备份文件数量限制
void test_max_backup_limit() {
    printf("测试最大备份文件数量限制...\n");
    
    // 设置最大备份文件数量
    log_set_max_backup_files(3);
    printf("设置最大备份文件数量为: 3\n");
    
    // 设置更小的日志大小以触发更多轮转
    log_set_max_file_size(512); // 512字节
    
    // 生成大量日志，触发多次轮转
    for (int i = 0; i < 100; i++) {
        log_info(TEST_MODULE, "这是用于测试备份文件数量限制的日志 %d - 应该触发多次轮转...", i);
    }
    
    // 计算轮转文件数量
    int rotate_count = count_files_with_prefix(LOG_TEST_FILE);
    printf("轮转后的日志文件总数: %d\n", rotate_count);
    
    // 检查是否符合我们设置的限制 (1个主文件 + 3个备份文件)
    if (rotate_count <= 4) {
        printf("✅ 测试通过: 备份文件数量符合限制\n\n");
    } else {
        printf("❌ 测试失败: 备份文件数量超出限制\n\n");
    }
}

// 测试手动轮转功能
void test_manual_rotation() {
    printf("测试手动轮转功能...\n");
    
    // 确保写入一些内容到新文件
    log_info(TEST_MODULE, "这是手动轮转测试前的标记内容: %ld", (long)time(NULL));
    fflush(NULL);
    
    // 记录主日志文件的修改时间
    struct stat st_before;
    if (stat(LOG_TEST_FILE, &st_before) != 0) {
        printf("❌ 测试失败: 无法获取文件状态\n\n");
        return;
    }
    
    // 等待一小段时间，确保时间戳会有差异
    usleep(100000); // 100毫秒
    
    // 执行手动轮转
    printf("执行手动轮转...\n");
    bool success = log_rotate_now();
    
    if (success) {
        printf("手动轮转报告成功\n");
    } else {
        printf("手动轮转报告失败\n");
        printf("❌ 测试失败: 手动轮转函数返回失败\n\n");
        return;
    }
    
    // 写入一些内容到新文件，用于标识
    log_info(TEST_MODULE, "这是手动轮转测试后的标记内容: %ld", (long)time(NULL));
    fflush(NULL);
    
    // 再次获取主日志文件的信息
    struct stat st_after;
    if (stat(LOG_TEST_FILE, &st_after) != 0) {
        printf("❌ 测试失败: 无法获取轮转后文件状态\n\n");
        return;
    }
    
    // 对比文件修改时间
    printf("轮转前文件时间戳: %ld\n", (long)st_before.st_mtime);
    printf("轮转后文件时间戳: %ld\n", (long)st_after.st_mtime);
    
    // 检查文件大小（新文件应该比旧文件小）
    printf("轮转前文件大小: %ld 字节\n", (long)st_before.st_size);
    printf("轮转后文件大小: %ld 字节\n", (long)st_after.st_size);
    
    // 检查文件内容
    FILE* f = fopen(LOG_TEST_FILE, "r");
    if (f) {
        char buf[1024] = {0};
        size_t bytes_read = fread(buf, 1, sizeof(buf) - 1, f);
        fclose(f);
        
        if (bytes_read > 0) {
            buf[bytes_read] = '\0'; // 确保字符串终止
            printf("新文件内容样本:\n%s\n", buf);
        }
    }
    
    // 基于时间戳或大小判断轮转是否成功
    if (st_after.st_ctime > st_before.st_ctime || st_after.st_size < st_before.st_size) {
        printf("✅ 测试通过: 手动轮转成功 (检测到文件变化)\n\n");
    } else {
        printf("❌ 测试失败: 未检测到文件变化\n\n");
    }
}

// 主函数
int main() {
    // 初始化语言系统
    if (lang_init("zh") != 0) {
        fprintf(stderr, "初始化语言系统失败\n");
        return 1;
    }
    
    // 初始化日志系统
    if (log_init(LOG_LEVEL_INFO, true) != 0) {
        fprintf(stderr, "初始化日志系统失败\n");
        return 1;
    }
    
    // 设置日志输出文件
    printf("设置日志文件为: %s\n", LOG_TEST_FILE);
    if (!log_set_output_file(LOG_TEST_FILE)) {
        fprintf(stderr, "设置日志文件失败\n");
        return 1;
    }
    
    printf("=== Logloom 日志轮转功能测试 ===\n\n");
    
    // 运行测试
    test_basic_rotation();
    test_max_backup_limit();
    test_manual_rotation();
    
    // 清理资源
    printf("清理资源...\n");
    log_cleanup();
    lang_cleanup();
    
    printf("测试完成。\n");
    return 0;
}