#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include "lang.h"
#include "config.h"
#include "log.h"
#include "plugin.h"

int main(int argc, char** argv) {
    printf("=== Logloom 演示程序 ===\n\n");
    
    // 1. 初始化配置系统
    printf("正在加载配置...\n");
    if (config_init() != 0) {
        printf("错误：无法初始化配置\n");
        return 1;
    }
    
    // 从文件加载配置
    if (config_load_from_file("config.yaml") != 0) {
        printf("注意：无法从文件加载配置，使用默认配置\n");
    }
    
    // 显示一些配置信息
    printf("配置加载成功！\n");
    printf("日志文件路径: %s\n", config_get_log_file());
    printf("日志级别: %s\n", config_get_log_level());
    printf("默认语言: %s\n", config_get_language());
    
    // 2. 初始化语言系统，使用配置中的默认语言
    const char* default_lang = config_get_language();
    printf("\n正在初始化语言系统（默认语言：%s）...\n", default_lang);
    if (lang_init(default_lang) != 0) {
        printf("错误：无法初始化语言系统\n");
        config_cleanup();
        return 1;
    }
    
    printf("当前语言: %s\n", lang_get_current());
    printf("系统启动消息: %s\n", lang_get("system.start_message"));
    
    // 3. 初始化日志系统
    printf("\n正在初始化日志系统...\n");
    log_level_t log_level = LOG_LEVEL_INFO; // 默认日志级别
    
    // 根据配置设置日志级别
    const char* level_str = config_get_log_level();
    if (strcmp(level_str, "DEBUG") == 0) log_level = LOG_LEVEL_DEBUG;
    else if (strcmp(level_str, "WARN") == 0) log_level = LOG_LEVEL_WARN;
    else if (strcmp(level_str, "ERROR") == 0) log_level = LOG_LEVEL_ERROR;
    
    // 初始化日志系统，暂时使用控制台输出
    bool use_console = config_is_console_enabled();
    if (log_init(log_level, use_console) != 0) {
        printf("错误：无法初始化日志系统\n");
        lang_cleanup();
        config_cleanup();
        return 1;
    }
    
    // 设置日志文件
    const char* log_file = config_get_log_file();
    if (log_file && log_file[0] != '\0') {
        if (!log_set_output_file(log_file)) {
            printf("警告：无法设置日志文件：%s\n", log_file);
        }
    }
    
    // 设置日志文件大小限制
    log_set_max_file_size(config_get_max_log_size());
    
    printf("日志系统初始化成功！\n");
    
    // 5. 记录各种级别的日志
    printf("\n正在写入不同级别的日志...\n");
    
    // 定义一个模块名
    const char* module_name = "Demo";
    
    // DEBUG级别日志
    log_debug(module_name, "这是一条调试日志，包含详细信息: pid=%d", getpid());
    
    // INFO级别日志
    log_info(module_name, "系统初始化完成，版本: %s", "1.0.0");
    
    // WARN级别日志
    log_warn(module_name, "发现潜在问题：配置项'%s'已弃用，请使用'%s'", "old_option", "new_option");
    
    // ERROR级别日志
    log_error(module_name, "处理请求时出错：%s", "连接超时");
    
    // 使用语言本地化
    char* error_msg = lang_getf("system.error_message", "示例错误");
    log_info(module_name, "本地化错误消息: %s", error_msg);
    free(error_msg);
    
    // 7. 切换语言演示
    printf("\n切换语言演示...\n");
    const char* current_lang = lang_get_current();
    const char* target_lang = strcmp(current_lang, "en") == 0 ? "zh" : "en";
    
    if (lang_set_language(target_lang)) {
        printf("成功切换到语言: %s\n", target_lang);
        printf("欢迎消息: %s\n", lang_get("system.start_message"));
    } else {
        printf("无法切换到语言: %s\n", target_lang);
    }
    
    // 8. 清理资源
    printf("\n正在清理资源...\n");
    log_cleanup();
    lang_cleanup();
    config_cleanup();
    
    printf("\n演示程序运行完毕！\n");
    return 0;
}
