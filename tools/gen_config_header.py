#!/usr/bin/env python3
"""
生成配置头文件的工具脚本

用法: python3 gen_config_header.py config.yaml output_header.h
"""

import os
import sys
import re
import yaml
import json
from datetime import datetime

def validate_config(config):
    """
    验证配置是否有效
    """
    # 检查顶级键是否为 logloom
    if 'logloom' not in config:
        raise ValueError("配置文件必须有顶级键 'logloom'")

    logloom = config['logloom']
    
    # 验证语言配置
    if 'language' in logloom:
        lang = logloom['language']
        if not isinstance(lang, str) or len(lang) > 7:
            raise ValueError(f"无效的语言值: {lang}, 应该是字符串且长度小于8")
    
    # 验证日志配置
    if 'log' in logloom:
        log = logloom['log']
        
        # 验证日志级别
        if 'level' in log:
            level = log['level']
            if not isinstance(level, str) or level not in ['DEBUG', 'INFO', 'WARN', 'ERROR']:
                raise ValueError(f"无效的日志级别: {level}, 应该是 DEBUG/INFO/WARN/ERROR 之一")
        
        # 验证日志文件路径
        if 'file' in log:
            file_path = log['file']
            if not isinstance(file_path, str) or len(file_path) > 255:
                raise ValueError(f"无效的日志文件路径: {file_path}, 应该是字符串且长度小于256")
        
        # 验证最大文件大小
        if 'max_size' in log:
            max_size = log['max_size']
            if not isinstance(max_size, int) or max_size <= 0:
                raise ValueError(f"无效的最大文件大小: {max_size}, 应该是正整数")
        
        # 验证控制台输出设置
        if 'console' in log:
            console = log['console']
            if not isinstance(console, bool):
                raise ValueError(f"无效的控制台输出设置: {console}, 应该是布尔值")
    
    # 验证插件配置
    if 'plugin' in logloom:
        plugin = logloom['plugin']
        
        # 验证插件路径列表
        if 'paths' in plugin and not isinstance(plugin['paths'], list):
            raise ValueError("插件路径必须是一个列表")
            
        # 验证启用的插件列表
        if 'enabled' in plugin and not isinstance(plugin['enabled'], list):
            raise ValueError("启用的插件必须是一个列表")
            
        # 验证禁用的插件列表
        if 'disabled' in plugin and not isinstance(plugin['disabled'], list):
            raise ValueError("禁用的插件必须是一个列表")
            
        # 验证插件顺序列表
        if 'order' in plugin and not isinstance(plugin['order'], list):
            raise ValueError("插件顺序必须是一个列表")
            
        # 验证插件特定配置
        if 'config' in plugin and not isinstance(plugin['config'], dict):
            raise ValueError("插件特定配置必须是一个字典")
    
    return True

def generate_header_content(config):
    """
    根据配置生成头文件内容
    """
    # 默认值，如果配置中没有相应的键
    defaults = {
        'language': 'en',
        'log': {
            'level': 'INFO',
            'file': '',
            'max_size': 1048576,
            'console': True
        },
        'plugin': {
            'paths': ["/usr/lib/logloom/plugins", "./plugins"],
            'enabled': [],
            'disabled': [],
            'order': [],
            'config': {}
        }
    }
    
    # 从配置中获取值，如果不存在则使用默认值
    logloom = config.get('logloom', {})
    language = logloom.get('language', defaults['language'])
    
    log = logloom.get('log', {})
    log_level = log.get('level', defaults['log']['level'])
    log_file = log.get('file', defaults['log']['file'])
    log_max_size = log.get('max_size', defaults['log']['max_size'])
    log_console = 1 if log.get('console', defaults['log']['console']) else 0
    
    # 获取插件配置
    plugin = logloom.get('plugin', {})
    plugin_paths = plugin.get('paths', defaults['plugin']['paths'])
    plugin_enabled = plugin.get('enabled', defaults['plugin']['enabled'])
    plugin_disabled = plugin.get('disabled', defaults['plugin']['disabled'])
    plugin_order = plugin.get('order', defaults['plugin']['order'])
    plugin_config = plugin.get('config', defaults['plugin']['config'])
    
    # 转换插件路径列表为字符串表示
    plugin_paths_str = json.dumps(plugin_paths)
    plugin_enabled_str = json.dumps(plugin_enabled)
    plugin_disabled_str = json.dumps(plugin_disabled)
    plugin_order_str = json.dumps(plugin_order)
    
    # 转换插件特定配置为C结构体形式的字符串
    plugin_config_str = json.dumps(plugin_config)
    
    # 生成头文件内容
    header = f"""/**
 * 自动生成的配置头文件
 * 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 * 请勿手动修改此文件
 */

#ifndef LOGLOOM_GENERATED_CONFIG_H
#define LOGLOOM_GENERATED_CONFIG_H

/* 基本配置 */
#define LOGLOOM_LANG_DEFAULT "{language}"
#define LOGLOOM_LOG_LEVEL    "{log_level}"
#define LOGLOOM_LOG_FILE     "{log_file}"
#define LOGLOOM_LOG_MAXSIZE  {log_max_size}
#define LOGLOOM_LOG_CONSOLE  {log_console}

/* 插件系统配置 */
#define LOGLOOM_PLUGIN_PATHS_JSON     "{plugin_paths_str.replace('"', '\\"')}"
#define LOGLOOM_PLUGIN_ENABLED_JSON   "{plugin_enabled_str.replace('"', '\\"')}"
#define LOGLOOM_PLUGIN_DISABLED_JSON  "{plugin_disabled_str.replace('"', '\\"')}"
#define LOGLOOM_PLUGIN_ORDER_JSON     "{plugin_order_str.replace('"', '\\"')}"
#define LOGLOOM_PLUGIN_CONFIG_JSON    "{plugin_config_str.replace('"', '\\"')}"

/* 插件路径数量 */
#define LOGLOOM_PLUGIN_PATHS_COUNT    {len(plugin_paths)}

/* 
 * 将JSON配置解析为C结构体的工作应该在运行时进行，
 * 这里仅提供原始JSON字符串作为配置源
 */

#endif /* LOGLOOM_GENERATED_CONFIG_H */
"""
    return header

def main():
    if len(sys.argv) != 3:
        print(f"用法: {sys.argv[0]} <yaml配置文件> <输出头文件>")
        sys.exit(1)
    
    yaml_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # 验证配置
        validate_config(config)
        
        # 生成头文件内容
        header_content = generate_header_content(config)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 写入头文件
        with open(output_file, 'w') as f:
            f.write(header_content)
        
        print(f"成功生成配置头文件: {output_file}")
        
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()