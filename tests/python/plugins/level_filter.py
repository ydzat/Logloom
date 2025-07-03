#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
示例过滤器插件：级别过滤器

这个插件可以过滤掉低于指定级别的日志消息。
"""

import os
import sys
import traceback

# 添加项目根目录到Python路径，以便导入logloom模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src/bindings/python')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src/bindings/python/build/lib.linux-x86_64-cpython-312')))

# 输出调试信息
print(f"[DEBUG] LevelFilter插件的Python路径: {sys.path}")
print(f"[DEBUG] LevelFilter插件的当前目录: {os.getcwd()}")

# 尝试不同的导入路径，以支持多种安装方式
try:
    # 首先尝试导入已安装的logloom包
    print("[DEBUG] 尝试导入 logloom.plugin...")
    from logloom.plugin import FilterPlugin, PluginResult, PluginMode, PluginCapability
    print("[DEBUG] 成功导入 logloom.plugin")
except ImportError as e1:
    print(f"[DEBUG] 导入logloom.plugin失败: {str(e1)}")
    print(f"[DEBUG] 错误详情: {traceback.format_exc()}")
    try:
        # 然后尝试直接从源代码目录导入
        print("[DEBUG] 尝试导入 src.bindings.python.plugin...")
        from src.bindings.python.plugin import FilterPlugin, PluginResult, PluginMode, PluginCapability
        print("[DEBUG] 成功导入 src.bindings.python.plugin")
    except ImportError as e2:
        print(f"[DEBUG] 导入src.bindings.python.plugin失败: {str(e2)}")
        print(f"[DEBUG] 错误详情: {traceback.format_exc()}")
        try:
            # 最后尝试从logloom_py导入
            print("[DEBUG] 尝试导入 logloom_py.plugin...")
            from logloom_py.plugin import FilterPlugin, PluginResult, PluginMode, PluginCapability
            print("[DEBUG] 成功导入 logloom_py.plugin")
        except ImportError as e3:
            # 导入失败时显示错误信息
            print(f"[DEBUG] 导入logloom_py.plugin失败: {str(e3)}")
            print(f"[DEBUG] 错误详情: {traceback.format_exc()}")
            raise ImportError("无法导入Logloom插件系统。请确保Logloom已正确安装，或在开发环境中正确设置了PYTHONPATH。")


class LevelFilterPlugin(FilterPlugin):
    """
    级别过滤器插件
    过滤低于指定级别的日志消息
    """
    
    def __init__(self):
        super().__init__(
            name="level_filter",
            version="1.0.0",
            author="Logloom Team",
            mode=PluginMode.SYNC,
            capabilities=PluginCapability.NONE,
            description="过滤低于指定级别的日志消息"
        )
        self._min_level = 0  # 默认不过滤任何级别
    
    def init(self, helpers):
        """
        初始化插件
        
        Args:
            helpers: 插件辅助函数
        
        Returns:
            0表示成功，非0表示失败
        """
        self._helpers = helpers
        
        # 从配置中读取最小日志级别
        self._min_level = self.get_config_int("min_level", 0)
        print(f"[LevelFilterPlugin] 初始化成功，最小日志级别: {self._min_level}")
        return 0
    
    def process(self, log_entry):
        """
        处理日志条目
        
        Args:
            log_entry: 日志条目
        
        Returns:
            处理结果状态码
        """
        # 如果日志级别低于配置的最小级别，则过滤掉
        if log_entry.level < self._min_level:
            print(f"[LevelFilterPlugin] 过滤掉级别为 {log_entry.level} 的日志: {log_entry.message}")
            return PluginResult.SKIP
        
        print(f"[LevelFilterPlugin] 允许级别为 {log_entry.level} 的日志通过: {log_entry.message}")
        return PluginResult.OK
    
    def shutdown(self):
        """关闭插件"""
        print("[LevelFilterPlugin] 关闭")