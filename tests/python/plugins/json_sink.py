#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
示例输出插件：JSON输出器

这个插件将日志消息输出为JSON格式。
"""

import os
import sys
import json
import time
from datetime import datetime

# 添加项目根目录到Python路径，以便导入logloom模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 尝试不同的导入路径，以支持多种安装方式
try:
    # 首先尝试导入已安装的logloom包
    from logloom.plugin import SinkPlugin, PluginResult, PluginMode, PluginCapability
except ImportError:
    try:
        # 然后尝试直接从源代码目录导入
        from src.bindings.python.plugin import SinkPlugin, PluginResult, PluginMode, PluginCapability
    except ImportError:
        try:
            # 最后尝试从logloom_py导入
            from logloom_py.plugin import SinkPlugin, PluginResult, PluginMode, PluginCapability
        except ImportError:
            # 导入失败时显示错误信息
            raise ImportError("无法导入Logloom插件系统。请确保Logloom已正确安装，或在开发环境中正确设置了PYTHONPATH。")


class JsonSinkPlugin(SinkPlugin):
    """
    JSON输出插件
    将日志条目转换为JSON格式并输出到文件
    """
    
    def __init__(self):
        super().__init__(
            name="json_sink",
            version="1.0.0",
            author="Logloom Team",
            mode=PluginMode.SYNC,
            capabilities=PluginCapability.JSON,
            description="将日志条目输出为JSON格式"
        )
        self._output_file = None
        self._file_path = None
    
    def init(self, helpers):
        """
        初始化插件
        
        Args:
            helpers: 插件辅助函数
        
        Returns:
            0表示成功，非0表示失败
        """
        self._helpers = helpers
        
        # 从配置中读取输出文件路径
        self._file_path = self.get_config_string("file_path", "logs/json_output.json")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
        
        # 打开输出文件
        try:
            self._output_file = open(self._file_path, "a", encoding="utf-8")
            print(f"[JsonSinkPlugin] 初始化成功，输出文件: {self._file_path}")
            return 0
        except Exception as e:
            print(f"[JsonSinkPlugin] 初始化失败: {str(e)}")
            return 1
    
    def process(self, log_entry):
        """
        处理日志条目
        
        Args:
            log_entry: 日志条目
        
        Returns:
            处理结果状态码
        """
        if not self._output_file:
            print("[JsonSinkPlugin] 未初始化输出文件")
            return PluginResult.ERROR
        
        # 构建JSON记录
        log_record = {
            "timestamp": log_entry.timestamp,
            "datetime": datetime.fromtimestamp(log_entry.timestamp).isoformat(),
            "level": log_entry.level,
            "message": log_entry.message,
            "module": log_entry.module,
            "file": log_entry.file,
            "line": log_entry.line,
            "context": log_entry.context
        }
        
        try:
            # 写入JSON记录
            json_line = json.dumps(log_record)
            self._output_file.write(json_line + "\n")
            self._output_file.flush()
            print(f"[JsonSinkPlugin] 写入日志: {log_entry.message}")
            return PluginResult.OK
        except Exception as e:
            print(f"[JsonSinkPlugin] 写入日志失败: {str(e)}")
            return PluginResult.ERROR
    
    def shutdown(self):
        """关闭插件"""
        if self._output_file:
            try:
                self._output_file.close()
                print(f"[JsonSinkPlugin] 已关闭输出文件: {self._file_path}")
            except Exception as e:
                print(f"[JsonSinkPlugin] 关闭输出文件时出错: {str(e)}")
        
        print("[JsonSinkPlugin] 关闭")