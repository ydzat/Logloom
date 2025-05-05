#!/usr/bin/env python3
"""
Logloom Python绑定国际化功能测试
==============================

测试Logloom Python绑定的国际化(i18n)功能
"""

import os
import sys
import unittest
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'bindings' / 'python'))
    
try:
    import logloom_py as ll
except ImportError:
    print("无法导入logloom_py模块。请确保Python绑定已正确构建。")
    print("可能需要在src/bindings/python目录运行: python setup.py install --user")
    sys.exit(1)

class LogloomI18nTest(unittest.TestCase):
    def setUp(self):
        """测试开始前的设置"""
        self.config_path = os.path.join(os.path.dirname(__file__), '../../config.yaml')
        # 初始化Logloom
        ll.initialize(self.config_path)
        
    def tearDown(self):
        """测试结束后的清理"""
        ll.cleanup()
    
    def test_get_text(self):
        """测试获取翻译文本功能"""
        # 测试获取存在的翻译
        try:
            text = ll.get_text("system.welcome")
            self.assertIsNotNone(text, "系统欢迎信息应该存在")
            self.assertNotEqual(text, "", "翻译文本不应为空")
        except Exception as e:
            self.fail(f"获取翻译文本时出错: {e}")
            
        # 测试获取不存在的翻译
        with self.assertRaises(KeyError):
            ll.get_text("non.existent.key")
    
    def test_set_language(self):
        """测试设置语言功能"""
        # 保存当前语言以便后续恢复
        current_lang = ll.get_current_language()
        
        # 测试设置为中文
        result = ll.set_language("zh")
        self.assertTrue(result, "设置语言为中文应该成功")
        self.assertEqual(ll.get_current_language(), "zh", "当前语言应该为中文")
        
        # 测试设置为英文
        result = ll.set_language("en")
        self.assertTrue(result, "设置语言为英文应该成功")
        self.assertEqual(ll.get_current_language(), "en", "当前语言应该为英文")
        
        # 测试设置为不支持的语言
        result = ll.set_language("fr")
        self.assertFalse(result, "设置不支持的语言应该失败")
        
        # 恢复原语言
        ll.set_language(current_lang)
        
    def test_format_text(self):
        """测试格式化翻译文本功能"""
        # 测试使用位置参数格式化文本
        try:
            # 假设"error.file_not_found"的模板为"找不到文件: {0}"
            text = ll.format_text("error.file_not_found", "example.txt")
            self.assertIn("example.txt", text, "格式化后的文本应包含参数")
        except Exception as e:
            self.fail(f"使用位置参数格式化文本时出错: {e}")
            
        # 测试使用关键字参数格式化文本
        try:
            # 假设"error.invalid_value"的模板为"无效的值: {value}，期望: {expected}"
            text = ll.format_text("error.invalid_value", value="123", expected="数字")
            self.assertIn("123", text, "格式化后的文本应包含value参数")
            self.assertIn("数字", text, "格式化后的文本应包含expected参数")
        except Exception as e:
            self.fail(f"使用关键字参数格式化文本时出错: {e}")

if __name__ == "__main__":
    unittest.main()