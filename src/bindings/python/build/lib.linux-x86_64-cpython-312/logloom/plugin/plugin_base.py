#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python 版本的 Logloom 插件系统基础接口

本模块定义了 Logloom Python 插件系统的基础接口和数据结构，
确保与 C 版本的插件系统功能一致，包括：
- 插件类型和模式枚举
- 插件信息结构
- 插件基类定义
"""

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Dict, Any, List, Optional, Union


class PluginType(IntEnum):
    """插件类型枚举，对应 C 中的 plugin_type_t"""
    FILTER = 0  # 日志过滤器插件
    SINK = 1    # 日志输出插件
    AI = 2      # AI分析插件
    LANG = 3    # 语言资源插件
    UNKNOWN = 4  # 未知类型


class PluginMode(IntEnum):
    """插件调用模式枚举，对应 C 中的 plugin_mode_t"""
    SYNC = 0    # 同步调用模式
    ASYNC = 1   # 异步调用模式


class PluginCapability(IntEnum):
    """插件能力标识枚举，对应 C 中的 plugin_capability_t"""
    NONE = 0           # 无特殊能力
    BATCH = 1 << 0     # 支持批处理
    JSON = 1 << 1      # 支持JSON格式
    STREAM = 1 << 2    # 支持流式处理


class PluginResult(IntEnum):
    """插件处理结果状态码，对应 C 中的 plugin_result_t"""
    OK = 0      # 处理成功
    ERROR = 1   # 处理失败
    SKIP = 2    # 跳过处理
    RETRY = 3   # 重试请求


class PluginInfo:
    """插件信息类，对应 C 中的 plugin_info_t"""
    
    def __init__(self,
                 name: str,
                 version: str,
                 author: str,
                 plugin_type: PluginType = PluginType.UNKNOWN,
                 mode: PluginMode = PluginMode.SYNC,
                 capabilities: int = 0,
                 description: str = ""):
        """
        初始化插件信息
        
        Args:
            name: 插件名称
            version: 插件版本
            author: 插件作者
            plugin_type: 插件类型
            mode: 调用模式
            capabilities: 插件能力标识
            description: 插件描述
        """
        self.name = name
        self.version = version
        self.author = author
        self.type = plugin_type
        self.mode = mode
        self.capabilities = capabilities
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典形式"""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "type": self.type,
            "mode": self.mode,
            "capabilities": self.capabilities,
            "description": self.description
        }


class LogEntry:
    """日志条目类，对应 C 中的 log_entry_t"""
    
    def __init__(self,
                 level: int,
                 timestamp: float,
                 message: str,
                 module: str = "",
                 file: str = "",
                 line: int = 0,
                 context: Dict[str, Any] = None):
        """
        初始化日志条目
        
        Args:
            level: 日志级别
            timestamp: 时间戳（UNIX时间戳）
            message: 日志消息
            module: 模块名
            file: 源文件名
            line: 行号
            context: 上下文信息字典
        """
        self.level = level
        self.timestamp = timestamp
        self.message = message
        self.module = module
        self.file = file
        self.line = line
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典形式"""
        return {
            "level": self.level,
            "timestamp": self.timestamp,
            "message": self.message,
            "module": self.module,
            "file": self.file,
            "line": self.line,
            "context": self.context
        }


class PluginHelpers:
    """插件辅助函数类，对应 C 中的 plugin_helpers_t"""
    
    def __init__(self,
                 get_config_int_func=None,
                 get_config_string_func=None,
                 get_config_bool_func=None,
                 get_config_array_func=None):
        """
        初始化插件辅助函数
        
        Args:
            get_config_int_func: 获取整数配置的函数
            get_config_string_func: 获取字符串配置的函数
            get_config_bool_func: 获取布尔值配置的函数
            get_config_array_func: 获取字符串数组配置的函数
        """
        self.get_config_int = get_config_int_func
        self.get_config_string = get_config_string_func
        self.get_config_bool = get_config_bool_func
        self.get_config_array = get_config_array_func
    
    def get_int(self, plugin_name: str, key: str, default_value: int = 0) -> int:
        """
        获取整数配置
        
        Args:
            plugin_name: 插件名称
            key: 配置键
            default_value: 默认值
        
        Returns:
            配置值，如果未找到则返回默认值
        """
        if self.get_config_int:
            return self.get_config_int(plugin_name, key, default_value)
        return default_value
    
    def get_string(self, plugin_name: str, key: str, default_value: str = "") -> str:
        """
        获取字符串配置
        
        Args:
            plugin_name: 插件名称
            key: 配置键
            default_value: 默认值
        
        Returns:
            配置值，如果未找到则返回默认值
        """
        if self.get_config_string:
            return self.get_config_string(plugin_name, key, default_value)
        return default_value
    
    def get_bool(self, plugin_name: str, key: str, default_value: bool = False) -> bool:
        """
        获取布尔值配置
        
        Args:
            plugin_name: 插件名称
            key: 配置键
            default_value: 默认值
        
        Returns:
            配置值，如果未找到则返回默认值
        """
        if self.get_config_bool:
            return self.get_config_bool(plugin_name, key, default_value)
        return default_value
    
    def get_array(self, plugin_name: str, key: str) -> List[str]:
        """
        获取字符串数组配置
        
        Args:
            plugin_name: 插件名称
            key: 配置键
        
        Returns:
            字符串数组，如果未找到则返回空数组
        """
        if self.get_config_array:
            return self.get_config_array(plugin_name, key)
        return []


class Plugin(ABC):
    """
    插件基类，所有Python插件都应该继承此类并实现其接口方法
    
    这个类对应C插件中导出的函数集合（plugin_init、plugin_process、plugin_shutdown、plugin_info）
    """
    
    def __init__(self, name: str, version: str, author: str, 
                 plugin_type: PluginType = PluginType.UNKNOWN,
                 mode: PluginMode = PluginMode.SYNC,
                 capabilities: int = PluginCapability.NONE,
                 description: str = ""):
        """
        初始化插件
        
        Args:
            name: 插件名称
            version: 插件版本
            author: 插件作者
            plugin_type: 插件类型
            mode: 调用模式
            capabilities: 插件能力标识
            description: 插件描述
        """
        self._info = PluginInfo(
            name=name,
            version=version,
            author=author,
            plugin_type=plugin_type,
            mode=mode,
            capabilities=capabilities,
            description=description
        )
        self._helpers = None
        self._enabled = False
    
    @property
    def info(self) -> PluginInfo:
        """获取插件信息"""
        return self._info
    
    @property
    def name(self) -> str:
        """获取插件名称"""
        return self._info.name
    
    @property
    def enabled(self) -> bool:
        """获取插件启用状态"""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool):
        """设置插件启用状态"""
        self._enabled = value
    
    @abstractmethod
    def init(self, helpers: PluginHelpers) -> int:
        """
        初始化插件（对应C中的plugin_init函数）
        
        Args:
            helpers: 插件辅助函数
        
        Returns:
            0表示成功，非0表示失败
        """
        self._helpers = helpers
        return 0
    
    @abstractmethod
    def process(self, log_entry: LogEntry) -> int:
        """
        处理日志条目（对应C中的plugin_process函数）
        
        Args:
            log_entry: 日志条目
        
        Returns:
            处理结果状态码
        """
        pass
    
    @abstractmethod
    def shutdown(self):
        """
        关闭插件（对应C中的plugin_shutdown函数）
        在插件卸载前调用，用于释放资源
        """
        pass
    
    def get_config_int(self, key: str, default_value: int = 0) -> int:
        """
        获取整数配置
        
        Args:
            key: 配置键
            default_value: 默认值
        
        Returns:
            配置值，如果未找到则返回默认值
        """
        if self._helpers and self._helpers.get_config_int:
            return self._helpers.get_int(self.name, key, default_value)
        return default_value
    
    def get_config_string(self, key: str, default_value: str = "") -> str:
        """
        获取字符串配置
        
        Args:
            key: 配置键
            default_value: 默认值
        
        Returns:
            配置值，如果未找到则返回默认值
        """
        if self._helpers and self._helpers.get_config_string:
            return self._helpers.get_string(self.name, key, default_value)
        return default_value
    
    def get_config_bool(self, key: str, default_value: bool = False) -> bool:
        """
        获取布尔值配置
        
        Args:
            key: 配置键
            default_value: 默认值
        
        Returns:
            配置值，如果未找到则返回默认值
        """
        if self._helpers and self._helpers.get_config_bool:
            return self._helpers.get_bool(self.name, key, default_value)
        return default_value
    
    def get_config_array(self, key: str) -> List[str]:
        """
        获取字符串数组配置
        
        Args:
            key: 配置键
        
        Returns:
            字符串数组，如果未找到则返回空数组
        """
        if self._helpers and self._helpers.get_config_array:
            return self._helpers.get_array(self.name, key)
        return []


# 抽象插件类型，这些类为特定类型的插件提供模板
class FilterPlugin(Plugin):
    """过滤器插件基类"""
    
    def __init__(self, name: str, version: str, author: str,
                 mode: PluginMode = PluginMode.SYNC,
                 capabilities: int = PluginCapability.NONE,
                 description: str = ""):
        super().__init__(
            name=name,
            version=version,
            author=author,
            plugin_type=PluginType.FILTER,
            mode=mode,
            capabilities=capabilities,
            description=description
        )


class SinkPlugin(Plugin):
    """输出插件基类"""
    
    def __init__(self, name: str, version: str, author: str,
                 mode: PluginMode = PluginMode.SYNC,
                 capabilities: int = PluginCapability.NONE,
                 description: str = ""):
        super().__init__(
            name=name,
            version=version,
            author=author,
            plugin_type=PluginType.SINK,
            mode=mode,
            capabilities=capabilities,
            description=description
        )


class AIPlugin(Plugin):
    """AI分析插件基类"""
    
    def __init__(self, name: str, version: str, author: str,
                 mode: PluginMode = PluginMode.SYNC,
                 capabilities: int = PluginCapability.NONE,
                 description: str = ""):
        super().__init__(
            name=name,
            version=version,
            author=author,
            plugin_type=PluginType.AI,
            mode=mode,
            capabilities=capabilities,
            description=description
        )


class LangPlugin(Plugin):
    """语言资源插件基类"""
    
    def __init__(self, name: str, version: str, author: str,
                 mode: PluginMode = PluginMode.SYNC,
                 capabilities: int = PluginCapability.NONE,
                 description: str = ""):
        super().__init__(
            name=name,
            version=version,
            author=author,
            plugin_type=PluginType.LANG,
            mode=mode,
            capabilities=capabilities,
            description=description
        )