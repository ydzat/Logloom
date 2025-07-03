#!/usr/bin/env python3
"""
调试Logloom国际化扩展功能导入问题
"""

import os
import sys
from pathlib import Path

# 将Logloom模块目录添加到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'bindings' / 'python'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'bindings' / 'python' / 'logloom_py'))

print("Python路径:")
for p in sys.path:
    print(f"  {p}")

# 尝试直接导入纯Python实现
try:
    from logloom_py import logloom_pure
    print("\n成功导入纯Python实现")
    print("可用函数:")
    for name in dir(logloom_pure):
        if not name.startswith('_'):
            print(f"  {name}")
except ImportError as e:
    print(f"\n导入纯Python实现失败: {e}")

# 尝试导入主模块
try:
    import logloom
    print("\n成功导入Logloom主模块")
    print("可用函数:")
    for name in dir(logloom):
        if not name.startswith('_'):
            print(f"  {name}")
        
    # 创建法语测试文件路径
    fr_yaml_path = os.path.join(os.path.dirname(__file__), 'test_locales', 'fr.yaml')
    
    # 初始化Logloom
    print("\n初始化Logloom")
    logloom.initialize()
    
    # 尝试使用新API (如果可用)
    if hasattr(logloom, 'register_locale_file'):
        print("\n测试注册法语资源文件")
        result = logloom.register_locale_file(fr_yaml_path)
        print(f"注册结果: {result}")
        
        print("\n测试切换到法语")
        logloom.set_language("fr")
        print(f"当前语言: {logloom.get_language()}")
        
        print("\n测试获取法语文本")
        text = logloom.get_text("test.hello")
        print(f"文本: {text}")
        
        print("\n测试格式化法语文本")
        formatted = logloom.format_text("test.hello", "monde")
        print(f"格式化文本: {formatted}")
    else:
        print("\n新API不可用")
        print("可能需要重新编译Python模块或修复导入路径")
except ImportError as e:
    print(f"\n导入Logloom主模块失败: {e}")