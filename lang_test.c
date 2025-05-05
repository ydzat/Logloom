#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "lang.h"

int main(int argc, char** argv) {
    // 初始化语言系统，默认使用英文
    printf("测试语言模块 (Testing Language Module)\n");
    printf("======================================\n\n");
    
    if (lang_init("en") != 0) {
        printf("初始化语言系统失败 (Failed to initialize language system)\n");
        return 1;
    }
    
    printf("当前语言 (Current language): %s\n", lang_get_current());
    
    // 测试获取基本字符串
    printf("\n基本字符串测试 (Basic string test):\n");
    printf("系统启动消息 (System start message): %s\n", lang_get("system.start_message"));
    printf("登录成功消息 (Login success message): %s\n", lang_get("auth.login_success"));
    
    // 测试格式化字符串
    printf("\n格式化字符串测试 (Formatted string test):\n");
    char* error_msg = lang_getf("system.error_message", "File not found");
    if (error_msg) {
        printf("格式化错误消息 (Formatted error message): %s\n", error_msg);
        free(error_msg);  // 注意释放内存
    }
    
    // 测试语言切换到中文
    printf("\n语言切换测试 (Language switching test):\n");
    if (lang_set_language("zh")) {
        printf("已切换到中文 (Switched to Chinese)\n");
        printf("当前语言 (Current language): %s\n", lang_get_current());
        
        // 重新测试相同的键
        printf("\n基本字符串测试 (Basic string test):\n");
        printf("系统启动消息 (System start message): %s\n", lang_get("system.start_message"));
        printf("登录成功消息 (Login success message): %s\n", lang_get("auth.login_success"));
        
        // 重新测试格式化字符串
        printf("\n格式化字符串测试 (Formatted string test):\n");
        error_msg = lang_getf("system.error_message", "文件未找到");
        if (error_msg) {
            printf("格式化错误消息 (Formatted error message): %s\n", error_msg);
            free(error_msg);
        }
    } else {
        printf("无法切换到中文 (Failed to switch language to Chinese)\n");
    }
    
    // 测试错误情况
    printf("\n错误处理测试 (Error handling test):\n");
    printf("不存在的键 (Non-existent key): %s\n", lang_get("non.existent.key"));
    
    // 切换到不存在的语言
    printf("\n不存在的语言测试 (Non-existent language test):\n");
    if (!lang_set_language("fr")) {
        printf("成功处理了不存在的语言 (Successfully handled non-existent language)\n");
    }
    
    // 清理
    lang_cleanup();
    printf("\n语言系统清理完成 (Language system cleanup complete)\n");
    
    return 0;
}