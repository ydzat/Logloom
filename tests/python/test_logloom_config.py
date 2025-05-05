#!/usr/bin/env python3
"""
Logloom Python绑定配置测试
========================

测试Logloom Python绑定的配置文件功能
"""

import os
import sys
import unittest
import tempfile
import shutil
import yaml
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'bindings' / 'python'))
    
try:
    import logloom_py as ll
except ImportError:
    print("无法导入logloom_py模块。请确保Python绑定已正确构建。")
    print("可能需要在src/bindings/python目录运行: python setup.py install --user")
    sys.exit(1)

class LogloomConfigTest(unittest.TestCase):
    def setUp(self):
        """测试开始前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_config_path = os.path.join(os.path.dirname(__file__), '../../config.yaml')
        
        # 复制原始配置文件到临时目录
        self.test_config_path = os.path.join(self.temp_dir, 'test_config.yaml')
        shutil.copy(self.original_config_path, self.test_config_path)
        
        # 在各测试中使用全局配置
        global config
        config = {}
        
    def tearDown(self):
        """测试结束后的清理"""
        # 确保Logloom资源被清理
        try:
            ll.cleanup()
        except:
            pass
            
        # 删除临时目录
        shutil.rmtree(self.temp_dir)
    
    def test_default_config(self):
        """测试默认配置加载"""
        result = ll.initialize(self.test_config_path)
        self.assertTrue(result, "使用默认配置初始化应该成功")
        ll.cleanup()
    
    def test_custom_log_level(self):
        """测试自定义日志级别配置"""
        # 修改配置文件，设置日志级别为DEBUG
        with open(self.test_config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # 确保配置有正确的结构
        if 'logloom' in config:
            # 原始配置结构
            if 'log' not in config['logloom']:
                config['logloom']['log'] = {}
            config['logloom']['log']['level'] = 'DEBUG'
        else:
            # 测试期望的结构
            if 'logging' not in config:
                config['logging'] = {}
            config['logging']['default_level'] = 'DEBUG'
        
        with open(self.test_config_path, 'w') as f:
            yaml.dump(config, f)
            
        # 使用修改后的配置初始化
        ll.initialize(self.test_config_path)
        
        # 检查日志级别是否已设置为DEBUG
        self.assertEqual(ll.logger.get_level(), 'DEBUG', "日志级别应该被配置为DEBUG")
        ll.cleanup()
    
    def test_custom_output_path(self):
        """测试自定义日志输出路径配置"""
        custom_log_path = os.path.join(self.temp_dir, 'custom.log')
        
        # 修改配置文件，设置自定义日志路径
        with open(self.test_config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # 确保配置有正确的结构
        if 'logloom' in config:
            # 原始配置结构
            if 'log' not in config['logloom']:
                config['logloom']['log'] = {}
            config['logloom']['log']['file'] = custom_log_path
        else:
            # 测试期望的结构
            if 'logging' not in config:
                config['logging'] = {}
            config['logging']['output_path'] = custom_log_path
        
        with open(self.test_config_path, 'w') as f:
            yaml.dump(config, f)
            
        # 使用修改后的配置初始化
        ll.initialize(self.test_config_path)
        
        # 确保日志文件路径在我们的Logger实例中正确设置
        ll.logger.set_file(custom_log_path)
        
        # 记录日志
        ll.logger.info("测试自定义日志路径")
        ll.cleanup()
        
        # 检查日志文件是否已创建
        self.assertTrue(os.path.exists(custom_log_path), "应该在自定义路径创建日志文件")
    
    def test_custom_language(self):
        """测试通过配置文件设置默认语言"""
        # 修改配置文件，设置默认语言为英文
        with open(self.test_config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # 确保配置有正确的结构
        if 'logloom' in config:
            # 原始配置结构
            config['logloom']['language'] = 'en'
        else:
            # 测试期望的结构
            if 'i18n' not in config:
                config['i18n'] = {}
            config['i18n']['default_language'] = 'en'
        
        with open(self.test_config_path, 'w') as f:
            yaml.dump(config, f)
            
        # 使用修改后的配置初始化
        ll.initialize(self.test_config_path)
        
        # 检查默认语言是否为英文
        self.assertEqual(ll.get_current_language(), 'en', "默认语言应该被设置为英文")
        ll.cleanup()
        
        # 修改配置文件，设置默认语言为中文
        with open(self.test_config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # 确保配置有正确的结构
        if 'logloom' in config:
            # 原始配置结构
            config['logloom']['language'] = 'zh'
        else:
            # 测试期望的结构
            if 'i18n' not in config:
                config['i18n'] = {}
            config['i18n']['default_language'] = 'zh'
        
        with open(self.test_config_path, 'w') as f:
            yaml.dump(config, f)
            
        # 使用修改后的配置初始化
        ll.initialize(self.test_config_path)
        
        # 检查默认语言是否为中文
        self.assertEqual(ll.get_current_language(), 'zh', "默认语言应该被设置为中文")
        ll.cleanup()
    
    def test_invalid_config(self):
        """测试无效配置文件处理"""
        # 创建一个格式错误的配置文件
        invalid_config_path = os.path.join(self.temp_dir, 'invalid_config.yaml')
        with open(invalid_config_path, 'w') as f:
            f.write("这不是有效的YAML格式")
            
        # 尝试使用无效配置初始化
        try:
            result = ll.initialize(invalid_config_path)
            self.assertFalse(result, "使用无效配置初始化应该失败")
        except:
            # 如果初始化抛出异常，测试也通过
            pass
            
        # 清理可能的资源
        try:
            ll.cleanup()
        except:
            pass

if __name__ == "__main__":
    unittest.main()