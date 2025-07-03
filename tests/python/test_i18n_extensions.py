#!/usr/bin/env python3
"""
测试Logloom国际化扩展功能
这个脚本测试动态注册语言资源文件和查询语言状态的新功能
"""

import os
import sys
import unittest
from pathlib import Path

# 将Logloom模块目录添加到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'bindings' / 'python'))

try:
    import logloom
    print("成功导入Logloom模块")
except ImportError as e:
    print(f"导入Logloom模块失败: {e}")
    sys.exit(1)

class TestI18nExtensions(unittest.TestCase):
    """测试国际化扩展功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 初始化Logloom
        logloom.initialize()
        
        # 测试资源目录
        self.test_locales_dir = os.path.join(os.path.dirname(__file__), 'test_locales')
        self.fr_yaml_path = os.path.join(self.test_locales_dir, 'fr.yaml')
        
    def tearDown(self):
        """测试后的清理工作"""
        logloom.cleanup()
    
    def test_register_locale_file(self):
        """测试注册语言资源文件功能"""
        # 确保文件存在
        self.assertTrue(os.path.isfile(self.fr_yaml_path), f"测试文件不存在: {self.fr_yaml_path}")
        
        # 注册法语资源文件
        result = logloom.register_locale_file(self.fr_yaml_path)
        self.assertTrue(result, "注册语言资源文件失败")
        
        # 切换到法语
        logloom.set_language("fr")
        
        # 测试获取翻译文本
        text = logloom.get_text("test.hello")
        self.assertEqual(text, "Bonjour, {0}!", "获取法语文本失败")
        
        # 测试格式化翻译文本
        formatted = logloom.format_text("test.hello", "monde")
        self.assertEqual(formatted, "Bonjour, monde!", "格式化法语文本失败")
        
        # 测试自定义键
        custom_text = logloom.get_text("test.custom_key")
        self.assertEqual(custom_text, "Ceci est une clé personnalisée en français", "获取自定义法语文本失败")
    
    def test_register_locale_directory(self):
        """测试注册整个目录的语言资源文件"""
        # 注册测试目录
        count = logloom.register_locale_directory(self.test_locales_dir)
        self.assertGreaterEqual(count, 1, "注册目录下的语言资源文件失败")
    
    def test_get_supported_languages(self):
        """测试获取支持的语言列表"""
        # 注册法语资源
        logloom.register_locale_file(self.fr_yaml_path)
        
        # 获取支持的语言列表
        languages = logloom.get_supported_languages()
        self.assertIn("en", languages, "支持的语言列表中应该包含英语")
        self.assertIn("fr", languages, "支持的语言列表中应该包含法语")
    
    def test_get_language_keys(self):
        """测试获取语言键列表"""
        # 注册法语资源
        logloom.register_locale_file(self.fr_yaml_path)
        
        # 获取法语键列表
        keys = logloom.get_language_keys("fr")
        self.assertIn("test.hello", keys, "法语键列表中应该包含test.hello")
        self.assertIn("test.custom_key", keys, "法语键列表中应该包含test.custom_key")
        
        # 获取当前语言的键列表（默认英语）
        en_keys = logloom.get_language_keys()
        self.assertIn("system.welcome", en_keys, "英语键列表中应该包含system.welcome")

if __name__ == '__main__':
    unittest.main()