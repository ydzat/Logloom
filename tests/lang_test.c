/**
 * 语言模块测试
 * 测试语言模块的基本功能：初始化、获取文本、格式化、语言切换等
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include "lang.h"
#include "generated/lang_registry.h"

// 测试初始化和获取文本
void test_lang_init_and_get() {
    printf("测试1：测试语言初始化和基本文本获取\n");
    
    // 初始化语言模块为英语
    int result = lang_init("en");
    assert(result == 0 && "语言初始化应该成功");
    
    // 验证当前语言
    const char* current = lang_get_current();
    assert(strcmp(current, "en") == 0 && "当前语言应该是英语");
    
    // 获取简单文本
    const char* text = lang_get("system.start_message");
    assert(text != NULL && "文本不应为NULL");
    printf("获取到的文本：%s\n", text);
    
    printf("测试1通过！\n\n");
}

// 测试格式化文本
void test_lang_format() {
    printf("测试2：测试语言格式化功能\n");
    
    // 获取格式化文本
    char* formatted = lang_getf("system.error_message", "测试错误");
    assert(formatted != NULL && "格式化文本不应为NULL");
    printf("格式化文本：%s\n", formatted);
    
    // 验证格式化结果是否包含参数
    assert(strstr(formatted, "测试错误") != NULL && "格式化文本应包含参数");
    
    // 释放内存
    free(formatted);
    
    printf("测试2通过！\n\n");
}

// 测试语言切换
void test_lang_switch() {
    printf("测试3：测试语言切换功能\n");
    
    // 获取当前语言下的测试文本
    const char* text_en = lang_get("system.start_message");
    printf("英语文本：%s\n", text_en);
    
    // 切换到中文
    bool switched = lang_set_language("zh");
    assert(switched && "语言切换应该成功");
    
    // 验证当前语言
    const char* current = lang_get_current();
    assert(strcmp(current, "zh") == 0 && "当前语言应该是中文");
    
    // 获取切换语言后的文本
    const char* text_zh = lang_get("system.start_message");
    printf("中文文本：%s\n", text_zh);
    
    // 确保两种语言文本不同
    assert(strcmp(text_en, text_zh) != 0 && "不同语言的文本应该不同");
    
    // 切换回英语
    lang_set_language("en");
    
    printf("测试3通过！\n\n");
}

// 测试错误处理：不存在的语言键
void test_lang_error_handling() {
    printf("测试4：测试语言错误处理\n");
    
    // 尝试获取不存在的键
    const char* text = lang_get("nonexistent.key");
    assert(text != NULL && "即使键不存在也不应返回NULL");
    printf("获取不存在键的结果：%s\n", text);
    
    printf("测试4通过！\n\n");
}

int main() {
    printf("=== 开始语言模块测试 ===\n\n");
    
    // 运行测试用例
    test_lang_init_and_get();
    test_lang_format();
    test_lang_switch();
    test_lang_error_handling();
    
    // 清理资源
    lang_cleanup();
    
    printf("所有测试成功完成！\n");
    return 0;
}