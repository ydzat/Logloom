#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <unistd.h>
#include "config.h"

/** 全局配置对象实例化 */
logloom_config_t g_config;

/** 默认配置文件路径 */
#define DEFAULT_CONFIG_PATH "/etc/logloom/config.yaml"

/**
 * @brief 设置配置默认值
 * 
 * @param cfg 配置结构体指针
 */
static void config_set_defaults(logloom_config_t* cfg) {
    if (!cfg) return;

    /* 默认语言设置为英文 */
    strcpy(cfg->language, "en");
    
    /* 日志相关默认设置 */
    strcpy(cfg->log.level, "INFO");
    cfg->log.file[0] = '\0';  /* 默认不输出到文件 */
    cfg->log.max_size = 1048576;  /* 默认 1MB */
    cfg->log.console = true;  /* 默认输出到控制台 */
}

/**
 * @brief 从YAML文件解析配置（简化版，仅读取键值对）
 * 此处为简单实现，实际项目中应使用libyaml或yaml-cpp等库
 * 
 * @param path 配置文件路径
 * @param cfg 配置结构体指针
 * @return 0表示成功，非0表示失败
 */
static int parse_yaml_file(const char* path, logloom_config_t* cfg) {
    FILE* file = fopen(path, "r");
    if (!file) {
        fprintf(stderr, "[WARN] 无法打开配置文件: %s\n", path);
        return -1;
    }

    char line[512];
    char key[128];
    char value[256];
    
    /* 简单解析YAML文件的键值对 */
    while (fgets(line, sizeof(line), file)) {
        /* 跳过注释和空行 */
        if (line[0] == '#' || line[0] == '\n') continue;
        
        /* 尝试解析键值对，格式为：key: value */
        if (sscanf(line, "%[^:]: %[^\n]", key, value) == 2) {
            /* 去除可能的引号 */
            if (value[0] == '"' && value[strlen(value)-1] == '"') {
                value[strlen(value)-1] = '\0';
                memmove(value, value+1, strlen(value));
            }
            
            /* 处理特定配置项 */
            if (strstr(key, "language") != NULL) {
                strncpy(cfg->language, value, sizeof(cfg->language) - 1);
            } 
            else if (strstr(key, "log.level") != NULL) {
                strncpy(cfg->log.level, value, sizeof(cfg->log.level) - 1);
            }
            else if (strstr(key, "log.file") != NULL) {
                strncpy(cfg->log.file, value, sizeof(cfg->log.file) - 1);
            }
            else if (strstr(key, "log.max_size") != NULL) {
                cfg->log.max_size = atoi(value);
            }
            else if (strstr(key, "log.console") != NULL) {
                if (strcmp(value, "true") == 0 || strcmp(value, "1") == 0) {
                    cfg->log.console = true;
                } else if (strcmp(value, "false") == 0 || strcmp(value, "0") == 0) {
                    cfg->log.console = false;
                }
            }
        }
    }
    
    fclose(file);
    return 0;
}

int config_init(void) {
    /* 使用默认值初始化配置 */
    config_set_defaults(&g_config);
    return 0;
}

int config_load_from_file(const char* path) {
    /* 确保配置已初始化为默认值 */
    config_init();
    
    /* 如果未指定路径，尝试使用环境变量或默认路径 */
    const char* config_path = path;
    if (!config_path) {
        config_path = getenv("LOGLOOM_CONFIG");
        if (!config_path) {
            config_path = DEFAULT_CONFIG_PATH;
        }
    }
    
    /* 尝试解析配置文件 */
    if (access(config_path, R_OK) == 0) {
        printf("[INFO] 加载配置文件: %s\n", config_path);
        return parse_yaml_file(config_path, &g_config);
    } else {
        fprintf(stderr, "[WARN] 配置文件不存在或无法访问: %s，使用默认设置\n", config_path);
        return -1;
    }
}

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

void config_cleanup(void) {
    /* 目前没有需要清理的资源，预留接口以便未来扩展 */
}