/**
 * 自动生成的内核配置头文件
 * 此文件通常由构建系统根据配置文件生成
 * 为了测试，这里提供了一个简化版本
 */

#ifndef LOGLOOM_CONFIG_GEN_H
#define LOGLOOM_CONFIG_GEN_H

/* 默认语言设置 */
#define LOGLOOM_CONFIG_LANG "en"

/* 日志配置 */
#define LOGLOOM_CONFIG_LOG_LEVEL "INFO"
#define LOGLOOM_CONFIG_LOG_FILE "/var/log/logloom.log"
#define LOGLOOM_CONFIG_LOG_MAX_SIZE 1048576 /* 1MB */
#define LOGLOOM_CONFIG_LOG_CONSOLE 1

/* 用于在内核模块中加载静态配置的函数 */
#define LOAD_STATIC_CONFIG(config) do { \
    strncpy((config)->language, LOGLOOM_CONFIG_LANG, sizeof((config)->language)); \
    (config)->language[sizeof((config)->language) - 1] = '\0'; \
    strncpy((config)->log.level, LOGLOOM_CONFIG_LOG_LEVEL, sizeof((config)->log.level)); \
    (config)->log.level[sizeof((config)->log.level) - 1] = '\0'; \
    strncpy((config)->log.file, LOGLOOM_CONFIG_LOG_FILE, sizeof((config)->log.file)); \
    (config)->log.file[sizeof((config)->log.file) - 1] = '\0'; \
    (config)->log.max_size = LOGLOOM_CONFIG_LOG_MAX_SIZE; \
    (config)->log.console = LOGLOOM_CONFIG_LOG_CONSOLE; \
} while(0)

#endif /* LOGLOOM_CONFIG_GEN_H */
