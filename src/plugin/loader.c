/**
 * @file loader.c
 * @brief Logloom插件系统加载器实现
 * 
 * 本文件实现了Logloom插件系统的核心加载与管理功能，包括：
 * - 插件动态加载
 * - 插件注册与管理
 * - 插件调用与生命周期控制
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>
#include <dirent.h>
#include <pthread.h>
#include <unistd.h>
#include <sys/stat.h>
#include <errno.h>
#include <limits.h>  // 添加limits.h用于INT_MAX定义
#include <cjson/cJSON.h>

// 兼容性定义：某些系统可能没有定义DT_REG
#ifndef DT_REG
#define DT_REG 8
#endif

#include "plugin.h"
#include "log.h"
#include "lang.h"  // 添加语言模块头文件
#include "generated/config_gen.h"

// 最大插件路径数量
#define MAX_PLUGIN_PATHS 10

/**
 * @brief 插件实例结构
 */
typedef struct plugin_instance {
    char name[64];               /**< 插件名称 */
    char path[256];              /**< 插件文件路径 */
    void* handle;                /**< 动态库句柄 */
    plugin_info_t info;          /**< 插件信息副本 */
    plugin_init_func_t init;     /**< 初始化函数 */
    plugin_process_func_t process; /**< 处理函数 */
    plugin_shutdown_func_t shutdown; /**< 关闭函数 */
    bool enabled;                /**< 是否启用 */
    int order;                   /**< 执行顺序（数字越小优先级越高） */
    cJSON* config;               /**< 插件特定配置 */
    struct plugin_instance* next; /**< 链表下一节点 */
} plugin_instance_t;

// 插件系统全局状态
static struct {
    plugin_instance_t* plugin_list;  /**< 插件链表头 */
    size_t plugin_count;             /**< 已加载插件数量 */
    pthread_mutex_t lock;            /**< 线程锁 */
    char plugin_paths[MAX_PLUGIN_PATHS][256]; /**< 插件目录 */
    int plugin_paths_count;          /**< 插件目录数量 */
    char** enabled_plugins;          /**< 启用的插件列表 */
    int enabled_plugins_count;       /**< 启用的插件数量 */
    char** disabled_plugins;         /**< 禁用的插件列表 */
    int disabled_plugins_count;      /**< 禁用的插件数量 */
    char** ordered_plugins;          /**< 顺序插件列表 */
    int ordered_plugins_count;       /**< 顺序插件数量 */
    cJSON* plugin_configs;           /**< 插件特定配置 */
    bool initialized;                /**< 是否已初始化 */
} plugin_ctx = {
    .plugin_list = NULL,
    .plugin_count = 0,
    .initialized = false,
    .plugin_paths_count = 0,
    .enabled_plugins_count = 0,
    .disabled_plugins_count = 0,
    .ordered_plugins_count = 0,
    .plugin_configs = NULL
};

// 前向声明
static plugin_instance_t* find_plugin_by_name(const char* name);
static bool load_plugin_symbols(plugin_instance_t* plugin);
static void log_plugin_error(const char* plugin_name, const char* message);
static bool parse_plugin_config(void);
static void free_plugin_config(void);
static int get_plugin_order(const char* plugin_name);
static bool is_plugin_enabled(const char* plugin_name);
static cJSON* get_plugin_specific_config(const char* plugin_name);

// 配置辅助函数前向声明
int plugin_get_config_int(const char* plugin_name, const char* key, int default_value);
const char* plugin_get_config_string(const char* plugin_name, const char* key, const char* default_value);
bool plugin_get_config_bool(const char* plugin_name, const char* key, bool default_value);
int plugin_get_config_string_array(const char* plugin_name, const char* key, const char** values, int max_count);

/**
 * @brief 解析插件配置
 * 
 * 从生成的配置头文件中解析插件配置
 * 
 * @return 成功返回true，失败返回false
 */
static bool parse_plugin_config(void) {
    bool result = false;
    cJSON* paths = NULL;
    cJSON* enabled = NULL;
    cJSON* disabled = NULL;
    cJSON* order = NULL;
    
    // 解析插件路径
    paths = cJSON_Parse(LOGLOOM_PLUGIN_PATHS_JSON);
    if (!paths || !cJSON_IsArray(paths)) {
        log_error("PLUGIN", "%s", lang_get("plugin.error.parsing_paths"));
        goto cleanup;
    }
    
    // 获取路径数量
    int paths_count = cJSON_GetArraySize(paths);
    if (paths_count > MAX_PLUGIN_PATHS) {
        char* msg = lang_getf("plugin.warning.too_many_paths", paths_count, MAX_PLUGIN_PATHS);
        log_warn("PLUGIN", "%s", msg);
        free(msg);
        paths_count = MAX_PLUGIN_PATHS;
    }
    
    // 复制插件路径
    for (int i = 0; i < paths_count; i++) {
        cJSON* path = cJSON_GetArrayItem(paths, i);
        if (cJSON_IsString(path) && path->valuestring) {
            strncpy(plugin_ctx.plugin_paths[i], path->valuestring, sizeof(plugin_ctx.plugin_paths[i]) - 1);
            plugin_ctx.plugin_paths[i][sizeof(plugin_ctx.plugin_paths[i]) - 1] = '\0';
            plugin_ctx.plugin_paths_count++;
        }
    }
    
    // 解析启用的插件列表
    enabled = cJSON_Parse(LOGLOOM_PLUGIN_ENABLED_JSON);
    if (enabled && cJSON_IsArray(enabled)) {
        int count = cJSON_GetArraySize(enabled);
        if (count > 0) {
            plugin_ctx.enabled_plugins = (char**)malloc(count * sizeof(char*));
            if (plugin_ctx.enabled_plugins) {
                for (int i = 0; i < count; i++) {
                    cJSON* item = cJSON_GetArrayItem(enabled, i);
                    if (cJSON_IsString(item) && item->valuestring) {
                        plugin_ctx.enabled_plugins[i] = strdup(item->valuestring);
                        if (plugin_ctx.enabled_plugins[i]) {
                            plugin_ctx.enabled_plugins_count++;
                        }
                    }
                }
            }
        }
    }
    
    // 解析禁用的插件列表
    disabled = cJSON_Parse(LOGLOOM_PLUGIN_DISABLED_JSON);
    if (disabled && cJSON_IsArray(disabled)) {
        int count = cJSON_GetArraySize(disabled);
        if (count > 0) {
            plugin_ctx.disabled_plugins = (char**)malloc(count * sizeof(char*));
            if (plugin_ctx.disabled_plugins) {
                for (int i = 0; i < count; i++) {
                    cJSON* item = cJSON_GetArrayItem(disabled, i);
                    if (cJSON_IsString(item) && item->valuestring) {
                        plugin_ctx.disabled_plugins[i] = strdup(item->valuestring);
                        if (plugin_ctx.disabled_plugins[i]) {
                            plugin_ctx.disabled_plugins_count++;
                        }
                    }
                }
            }
        }
    }
    
    // 解析插件顺序列表
    order = cJSON_Parse(LOGLOOM_PLUGIN_ORDER_JSON);
    if (order && cJSON_IsArray(order)) {
        int count = cJSON_GetArraySize(order);
        if (count > 0) {
            plugin_ctx.ordered_plugins = (char**)malloc(count * sizeof(char*));
            if (plugin_ctx.ordered_plugins) {
                for (int i = 0; i < count; i++) {
                    cJSON* item = cJSON_GetArrayItem(order, i);
                    if (cJSON_IsString(item) && item->valuestring) {
                        plugin_ctx.ordered_plugins[i] = strdup(item->valuestring);
                        if (plugin_ctx.ordered_plugins[i]) {
                            plugin_ctx.ordered_plugins_count++;
                        }
                    }
                }
            }
        }
    }
    
    // 解析插件特定配置
    plugin_ctx.plugin_configs = cJSON_Parse(LOGLOOM_PLUGIN_CONFIG_JSON);
    if (!plugin_ctx.plugin_configs) {
        log_warn("PLUGIN", "%s", lang_get("plugin.warning.config_parse_failed"));
    }
    
    result = true;
    
cleanup:
    if (paths) cJSON_Delete(paths);
    if (enabled) cJSON_Delete(enabled);
    if (disabled) cJSON_Delete(disabled);
    if (order) cJSON_Delete(order);
    
    return result;
}

/**
 * @brief 释放插件配置资源
 */
static void free_plugin_config(void) {
    // 释放启用的插件列表
    if (plugin_ctx.enabled_plugins) {
        for (int i = 0; i < plugin_ctx.enabled_plugins_count; i++) {
            free(plugin_ctx.enabled_plugins[i]);
        }
        free(plugin_ctx.enabled_plugins);
        plugin_ctx.enabled_plugins = NULL;
        plugin_ctx.enabled_plugins_count = 0;
    }
    
    // 释放禁用的插件列表
    if (plugin_ctx.disabled_plugins) {
        for (int i = 0; i < plugin_ctx.disabled_plugins_count; i++) {
            free(plugin_ctx.disabled_plugins[i]);
        }
        free(plugin_ctx.disabled_plugins);
        plugin_ctx.disabled_plugins = NULL;
        plugin_ctx.disabled_plugins_count = 0;
    }
    
    // 释放顺序插件列表
    if (plugin_ctx.ordered_plugins) {
        for (int i = 0; i < plugin_ctx.ordered_plugins_count; i++) {
            free(plugin_ctx.ordered_plugins[i]);
        }
        free(plugin_ctx.ordered_plugins);
        plugin_ctx.ordered_plugins = NULL;
        plugin_ctx.ordered_plugins_count = 0;
    }
    
    // 释放插件特定配置
    if (plugin_ctx.plugin_configs) {
        cJSON_Delete(plugin_ctx.plugin_configs);
        plugin_ctx.plugin_configs = NULL;
    }
}

/**
 * @brief 获取插件执行顺序
 * 
 * @param plugin_name 插件名称
 * @return 执行顺序（数字越小优先级越高），如果未找到则返回INT_MAX
 */
static int get_plugin_order(const char* plugin_name) {
    for (int i = 0; i < plugin_ctx.ordered_plugins_count; i++) {
        if (strcmp(plugin_ctx.ordered_plugins[i], plugin_name) == 0) {
            return i;
        }
    }
    return INT_MAX;  // 未找到，最低优先级
}

/**
 * @brief 判断插件是否启用
 * 
 * @param plugin_name 插件名称
 * @return 如果启用返回true，否则返回false
 */
static bool is_plugin_enabled(const char* plugin_name) {
    // 检查是否在禁用列表中
    for (int i = 0; i < plugin_ctx.disabled_plugins_count; i++) {
        if (strcmp(plugin_ctx.disabled_plugins[i], plugin_name) == 0) {
            return false;  // 在禁用列表中
        }
    }
    
    // 如果启用列表为空，则默认启用所有未禁用的插件
    if (plugin_ctx.enabled_plugins_count == 0) {
        return true;
    }
    
    // 检查是否在启用列表中
    for (int i = 0; i < plugin_ctx.enabled_plugins_count; i++) {
        if (strcmp(plugin_ctx.enabled_plugins[i], plugin_name) == 0) {
            return true;  // 在启用列表中
        }
    }
    
    return false;  // 不在启用列表中
}

/**
 * @brief 获取插件特定配置
 * 
 * @param plugin_name 插件名称
 * @return 插件配置对象，如果未找到则返回NULL
 */
static cJSON* get_plugin_specific_config(const char* plugin_name) {
    if (!plugin_ctx.plugin_configs) {
        return NULL;
    }
    
    return cJSON_GetObjectItem(plugin_ctx.plugin_configs, plugin_name);
}

/**
 * @brief 初始化插件系统
 * 
 * @param plugin_dir 插件目录路径，NULL表示使用配置文件中的路径
 * @return 成功返回0，失败返回非0值
 */
int plugin_system_init(const char* plugin_dir) {
    if (plugin_ctx.initialized) {
        log_warn("PLUGIN", "%s", lang_get("plugin.warning.already_initialized"));
        return 0;
    }
    
    // 初始化互斥锁
    if (pthread_mutex_init(&plugin_ctx.lock, NULL) != 0) {
        char* msg = lang_getf("plugin.error.mutex_init_failed", strerror(errno));
        log_error("PLUGIN", "%s", msg);
        free(msg);
        return -1;
    }
    
    // 解析配置
    if (!parse_plugin_config()) {
        log_warn("PLUGIN", "%s", lang_get("plugin.warning.config_parse_failed_using_default"));
    }
    
    // 如果提供了插件目录参数，覆盖配置中的第一个路径
    if (plugin_dir != NULL) {
        strncpy(plugin_ctx.plugin_paths[0], plugin_dir, sizeof(plugin_ctx.plugin_paths[0]) - 1);
        plugin_ctx.plugin_paths[0][sizeof(plugin_ctx.plugin_paths[0]) - 1] = '\0';
        if (plugin_ctx.plugin_paths_count == 0) {
            plugin_ctx.plugin_paths_count = 1;
        }
    }
    
    // 如果没有配置任何插件路径，使用默认路径
    if (plugin_ctx.plugin_paths_count == 0) {
        strncpy(plugin_ctx.plugin_paths[0], "/usr/lib/logloom/plugins", sizeof(plugin_ctx.plugin_paths[0]) - 1);
        plugin_ctx.plugin_paths_count = 1;
    }
    
    char* msg = lang_getf("plugin.info.initialized", plugin_ctx.plugin_paths[0]);
    log_info("PLUGIN", "%s", msg);
    free(msg);
    plugin_ctx.initialized = true;
    return 0;
}

/**
 * @brief 加载单个插件
 * 
 * @param plugin_path 插件文件路径
 * @return 成功返回插件实例指针，失败返回NULL
 */
static plugin_instance_t* load_plugin(const char* plugin_path) {
    // 创建插件实例
    plugin_instance_t* plugin = (plugin_instance_t*)malloc(sizeof(plugin_instance_t));
    if (!plugin) {
        char* msg = lang_getf("plugin.error.memory_allocation_failed", plugin_path);
        log_error("PLUGIN", "%s", msg);
        free(msg);
        return NULL;
    }
    
    memset(plugin, 0, sizeof(plugin_instance_t));
    strncpy(plugin->path, plugin_path, sizeof(plugin->path) - 1);
    
    // 提取插件名称（从路径中）
    const char* base_name = strrchr(plugin_path, '/');
    if (base_name) {
        base_name++; // 跳过'/'
    } else {
        base_name = plugin_path;
    }
    
    // 去掉扩展名
    char name_buf[64] = {0};
    strncpy(name_buf, base_name, sizeof(name_buf) - 1);
    char* ext = strrchr(name_buf, '.');
    if (ext) {
        *ext = '\0';
    }
    strncpy(plugin->name, name_buf, sizeof(plugin->name) - 1);
    
    // 检查插件是否启用
    plugin->enabled = is_plugin_enabled(plugin->name);
    if (!plugin->enabled) {
        char* msg = lang_getf("plugin.info.plugin_disabled", plugin->name);
        log_info("PLUGIN", "%s", msg);
        free(msg);
        free(plugin);
        return NULL;
    }
    
    // 获取插件执行顺序
    plugin->order = get_plugin_order(plugin->name);
    
    // 加载动态库
    plugin->handle = dlopen(plugin_path, RTLD_LAZY);
    if (!plugin->handle) {
        char* msg = lang_getf("plugin.error.load_failed", plugin->name, dlerror());
        log_error("PLUGIN", "%s", msg);
        free(msg);
        free(plugin);
        return NULL;
    }
    
    // 加载符号
    if (!load_plugin_symbols(plugin)) {
        dlclose(plugin->handle);
        free(plugin);
        return NULL;
    }
    
    // 获取插件信息
    plugin_info_func_t get_info = (plugin_info_func_t)dlsym(plugin->handle, "plugin_info");
    if (get_info) {
        const plugin_info_t* info = get_info();
        if (info) {
            // 复制信息到插件实例
            plugin->info.name = strdup(info->name ? info->name : plugin->name);
            plugin->info.version = strdup(info->version ? info->version : lang_get("plugin.info.unknown_version"));
            plugin->info.author = strdup(info->author ? info->author : lang_get("plugin.info.unknown_author"));
            plugin->info.type = info->type;
            plugin->info.mode = info->mode;
            plugin->info.capabilities = info->capabilities;
            plugin->info.description = strdup(info->description ? info->description : "");
        } else {
            char* msg = lang_getf("plugin.error.empty_info", plugin->name);
            log_error("PLUGIN", "%s", msg);
            free(msg);
            plugin->info.name = strdup(plugin->name);
            plugin->info.version = strdup(lang_get("plugin.info.unknown_version"));
            plugin->info.author = strdup(lang_get("plugin.info.unknown_author"));
            plugin->info.type = PLUGIN_TYPE_UNKNOWN;
            plugin->info.mode = PLUGIN_MODE_SYNC;
            plugin->info.capabilities = PLUGIN_CAP_NONE;
            plugin->info.description = strdup("");
        }
    } else {
        char* msg = lang_getf("plugin.warning.no_info_function", plugin->name);
        log_warn("PLUGIN", "%s", msg);
        free(msg);
        plugin->info.name = strdup(plugin->name);
        plugin->info.version = strdup(lang_get("plugin.info.unknown_version"));
        plugin->info.author = strdup(lang_get("plugin.info.unknown_author"));
        plugin->info.type = PLUGIN_TYPE_UNKNOWN;
        plugin->info.mode = PLUGIN_MODE_SYNC;
        plugin->info.capabilities = PLUGIN_CAP_NONE;
        plugin->info.description = strdup("");
    }
    
    // 获取插件特定配置
    plugin->config = get_plugin_specific_config(plugin->name);
    
    plugin->enabled = true;
    char* msg = lang_getf("plugin.info.load_success", plugin->info.name, plugin->info.version);
    log_info("PLUGIN", "%s", msg);
    free(msg);
    
    return plugin;
}

/**
 * @brief 加载插件符号
 * 
 * @param plugin 插件实例
 * @return 成功返回true，失败返回false
 */
static bool load_plugin_symbols(plugin_instance_t* plugin) {
    // 加载初始化函数（必需）
    plugin->init = (plugin_init_func_t)dlsym(plugin->handle, "plugin_init");
    if (!plugin->init) {
        log_plugin_error(plugin->name, lang_get("plugin.error.missing_init_function"));
        return false;
    }
    
    // 加载处理函数（必需）
    plugin->process = (plugin_process_func_t)dlsym(plugin->handle, "plugin_process");
    if (!plugin->process) {
        log_plugin_error(plugin->name, lang_get("plugin.error.missing_process_function"));
        return false;
    }
    
    // 加载关闭函数（必需）
    plugin->shutdown = (plugin_shutdown_func_t)dlsym(plugin->handle, "plugin_shutdown");
    if (!plugin->shutdown) {
        log_plugin_error(plugin->name, lang_get("plugin.error.missing_shutdown_function"));
        return false;
    }
    
    return true;
}

/**
 * @brief 记录插件错误
 * 
 * @param plugin_name 插件名称
 * @param message 错误消息
 */
static void log_plugin_error(const char* plugin_name, const char* message) {
    char* msg = lang_getf("plugin.error.general", plugin_name, message);
    log_error("PLUGIN", "%s", msg);
    free(msg);
}

/**
 * @brief 扫描插件目录并加载所有插件
 * 
 * @return 成功加载的插件数量
 */
size_t plugin_scan_and_load(void) {
    if (!plugin_ctx.initialized) {
        log_error("PLUGIN", "%s", lang_get("plugin.error.not_initialized"));
        return 0;
    }
    
    size_t loaded_count = 0;
    
    // 创建插件辅助函数结构体
    plugin_helpers_t helpers = {
        .get_config_int = plugin_get_config_int,
        .get_config_string = plugin_get_config_string,
        .get_config_bool = plugin_get_config_bool,
        .get_config_array = plugin_get_config_string_array
    };
    
    // 遍历所有配置的插件目录
    for (int dir_idx = 0; dir_idx < plugin_ctx.plugin_paths_count; dir_idx++) {
        DIR* dir = opendir(plugin_ctx.plugin_paths[dir_idx]);
        if (!dir) {
            char* msg = lang_getf("plugin.error.cannot_open_dir", 
                     plugin_ctx.plugin_paths[dir_idx], strerror(errno));
            log_error("PLUGIN", "%s", msg);
            free(msg);
            continue;
        }
        
        // 遍历目录
        struct dirent* entry;
        while ((entry = readdir(dir)) != NULL) {
            if (entry->d_type != DT_REG) {
                continue;  // 只处理常规文件
            }
            
            // 检查是否为.so文件
            const char* ext = strrchr(entry->d_name, '.');
            if (!ext || strcmp(ext, ".so") != 0) {
                continue;
            }
            
            // 构建完整路径
            char plugin_path[512];
            snprintf(plugin_path, sizeof(plugin_path), "%s/%s", 
                     plugin_ctx.plugin_paths[dir_idx], entry->d_name);
            
            // 加载插件
            pthread_mutex_lock(&plugin_ctx.lock);
            
            // 检查插件是否已加载
            if (find_plugin_by_name(entry->d_name)) {
                char* msg = lang_getf("plugin.warning.already_loaded", entry->d_name);
                log_warn("PLUGIN", "%s", msg);
                free(msg);
                pthread_mutex_unlock(&plugin_ctx.lock);
                continue;
            }
            
            plugin_instance_t* plugin = load_plugin(plugin_path);
            if (plugin) {
                // 添加到插件列表
                plugin->next = plugin_ctx.plugin_list;
                plugin_ctx.plugin_list = plugin;
                plugin_ctx.plugin_count++;
                loaded_count++;
                
                // 初始化插件，传递辅助函数
                int init_result = plugin->init(&helpers);
                if (init_result != 0) {
                    char* msg = lang_getf("plugin.error.init_failed", 
                              plugin->name, init_result);
                    log_error("PLUGIN", "%s", msg);
                    free(msg);
                    plugin->enabled = false;
                } else {
                    char* msg = lang_getf("plugin.info.init_success", plugin->name);
                    log_info("PLUGIN", "%s", msg);
                    free(msg);
                }
            }
            
            pthread_mutex_unlock(&plugin_ctx.lock);
        }
        
        closedir(dir);
    }
    
    char* msg = lang_getf("plugin.info.scan_complete", loaded_count);
    log_info("PLUGIN", "%s", msg);
    free(msg);
    return loaded_count;
}

/**
 * @brief 通过名称查找插件
 * 
 * @param name 插件名称
 * @return 找到返回插件实例指针，未找到返回NULL
 */
static plugin_instance_t* find_plugin_by_name(const char* name) {
    plugin_instance_t* current = plugin_ctx.plugin_list;
    while (current) {
        if (strcmp(current->name, name) == 0) {
            return current;
        }
        current = current->next;
    }
    return NULL;
}

/**
 * @brief 卸载所有插件
 */
void plugin_unload_all(void) {
    if (!plugin_ctx.initialized) {
        return;
    }
    
    pthread_mutex_lock(&plugin_ctx.lock);
    
    plugin_instance_t* current = plugin_ctx.plugin_list;
    while (current) {
        plugin_instance_t* next = current->next;
        
        // 调用关闭函数
        if (current->enabled && current->shutdown) {
            char* msg = lang_getf("plugin.info.shutting_down", current->name);
            log_info("PLUGIN", "%s", msg);
            free(msg);
            current->shutdown();
        }
        
        // 关闭动态库
        if (current->handle) {
            dlclose(current->handle);
        }
        
        // 释放插件信息
        free((void*)current->info.name);
        free((void*)current->info.version);
        free((void*)current->info.author);
        free((void*)current->info.description);
        
        // 释放插件实例
        free(current);
        current = next;
    }
    
    plugin_ctx.plugin_list = NULL;
    plugin_ctx.plugin_count = 0;
    
    pthread_mutex_unlock(&plugin_ctx.lock);
    log_info("PLUGIN", "%s", lang_get("plugin.info.all_plugins_unloaded"));
}

/**
 * @brief 设置插件状态（启用/禁用）
 * 
 * @param name 插件名称
 * @param enabled 是否启用
 * @return 成功返回true，失败返回false
 */
bool plugin_set_enabled(const char* name, bool enabled) {
    if (!plugin_ctx.initialized || !name) {
        return false;
    }
    
    pthread_mutex_lock(&plugin_ctx.lock);
    
    plugin_instance_t* plugin = find_plugin_by_name(name);
    if (!plugin) {
        pthread_mutex_unlock(&plugin_ctx.lock);
        char* msg = lang_getf("plugin.error.plugin_not_found", name);
        log_error("PLUGIN", "%s", msg);
        free(msg);
        return false;
    }
    
    plugin->enabled = enabled;
    
    pthread_mutex_unlock(&plugin_ctx.lock);
    char* msg = lang_getf("plugin.info.plugin_state_changed", name, enabled ? lang_get("plugin.enabled") : lang_get("plugin.disabled"));
    log_info("PLUGIN", "%s", msg);
    free(msg);
    return true;
}

/**
 * @brief 调用所有启用的过滤器插件处理日志条目
 * 
 * @param entry 日志条目
 * @return 允许通过的日志返回true，需要过滤的返回false
 */
bool plugin_filter_log(const log_entry_t* entry) {
    if (!plugin_ctx.initialized || !entry) {
        return true;  // 默认通过
    }
    
    bool should_pass = true;
    
    pthread_mutex_lock(&plugin_ctx.lock);
    
    plugin_instance_t* current = plugin_ctx.plugin_list;
    while (current) {
        // 只调用启用的过滤器插件
        if (current->enabled && 
            current->info.type == PLUGIN_TYPE_FILTER && 
            current->process) {
            
            int result = current->process(entry);
            if (result != PLUGIN_RESULT_OK) {
                // 过滤器插件要求过滤
                should_pass = false;
                break;
            }
        }
        current = current->next;
    }
    
    pthread_mutex_unlock(&plugin_ctx.lock);
    return should_pass;
}

/**
 * @brief 调用所有启用的输出插件处理日志条目
 * 
 * @param entry 日志条目
 */
void plugin_sink_log(const log_entry_t* entry) {
    if (!plugin_ctx.initialized || !entry) {
        return;
    }
    
    pthread_mutex_lock(&plugin_ctx.lock);
    
    plugin_instance_t* current = plugin_ctx.plugin_list;
    while (current) {
        // 只调用启用的输出插件
        if (current->enabled && 
            current->info.type == PLUGIN_TYPE_SINK && 
            current->process) {
            
            current->process(entry);
        }
        current = current->next;
    }
    
    pthread_mutex_unlock(&plugin_ctx.lock);
}

/**
 * @brief 调用所有启用的AI插件处理日志条目
 * 
 * @param entry 日志条目
 */
void plugin_ai_process(const log_entry_t* entry) {
    if (!plugin_ctx.initialized || !entry) {
        return;
    }
    
    pthread_mutex_lock(&plugin_ctx.lock);
    
    plugin_instance_t* current = plugin_ctx.plugin_list;
    while (current) {
        // 只调用启用的AI插件
        if (current->enabled && 
            current->info.type == PLUGIN_TYPE_AI && 
            current->process) {
            
            current->process(entry);
        }
        current = current->next;
    }
    
    pthread_mutex_unlock(&plugin_ctx.lock);
}

/**
 * @brief 获取已加载插件数量
 * 
 * @return 插件数量
 */
size_t plugin_get_count(void) {
    return plugin_ctx.plugin_count;
}

/**
 * @brief 获取插件信息
 * 
 * @param index 插件索引（从0开始）
 * @return 插件信息指针，未找到返回NULL
 */
const plugin_info_t* plugin_get_info(size_t index) {
    if (!plugin_ctx.initialized || index >= plugin_ctx.plugin_count) {
        return NULL;
    }
    
    pthread_mutex_lock(&plugin_ctx.lock);
    
    plugin_instance_t* current = plugin_ctx.plugin_list;
    size_t current_index = 0;
    
    while (current && current_index < index) {
        current = current->next;
        current_index++;
    }
    
    const plugin_info_t* info = current ? &current->info : NULL;
    
    pthread_mutex_unlock(&plugin_ctx.lock);
    return info;
}

/**
 * @brief 通过名称获取插件信息
 * 
 * @param name 插件名称
 * @return 插件信息指针，未找到返回NULL
 */
const plugin_info_t* plugin_get_info_by_name(const char* name) {
    if (!plugin_ctx.initialized || !name) {
        return NULL;
    }
    
    pthread_mutex_lock(&plugin_ctx.lock);
    
    plugin_instance_t* plugin = find_plugin_by_name(name);
    const plugin_info_t* info = plugin ? &plugin->info : NULL;
    
    pthread_mutex_unlock(&plugin_ctx.lock);
    return info;
}

/**
 * @brief 清理插件系统
 */
void plugin_system_cleanup(void) {
    if (!plugin_ctx.initialized) {
        return;
    }
    
    // 卸载所有插件
    plugin_unload_all();
    
    // 销毁互斥锁
    pthread_mutex_destroy(&plugin_ctx.lock);
    
    // 释放配置资源
    free_plugin_config();
    
    plugin_ctx.initialized = false;
    log_info("PLUGIN", "%s", lang_get("plugin.system.cleanup"));
}

/**
 * @brief 获取插件特定配置值（整数）
 * 
 * @param plugin_name 插件名称
 * @param key 配置键
 * @param default_value 默认值
 * @return 配置值，如果未找到则返回默认值
 */
int plugin_get_config_int(const char* plugin_name, const char* key, int default_value) {
    if (!plugin_ctx.plugin_configs) {
        return default_value;
    }
    
    cJSON* plugin_config = cJSON_GetObjectItem(plugin_ctx.plugin_configs, plugin_name);
    if (!plugin_config) {
        return default_value;
    }
    
    cJSON* value = cJSON_GetObjectItem(plugin_config, key);
    if (!value || !cJSON_IsNumber(value)) {
        return default_value;
    }
    
    return value->valueint;
}

/**
 * @brief 获取插件特定配置值（字符串）
 * 
 * @param plugin_name 插件名称
 * @param key 配置键
 * @param default_value 默认值
 * @return 配置值，如果未找到则返回默认值
 */
const char* plugin_get_config_string(const char* plugin_name, const char* key, const char* default_value) {
    if (!plugin_ctx.plugin_configs) {
        return default_value;
    }
    
    cJSON* plugin_config = cJSON_GetObjectItem(plugin_ctx.plugin_configs, plugin_name);
    if (!plugin_config) {
        return default_value;
    }
    
    cJSON* value = cJSON_GetObjectItem(plugin_config, key);
    if (!value || !cJSON_IsString(value)) {
        return default_value;
    }
    
    return value->valuestring;
}

/**
 * @brief 获取插件特定配置值（布尔值）
 * 
 * @param plugin_name 插件名称
 * @param key 配置键
 * @param default_value 默认值
 * @return 配置值，如果未找到则返回默认值
 */
bool plugin_get_config_bool(const char* plugin_name, const char* key, bool default_value) {
    if (!plugin_ctx.plugin_configs) {
        return default_value;
    }
    
    cJSON* plugin_config = cJSON_GetObjectItem(plugin_ctx.plugin_configs, plugin_name);
    if (!plugin_config) {
        return default_value;
    }
    
    cJSON* value = cJSON_GetObjectItem(plugin_config, key);
    if (!value || !cJSON_IsBool(value)) {
        return default_value;
    }
    
    return cJSON_IsTrue(value);
}

/**
 * @brief 获取插件特定配置值（字符串数组）
 * 
 * @param plugin_name 插件名称
 * @param key 配置键
 * @param values 存放字符串数组的指针
 * @param max_count 最大数组元素数量
 * @return 实际获取的数组元素数量
 */
int plugin_get_config_string_array(const char* plugin_name, const char* key, 
                                   const char** values, int max_count) {
    if (!plugin_ctx.plugin_configs || !values || max_count <= 0) {
        return 0;
    }
    
    cJSON* plugin_config = cJSON_GetObjectItem(plugin_ctx.plugin_configs, plugin_name);
    if (!plugin_config) {
        return 0;
    }
    
    cJSON* array = cJSON_GetObjectItem(plugin_config, key);
    if (!array || !cJSON_IsArray(array)) {
        return 0;
    }
    
    int count = 0;
    for (int i = 0; i < cJSON_GetArraySize(array) && i < max_count; i++) {
        cJSON* item = cJSON_GetArrayItem(array, i);
        if (cJSON_IsString(item) && item->valuestring) {
            values[count++] = item->valuestring;
        }
    }
    
    return count;
}