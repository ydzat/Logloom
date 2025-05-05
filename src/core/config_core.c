#include "config.h"
#include "../shared/platform.h"

/** 全局配置对象实例化 */
logloom_config_t g_config;

/**
 * @brief 设置配置默认值
 * 
 * @param cfg 配置结构体指针
 */
void config_set_defaults(logloom_config_t* cfg) {
    if (!cfg) return;

    /* 默认语言设置为英文 */
    strcpy(cfg->language, "en");
    
    /* 日志相关默认设置 */
    strcpy(cfg->log.level, "INFO");
    cfg->log.file[0] = '\0';  /* 默认不输出到文件 */
    cfg->log.max_size = 1048576;  /* 默认 1MB */
    cfg->log.console = 1;  /* 默认输出到控制台 */
}

#ifndef __KERNEL__
/* 以下函数在内核模块中有各自的实现，避免重复定义 */

const char* config_get_log_level(void) {
    return g_config.log.level;
}

const char* config_get_log_file(void) {
    return g_config.log.file;
}

bool config_is_console_enabled(void) {
    return g_config.log.console;
}

size_t config_get_max_log_size(void) {
    return g_config.log.max_size;
}

const char* config_get_language(void) {
    return g_config.language;
}
#endif /* !__KERNEL__ */