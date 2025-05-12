#!/usr/bin/env python3
"""
Logloom Python 测试运行器
========================

这个脚本自动发现并运行所有 Logloom Python 绑定测试
"""

import os
import sys
import unittest
import importlib
import argparse
from pathlib import Path

# 确保测试适配器在路径中
sys.path.insert(0, str(Path(__file__).parent))

# 使用测试适配器
import test_adapter


def discover_and_run_tests(pattern=None, verbosity=1):
    """发现并运行匹配指定模式的测试"""
    # 获取当前测试目录
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 如果指定了测试模式，使用它进行过滤
    if pattern:
        pattern = f"test_{pattern}.py"
    else:
        pattern = "test_*.py"
        
    print(f"[信息] 在 {test_dir} 中寻找匹配 '{pattern}' 的测试...")
    
    # 初始化测试适配器
    config_path = os.path.join(test_dir, "config", "test_config.yaml")
    if not os.path.exists(os.path.dirname(config_path)):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
    # 如果测试配置文件不存在，创建一个基本配置
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            f.write("""# Logloom 测试配置
logloom:
  language: zh
  log:
    level: DEBUG
    path: ./logs
""")
    
    # 初始化 Logloom
    test_adapter.initialize(config_path)
    
    # 发现测试
    test_suite = unittest.defaultTestLoader.discover(
        test_dir, pattern=pattern
    )
    
    # 运行测试
    test_runner = unittest.TextTestRunner(verbosity=verbosity)
    result = test_runner.run(test_suite)
    
    # 清理资源
    test_adapter.cleanup()
    
    # 返回成功或失败
    if result.wasSuccessful():
        print("[成功] 所有测试通过!")
        return 0
    else:
        print(f"[失败] {len(result.failures) + len(result.errors)} 测试失败!")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行 Logloom Python 测试")
    parser.add_argument("--module", "-m", 
                      help="指定要测试的模块名称 (例如: 'basic' 将运行 test_basic.py)")
    parser.add_argument("--verbose", "-v", action="count", default=1,
                      help="增加输出详细程度")
    
    args = parser.parse_args()
    
    try:
        sys.exit(discover_and_run_tests(args.module, args.verbose))
    except KeyboardInterrupt:
        print("\n[中断] 测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"[错误] 运行测试时发生错误: {str(e)}")
        sys.exit(1)