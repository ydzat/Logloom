#!/usr/bin/env python3
"""
Logloom Python绑定插件系统测试
===========================

测试Logloom Python绑定的插件系统功能
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'bindings' / 'python'))
    
try:
    import logloom_py as ll
except ImportError:
    print("无法导入logloom_py模块。请确保Python绑定已正确构建。")
    print("可能需要在src/bindings/python目录运行: python setup.py install --user")
    sys.exit(1)

class SamplePlugin:
    """用于测试的简单插件类"""
    
    def __init__(self):
        self.message_count = 0
        self.processed_messages = []
    
    def filter(self, level, module, message):
        """过滤日志消息"""
        self.message_count += 1
        self.processed_messages.append((level, module, message))
        
        # 例如：过滤掉包含"过滤"字样的日志
        if "过滤" in message:
            return None
        return message
    
    def get_stats(self):
        """获取插件统计信息"""
        return {
            "processed_count": self.message_count,
            "messages": self.processed_messages
        }

class LogloomPluginTest(unittest.TestCase):
    def setUp(self):
        """测试开始前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(os.path.dirname(__file__), '../../config.yaml')
        self.log_file = os.path.join(self.temp_dir, "plugin_test.log")
        
        # 初始化Logloom
        ll.initialize(self.config_path)
        
    def tearDown(self):
        """测试结束后的清理"""
        ll.cleanup()
        shutil.rmtree(self.temp_dir)
    
    def test_register_plugin(self):
        """测试注册和使用插件"""
        # 检查插件注册功能是否可用
        if not hasattr(ll, "register_plugin"):
            self.skipTest("Python绑定不支持插件注册功能")
            return
            
        # 创建并注册插件
        plugin = SamplePlugin()
        plugin_id = ll.register_plugin(plugin)
        
        self.assertIsNotNone(plugin_id, "插件注册应该返回有效ID")
        
        # 创建日志记录器并记录消息
        logger = ll.Logger("plugin_test")
        logger.info("这是一条普通消息")
        logger.warn("这条消息应该被过滤掉，因为包含'过滤'字样")
        logger.error("另一条普通错误消息")
        
        # 获取插件统计信息
        stats = plugin.get_stats()
        
        # 验证插件是否处理了所有日志消息
        self.assertEqual(stats["processed_count"], 3, "插件应该处理了3条消息")
        
        # 验证过滤功能
        filtered_messages = [msg for _, _, msg in stats["messages"] if "过滤" in msg]
        self.assertEqual(len(filtered_messages), 1, "应该有1条包含'过滤'字样的消息")
    
    def test_unregister_plugin(self):
        """测试取消注册插件"""
        if not hasattr(ll, "register_plugin") or not hasattr(ll, "unregister_plugin"):
            self.skipTest("Python绑定不支持插件注册/注销功能")
            return
            
        # 注册插件
        plugin = SamplePlugin()
        plugin_id = ll.register_plugin(plugin)
        
        # 创建日志记录器并记录一些初始消息
        logger = ll.Logger("plugin_test")
        logger.info("初始消息")
        
        # 取消注册插件
        result = ll.unregister_plugin(plugin_id)
        self.assertTrue(result, "取消注册插件应该成功")
        
        # 再次记录消息
        logger.info("插件注销后的消息")
        
        # 验证只有初始消息被插件处理
        stats = plugin.get_stats()
        self.assertEqual(stats["processed_count"], 1, "注销后的消息不应该被处理")
    
    def test_multiple_plugins(self):
        """测试多个插件同时工作"""
        if not hasattr(ll, "register_plugin"):
            self.skipTest("Python绑定不支持插件注册功能")
            return
            
        # 创建并注册两个插件
        plugin1 = SamplePlugin()
        plugin2 = SamplePlugin()
        
        plugin_id1 = ll.register_plugin(plugin1)
        plugin_id2 = ll.register_plugin(plugin2)
        
        # 创建日志记录器并记录消息
        logger = ll.Logger("multi_plugin_test")
        logger.info("测试多插件消息")
        logger.warn("这是一个警告")
        
        # 验证两个插件都处理了消息
        self.assertEqual(plugin1.get_stats()["processed_count"], 2, "插件1应该处理2条消息")
        self.assertEqual(plugin2.get_stats()["processed_count"], 2, "插件2应该处理2条消息")
        
        # 卸载第一个插件
        ll.unregister_plugin(plugin_id1)
        
        # 再次记录消息
        logger.error("插件1注销后的消息")
        
        # 验证只有插件2处理了新消息
        self.assertEqual(plugin1.get_stats()["processed_count"], 2, "插件1不应处理新消息")
        self.assertEqual(plugin2.get_stats()["processed_count"], 3, "插件2应该处理所有3条消息")
    
    def test_c_plugin_loading(self):
        """测试加载C语言实现的插件"""
        if not hasattr(ll, "load_plugin"):
            self.skipTest("Python绑定不支持C插件加载功能")
            return
            
        # 假设我们有一个示例插件位于tests/sample_filter_plugin.so
        plugin_path = os.path.join(os.path.dirname(__file__), 
                                   "../../build/tests/plugins/sample_filter.so")
        
        if not os.path.exists(plugin_path):
            self.skipTest(f"示例C插件不存在于: {plugin_path}")
            return
            
        # 尝试加载C插件
        try:
            plugin_id = ll.load_plugin(plugin_path)
            self.assertIsNotNone(plugin_id, "应该能够加载C插件")
            
            # 记录一些消息，验证插件工作正常
            logger = ll.Logger("c_plugin_test")
            logger.info("测试C插件处理")
            
            # 由于我们无法直接获取C插件的内部状态，这里只测试加载是否成功
            # 实际应用中，可以通过日志输出或其他方式检查插件的行为
        except Exception as e:
            self.fail(f"加载C插件失败: {e}")

if __name__ == "__main__":
    unittest.main()