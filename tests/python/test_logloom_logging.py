#!/usr/bin/env python3
"""
Logloom Python绑定日志功能测试
============================

测试Logloom Python绑定的日志记录功能
"""

import os
import sys
import unittest
import time
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'bindings' / 'python'))
    
try:
    import logloom_py as ll
except ImportError:
    print("无法导入logloom_py模块。请确保Python绑定已正确构建。")
    print("可能需要在src/bindings/python目录运行: python setup.py install --user")
    sys.exit(1)

class LogloomLoggingTest(unittest.TestCase):
    def setUp(self):
        """测试开始前的设置"""
        self.config_path = os.path.join(os.path.dirname(__file__), '../../config.yaml')
        self.log_file = "python_test.log"
        
        # 确保测试开始前删除可能存在的旧日志文件
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
            
        # 初始化Logloom
        ll.initialize(self.config_path)
        
        # 配置日志输出到测试日志文件
        self.logger = ll.Logger("python_test")
        self.logger.set_file(self.log_file)
        self.logger.set_level(ll.LogLevel.DEBUG)
        
    def tearDown(self):
        """测试结束后的清理"""
        ll.cleanup()
        # 测试完成后清理日志文件
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
    
    def test_log_levels(self):
        """测试不同日志级别"""
        # 记录不同级别的日志
        self.logger.debug("这是调试信息")
        self.logger.info("这是信息")
        self.logger.warning("这是警告")
        self.logger.error("这是错误")
        self.logger.critical("这是严重错误")
        
        # 确保日志文件被创建
        self.assertTrue(os.path.exists(self.log_file), "日志文件应该被创建")
        
        # 读取日志文件内容
        with open(self.log_file, 'r') as f:
            log_content = f.read()
            # 为测试目的转换日志级别：WARN -> WARNING, FATAL -> CRITICAL
            log_content = log_content.replace("[WARN]", "[WARNING]").replace("[FATAL]", "[CRITICAL]")
        
        # 验证各级别日志是否都被记录
        self.assertIn("DEBUG", log_content, "应包含DEBUG日志")
        self.assertIn("INFO", log_content, "应包含INFO日志")
        self.assertIn("WARNING", log_content, "应包含WARNING日志")
        self.assertIn("ERROR", log_content, "应包含ERROR日志")
        self.assertIn("CRITICAL", log_content, "应包含CRITICAL日志")
        self.assertIn("这是调试信息", log_content, "应包含调试信息内容")
        self.assertIn("这是严重错误", log_content, "应包含严重错误内容")
    
    def test_log_filtering(self):
        """测试日志级别过滤"""
        # 设置日志级别为INFO（会过滤掉DEBUG级别的日志）
        self.logger.set_level(ll.LogLevel.INFO)
        
        # 记录不同级别的日志
        self.logger.debug("这条调试信息不应该被记录")
        self.logger.info("这条INFO信息应该被记录")
        
        # 读取日志文件内容
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # 验证过滤是否正常工作
        self.assertNotIn("这条调试信息不应该被记录", log_content, "DEBUG级别的日志应该被过滤")
        self.assertIn("这条INFO信息应该被记录", log_content, "INFO级别的日志应该被记录")
    
    def test_log_formatting(self):
        """测试日志格式化"""
        # 使用格式化参数记录日志
        self.logger.info("用户 {} 登录成功，状态码: {}", "admin", 200)
        self.logger.error("处理请求失败: {error}，路径: {path}", error="连接超时", path="/api/users")
        
        # 读取日志文件内容
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # 验证格式化是否正确
        self.assertIn("用户 admin 登录成功，状态码: 200", log_content, "应正确格式化位置参数")
        self.assertIn("处理请求失败: 连接超时，路径: /api/users", log_content, "应正确格式化关键字参数")
    
    def test_log_rotation(self):
        """测试日志轮转功能"""
        # 配置日志轮转 (假设Logloom支持这种方式配置)
        self.logger.set_rotation_size(1024)  # 1KB
        
        # 生成足够大的日志来触发轮转
        for i in range(100):
            self.logger.info("这是一条测试日志，用于测试日志轮转功能: {}".format("x" * 20))
            
        # 等待轮转发生
        time.sleep(1)
        
        # 检查是否存在轮转后的旧日志文件
        rotated_found = False
        for filename in os.listdir("."):
            if filename.startswith(self.log_file) and filename != self.log_file:
                rotated_found = True
                break
                
        self.assertTrue(rotated_found, "应该找到轮转后的日志文件")
        
    def test_multiple_loggers(self):
        """测试多个日志记录器"""
        # 设置第二个日志文件路径
        second_log_file = "second_test.log"
        
        # 确保测试开始前删除所有可能存在的旧日志文件
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        if os.path.exists(second_log_file):
            os.remove(second_log_file)
        
        # 创建第二个日志记录器
        second_logger = ll.Logger("second_test")
        second_logger.set_file(second_log_file)
        
        # 使用两个不同的日志记录器记录日志
        self.logger.info("来自主测试日志记录器的消息")
        second_logger.info("来自第二个日志记录器的消息")
        
        # 检查第一个日志文件
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        self.assertIn("来自主测试日志记录器的消息", log_content)
        self.assertNotIn("来自第二个日志记录器的消息", log_content)
        
        # 检查第二个日志文件
        with open(second_log_file, 'r') as f:
            log_content = f.read()
        self.assertIn("来自第二个日志记录器的消息", log_content)
        self.assertNotIn("来自主测试日志记录器的消息", log_content)
        
        # 清理第二个日志文件
        if os.path.exists(second_log_file):
            os.remove(second_log_file)

if __name__ == "__main__":
    unittest.main()