"""
Logloom Python Plugin System
===========================

This module provides the plugin system for Logloom in Python.
"""

# 从原始插件模块导入所有API
try:
    from ...plugin import (
        Plugin, FilterPlugin, SinkPlugin, AIPlugin, LangPlugin,
        PluginType, PluginMode, PluginCapability, PluginResult,
        PluginInfo, LogEntry, PluginHelpers,
        initialize, scan_and_load, unload_all, shutdown,
        filter_log, sink_log, ai_process,
        set_plugin_enabled, get_plugin, get_plugin_info, get_plugins_by_type
    )
    
    __all__ = [
        'Plugin', 'FilterPlugin', 'SinkPlugin', 'AIPlugin', 'LangPlugin',
        'PluginType', 'PluginMode', 'PluginCapability', 'PluginResult',
        'PluginInfo', 'LogEntry', 'PluginHelpers',
        'initialize', 'scan_and_load', 'unload_all', 'shutdown',
        'filter_log', 'sink_log', 'ai_process',
        'set_plugin_enabled', 'get_plugin', 'get_plugin_info', 'get_plugins_by_type'
    ]
except ImportError:
    import sys
    sys.stderr.write("警告: 无法导入插件系统模块。请确保Logloom已正确安装。\n")