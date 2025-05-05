/**
 * @file plugin_test.c
 * @brief 插件系统测试文件
 *
 * 本文件测试Logloom插件系统的基础功能，包括：
 * - 插件系统初始化
 * - 插件加载
 * - 插件API调用
 * - 插件配置读取
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <dlfcn.h>
#include <assert.h>
#include <time.h>

#include "log.h"
#include "plugin.h"
#include "generated/config_gen.h"

// 声明插件系统函数
extern int plugin_system_init(const char* plugin_dir);
extern size_t plugin_scan_and_load(void);
extern void plugin_unload_all(void);
extern void plugin_system_cleanup(void);
extern bool plugin_set_enabled(const char* name, bool enabled);
extern bool plugin_filter_log(const log_entry_t* entry);
extern void plugin_sink_log(const log_entry_t* entry);
extern size_t plugin_get_count(void);
extern const plugin_info_t* plugin_get_info(size_t index);
extern const plugin_info_t* plugin_get_info_by_name(const char* name);
extern int plugin_get_config_int(const char* plugin_name, const char* key, int default_value);
extern const char* plugin_get_config_string(const char* plugin_name, const char* key, const char* default_value);
extern bool plugin_get_config_bool(const char* plugin_name, const char* key, bool default_value);

// 测试插件实现函数
int plugin_init(const plugin_helpers_t* helpers) {
    printf("测试插件初始化成功\n");
    return 0;
}

int plugin_process(const log_entry_t* entry) {
    printf("测试插件处理日志：[%s] %s\n", entry->module, entry->message);
    return 0;  // 返回PLUGIN_RESULT_OK
}

void plugin_shutdown(void) {
    printf("测试插件关闭\n");
}

// 插件信息
static const plugin_info_t test_plugin_info = {
    .name = "test_plugin",
    .version = "1.0.0",
    .author = "Logloom Test",
    .type = PLUGIN_TYPE_FILTER,
    .mode = PLUGIN_MODE_SYNC,
    .capabilities = PLUGIN_CAP_NONE,
    .description = "用于测试的插件"
};

const plugin_info_t* plugin_info(void) {
    return &test_plugin_info;
}

// 创建测试日志条目
static log_entry_t create_test_log_entry(const char* message) {
    log_entry_t entry;
    
    // 设置时间戳
    entry.timestamp = time(NULL);
    
    // 设置日志级别
    entry.level = LOG_LEVEL_INFO;
    
    // 设置其他字段（使用静态字符串，无需复制）
    entry.module = "TEST";
    entry.message = message ? message : "这是一条测试日志消息";
    entry.lang_key = "test.message";
    
    return entry;
}

// 测试插件系统初始化
static void test_plugin_system_init(void) {
    printf("\n===== 测试插件系统初始化 =====\n");
    
    // 初始化插件系统
    int result = plugin_system_init("./plugins");
    assert(result == 0);
    printf("插件系统初始化成功\n");
    
    // 输出插件配置信息
    printf("插件配置信息:\n");
    printf("路径: %s\n", LOGLOOM_PLUGIN_PATHS_JSON);
    printf("启用的插件: %s\n", LOGLOOM_PLUGIN_ENABLED_JSON);
    printf("禁用的插件: %s\n", LOGLOOM_PLUGIN_DISABLED_JSON);
    printf("插件顺序: %s\n", LOGLOOM_PLUGIN_ORDER_JSON);
    printf("插件特定配置: %s\n", LOGLOOM_PLUGIN_CONFIG_JSON);
}

// 测试插件加载
static void test_plugin_loading(void) {
    printf("\n===== 测试插件加载 =====\n");
    
    // 扫描并加载插件
    size_t loaded_count = plugin_scan_and_load();
    printf("加载了 %zu 个插件\n", loaded_count);
    
    // 获取插件信息
    if (loaded_count > 0) {
        for (size_t i = 0; i < loaded_count; i++) {
            const plugin_info_t* info = plugin_get_info(i);
            if (info) {
                printf("插件 #%zu:\n", i + 1);
                printf("  名称：%s\n", info->name);
                printf("  版本：%s\n", info->version);
                printf("  作者：%s\n", info->author);
                printf("  描述：%s\n", info->description);
                printf("  类型：%d\n", info->type);
            }
        }
    }
}

// 测试示例过滤器插件
static void test_sample_filter_plugin(void) {
    printf("\n===== 测试示例过滤器插件 =====\n");
    
    // 获取示例过滤器插件配置
    printf("示例过滤器插件配置:\n");
    bool case_sensitive = plugin_get_config_bool("sample_filter", "case_sensitive", false);
    printf("  大小写敏感: %s\n", case_sensitive ? "是" : "否");
    
    // 创建正常日志
    log_entry_t normal_entry = create_test_log_entry("这是一条正常日志");
    
    // 创建包含配置中关键字的日志（ERROR、FATAL、CRITICAL）
    log_entry_t error_entry = create_test_log_entry("这是一条包含ERROR的日志");
    log_entry_t fatal_entry = create_test_log_entry("这是一条包含FATAL的日志");
    log_entry_t critical_entry = create_test_log_entry("这是一条包含CRITICAL的日志");
    
    // 创建小写关键字的日志
    log_entry_t lower_error_entry = create_test_log_entry("这是一条包含error的日志");
    
    // 调用过滤器插件API处理正常日志
    printf("处理正常日志...\n");
    bool should_pass_normal = plugin_filter_log(&normal_entry);
    printf("过滤器结果（应该通过）：%s\n", should_pass_normal ? "通过" : "过滤");
    
    // 调用过滤器插件API处理包含ERROR的日志
    printf("处理包含ERROR的日志...\n");
    bool should_pass_error = plugin_filter_log(&error_entry);
    printf("过滤器结果（应该过滤）：%s\n", should_pass_error ? "通过" : "过滤");
    
    // 调用过滤器插件API处理包含FATAL的日志
    printf("处理包含FATAL的日志...\n");
    bool should_pass_fatal = plugin_filter_log(&fatal_entry);
    printf("过滤器结果（应该过滤）：%s\n", should_pass_fatal ? "通过" : "过滤");
    
    // 调用过滤器插件API处理包含CRITICAL的日志
    printf("处理包含CRITICAL的日志...\n");
    bool should_pass_critical = plugin_filter_log(&critical_entry);
    printf("过滤器结果（应该过滤）：%s\n", should_pass_critical ? "通过" : "过滤");
    
    // 调用过滤器插件API处理包含小写error的日志
    printf("处理包含小写error的日志...\n");
    bool should_pass_lower_error = plugin_filter_log(&lower_error_entry);
    printf("过滤器结果（%s大小写敏感，应该%s）：%s\n", 
           case_sensitive ? "" : "不",
           case_sensitive ? "通过" : "过滤", 
           should_pass_lower_error ? "通过" : "过滤");
}

// 测试插件API调用
static void test_plugin_api(void) {
    printf("\n===== 测试插件API调用 =====\n");
    
    // 创建测试日志条目
    log_entry_t entry = create_test_log_entry(NULL);
    
    // 调用过滤器插件API
    printf("调用过滤器插件API...\n");
    bool should_pass = plugin_filter_log(&entry);
    printf("过滤器结果：%s\n", should_pass ? "通过" : "过滤");
    
    // 调用输出插件API
    printf("调用输出插件API...\n");
    plugin_sink_log(&entry);
    
    // 获取插件数量
    size_t count = plugin_get_count();
    printf("已加载插件数量：%zu\n", count);
}

// 主函数
int main(int argc, char* argv[]) {
    // 初始化日志系统
    log_init("DEBUG", NULL);
    log_set_console_enabled(1);
    
    printf("Logloom插件系统测试开始...\n");
    
    // 测试插件系统初始化
    test_plugin_system_init();
    
    // 测试插件加载
    test_plugin_loading();
    
    // 测试示例过滤器插件
    test_sample_filter_plugin();
    
    // 测试插件API调用
    test_plugin_api();
    
    // 清理插件系统
    printf("\n===== 清理插件系统 =====\n");
    plugin_unload_all();
    plugin_system_cleanup();
    printf("插件系统清理完成\n");
    
    // 清理日志系统
    log_cleanup();
    
    printf("\nLogloom插件系统测试完成\n");
    return 0;
}