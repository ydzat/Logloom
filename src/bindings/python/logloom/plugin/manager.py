#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Logloom Python 插件管理工具

提供命令行接口用于管理Logloom的Python插件，包括：
- 列出可用插件
- 启用/禁用插件
- 显示插件信息
- 创建插件配置文件
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("logloom.plugin.manager")

try:
    # 尝试导入插件系统
    from . import (
        initialize, scan_and_load, shutdown, get_plugin, get_plugin_info,
        get_plugins_by_type, PluginType
    )
except ImportError:
    logger.error("无法导入Logloom插件系统。请确保Logloom已正确安装。")
    sys.exit(1)


def find_plugin_paths() -> List[str]:
    """
    查找可能的插件目录
    
    Returns:
        插件目录列表
    """
    paths = []
    
    # 当前目录下的plugins
    if os.path.isdir("./plugins"):
        paths.append(os.path.abspath("./plugins"))
    
    # 用户级别插件目录
    user_plugin_dir = os.path.expanduser("~/.local/lib/logloom/plugins")
    if os.path.isdir(user_plugin_dir):
        paths.append(user_plugin_dir)
    
    # 系统级别插件目录
    system_plugin_dir = "/usr/lib/logloom/plugins"
    if os.path.isdir(system_plugin_dir):
        paths.append(system_plugin_dir)
    
    return paths


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置文件，如果文件不存在则创建默认配置
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        配置字典
    """
    # 默认配置文件路径
    if config_path is None:
        config_dir = os.path.expanduser("~/.config/logloom")
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "plugin_config.json")
    
    # 默认配置
    default_config = {
        "plugin_paths": find_plugin_paths(),
        "enabled_plugins": [],
        "disabled_plugins": [],
        "plugin_order": [],
        "plugin_configs": {}
    }
    
    # 尝试加载配置
    if os.path.isfile(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"已加载配置：{config_path}")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}，使用默认配置")
            return default_config
    else:
        # 创建默认配置
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            logger.info(f"已创建默认配置：{config_path}")
        except Exception as e:
            logger.error(f"创建默认配置失败: {str(e)}")
        
        return default_config


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """
    保存配置到文件
    
    Args:
        config: 配置字典
        config_path: 配置文件路径
    
    Returns:
        是否保存成功
    """
    # 默认配置文件路径
    if config_path is None:
        config_dir = os.path.expanduser("~/.config/logloom")
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "plugin_config.json")
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        logger.info(f"已保存配置：{config_path}")
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")
        return False


def list_plugins(args):
    """列出所有插件"""
    config = load_config(args.config)
    
    if initialize(None, args.config) != 0:
        logger.error("初始化插件系统失败")
        return
    
    # 扫描并加载插件
    loaded_count = scan_and_load()
    logger.info(f"发现 {loaded_count} 个插件")
    
    # 按类型分组显示插件
    for plugin_type in PluginType:
        plugins = get_plugins_by_type(plugin_type)
        if plugins:
            print(f"\n=== {plugin_type.name} 插件 ===")
            for plugin in plugins:
                status = "启用" if plugin.enabled else "禁用"
                print(f"- {plugin.name} (v{plugin.info.version}) [{status}]")
                print(f"  描述: {plugin.info.description}")
                print(f"  作者: {plugin.info.author}")
    
    # 关闭插件系统
    shutdown()


def show_plugin_info(args):
    """显示插件详细信息"""
    if initialize(None, args.config) != 0:
        logger.error("初始化插件系统失败")
        return
    
    # 扫描并加载插件
    scan_and_load()
    
    # 获取插件信息
    plugin = get_plugin(args.name)
    if plugin:
        info = plugin.info
        status = "启用" if plugin.enabled else "禁用"
        
        print(f"插件名称: {info.name}")
        print(f"版本: {info.version}")
        print(f"作者: {info.author}")
        print(f"状态: {status}")
        print(f"类型: {PluginType(info.type).name}")
        print(f"描述: {info.description}")
        
        # 显示配置
        config = load_config(args.config)
        plugin_config = config.get("plugin_configs", {}).get(info.name)
        if plugin_config:
            print("\n插件配置:")
            for key, value in plugin_config.items():
                print(f"- {key}: {value}")
    else:
        logger.error(f"未找到插件 '{args.name}'")
    
    # 关闭插件系统
    shutdown()


def enable_plugin(args):
    """启用插件"""
    config = load_config(args.config)
    
    # 更新配置
    if args.name in config.get("disabled_plugins", []):
        config["disabled_plugins"].remove(args.name)
    
    if args.name not in config.get("enabled_plugins", []):
        if "enabled_plugins" not in config:
            config["enabled_plugins"] = []
        config["enabled_plugins"].append(args.name)
    
    # 保存配置
    if save_config(config, args.config):
        print(f"插件 '{args.name}' 已启用")
    else:
        logger.error(f"启用插件 '{args.name}' 失败")


def disable_plugin(args):
    """禁用插件"""
    config = load_config(args.config)
    
    # 更新配置
    if args.name in config.get("enabled_plugins", []):
        config["enabled_plugins"].remove(args.name)
    
    if args.name not in config.get("disabled_plugins", []):
        if "disabled_plugins" not in config:
            config["disabled_plugins"] = []
        config["disabled_plugins"].append(args.name)
    
    # 保存配置
    if save_config(config, args.config):
        print(f"插件 '{args.name}' 已禁用")
    else:
        logger.error(f"禁用插件 '{args.name}' 失败")


def create_config(args):
    """创建或更新插件配置文件"""
    config = load_config(args.config)
    
    # 添加插件路径
    if args.add_path:
        abs_path = os.path.abspath(args.add_path)
        if os.path.isdir(abs_path) and abs_path not in config["plugin_paths"]:
            config["plugin_paths"].append(abs_path)
            print(f"已添加插件路径: {abs_path}")
    
    # 设置插件配置
    if args.plugin and args.key and args.value:
        if "plugin_configs" not in config:
            config["plugin_configs"] = {}
        
        if args.plugin not in config["plugin_configs"]:
            config["plugin_configs"][args.plugin] = {}
        
        # 尝试将值转换为适当的类型
        value = args.value
        try:
            # 尝试作为数字
            if value.isdigit():
                value = int(value)
            # 尝试作为布尔值
            elif value.lower() in ("true", "false"):
                value = value.lower() == "true"
            # 尝试作为JSON
            elif value.startswith("{") or value.startswith("["):
                value = json.loads(value)
        except (ValueError, json.JSONDecodeError):
            # 如果转换失败，保持原始字符串
            pass
        
        config["plugin_configs"][args.plugin][args.key] = value
        print(f"已设置 {args.plugin}.{args.key} = {value}")
    
    # 保存配置
    if save_config(config, args.config):
        print(f"配置已保存到: {args.config or '默认路径'}")
    else:
        logger.error("保存配置失败")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Logloom Python 插件管理工具")
    parser.add_argument("--config", help="配置文件路径")
    
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # list 子命令
    list_parser = subparsers.add_parser("list", help="列出所有插件")
    
    # info 子命令
    info_parser = subparsers.add_parser("info", help="显示插件详细信息")
    info_parser.add_argument("name", help="插件名称")
    
    # enable 子命令
    enable_parser = subparsers.add_parser("enable", help="启用插件")
    enable_parser.add_argument("name", help="插件名称")
    
    # disable 子命令
    disable_parser = subparsers.add_parser("disable", help="禁用插件")
    disable_parser.add_argument("name", help="插件名称")
    
    # config 子命令
    config_parser = subparsers.add_parser("config", help="创建或更新插件配置")
    config_parser.add_argument("--add-path", help="添加插件路径")
    config_parser.add_argument("--plugin", help="插件名称")
    config_parser.add_argument("--key", help="配置键")
    config_parser.add_argument("--value", help="配置值")
    
    # 解析参数
    args = parser.parse_args()
    
    if args.command == "list":
        list_plugins(args)
    elif args.command == "info":
        show_plugin_info(args)
    elif args.command == "enable":
        enable_plugin(args)
    elif args.command == "disable":
        disable_plugin(args)
    elif args.command == "config":
        create_config(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()