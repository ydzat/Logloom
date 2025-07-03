#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/string.h>
#include "config.h"
#include "../../src/shared/platform.h"

/* 声明在config_core.c中定义的函数 */
extern void config_set_defaults(logloom_config_t* cfg);
extern logloom_config_t g_config;

/* 预生成的配置头文件，由构建工具从YAML生成 */
#include "generated/config_gen.h"

int config_init(void) {
    /* 先设置默认值 */
    config_set_defaults(&g_config);
    
    /* 然后使用预定义的宏加载配置 */
    LOAD_STATIC_CONFIG(&g_config);
    return 0;
}

int config_load_from_file(const char* path) {
    /* 内核态中不支持从文件加载配置，忽略参数 */
    (void)path;
    LOGLOOM_INFO("内核态不支持从文件加载配置，使用预编译值");
    return 0;
}

void config_cleanup(void) {
    /* 内核态中没有需要清理的资源 */
}

/**
 * @brief 获取配置中的语言设置
 * 
 * @return 语言代码字符串
 */
const char* config_get_language(void) {
    return g_config.language;
}

/**
 * @brief 获取配置中的日志级别
 * 
 * @return 日志级别字符串
 */
const char* config_get_log_level(void) {
    return g_config.log.level;
}

/**
 * @brief 获取配置中的日志文件路径
 * 
 * @return 日志文件路径
 */
const char* config_get_log_file(void) {
    return g_config.log.file;
}

/**
 * @brief 检查控制台日志是否启用
 * 
 * @return 如果启用返回1，否则返回0
 */
int config_is_console_enabled(void) {
    return g_config.log.console;
}

/**
 * @brief 获取配置中的日志文件最大大小
 * 
 * @return 日志文件最大大小（字节）
 */
size_t config_get_max_log_size(void) {
    return g_config.log.max_size;
}

// 导出这些符号，以便其他内核模块可以使用它们
EXPORT_SYMBOL(config_get_language);
EXPORT_SYMBOL(config_get_log_level);
EXPORT_SYMBOL(config_get_log_file);
EXPORT_SYMBOL(config_is_console_enabled);
EXPORT_SYMBOL(config_get_max_log_size);