#!/usr/bin/env python3
"""
Logloom Python绑定基础测试
==========================

测试Logloom Python绑定的基础功能
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# 导入测试适配器
sys.path.insert(0, os.path.dirname(__file__))
from test_adapter import logger as ll, initialize, cleanup, Logger, LogLevel

class LogloomBasicTest(unittest.TestCase):
    def setUp(self):
        """测试开始前的设置"""
        # 创建临时目录，用于存放日志文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(os.path.dirname(__file__), '../../config.yaml')
        # 初始化Logloom
        initialize(self.config_path)
        
        # 确保日志文件路径设置正确
        self.log_file_path = os.path.join(self.temp_dir, 'python_test.log')
        # 创建logger并设置日志文件路径
        self.logger = Logger("basic_test")
        self.logger.set_file(self.log_file_path)
        
    def tearDown(self):
        """测试结束后的清理"""
        # 清理Logloom资源
        cleanup()
        # 删除临时目录
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """测试Logloom初始化功能"""
        # 重新初始化Logloom以确认初始化逻辑可以多次调用
        cleanup()
        result = initialize(self.config_path)
        self.assertTrue(result, "Logloom初始化应该成功")
        # 确保重新设置日志文件路径
        self.logger = Logger("basic_test")
        self.logger.set_file(self.log_file_path)
        
        # 使用空配置初始化
        cleanup()
        result = initialize(None)
        self.assertTrue(result, "Logloom使用默认配置初始化应该成功")
        # 确保重新设置日志文件路径
        self.logger = Logger("basic_test")
        self.logger.set_file(self.log_file_path)
    
    def test_logging(self):
        """测试基本的日志记录功能"""
        # 记录不同级别的日志
        self.logger.debug("Debug日志测试")
        self.logger.info("Info日志测试")
        self.logger.warning("Warning日志测试")  # 修改为warning而不是warn
        self.logger.error("Error日志测试")
        
        # 这里我们不做具体日志内容的断言，因为日志通常写入文件或标准输出
        # 如果需要检查日志内容，可以重定向日志到字符串或临时文件进行比较
        
    def test_custom_logger(self):
        """测试创建自定义模块的日志器"""
        custom_logger = Logger("TestModule")
        self.assertIsNotNone(custom_logger, "应该能够创建自定义日志器")
        custom_logger.info("来自测试模块的消息")
        
    def test_log_level(self):
        """测试设置和获取日志级别"""
        # 设置日志级别为WARN
        self.logger.set_level("WARN")
        self.assertEqual(self.logger.get_level(), "WARN", "日志级别应该正确设置为WARN")
        
        # 设置日志级别为DEBUG
        self.logger.set_level("DEBUG")
        self.assertEqual(self.logger.get_level(), "DEBUG", "日志级别应该正确设置为DEBUG")

if __name__ == "__main__":
    unittest.main()