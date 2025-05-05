#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/slab.h>
#include <linux/version.h>
#include <linux/utsname.h>
#include "log.h"
#include "lang.h"
#include "config.h"

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Logloom Team");
MODULE_DESCRIPTION("Logloom kernel module for logging and internationalization");
MODULE_VERSION("0.1.0");

// 定义一个模块版本常量，可以在代码中使用
#define LOGLOOM_MODULE_VERSION "0.1.0"

/* 模块参数定义 */
static char* log_level = "INFO";
module_param(log_level, charp, 0644);
MODULE_PARM_DESC(log_level, "Default log level (DEBUG, INFO, WARN, ERROR, FATAL)");

static char* log_file = NULL;
module_param(log_file, charp, 0644);
MODULE_PARM_DESC(log_file, "Path to log file");

static char* language = "en";
module_param(language, charp, 0644);
MODULE_PARM_DESC(language, "Default language (e.g., en, zh)");

static bool console_output = true;
module_param(console_output, bool, 0644);
MODULE_PARM_DESC(console_output, "Enable console output (true/false)");

/* 模块状态跟踪 */
typedef enum {
    MODULE_STATE_NONE = 0,
    MODULE_STATE_CONFIG_INIT,
    MODULE_STATE_LANG_INIT,
    MODULE_STATE_LOG_INIT,
    MODULE_STATE_FULLY_INITIALIZED
} module_state_t;

static module_state_t current_state = MODULE_STATE_NONE;

/* 模块初始化 */
static int __init logloom_init(void)
{
    int ret;
    
    pr_info("Initializing Logloom kernel module v%s...\n", LOGLOOM_MODULE_VERSION);
    pr_info("Kernel version: %s\n", utsname()->release);
    
    /* 初始化配置 */
    ret = config_init();
    if (ret != 0) {
        pr_err("Failed to initialize configuration\n");
        goto cleanup;
    }
    current_state = MODULE_STATE_CONFIG_INIT;
    
    /* 初始化国际化模块 */
    ret = lang_init(language);
    if (ret != 0) {
        pr_err("Failed to initialize language module with '%s'\n", language);
        goto cleanup;
    }
    current_state = MODULE_STATE_LANG_INIT;
    
    /* 初始化日志系统 */
    ret = log_init(log_level, log_file);
    if (ret != 0) {
        pr_err("Failed to initialize log system (level=%s, file=%s)\n", 
               log_level, log_file ? log_file : "none");
        goto cleanup;
    }
    current_state = MODULE_STATE_LOG_INIT;
    
    /* 应用其他配置 */
    log_set_console_enabled(console_output);
    
    /* 一切准备就绪 */
    current_state = MODULE_STATE_FULLY_INITIALIZED;
    log_info("SYSTEM", "Logloom kernel module v%s loaded successfully", LOGLOOM_MODULE_VERSION);
    
    return 0;
    
cleanup:
    /* 根据当前状态进行清理 */
    if (current_state >= MODULE_STATE_LOG_INIT) {
        log_cleanup();
    }
    if (current_state >= MODULE_STATE_LANG_INIT) {
        lang_cleanup();
    }
    if (current_state >= MODULE_STATE_CONFIG_INIT) {
        config_cleanup();
    }
    
    return ret;
}

/* 模块退出 */
static void __exit logloom_exit(void)
{
    if (current_state >= MODULE_STATE_LOG_INIT) {
        log_info("SYSTEM", "Logloom kernel module unloading...");
    } else {
        pr_info("Logloom kernel module unloading...\n");
    }
    
    /* 按照相反的顺序清理各个模块 */
    if (current_state >= MODULE_STATE_LOG_INIT) {
        log_cleanup();
    }
    if (current_state >= MODULE_STATE_LANG_INIT) {
        lang_cleanup();
    }
    if (current_state >= MODULE_STATE_CONFIG_INIT) {
        config_cleanup();
    }
    
    pr_info("Logloom kernel module unloaded\n");
}

module_init(logloom_init);
module_exit(logloom_exit);