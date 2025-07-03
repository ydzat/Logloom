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
    // 打印固定标题，不使用国际化（因为语言系统还未初始化）
    printf("=== Logloom Demo Program ===\n\n");
    
    // 1. 初始化配置系统
    printf("Loading configuration...\n");
    if (config_init() != 0) {
        printf("Error: Failed to initialize configuration\n");
        return 1;
    }
    
    // 从文件加载配置
    if (config_load_from_file("config.yaml") != 0) {
        printf("Notice: Failed to load configuration from file, using default settings\n");
    } else {
        printf("Configuration loaded successfully!\n");
    }
    
    // 2. 初始化语言系统，使用配置中的默认语言
    const char* default_lang = config_get_language();
    printf("\nInitializing language system (default language: %s)...\n", default_lang);
    if (lang_init(default_lang) != 0) {
        printf("Error: Failed to initialize language system\n");
        config_cleanup();
        return 1;
    }
    
    // 现在语言系统已初始化，可以安全地使用国际化功能
    char* current_lang_msg = lang_getf("demo.current_language", lang_get_current());
    printf("%s\n", current_lang_msg);
    free(current_lang_msg);
    
    // 显示一些配置信息 (现在使用国际化)
    char* log_path_msg = lang_getf("demo.log_file_path", config_get_log_file());
    printf("%s\n", log_path_msg);
    free(log_path_msg);
    
    char* log_level_msg = lang_getf("demo.log_level", config_get_log_level());
    printf("%s\n", log_level_msg);
    free(log_level_msg);
    
    char* default_lang_msg = lang_getf("demo.default_language", config_get_language());
    printf("%s\n", default_lang_msg);
    free(default_lang_msg);
    
    // 3. 初始化日志系统
    printf("\n%s\n", lang_get("demo.init_log_system"));
    
    // 获取配置中的日志级别
    const char* level_str = config_get_log_level();
    
    // 初始化日志系统
    if (log_init(level_str, NULL) != 0) {
        printf("%s\n", lang_get("demo.error.log_init_failed"));
        lang_cleanup();
        config_cleanup();
        return 1;
    }
    
    // 设置控制台输出
    log_set_console_enabled(config_is_console_enabled());
    
    // 设置日志文件
    const char* log_file = config_get_log_file();
    if (log_file && log_file[0] != '\0') {
        log_set_file(log_file);
        // 注意：log_set_file函数返回void，不再检查返回值
    }
    
    // 设置日志级别 - 确保直接使用配置获取的字符串
    log_set_level(level_str);
    
    // 设置日志文件大小限制
    log_set_max_file_size(config_get_max_log_size());
    
    printf("%s\n", lang_get("demo.log_init_success"));
    
    // 5. 记录各种级别的日志
    printf("\n%s\n", lang_get("demo.writing_logs"));
    
    // 定义一个模块名
    const char* module_name = "Demo";
    
    // DEBUG级别日志
    log_debug(module_name, lang_getf("demo.log.debug_message", getpid()));
    
    // INFO级别日志
    log_info(module_name, lang_getf("demo.log.info_message", "1.0.0"));
    
    // WARN级别日志
    log_warn(module_name, lang_getf("demo.log.warning_message", "old_option", "new_option"));
    
    // ERROR级别日志
    log_error(module_name, lang_getf("demo.log.error_message", "连接超时"));
    
    // 使用语言本地化
    char* error_msg = lang_getf("system.error_message", lang_get("demo.sample_error"));
    char* localized_msg = lang_getf("demo.localized_error", error_msg);
    log_info(module_name, "%s", localized_msg);
    free(error_msg);
    free(localized_msg);
    
    // 7. 切换语言演示
    printf("\n%s\n", lang_get("demo.language_switch_demo"));
    const char* current_lang = lang_get_current();
    const char* target_lang = strcmp(current_lang, "en") == 0 ? "zh" : "en";
    
    if (lang_set_language(target_lang)) {
        char* switch_success_msg = lang_getf("demo.language_switch_success", target_lang);
        printf("%s\n", switch_success_msg);
        free(switch_success_msg);
        
        char* welcome_after_switch_msg = lang_getf("demo.welcome_after_switch", lang_get("system.start_message"));
        printf("%s\n", welcome_after_switch_msg);
        free(welcome_after_switch_msg);
    } else {
        char* switch_failed_msg = lang_getf("demo.language_switch_failed", target_lang);
        printf("%s\n", switch_failed_msg);
        free(switch_failed_msg);
    }
    
    // 8. 清理资源
    printf("\n%s\n", lang_get("demo.cleaning_up"));
    
    // 保存退出消息，因为清理后无法再访问语言资源
    const char* exit_message = lang_get("demo.program_finished");
    
    log_cleanup();
    lang_cleanup();
    config_cleanup();
    
    printf("\n%s\n", exit_message);
    return 0;
}
