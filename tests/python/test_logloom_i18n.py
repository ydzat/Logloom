#!/usr/bin/env python3
"""
Logloom国际化功能测试

此测试验证Logloom的国际化功能，包括：
- 不同语言的文本翻译
- 语言切换
- 文本格式化
"""

import sys
import os
import unittest

# 添加测试适配器路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_adapter import logger, initialize, cleanup, Logger, LogLevel, get_text, get_current_language, set_language, format_text

class TestLogloomI18n(unittest.TestCase):
    """测试Logloom的国际化功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.config_path = './config.yaml'
        # 初始化Logloom
        self.assertTrue(initialize(self.config_path), "初始化Logloom失败")
    
    def tearDown(self):
        """测试后的清理工作"""
        # 清理Logloom资源
        self.assertTrue(cleanup(), "清理Logloom资源失败")
    
    def test_get_text(self):
        """测试获取翻译文本功能"""
        # 获取欢迎消息
        welcome_text = get_text('system.welcome')
        self.assertIsNotNone(welcome_text, "获取翻译文本失败")
        self.assertTrue(len(welcome_text) > 0, "翻译文本内容为空")
        print(f"当前语言的欢迎消息: {welcome_text}")
    
    def test_language_switch(self):
        """测试语言切换功能"""
        # 记录当前语言
        current_lang = get_current_language()
        self.assertIsNotNone(current_lang, "获取当前语言失败")
        print(f"当前语言: {current_lang}")
        
        # 切换到中文
        target_lang = 'zh' if current_lang != 'zh' else 'en'
        self.assertTrue(set_language(target_lang), f"切换到{target_lang}失败")
        print(f"切换到{target_lang}成功")
        
        # 验证语言是否切换成功
        welcome_text = get_text('system.welcome')
        self.assertIsNotNone(welcome_text, "获取翻译文本失败")
        print(f"{target_lang}欢迎消息: {welcome_text}")
        
        # 切换回原来的语言
        self.assertTrue(set_language(current_lang), f"切换回{current_lang}失败")
    
    def test_format_text(self):
        """测试格式化翻译文本功能"""
        # 使用位置参数格式化
        test_file = 'example.txt'
        formatted_text = format_text('error.file_not_found', test_file)
        self.assertIsNotNone(formatted_text, "格式化文本失败")
        self.assertIn(test_file, formatted_text, "格式化文本中不包含参数值")
        print(f"位置参数格式化结果: {formatted_text}")
        
        # 使用关键字参数格式化
        test_value = '123'
        test_expected = 'number'
        formatted_text = format_text('error.invalid_value', value=test_value, expected=test_expected)
        self.assertIsNotNone(formatted_text, "格式化文本失败")
        self.assertIn(test_value, formatted_text, "格式化文本中不包含value参数值")
        self.assertIn(test_expected, formatted_text, "格式化文本中不包含expected参数值")
        print(f"关键字参数格式化结果: {formatted_text}")

if __name__ == '__main__':
    unittest.main()