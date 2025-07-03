#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "log.h"
#include "lang.h"

// 测试模块名称
#define TEST_MODULE "TEST"
#define LOG_TEST_FILE "log_test.log"

// 日志测试步骤
void test_log_levels() {
    printf("Testing different log levels...\n");
    
    log_debug(TEST_MODULE, "This is a debug message");
    log_info(TEST_MODULE, "This is an info message");
    log_warn(TEST_MODULE, "This is a warning message");
    log_error(TEST_MODULE, "This is an error message");
    
    printf("Done. Check console and log file.\n\n");
}

// 测试日志级别过滤
void test_log_filtering() {
    printf("Testing log level filtering...\n");
    
    // 设置日志级别为WARNING，应该只显示WARN和ERROR
    printf("Setting log level to WARN, only WARN and ERROR should appear:\n");
    log_set_level("WARN");
    
    log_debug(TEST_MODULE, "This debug message should NOT appear");
    log_info(TEST_MODULE, "This info message should NOT appear");
    log_warn(TEST_MODULE, "This warning message should appear");
    log_error(TEST_MODULE, "This error message should appear");
    
    // 恢复为INFO级别
    log_set_level("INFO");
    printf("Reset to INFO level\n\n");
}

// 测试国际化日志
void test_multilanguage() {
    printf("Testing multilanguage logs...\n");
    
    // 使用语言键输出日志
    log_with_lang(LOG_LEVEL_INFO, TEST_MODULE, "test.hello", "World");
    log_with_lang(LOG_LEVEL_ERROR, TEST_MODULE, "test.error_count", 5);
    
    // 测试语言切换
    printf("Switching language to Chinese...\n");
    lang_set_language("zh");
    
    log_with_lang(LOG_LEVEL_INFO, TEST_MODULE, "test.hello", "世界");
    log_with_lang(LOG_LEVEL_ERROR, TEST_MODULE, "test.error_count", 5);
    
    printf("Done testing multilanguage logs\n\n");
}

// 测试控制台禁用
void test_console_disable() {
    printf("Testing console output disable...\n");
    printf("Next logs will NOT appear on console but WILL be in file:\n");
    
    log_set_console_enabled(0);  // 0表示禁用
    log_info(TEST_MODULE, "This should only go to file, not console");
    log_error(TEST_MODULE, "This error also should only go to file");
    
    // 重新启用控制台输出
    log_set_console_enabled(1);  // 1表示启用
    printf("Console output re-enabled\n\n");
}

int main() {
    // 初始化语言系统
    if (lang_init("en") != 0) {
        fprintf(stderr, "Failed to initialize language system\n");
        return 1;
    }
    
    // 初始化日志系统，使用正确的字符串参数
    if (log_init("INFO", NULL) != 0) {
        fprintf(stderr, "Failed to initialize logging system\n");
        return 1;
    }
    
    // 设置日志输出文件
    printf("Setting log file to: %s\n", LOG_TEST_FILE);
    log_set_file(LOG_TEST_FILE);
    // 不需要检查返回值，因为log_set_file返回void
    
    // 设置小文件大小，便于测试轮转
    log_set_max_file_size(1024); // 1KB，便于测试轮转
    
    printf("=== Logloom Log System Test ===\n\n");
    
    // 执行各项测试
    test_log_levels();
    test_log_filtering();
    test_multilanguage();
    test_console_disable();
    
    // 生成足够多的日志以触发轮转
    printf("Testing log rotation (generating many logs)...\n");
    for (int i = 0; i < 50; i++) {
        log_info(TEST_MODULE, "Rotation test log entry %d - generating data to trigger rotation", i);
    }
    printf("Check if log files were rotated\n\n");
    
    // 清理资源
    printf("Cleaning up resources...\n");
    log_cleanup();
    lang_cleanup();
    
    printf("Test completed successfully.\n");
    return 0;
}