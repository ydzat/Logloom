/**
 * @file sample_filter_plugin.c
 * @brief 示例过滤器插件
 * 
 * 这是一个简单的过滤器插件示例，用于演示Logloom插件系统的使用方法。
 * 该插件会过滤包含配置中指定关键字的日志。
 */

#define _GNU_SOURCE  // 为了使用strcasestr函数
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "plugin.h"

// 插件配置
static struct {
    const char** keywords;        // 关键字列表
    int keywords_count;           // 关键字数量
    bool case_sensitive;          // 是否大小写敏感
} plugin_config = {
    .keywords = NULL,
    .keywords_count = 0,
    .case_sensitive = false
};

// 插件辅助函数
static plugin_helpers_t plugin_helpers;

/**
 * @brief 插件初始化函数
 * 
 * 在插件加载时调用，用于初始化插件资源
 * 
 * @param helpers 插件辅助函数
 * @return 0表示成功，非0表示失败
 */
int plugin_init(const plugin_helpers_t* helpers) {
    printf("[示例过滤器插件] 初始化成功\n");
    
    // 存储辅助函数
    if (helpers) {
        plugin_helpers = *helpers;
    }
    
    // 获取配置中的大小写敏感设置
    if (helpers && helpers->get_config_bool) {
        plugin_config.case_sensitive = helpers->get_config_bool(
            "sample_filter", "case_sensitive", false);
    }
    
    // 获取配置中的关键字列表
    const char* keywords[20];  // 最多支持20个关键字
    if (helpers && helpers->get_config_array) {
        plugin_config.keywords_count = helpers->get_config_array(
            "sample_filter", "keywords", keywords, 20);
    }
    
    // 复制关键字列表
    if (plugin_config.keywords_count > 0) {
        plugin_config.keywords = (const char**)malloc(plugin_config.keywords_count * sizeof(char*));
        if (plugin_config.keywords) {
            for (int i = 0; i < plugin_config.keywords_count; i++) {
                plugin_config.keywords[i] = strdup(keywords[i]);
                printf("[示例过滤器插件] 加载关键字: %s\n", plugin_config.keywords[i]);
            }
        } else {
            plugin_config.keywords_count = 0;
        }
    }
    
    // 如果没有设置关键字，使用默认关键字"ERROR"
    if (plugin_config.keywords_count == 0) {
        plugin_config.keywords = (const char**)malloc(sizeof(char*));
        if (plugin_config.keywords) {
            plugin_config.keywords[0] = strdup("ERROR");
            plugin_config.keywords_count = 1;
            printf("[示例过滤器插件] 使用默认关键字: ERROR\n");
        }
    }
    
    printf("[示例过滤器插件] 大小写敏感: %s\n", 
           plugin_config.case_sensitive ? "是" : "否");
    
    return 0;
}

/**
 * @brief 插件处理函数
 * 
 * 过滤包含关键字的日志
 * 
 * @param entry 日志条目
 * @return 处理结果状态码
 */
int plugin_process(const log_entry_t* entry) {
    if (!entry || !entry->message) {
        return PLUGIN_RESULT_OK;  // 空消息不过滤
    }
    
    // 遍历所有关键字
    for (int i = 0; i < plugin_config.keywords_count; i++) {
        if (!plugin_config.keywords[i]) {
            continue;
        }
        
        // 根据大小写敏感设置选择搜索方式
        bool found = false;
        if (plugin_config.case_sensitive) {
            // 大小写敏感搜索
            found = strstr(entry->message, plugin_config.keywords[i]) != NULL;
        } else {
            // 大小写不敏感搜索
            found = strcasestr(entry->message, plugin_config.keywords[i]) != NULL;
        }
        
        // 如果找到关键字，过滤该日志
        if (found) {
            printf("[示例过滤器插件] 过滤包含 '%s' 的日志: %s\n", 
                   plugin_config.keywords[i], entry->message);
            return PLUGIN_RESULT_SKIP;
        }
    }
    
    // 未找到关键字，允许通过
    return PLUGIN_RESULT_OK;
}

/**
 * @brief 插件关闭函数
 * 
 * 在插件卸载时调用，用于释放插件资源
 */
void plugin_shutdown(void) {
    // 释放关键字列表
    if (plugin_config.keywords) {
        for (int i = 0; i < plugin_config.keywords_count; i++) {
            if (plugin_config.keywords[i]) {
                free((void*)plugin_config.keywords[i]);
            }
        }
        free(plugin_config.keywords);
        plugin_config.keywords = NULL;
        plugin_config.keywords_count = 0;
    }
    
    printf("[示例过滤器插件] 关闭成功\n");
}

/**
 * @brief 插件信息结构
 */
static const plugin_info_t filter_plugin_info = {
    .name = "sample_filter",
    .version = "1.0.0",
    .author = "Logloom Team",
    .type = PLUGIN_TYPE_FILTER,
    .mode = PLUGIN_MODE_SYNC,
    .capabilities = PLUGIN_CAP_NONE,
    .description = "示例过滤器插件，过滤包含配置中指定关键字的日志"
};

/**
 * @brief 获取插件信息
 * 
 * @return 插件信息结构指针
 */
const plugin_info_t* plugin_info(void) {
    return &filter_plugin_info;
}