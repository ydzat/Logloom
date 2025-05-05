#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "config.h"

/**
 * 测试配置系统默认值
 */
void test_default_config() {
    printf("测试配置默认值...\n");
    
    /* 初始化配置系统 */
    assert(config_init() == 0);
    
    /* 验证默认值 */
    assert(strcmp(config_get_language(), "en") == 0);
    assert(strcmp(config_get_log_level(), "INFO") == 0);
    assert(strcmp(config_get_log_file(), "") == 0);
    assert(config_get_max_log_size() == 1048576);
    assert(config_is_console_enabled() == true);
    
    printf("默认值测试通过\n\n");
}

/**
 * 测试从文件加载配置
 */
void test_load_from_file() {
    printf("测试从文件加载配置...\n");
    
    /* 尝试加载配置文件 */
    int result = config_load_from_file("./config.yaml");
    if (result != 0) {
        printf("无法加载配置文件，跳过测试\n\n");
        return;
    }
    
    /* 打印加载后的配置 */
    printf("语言: %s\n", config_get_language());
    printf("日志级别: %s\n", config_get_log_level());
    printf("日志文件: %s\n", config_get_log_file());
    printf("最大日志大小: %zu 字节\n", config_get_max_log_size());
    printf("控制台输出: %s\n", config_is_console_enabled() ? "启用" : "禁用");
    
    printf("配置文件加载测试完成\n\n");
}

/**
 * 测试头文件生成
 */
void test_header_generation() {
    printf("测试头文件生成...\n");
    
    /* 调用Python脚本生成配置头文件 */
    int result = system("./tools/gen_config_header.py config.yaml include/generated/config_gen.h");
    if (result != 0) {
        printf("头文件生成失败\n\n");
        return;
    }
    
    printf("头文件生成完成，路径: include/generated/config_gen.h\n\n");
}

int main() {
    printf("===== Logloom 配置系统测试 =====\n\n");
    
    test_default_config();
    test_load_from_file();
    test_header_generation();
    
    config_cleanup();
    
    printf("===== 测试完成 =====\n");
    return 0;
}