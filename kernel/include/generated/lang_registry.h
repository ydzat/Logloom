/**
 * 自动生成的语言资源注册表头文件
 * 此文件通常由构建系统根据语言文件生成
 * 为了测试，这里提供了一个简化版本
 */

#ifndef LOGLOOM_LANG_REGISTRY_H
#define LOGLOOM_LANG_REGISTRY_H

#include <linux/string.h>
#include "../lang.h" // 包含共享的lang.h以使用统一的类型定义

/**
 * 英文语言表
 */
static const lang_entry_t en_lang_table[] = {
    {"system.welcome", "Welcome to Logloom"},
    {"system.user_login", "User %s has logged in"},
    {"system.error.general", "An error occurred"},
    {"system.warn.diskfull", "Disk space is getting low"},
    {NULL, NULL} // 表结束标记
};

/**
 * 中文语言表
 */
static const lang_entry_t zh_lang_table[] = {
    {"system.welcome", "欢迎使用Logloom"},
    {"system.user_login", "用户 %s 已登录"},
    {"system.error.general", "发生了错误"},
    {"system.warn.diskfull", "磁盘空间不足"},
    {NULL, NULL} // 表结束标记
};

/**
 * 获取指定语言的语言表
 * @param lang_code 语言代码
 * @return 对应的语言表，如果未找到则返回NULL
 */
static inline const lang_entry_t* get_lang_table(const char* lang_code) {
    if (!lang_code) return NULL;
    
    if (strcmp(lang_code, "en") == 0) {
        return en_lang_table;
    } else if (strcmp(lang_code, "zh") == 0) {
        return zh_lang_table;
    }
    
    return NULL; // 未支持的语言
}

#endif /* LOGLOOM_LANG_REGISTRY_H */