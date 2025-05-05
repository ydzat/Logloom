/**
 * @file plugin.h
 * @brief Logloom插件系统接口定义
 * 
 * 本文件定义了Logloom插件系统的核心接口和数据结构，包括：
 * - 插件类型定义
 * - 插件元信息结构
 * - 核心插件API
 */

#ifndef LOGLOOM_PLUGIN_H
#define LOGLOOM_PLUGIN_H

#include <stdint.h>
#include <stdbool.h>
#include "log.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 插件类型枚举
 */
typedef enum {
    PLUGIN_TYPE_FILTER = 0,  /**< 日志过滤器插件 */
    PLUGIN_TYPE_SINK,        /**< 日志输出插件 */
    PLUGIN_TYPE_AI,          /**< AI分析插件 */
    PLUGIN_TYPE_LANG,        /**< 语言资源插件 */
    PLUGIN_TYPE_UNKNOWN      /**< 未知类型 */
} plugin_type_t;

/**
 * @brief 插件调用模式
 */
typedef enum {
    PLUGIN_MODE_SYNC = 0,    /**< 同步调用模式 */
    PLUGIN_MODE_ASYNC        /**< 异步调用模式 */
} plugin_mode_t;

/**
 * @brief 插件能力标识
 */
typedef enum {
    PLUGIN_CAP_NONE = 0,         /**< 无特殊能力 */
    PLUGIN_CAP_BATCH = 1 << 0,   /**< 支持批处理 */
    PLUGIN_CAP_JSON = 1 << 1,    /**< 支持JSON格式 */
    PLUGIN_CAP_STREAM = 1 << 2   /**< 支持流式处理 */
} plugin_capability_t;

/**
 * @brief 插件元信息结构
 */
typedef struct {
    const char* name;            /**< 插件名称 */
    const char* version;         /**< 插件版本 */
    const char* author;          /**< 插件作者 */
    plugin_type_t type;          /**< 插件类型 */
    plugin_mode_t mode;          /**< 调用模式 */
    uint32_t capabilities;       /**< 插件能力标识 */
    const char* description;     /**< 插件描述 */
} plugin_info_t;

/**
 * @brief 插件处理结果状态码
 */
typedef enum {
    PLUGIN_RESULT_OK = 0,        /**< 处理成功 */
    PLUGIN_RESULT_ERROR,         /**< 处理失败 */
    PLUGIN_RESULT_SKIP,          /**< 跳过处理 */
    PLUGIN_RESULT_RETRY          /**< 重试请求 */
} plugin_result_t;

/**
 * @brief 插件辅助函数类型定义
 */
typedef int (*plugin_get_config_int_func_t)(const char* plugin_name, const char* key, int default_value);
typedef const char* (*plugin_get_config_string_func_t)(const char* plugin_name, const char* key, const char* default_value);
typedef bool (*plugin_get_config_bool_func_t)(const char* plugin_name, const char* key, bool default_value);
typedef int (*plugin_get_config_string_array_func_t)(const char* plugin_name, const char* key, const char** values, int max_count);

/**
 * @brief 插件辅助函数结构体
 * 提供给插件使用的辅助函数
 */
typedef struct {
    plugin_get_config_int_func_t get_config_int;             /**< 获取整数配置 */
    plugin_get_config_string_func_t get_config_string;       /**< 获取字符串配置 */
    plugin_get_config_bool_func_t get_config_bool;           /**< 获取布尔值配置 */
    plugin_get_config_string_array_func_t get_config_array;  /**< 获取字符串数组配置 */
} plugin_helpers_t;

/**
 * @brief 插件接口函数类型定义
 */
typedef int (*plugin_init_func_t)(const plugin_helpers_t* helpers);
typedef int (*plugin_process_func_t)(const log_entry_t* entry);
typedef void (*plugin_shutdown_func_t)(void);
typedef const plugin_info_t* (*plugin_info_func_t)(void);

/* 
 * 插件必须导出以下符号：
 * - plugin_init
 * - plugin_process
 * - plugin_shutdown
 * - plugin_info（可选）
 */

/**
 * @brief 初始化插件
 * 
 * 在插件加载后调用，用于初始化插件资源
 * 
 * @param helpers 插件辅助函数结构体，提供配置访问等功能
 * @return 0表示成功，非0表示失败
 */
extern int plugin_init(const plugin_helpers_t* helpers);

/**
 * @brief 处理日志条目
 * 
 * 插件核心处理函数，根据插件类型处理日志数据
 * 
 * @param entry 日志条目指针
 * @return 处理结果状态码
 */
extern int plugin_process(const log_entry_t* entry);

/**
 * @brief 关闭插件
 * 
 * 在插件卸载前调用，用于释放插件资源
 */
extern void plugin_shutdown(void);

/**
 * @brief 获取插件信息
 * 
 * @return 插件元信息结构指针
 */
extern const plugin_info_t* plugin_info(void);

#ifdef __cplusplus
}
#endif

#endif /* LOGLOOM_PLUGIN_H */