/**
 * @file config.h
 * @brief Logloom 配置系统头文件
 */

#ifndef LOGLOOM_CONFIG_H
#define LOGLOOM_CONFIG_H

#include <stddef.h>
#include <stdbool.h>

/**
 * @brief Logloom 配置结构体
 */
typedef struct {
    char language[8];      /* 默认语言 */
    struct {
        char file[256];    /* 日志文件路径 */
        char level[8];     /* 日志级别 */
        size_t max_size;   /* 日志文件最大大小 */
        bool console;      /* 是否输出到控制台 */
    } log;
} logloom_config_t;

/** 全局配置对象 */
extern logloom_config_t g_config;

/**
 * @brief 初始化配置系统，使用默认值填充
 * @return 0 表示成功，非零表示失败
 */
int config_init(void);

/**
 * @brief 从文件加载配置
 * @param path 配置文件路径，如为 NULL 则使用默认路径
 * @return 0 表示成功，非零表示失败
 */
int config_load_from_file(const char* path);

/**
 * @brief 获取日志级别配置
 * @return 日志级别字符串
 */
const char* config_get_log_level(void);

/**
 * @brief 获取日志文件路径
 * @return 日志文件路径，空字符串表示未配置
 */
const char* config_get_log_file(void);

/**
 * @brief 检查是否启用控制台日志
 * @return true 表示启用，false 表示禁用
 */
bool config_is_console_enabled(void);

/**
 * @brief 获取日志文件大小上限
 * @return 日志文件最大大小（字节）
 */
size_t config_get_max_log_size(void);

/**
 * @brief 获取默认语言设置
 * @return 语言代码（如 "en", "zh" 等）
 */
const char* config_get_language(void);

/**
 * @brief 配置清理函数
 */
void config_cleanup(void);

#endif /* LOGLOOM_CONFIG_H */