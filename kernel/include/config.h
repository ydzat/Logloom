#ifndef LOGLOOM_KERNEL_CONFIG_H
#define LOGLOOM_KERNEL_CONFIG_H

#ifdef __KERNEL__
/* 内核环境 */
#include <linux/types.h>
#include <linux/string.h>
typedef _Bool bool;
#define true 1
#define false 0
#else
/* 用户态环境 */
#include <stdbool.h>
#include <stddef.h>
#endif

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
int config_is_console_enabled(void);

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
 * @brief 设置配置默认值
 * 
 * @param cfg 配置结构体指针
 */
void config_set_defaults(logloom_config_t* cfg);

/**
 * @brief 配置清理函数
 */
void config_cleanup(void);

#endif /* LOGLOOM_KERNEL_CONFIG_H */