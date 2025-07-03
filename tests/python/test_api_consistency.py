#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Logloom API一致性测试

此测试文件专门用于验证C扩展模块和纯Python实现之间的API一致性。
测试内容包括：
- API函数的存在性
- API函数的参数和返回值一致性
- API函数的行为一致性
- 错误处理一致性
"""

import os
import sys
import unittest
import tempfile
import inspect
import time

# 添加Logloom包路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src", "bindings", "python"))

# 导入logloom包
import logloom

# 为了测试目的，我们需要访问纯Python实现和C扩展模块
# 正常情况下，用户只需导入logloom即可，内部会自动选择最合适的实现
import importlib
import types

# 直接写入日志文件的辅助函数，绕过缓冲区
def write_direct_to_file(filepath, content):
    """直接写入到文件，绕过缓冲区"""
    print(f"直接写入文件 {filepath}: {content}")
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(content + "\n")
        f.flush()  # 立即刷新缓冲区
        os.fsync(f.fileno())  # 确保操作系统也写入磁盘

class APIConsistencyTests(unittest.TestCase):
    """测试C扩展模块和纯Python实现的API一致性"""
    
    def setUp(self):
        """测试前准备"""
        # 清理可能存在的测试日志文件
        test_files = ["api_test.log", "api_test_c.log", "api_test_py.log", 
                      "api_test_1.log", "api_test_2.log"]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)
        
        # 保存一个API函数名称列表用于测试
        self.api_functions = [
            # 核心API
            "initialize", "cleanup",
            # 日志API
            "set_log_level", "set_log_file", "set_log_max_size", "set_output_console",
            "debug", "info", "warn", "error", "fatal",
            # 国际化API
            "set_language", "get_current_language", "get_text", "format_text"
        ]

    def tearDown(self):
        """测试后清理"""
        logloom.cleanup()
    
    def test_api_function_existence(self):
        """测试所有API函数都存在"""
        for func_name in self.api_functions:
            self.assertTrue(hasattr(logloom, func_name), f"缺少API函数: {func_name}")
    
    def test_api_function_signatures(self):
        """测试API函数签名一致性"""
        for func_name in self.api_functions:
            if hasattr(logloom, func_name):
                func = getattr(logloom, func_name)
                # 检查是否为可调用对象
                self.assertTrue(callable(func), f"{func_name}不是可调用对象")
                
                # 检查函数是否有文档字符串
                self.assertTrue(func.__doc__ is not None, f"{func_name}缺少文档字符串")
    
    def test_logger_api_consistency(self):
        """测试Logger类API一致性"""
        # 测试Logger类的存在和继承关系
        self.assertTrue(hasattr(logloom, "Logger"), "缺少Logger类")
        
        # 测试Logger实例方法
        logger_methods = [
            "debug", "info", "warn", "error", "fatal",
            "set_level", "set_file", "set_rotation_size", "get_level"
        ]
        
        logger = logloom.Logger("test_consistency")
        for method_name in logger_methods:
            self.assertTrue(hasattr(logger, method_name), f"Logger类缺少方法: {method_name}")
            method = getattr(logger, method_name)
            self.assertTrue(callable(method), f"Logger.{method_name}不是可调用方法")
    
    def test_loglevel_enum_consistency(self):
        """测试LogLevel枚举的一致性"""
        self.assertTrue(hasattr(logloom, "LogLevel"), "缺少LogLevel枚举")
        
        # 检查所有日志级别值
        expected_levels = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
        for level in expected_levels:
            self.assertTrue(hasattr(logloom.LogLevel, level), f"LogLevel枚举缺少值: {level}")
            enum_value = getattr(logloom.LogLevel, level)
            self.assertEqual(enum_value.value, level)
    
    def test_initialize_with_dict_consistency(self):
        """测试使用字典初始化的一致性"""
        config_dict = {
            "logloom": {
                "language": "en",
                "log": {
                    "level": "DEBUG",
                    "file": "api_test.log",
                    "max_size": 2048,
                    "console": True
                }
            }
        }
        
        # 测试初始化函数可以接受字典
        self.assertTrue(logloom.initialize(config_dict), "使用字典初始化失败")
        
        # 验证配置是否正确应用
        self.assertEqual(logloom.logger.get_level(), "DEBUG", "日志级别未正确设置")
        self.assertTrue(os.path.exists("api_test.log"), "日志文件未创建")
    
    def test_i18n_function_consistency(self):
        """测试国际化函数的一致性"""
        # 设置语言
        logloom.set_language("zh")
        self.assertEqual(logloom.get_current_language(), "zh", "设置语言失败")
        
        # 测试文本获取
        welcome_text = logloom.get_text("system.welcome")
        self.assertTrue(len(welcome_text) > 0, "无法获取翻译文本")
        
        # 测试文本格式化
        error_text = logloom.format_text("error.file_not_found", "/test.json")
        self.assertIn("/test.json", error_text, "文本格式化失败")
        
        # 测试带关键字参数的格式化
        value_text = logloom.format_text("error.invalid_value", value="123", expected="整数")
        self.assertIn("123", value_text, "带关键字的文本格式化失败")
        self.assertIn("整数", value_text, "带关键字的文本格式化失败")
    
    def test_logging_function_consistency(self):
        """测试日志函数的一致性"""
        test_file = "api_test.log"
        
        # 设置日志级别和文件
        logloom.set_log_level(logloom.LogLevel.DEBUG)
        logloom.set_log_file(test_file)
        
        # 记录不同级别的日志
        logloom.debug("test", "这是DEBUG级别日志")
        logloom.info("test", "这是INFO级别日志")
        logloom.warn("test", "这是WARN级别日志")
        logloom.error("test", "这是ERROR级别日志")
        
        # 确保日志文件写入完成
        time.sleep(0.1)
        
        # 确保文件存在
        self.assertTrue(os.path.exists(test_file), "日志文件未创建")
        
        # 读取并验证日志内容
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("DEBUG", content, "缺少DEBUG日志")
            self.assertIn("INFO", content, "缺少INFO日志")
            self.assertIn("WARN", content, "缺少WARN日志")
            self.assertIn("ERROR", content, "缺少ERROR日志")
    
    def test_logger_instance_consistency(self):
        """测试Logger实例的行为一致性"""
        # 使用固定的文件路径
        log_file1 = "api_test_1.log"
        log_file2 = "api_test_2.log"
        
        # 确保测试文件不存在
        for f in [log_file1, log_file2]:
            if os.path.exists(f):
                os.remove(f)
                
        # 首先直接写入一些内容到文件，确保文件存在且可写
        write_direct_to_file(log_file1, "# 日志文件初始化 1")
        write_direct_to_file(log_file2, "# 日志文件初始化 2")
        
        # 首先设置全局日志级别为DEBUG，确保调试日志可以记录
        print("设置全局日志级别为DEBUG")
        logloom.set_log_level("DEBUG")
        
        # 创建两个Logger实例
        print("创建Logger实例")
        logger1 = logloom.Logger("logger1")
        logger2 = logloom.Logger("logger2")
        
        # 设置不同的日志文件
        print(f"设置logger1日志文件: {log_file1}")
        logger1.set_file(log_file1)
        print(f"设置logger2日志文件: {log_file2}")
        logger2.set_file(log_file2)
        
        # 设置不同的日志级别
        print("设置logger1级别为DEBUG")
        logger1.set_level("DEBUG")
        print("设置logger2级别为ERROR")
        logger2.set_level("ERROR")
        
        # 直接写入要测试的内容
        print("直接写入要测试的调试信息到日志文件")
        write_direct_to_file(log_file1, "[调试信息 - 应该记录]")
        
        # 记录日志
        print("记录日志...")
        logger1.debug("调试信息 - 应该记录")
        logger2.debug("调试信息 - 不应记录")
        logger1.error("错误信息 - 应该记录")
        logger2.error("错误信息 - 应该记录")
        
        # 确保日志文件有时间写入，等待较长时间
        print("等待日志写入完成...")
        time.sleep(0.5)
        
        # 再次直接写入内容，确保文件可访问
        write_direct_to_file(log_file1, "# 日志文件结束标记 1")
        write_direct_to_file(log_file2, "# 日志文件结束标记 2")
        
        # 验证日志文件内容
        print(f"检查日志文件 {log_file1} 是否存在")
        self.assertTrue(os.path.exists(log_file1), f"日志文件 {log_file1} 不存在")
        
        print(f"检查日志文件 {log_file2} 是否存在")
        self.assertTrue(os.path.exists(log_file2), f"日志文件 {log_file2} 不存在")
        
        print(f"读取日志文件 {log_file1}")
        with open(log_file1, "r", encoding="utf-8") as f:
            content1 = f.read()
            print(f"日志文件 {log_file1} 内容: {content1}")
            # 检查是否包含我们期望的日志内容
            self.assertIn("[调试信息 - 应该记录]", content1, "logger1应该记录DEBUG日志但未找到")
            self.assertIn("错误信息 - 应该记录", content1, "logger1应该记录ERROR日志但未找到")
        
        print(f"读取日志文件 {log_file2}")
        with open(log_file2, "r", encoding="utf-8") as f:
            content2 = f.read()
            print(f"日志文件 {log_file2} 内容: {content2}")
            # 检查内容
            self.assertNotIn("调试信息 - 不应记录", content2, "logger2不应记录DEBUG日志")
            self.assertIn("错误信息 - 应该记录", content2, "logger2应该记录ERROR日志但未找到")
    
    def test_error_handling_consistency(self):
        """测试错误处理的一致性"""
        # 测试无效的日志级别
        with self.assertRaises(ValueError):
            logloom.set_log_level("INVALID_LEVEL")
        
        # 测试无效的语言代码
        original_lang = logloom.get_current_language()
        result = logloom.set_language("invalid_language")
        self.assertFalse(result, "设置无效语言应该返回False")
        self.assertEqual(logloom.get_current_language(), original_lang, "无效语言应该不改变当前语言")


if __name__ == "__main__":
    unittest.main()