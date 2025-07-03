#!/usr/bin/env python3
"""
Logloom Python绑定示例程序
=========================

演示如何使用Logloom的Python绑定
"""

import os
import sys
import logloom_py as ll

def main():
    # 获取配置文件路径
    config_path = os.path.join(os.path.dirname(__file__), '../../../config.yaml')
    if not os.path.exists(config_path):
        print(f"配置文件不存在: {config_path}")
        print("使用默认配置...")
        config_path = None
    
    # 初始化Logloom
    print("初始化Logloom...")
    ll.initialize(config_path)
    
    # 测试日志功能
    print("\n--- 测试日志功能 ---")
    ll.logger.debug("这是一条调试消息")
    ll.logger.info("这是一条信息消息")
    ll.logger.warn("这是一条警告消息")
    ll.logger.error("这是一条错误消息")
    
    # 创建自定义模块的日志器
    custom_logger = ll.Logger("CustomModule")
    custom_logger.info("来自自定义模块的消息")
    
    # 测试不同日志级别
    print("\n--- 测试日志级别 ---")
    print("设置日志级别为 WARN")
    ll.logger.set_level("WARN")
    ll.logger.debug("这条调试消息不应该显示")
    ll.logger.info("这条信息消息不应该显示")
    ll.logger.warn("这条警告消息应该显示")
    ll.logger.error("这条错误消息应该显示")
    
    # 测试国际化功能
    print("\n--- 测试国际化功能 ---")
    # 假设配置文件中设置了默认语言
    try:
        welcome_msg = ll.get_text("system.welcome")
        print(f"当前语言的欢迎消息: {welcome_msg}")
    except KeyError:
        print("找不到'system.welcome'键，请检查语言文件")
    
    # 切换语言
    print("\n--- 测试语言切换 ---")
    if ll.set_language("zh"):
        print("成功切换到中文")
        try:
            welcome_msg = ll.get_text("system.welcome")
            print(f"中文欢迎消息: {welcome_msg}")
        except KeyError:
            print("找不到'system.welcome'键，请检查语言文件")
    else:
        print("切换到中文失败")
    
    # 测试格式化文本
    print("\n--- 测试格式化文本 ---")
    try:
        # 假设有一个名为"error.file_not_found"的文本模板，内容如："找不到文件: {0}"
        error_msg = ll.format_text("error.file_not_found", "example.txt")
        print(f"格式化的错误消息: {error_msg}")
    except KeyError:
        print("找不到'error.file_not_found'键，请检查语言文件")
    
    # 使用关键字参数格式化（Python风格）
    try:
        # 尝试使用Python风格的格式化
        msg = ll.format_text("error.invalid_value", value="123", expected="数字")
        print(f"使用关键字参数的消息: {msg}")
    except (KeyError, ValueError) as e:
        print(f"格式化失败: {e}")
    
    # 清理资源
    print("\n清理Logloom资源...")
    ll.cleanup()
    print("示例程序执行完毕！")

if __name__ == "__main__":
    main()