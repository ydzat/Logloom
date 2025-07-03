#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python插件系统测试脚本

这个脚本演示了如何使用Logloom Python插件系统，包括：
- 初始化插件系统
- 加载插件
- 使用插件处理日志条目
- 关闭插件系统
"""

import os
import sys
import json
import time
import logging
from datetime import datetime

# 添加项目根目录到Python路径，以便导入logloom模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/bindings/python')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/bindings/python/build/lib.linux-x86_64-cpython-312')))

try:
    # 尝试不同的导入路径
    try:
        # 首先尝试从源码直接导入
        from src.bindings.python.plugin import (
            initialize, scan_and_load, unload_all, shutdown, filter_log, sink_log, LogEntry
        )
    except ImportError:
        try:
            # 然后尝试从logloom_py导入
            from logloom_py.plugin import (
                initialize, scan_and_load, unload_all, shutdown, filter_log, sink_log, LogEntry
            )
        except ImportError:
            # 最后尝试从logloom导入
            from logloom.plugin import (
                initialize, scan_and_load, unload_all, shutdown, filter_log, sink_log, LogEntry
            )
except ImportError as e:
    print(f"无法导入Logloom插件系统: {e}")
    print("请确保Logloom已正确安装，或在开发环境中正确设置了PYTHONPATH。")
    sys.exit(1)

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("logloom.test")


def create_log_entry(level, message, module="test", context=None):
    """创建一个测试日志条目"""
    return LogEntry(
        level=level,
        timestamp=time.time(),
        message=message,
        module=module,
        file=__file__,
        line=0,
        context=context or {}
    )


def create_plugin_config():
    """创建插件配置文件"""
    config_dir = os.path.join(os.path.dirname(__file__), 'config')
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, 'plugin_config.json')
    
    # 插件系统配置
    config = {
        "plugin_paths": [
            os.path.join(os.path.dirname(__file__), "plugins")
        ],
        "enabled_plugins": [
            "level_filter", 
            "json_sink"
        ],
        "plugin_order": [
            "level_filter",  # 过滤器先执行
            "json_sink"      # 输出插件后执行
        ],
        "plugin_configs": {
            "level_filter": {
                "min_level": 2  # 过滤掉DEBUG级别的日志（假设级别为：0=DEBUG, 1=INFO, 2=WARN, 3=ERROR）
            },
            "json_sink": {
                "file_path": os.path.join(os.path.dirname(__file__), "logs/test_output.json")
            }
        }
    }
    
    # 写入配置文件
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    
    logger.info(f"创建了插件配置文件: {config_path}")
    return config_path


def main():
    """主函数"""
    try:
        logger.info("开始测试Python插件系统")
        
        # 创建插件配置
        config_path = create_plugin_config()
        
        # 初始化插件系统
        logger.info("初始化插件系统")
        result = initialize(
            plugin_dir=os.path.join(os.path.dirname(__file__), "plugins"),
            config_path=config_path
        )
        if result != 0:
            logger.error(f"初始化插件系统失败，错误码: {result}")
            return 1
        
        # 扫描并加载插件
        logger.info("扫描并加载插件")
        loaded_count = scan_and_load()
        logger.info(f"成功加载了 {loaded_count} 个插件")
        
        # 创建测试日志条目
        log_entries = [
            create_log_entry(0, "这是一条DEBUG级别日志", context={"debug_key": "debug_value"}),
            create_log_entry(1, "这是一条INFO级别日志", context={"info_key": "info_value"}),
            create_log_entry(2, "这是一条WARN级别日志", context={"warning": True}),
            create_log_entry(3, "这是一条ERROR级别日志", context={"error_code": 500})
        ]
        
        # 使用插件处理日志条目
        logger.info("使用插件处理日志条目")
        for entry in log_entries:
            # 首先，使用过滤器插件过滤
            passed = filter_log(entry)
            if passed:
                # 如果通过过滤器，使用输出插件处理
                logger.info(f"日志通过过滤器: {entry.message}")
                sink_log(entry)
            else:
                logger.info(f"日志被过滤: {entry.message}")
        
        # 卸载所有插件
        logger.info("卸载所有插件")
        unload_all()
        
        # 关闭插件系统
        logger.info("关闭插件系统")
        shutdown()
        
        logger.info("测试完成")
        return 0
    
    except Exception as e:
        logger.exception(f"测试过程中出现异常: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())