"""
Logloom Python 插件系统

本模块提供了与 C 语言插件系统功能等效的 Python 插件系统实现，
允许开发者通过 Python 编写处理日志的插件。

基本用法:
    from logloom.plugin import FilterPlugin, PluginResult
    
    class MyFilter(FilterPlugin):
        def __init__(self):
            super().__init__(
                name="my_filter",
                version="1.0.0",
                author="Your Name",
                description="My filter plugin"
            )
        
        def init(self, helpers):
            self._helpers = helpers
            return 0
        
        def process(self, log_entry):
            # 过滤掉所有DEBUG级别日志
            if log_entry.level <= 1:  # DEBUG
                return PluginResult.SKIP
            return PluginResult.OK
        
        def shutdown(self):
            pass
"""

from .plugin_base import (
    Plugin, FilterPlugin, SinkPlugin, AIPlugin, LangPlugin,
    PluginType, PluginMode, PluginCapability, PluginResult,
    PluginInfo, LogEntry, PluginHelpers
)

from .loader import (
    initialize, 
    scan_and_load, 
    unload_all, 
    shutdown, 
    filter_log, 
    sink_log, 
    ai_process, 
    set_plugin_enabled, 
    get_plugin, 
    get_plugin_info, 
    get_plugins_by_type
)

__all__ = [
    # 基础类型
    'Plugin', 'FilterPlugin', 'SinkPlugin', 'AIPlugin', 'LangPlugin',
    'PluginType', 'PluginMode', 'PluginCapability', 'PluginResult',
    'PluginInfo', 'LogEntry', 'PluginHelpers',
    
    # 管理函数
    'initialize', 'scan_and_load', 'unload_all', 'shutdown',
    'filter_log', 'sink_log', 'ai_process',
    'set_plugin_enabled', 'get_plugin', 'get_plugin_info',
    'get_plugins_by_type'
]