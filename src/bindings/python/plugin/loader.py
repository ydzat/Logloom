#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python 版本的 Logloom 插件系统加载器

本模块实现了 Logloom Python 插件系统的发现、加载和管理功能，
确保与 C 版本的插件加载器功能一致，包括：
- 插件发现与加载
- 插件注册与管理
- 插件调用与生命周期控制
"""

import os
import sys
import json
import importlib.util
import importlib.machinery
import inspect
import threading
import logging
import traceback
from typing import Dict, List, Optional, Any, Type, Callable, Union, Set, Tuple

from .plugin_base import (
    Plugin, FilterPlugin, SinkPlugin, AIPlugin, LangPlugin,
    PluginType, PluginMode, PluginCapability, PluginResult, PluginInfo,
    LogEntry, PluginHelpers
)

# 配置日志记录器
logger = logging.getLogger("logloom.plugin.loader")

# 插件系统配置默认值
DEFAULT_PLUGIN_PATHS = [
    "./plugins",  # 相对路径，便于开发
    os.path.expanduser("~/.local/lib/logloom/plugins"),  # 用户级插件
    "/usr/lib/logloom/plugins"  # 系统级插件
]


class PluginInstance:
    """插件实例包装类，对应C中的plugin_instance_t"""
    
    def __init__(self, name: str, path: str, plugin: Plugin, order: int = 999):
        """
        初始化插件实例
        
        Args:
            name: 插件名称
            path: 插件文件路径
            plugin: 插件实例
            order: 执行顺序（数字越小优先级越高）
        """
        self.name = name
        self.path = path
        self.plugin = plugin
        self.enabled = True
        self.order = order
        self.config = None  # JSON格式的配置
        self.module = None  # Python模块对象


class PluginManager:
    """插件管理器，负责发现、加载和管理插件"""
    
    def __init__(self):
        """初始化插件管理器"""
        self.plugin_list: Dict[str, PluginInstance] = {}  # 名称到插件实例的映射
        self.plugin_paths: List[str] = []  # 插件搜索路径
        self.enabled_plugins: Set[str] = set()  # 启用的插件名称集合
        self.disabled_plugins: Set[str] = set()  # 禁用的插件名称集合
        self.ordered_plugins: List[str] = []  # 顺序插件列表
        self.plugin_configs: Dict[str, Any] = {}  # 插件特定配置
        self.initialized = False  # 是否已初始化
        self.lock = threading.RLock()  # 线程锁
    
    def initialize(self, plugin_dir: Optional[str] = None, config_path: Optional[str] = None) -> int:
        """
        初始化插件系统
        
        Args:
            plugin_dir: 插件目录，如果指定则添加到搜索路径
            config_path: 配置文件路径，如果指定则从中加载配置
        
        Returns:
            0表示成功，非0表示失败
        """
        if self.initialized:
            logger.warning("插件系统已初始化，忽略重复调用")
            return 0
        
        # 加载默认插件路径
        self.plugin_paths = DEFAULT_PLUGIN_PATHS.copy()
        
        # 如果提供了插件目录参数，添加到路径中
        if plugin_dir:
            abs_plugin_dir = os.path.abspath(plugin_dir)
            if os.path.isdir(abs_plugin_dir):
                # 确保自定义插件目录优先级最高
                self.plugin_paths.insert(0, abs_plugin_dir)
            else:
                logger.warning(f"指定的插件目录不存在: {abs_plugin_dir}")
        
        # 从配置文件加载
        if config_path and os.path.isfile(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # 加载插件路径
                if 'plugin_paths' in config and isinstance(config['plugin_paths'], list):
                    for path in config['plugin_paths']:
                        if path not in self.plugin_paths:
                            self.plugin_paths.append(path)
                
                # 加载启用的插件列表
                if 'enabled_plugins' in config and isinstance(config['enabled_plugins'], list):
                    self.enabled_plugins = set(config['enabled_plugins'])
                
                # 加载禁用的插件列表
                if 'disabled_plugins' in config and isinstance(config['disabled_plugins'], list):
                    self.disabled_plugins = set(config['disabled_plugins'])
                
                # 加载插件顺序
                if 'plugin_order' in config and isinstance(config['plugin_order'], list):
                    self.ordered_plugins = config['plugin_order']
                
                # 加载插件特定配置
                if 'plugin_configs' in config and isinstance(config['plugin_configs'], dict):
                    self.plugin_configs = config['plugin_configs']
                
                logger.info(f"从配置文件加载了插件系统配置: {config_path}")
            except Exception as e:
                logger.error(f"加载配置文件失败: {str(e)}")
        
        self.initialized = True
        logger.info(f"插件系统已初始化，插件搜索路径: {', '.join(self.plugin_paths)}")
        return 0
    
    def get_plugin_order(self, plugin_name: str) -> int:
        """
        获取插件执行顺序
        
        Args:
            plugin_name: 插件名称
        
        Returns:
            执行顺序（数字越小优先级越高），如果未找到则返回最低优先级
        """
        try:
            return self.ordered_plugins.index(plugin_name)
        except ValueError:
            return 999  # 最低优先级
    
    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """
        判断插件是否启用
        
        Args:
            plugin_name: 插件名称
        
        Returns:
            如果启用返回True，否则返回False
        """
        # 检查是否在禁用列表中
        if plugin_name in self.disabled_plugins:
            return False
        
        # 如果启用列表为空，则默认启用所有未禁用的插件
        if not self.enabled_plugins:
            return True
        
        # 检查是否在启用列表中
        return plugin_name in self.enabled_plugins
    
    def get_plugin_config(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        获取插件特定配置
        
        Args:
            plugin_name: 插件名称
        
        Returns:
            插件配置，如果未找到则返回None
        """
        return self.plugin_configs.get(plugin_name)
    
    def create_plugin_helpers(self) -> PluginHelpers:
        """
        创建插件辅助函数
        
        Returns:
            插件辅助函数对象
        """
        return PluginHelpers(
            get_config_int_func=self.get_config_int,
            get_config_string_func=self.get_config_string,
            get_config_bool_func=self.get_config_bool,
            get_config_array_func=self.get_config_array
        )
    
    def get_config_int(self, plugin_name: str, key: str, default_value: int) -> int:
        """
        获取整数配置值
        
        Args:
            plugin_name: 插件名称
            key: 配置键
            default_value: 默认值
        
        Returns:
            配置值，如果未找到则返回默认值
        """
        config = self.get_plugin_config(plugin_name)
        if not config or key not in config:
            return default_value
        
        try:
            return int(config[key])
        except (ValueError, TypeError):
            return default_value
    
    def get_config_string(self, plugin_name: str, key: str, default_value: str) -> str:
        """
        获取字符串配置值
        
        Args:
            plugin_name: 插件名称
            key: 配置键
            default_value: 默认值
        
        Returns:
            配置值，如果未找到则返回默认值
        """
        config = self.get_plugin_config(plugin_name)
        if not config or key not in config:
            return default_value
        
        try:
            return str(config[key])
        except (ValueError, TypeError):
            return default_value
    
    def get_config_bool(self, plugin_name: str, key: str, default_value: bool) -> bool:
        """
        获取布尔配置值
        
        Args:
            plugin_name: 插件名称
            key: 配置键
            default_value: 默认值
        
        Returns:
            配置值，如果未找到则返回默认值
        """
        config = self.get_plugin_config(plugin_name)
        if not config or key not in config:
            return default_value
        
        value = config[key]
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'on')
        elif isinstance(value, int):
            return value != 0
        return default_value
    
    def get_config_array(self, plugin_name: str, key: str) -> List[str]:
        """
        获取字符串数组配置
        
        Args:
            plugin_name: 插件名称
            key: 配置键
        
        Returns:
            字符串数组，如果未找到则返回空数组
        """
        config = self.get_plugin_config(plugin_name)
        if not config or key not in config:
            return []
        
        value = config[key]
        if isinstance(value, list):
            return [str(item) for item in value]
        return []
    
    def discover_plugins(self) -> List[str]:
        """
        发现所有可能的插件文件
        
        Returns:
            发现的插件文件路径列表
        """
        plugin_files = []
        
        for plugin_path in self.plugin_paths:
            if not os.path.isdir(plugin_path):
                logger.debug(f"跳过不存在的插件目录: {plugin_path}")
                continue
            
            try:
                # 查找所有.py文件
                for file in os.listdir(plugin_path):
                    if file.endswith('.py') and not file.startswith('__'):
                        full_path = os.path.join(plugin_path, file)
                        plugin_files.append(full_path)
                
                # 查找所有包含__init__.py的目录
                for item in os.listdir(plugin_path):
                    dir_path = os.path.join(plugin_path, item)
                    init_file = os.path.join(dir_path, '__init__.py')
                    if os.path.isdir(dir_path) and os.path.isfile(init_file):
                        plugin_files.append(dir_path)
            
            except OSError as e:
                logger.error(f"读取插件目录出错: {plugin_path}, {str(e)}")
        
        return plugin_files
    
    def load_plugin_module(self, plugin_path: str) -> Tuple[Optional[Any], str]:
        """
        加载插件模块
        
        Args:
            plugin_path: 插件文件或目录路径
        
        Returns:
            (模块对象, 模块名称)的元组，如果加载失败则模块对象为None
        """
        try:
            # 提取模块名称（去除路径和扩展名）
            if plugin_path.endswith('.py'):
                module_name = os.path.basename(plugin_path)[:-3]
            else:
                module_name = os.path.basename(plugin_path)
            
            # 确保模块名称是有效的标识符
            if not module_name.isidentifier():
                logger.error(f"无效的模块名称: {module_name}")
                return None, module_name
            
            # 添加唯一标识符，防止重名
            unique_name = f"logloom_plugin_{module_name}_{id(plugin_path)}"
            
            # 如果是目录，加载包
            if os.path.isdir(plugin_path):
                spec = importlib.machinery.PathFinder.find_spec(module_name, [os.path.dirname(plugin_path)])
            else:
                spec = importlib.util.spec_from_file_location(unique_name, plugin_path)
            
            if spec is None:
                logger.error(f"无法为插件创建规范: {plugin_path}")
                return None, module_name
            
            print(f"[DEBUG] 加载模块: {plugin_path}, spec: {spec}")
            module = importlib.util.module_from_spec(spec)
            sys.modules[unique_name] = module
            spec.loader.exec_module(module)
            
            return module, module_name
        
        except Exception as e:
            logger.error(f"加载插件模块失败: {plugin_path}, {str(e)}")
            print(f"[DEBUG] 加载插件模块失败: {plugin_path}, 错误: {str(e)}")
            print(f"[DEBUG] 详细错误信息: {traceback.format_exc()}")
            return None, os.path.basename(plugin_path)
    
    def find_plugin_classes(self, module: Any) -> List[Type[Plugin]]:
        """
        在模块中查找所有插件类
        
        Args:
            module: 模块对象
        
        Returns:
            插件类列表
        """
        plugin_classes = []
        
        try:
            print(f"[DEBUG] 查找插件类: 模块内容: {dir(module)}")
            
            # 检查模块中所有可能的插件类
            for name, obj in inspect.getmembers(module):
                try:
                    if not inspect.isclass(obj):
                        continue
                        
                    # 检查类名是否符合命名规范（以Plugin结尾）
                    if name.endswith('Plugin'):
                        print(f"[DEBUG] 找到潜在插件类: {name}")
                        
                        # 检查类是否有必要的插件方法
                        has_init = hasattr(obj, 'init') and callable(getattr(obj, 'init'))
                        has_process = hasattr(obj, 'process') and callable(getattr(obj, 'process'))
                        has_shutdown = hasattr(obj, 'shutdown') and callable(getattr(obj, 'shutdown'))
                        
                        if has_init and has_process and has_shutdown:
                            print(f"[DEBUG] 类 {name} 具有所需的插件方法")
                            plugin_classes.append(obj)
                            print(f"[DEBUG] 添加插件类: {name}")
                        else:
                            print(f"[DEBUG] 类 {name} 缺少必要的插件方法: init={has_init}, process={has_process}, shutdown={has_shutdown}")
                            
                except Exception as e:
                    print(f"[DEBUG] 检查类 {name} 时出错: {str(e)}")
                    print(f"[DEBUG] 详细错误信息: {traceback.format_exc()}")
                    
        except Exception as e:
            print(f"[DEBUG] 查找插件类时出错: {str(e)}")
            print(f"[DEBUG] 详细错误信息: {traceback.format_exc()}")
        
        return plugin_classes
    
    def instantiate_plugin(self, plugin_class: Type[Plugin], plugin_path: str) -> Optional[PluginInstance]:
        """
        实例化插件
        
        Args:
            plugin_class: 插件类
            plugin_path: 插件文件路径
        
        Returns:
            插件实例，如果失败则返回None
        """
        try:
            print(f"[DEBUG] 实例化插件类: {plugin_class.__name__}")
            plugin = plugin_class()
            
            # 从类名或路径推断插件名称
            plugin_name = getattr(plugin, 'name', None) or plugin_class.__name__
            print(f"[DEBUG] 插件名称: {plugin_name}")
            
            # 检查插件是否启用
            enabled = self.is_plugin_enabled(plugin_name)
            if not enabled:
                logger.info(f"插件 {plugin_name} 已被禁用，跳过加载")
                return None
            
            # 获取插件执行顺序
            order = self.get_plugin_order(plugin_name)
            
            # 获取插件配置
            config = self.get_plugin_config(plugin_name)
            print(f"[DEBUG] 插件配置: {config}")
            
            # 创建插件实例
            instance = PluginInstance(
                name=plugin_name,
                path=plugin_path,
                plugin=plugin,
                order=order
            )
            instance.config = config
            instance.enabled = enabled
            
            return instance
        
        except Exception as e:
            logger.error(f"实例化插件失败: {plugin_class.__name__}, {str(e)}")
            print(f"[DEBUG] 实例化插件失败: {plugin_class.__name__}, 错误: {str(e)}")
            print(f"[DEBUG] 详细错误信息: {traceback.format_exc()}")
            return None
    
    def load_all_plugins(self) -> int:
        """
        加载所有插件
        
        Returns:
            成功加载的插件数量
        """
        if not self.initialized:
            logger.error("插件系统尚未初始化，无法加载插件")
            return 0
        
        loaded_count = 0
        
        # 创建插件辅助函数
        helpers = self.create_plugin_helpers()
        
        # 发现所有插件文件
        plugin_files = self.discover_plugins()
        logger.info(f"发现了 {len(plugin_files)} 个潜在插件文件")
        
        for plugin_path in plugin_files:
            # 加载模块
            module, module_name = self.load_plugin_module(plugin_path)
            if not module:
                continue
            
            # 查找插件类
            plugin_classes = self.find_plugin_classes(module)
            if not plugin_classes:
                logger.debug(f"在模块中未找到插件类: {plugin_path}")
                print(f"[DEBUG] 在模块中未找到插件类: {plugin_path}")
                continue
            
            # 为每个插件类创建实例
            for plugin_class in plugin_classes:
                with self.lock:
                    # 实例化插件
                    instance = self.instantiate_plugin(plugin_class, plugin_path)
                    if not instance:
                        continue
                    
                    # 检查是否已存在同名插件
                    if instance.name in self.plugin_list:
                        logger.warning(f"插件 {instance.name} 已加载，跳过")
                        continue
                    
                    # 初始化插件
                    try:
                        print(f"[DEBUG] 初始化插件: {instance.name}")
                        init_result = instance.plugin.init(helpers)
                        if init_result != 0:
                            logger.error(f"初始化插件 {instance.name} 失败: 错误码 {init_result}")
                            print(f"[DEBUG] 初始化插件 {instance.name} 失败: 错误码 {init_result}")
                            instance.enabled = False
                        else:
                            logger.info(f"插件 {instance.name} 初始化成功")
                            print(f"[DEBUG] 插件 {instance.name} 初始化成功")
                            loaded_count += 1
                    except Exception as e:
                        logger.error(f"初始化插件 {instance.name} 异常: {str(e)}")
                        print(f"[DEBUG] 初始化插件 {instance.name} 异常: {str(e)}")
                        print(f"[DEBUG] 详细错误信息: {traceback.format_exc()}")
                        instance.enabled = False
                    
                    # 保存插件实例和模块
                    self.plugin_list[instance.name] = instance
                    instance.module = module
        
        logger.info(f"成功加载了 {loaded_count} 个插件")
        return loaded_count
    
    def unload_all_plugins(self):
        """卸载所有插件"""
        if not self.initialized:
            return
        
        with self.lock:
            # 复制键列表以避免在迭代过程中修改字典
            plugin_names = list(self.plugin_list.keys())
            
            for name in plugin_names:
                instance = self.plugin_list[name]
                
                # 调用关闭函数
                if instance.enabled:
                    try:
                        logger.info(f"正在关闭插件: {name}")
                        instance.plugin.shutdown()
                    except Exception as e:
                        logger.error(f"关闭插件 {name} 时出错: {str(e)}")
                
                # 从字典中移除
                del self.plugin_list[name]
            
            logger.info(f"已卸载所有插件")
    
    def set_plugin_enabled(self, name: str, enabled: bool) -> bool:
        """
        设置插件状态（启用/禁用）
        
        Args:
            name: 插件名称
            enabled: 是否启用
        
        Returns:
            成功返回True，失败返回False
        """
        if not self.initialized:
            return False
        
        with self.lock:
            if name not in self.plugin_list:
                logger.error(f"插件 {name} 未找到，无法更改其状态")
                return False
            
            instance = self.plugin_list[name]
            instance.enabled = enabled
            instance.plugin.enabled = enabled
            
            logger.info(f"插件 {name} 已{'启用' if enabled else '禁用'}")
            return True
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """
        通过名称获取插件实例
        
        Args:
            name: 插件名称
        
        Returns:
            插件实例，如果未找到则返回None
        """
        if not self.initialized or name not in self.plugin_list:
            return None
        
        return self.plugin_list[name].plugin
    
    def get_plugin_info(self, name: str) -> Optional[PluginInfo]:
        """
        获取插件信息
        
        Args:
            name: 插件名称
        
        Returns:
            插件信息，如果未找到则返回None
        """
        plugin = self.get_plugin(name)
        return plugin.info if plugin else None
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """
        获取指定类型的所有插件
        
        Args:
            plugin_type: 插件类型
        
        Returns:
            插件列表
        """
        if not self.initialized:
            return []
        
        plugins = []
        with self.lock:
            for instance in self.plugin_list.values():
                if (instance.enabled and 
                    instance.plugin and 
                    instance.plugin.info.type == plugin_type):
                    plugins.append(instance.plugin)
        
        # 按优先级排序
        plugins.sort(key=lambda p: self.get_plugin_order(p.name))
        return plugins
    
    def get_filter_plugins(self) -> List[Plugin]:
        """获取所有过滤器插件"""
        return self.get_plugins_by_type(PluginType.FILTER)
    
    def get_sink_plugins(self) -> List[Plugin]:
        """获取所有输出插件"""
        return self.get_plugins_by_type(PluginType.SINK)
    
    def get_ai_plugins(self) -> List[Plugin]:
        """获取所有AI分析插件"""
        return self.get_plugins_by_type(PluginType.AI)
    
    def process_with_filters(self, log_entry: LogEntry) -> bool:
        """
        使用所有过滤器插件处理日志条目
        
        Args:
            log_entry: 日志条目
        
        Returns:
            允许通过的日志返回True，需要过滤的返回False
        """
        if not self.initialized:
            return True  # 默认通过
        
        filters = self.get_filter_plugins()
        
        for plugin in filters:
            try:
                result = plugin.process(log_entry)
                if result != PluginResult.OK:
                    # 过滤器插件要求过滤
                    return False
            except Exception as e:
                logger.error(f"过滤器插件 {plugin.name} 处理日志时出错: {str(e)}")
                logger.debug(traceback.format_exc())
        
        return True
    
    def process_with_sinks(self, log_entry: LogEntry):
        """
        使用所有输出插件处理日志条目
        
        Args:
            log_entry: 日志条目
        """
        if not self.initialized:
            return
        
        sinks = self.get_sink_plugins()
        
        for plugin in sinks:
            try:
                plugin.process(log_entry)
            except Exception as e:
                logger.error(f"输出插件 {plugin.name} 处理日志时出错: {str(e)}")
                logger.debug(traceback.format_exc())
    
    def process_with_ai(self, log_entry: LogEntry):
        """
        使用所有AI分析插件处理日志条目
        
        Args:
            log_entry: 日志条目
        """
        if not self.initialized:
            return
        
        ai_plugins = self.get_ai_plugins()
        
        for plugin in ai_plugins:
            try:
                plugin.process(log_entry)
            except Exception as e:
                logger.error(f"AI分析插件 {plugin.name} 处理日志时出错: {str(e)}")
                logger.debug(traceback.format_exc())
    
    def shutdown(self):
        """关闭插件系统"""
        if not self.initialized:
            return
        
        self.unload_all_plugins()
        self.plugin_list = {}
        self.initialized = False
        logger.info("插件系统已关闭")


# 全局插件管理器实例
plugin_manager = PluginManager()


# 便于使用的API函数

def initialize(plugin_dir: Optional[str] = None, config_path: Optional[str] = None) -> int:
    """
    初始化插件系统
    
    Args:
        plugin_dir: 插件目录
        config_path: 配置文件路径
    
    Returns:
        0表示成功，非0表示失败
    """
    return plugin_manager.initialize(plugin_dir, config_path)


def scan_and_load() -> int:
    """
    扫描并加载所有插件
    
    Returns:
        成功加载的插件数量
    """
    return plugin_manager.load_all_plugins()


def unload_all():
    """卸载所有插件"""
    plugin_manager.unload_all_plugins()


def shutdown():
    """关闭插件系统"""
    plugin_manager.shutdown()


def filter_log(log_entry: LogEntry) -> bool:
    """
    使用过滤器插件处理日志条目
    
    Args:
        log_entry: 日志条目
    
    Returns:
        允许通过的日志返回True，需要过滤的返回False
    """
    return plugin_manager.process_with_filters(log_entry)


def sink_log(log_entry: LogEntry):
    """
    使用输出插件处理日志条目
    
    Args:
        log_entry: 日志条目
    """
    plugin_manager.process_with_sinks(log_entry)


def ai_process(log_entry: LogEntry):
    """
    使用AI分析插件处理日志条目
    
    Args:
        log_entry: 日志条目
    """
    plugin_manager.process_with_ai(log_entry)


def set_plugin_enabled(name: str, enabled: bool) -> bool:
    """
    设置插件状态（启用/禁用）
    
    Args:
        name: 插件名称
        enabled: 是否启用
    
    Returns:
        成功返回True，失败返回False
    """
    return plugin_manager.set_plugin_enabled(name, enabled)


def get_plugin(name: str) -> Optional[Plugin]:
    """
    通过名称获取插件实例
    
    Args:
        name: 插件名称
    
    Returns:
        插件实例，如果未找到则返回None
    """
    return plugin_manager.get_plugin(name)


def get_plugin_info(name: str) -> Optional[PluginInfo]:
    """
    获取插件信息
    
    Args:
        name: 插件名称
    
    Returns:
        插件信息，如果未找到则返回None
    """
    return plugin_manager.get_plugin_info(name)


def get_plugins_by_type(plugin_type: PluginType) -> List[Plugin]:
    """
    获取指定类型的所有插件
    
    Args:
        plugin_type: 插件类型
    
    Returns:
        插件列表
    """
    return plugin_manager.get_plugins_by_type(plugin_type)