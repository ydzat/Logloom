#!/usr/bin/env python3
"""
测试Logloom修复后的Python绑定
"""
import os
import sys
import time
import unittest

# 添加包路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src", "bindings", "python"))

# 直接导入C扩展模块
import logloom

class TestLogLoomFixes(unittest.TestCase):
    """测试Logloom修复"""
    
    def setUp(self):
        """测试前准备"""
        # 清理临时文件
        log_file = "logloom_test_fixes.log"
        if os.path.exists(log_file):
            os.remove(log_file)
    
    def tearDown(self):
        """测试后清理"""
        logloom.cleanup()
    
    def test_api_compatibility(self):
        """测试API兼容性 - 验证添加的文档中描述的API函数"""
        # 测试set_log_level API
        self.assertTrue(hasattr(logloom, "set_log_level"), "应该存在set_log_level函数")
        logloom.set_log_level(logloom.LogLevel.DEBUG)
        self.assertEqual(logloom.logger.get_level(), "DEBUG")
        
        # 测试set_log_file API
        self.assertTrue(hasattr(logloom, "set_log_file"), "应该存在set_log_file函数")
        test_log_file = "logloom_test_fixes.log"
        logloom.set_log_file(test_log_file)
        self.assertTrue(os.path.exists(test_log_file), "日志文件应该被创建")
        
        # 测试set_log_max_size API
        self.assertTrue(hasattr(logloom, "set_log_max_size"), "应该存在set_log_max_size函数")
        logloom.set_log_max_size(1024) # 设置1KB的日志文件大小限制
        
        # 测试set_output_console API
        self.assertTrue(hasattr(logloom, "set_output_console"), "应该存在set_output_console函数")
        logloom.set_output_console(True)
        
        # 记录日志确认API正常工作
        logloom.logger.info("测试API兼容性")
        logloom.logger.debug("这是一条调试日志")
        
        # 验证日志文件创建
        self.assertTrue(os.path.exists(test_log_file), "应该生成日志文件")
        with open(test_log_file, "r") as f:
            log_content = f.read()
            self.assertIn("测试API兼容性", log_content)
            self.assertIn("这是一条调试日志", log_content)
    
    def test_i18n_recursion(self):
        """测试国际化函数递归调用问题"""
        # 设置语言
        logloom.set_language("zh")
        self.assertEqual(logloom.get_current_language(), "zh")
        
        # 测试get_text
        welcome_text = logloom.get_text("system.welcome")
        self.assertEqual(welcome_text, "欢迎使用Logloom日志系统")
        
        # 测试format_text
        error_text = logloom.format_text("error.file_not_found", "/config.json")
        self.assertEqual(error_text, "找不到文件: /config.json")
        
        # 测试带关键字参数的format_text
        invalid_value_text = logloom.format_text("error.invalid_value", value="123", expected="数字")
        self.assertEqual(invalid_value_text, "无效的值: 123，期望: 数字")
    
    def test_initialize_with_dict(self):
        """测试使用字典初始化"""
        # 创建配置字典
        config_dict = {
            "logloom": {
                "language": "zh",
                "log": {
                    "level": "DEBUG",
                    "file": "logloom_dict_config_test.log",
                    "max_size": 2048,
                    "console": True
                }
            }
        }
        
        # 初始化
        logloom.initialize(config_dict)
        
        # 验证配置是否生效
        self.assertEqual(logloom.get_current_language(), "zh")
        self.assertEqual(logloom.logger.get_level(), "DEBUG")
        
        # 记录日志验证
        logloom.logger.info("使用字典配置初始化成功")
        
        # 验证日志文件
        self.assertTrue(os.path.exists("logloom_dict_config_test.log"))
        with open("logloom_dict_config_test.log", "r") as f:
            log_content = f.read()
            self.assertIn("使用字典配置初始化成功", log_content)
        
        # 清理
        if os.path.exists("logloom_dict_config_test.log"):
            os.remove("logloom_dict_config_test.log")

if __name__ == "__main__":
    unittest.main()
