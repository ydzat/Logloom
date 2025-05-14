"""
Logloom 纯Python实现

该模块提供了与C扩展模块兼容的API，当C扩展无法加载时会使用此实现。
"""

import os
import sys
import glob
import warnings
import datetime
import yaml
import inspect
import logging
from typing import List, Dict, Optional, Tuple, Any, Union

# 初始化日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('logloom')

# 内部状态
_initialized = False
_current_language = "en"  # 默认语言
_resources = {}  # 语言资源字典 {lang_code: {key: value}}
_log_level = "INFO"
_log_file = None
_log_max_size = 1024 * 1024  # 默认1MB

# 日志级别映射
_log_level_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARN": logging.WARNING,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "FATAL": logging.CRITICAL,
    "CRITICAL": logging.CRITICAL
}

def initialize(config_path=None):
    """初始化Logloom"""
    global _initialized, _current_language, _log_level, _log_file, _log_max_size
    
    if _initialized:
        return True
        
    # 加载配置文件
    if config_path and os.path.isfile(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # 提取配置项
            if config:
                if 'logloom' in config:
                    logloom_config = config['logloom']
                    if 'language' in logloom_config:
                        _current_language = logloom_config['language']
                    if 'log' in logloom_config:
                        log_config = logloom_config['log']
                        if 'level' in log_config:
                            _log_level = log_config['level']
                        if 'file' in log_config:
                            _log_file = log_config['file']
                        if 'max_size' in log_config:
                            _log_max_size = int(log_config['max_size'])
                            
                # 处理另一种可能的配置格式
                if 'i18n' in config and 'default_language' in config['i18n']:
                    _current_language = config['i18n']['default_language']
                if 'logging' in config:
                    logging_config = config['logging']
                    if 'default_level' in logging_config:
                        _log_level = logging_config['default_level']
                    if 'output_path' in logging_config:
                        _log_file = logging_config['output_path']
                    if 'max_file_size' in logging_config:
                        _log_max_size = int(logging_config['max_file_size'])
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
    
    # 应用配置
    set_log_level(_log_level)
    if _log_file:
        set_log_file(_log_file)
    
    # 加载语言资源
    auto_discover_resources()
    
    _initialized = True
    return True

def cleanup():
    """清理Logloom资源"""
    global _initialized, _resources
    _initialized = False
    _resources = {}
    return True

def debug(module, message):
    """记录调试消息"""
    logger.debug(f"[{module}] {message}")

def info(module, message):
    """记录信息消息"""
    logger.info(f"[{module}] {message}")

def warn(module, message):
    """记录警告消息"""
    logger.warning(f"[{module}] {message}")

def warning(module, message):
    """记录警告消息（warn的别名）"""
    warn(module, message)

def error(module, message):
    """记录错误消息"""
    logger.error(f"[{module}] {message}")

def fatal(module, message):
    """记录致命错误消息"""
    logger.critical(f"[{module}] {message}")

def critical(module, message):
    """记录致命错误消息（fatal的别名）"""
    fatal(module, message)

def get_text(key):
    """获取国际化文本"""
    if not key:
        return None
        
    # 先在当前语言中查找
    if _current_language in _resources:
        value = _resources[_current_language].get(key)
        if value:
            return value
    
    # 在默认语言（英语）中查找，如果当前语言不是英语
    if _current_language != "en" and "en" in _resources:
        value = _resources["en"].get(key)
        if value:
            logger.warning(f"Language key not found in '{_current_language}': {key}, using default language")
            return value
    
    # 如果找不到，返回键本身作为值
    logger.warning(f"Language key not found: {key}")
    return key

def format_text(key, *args, **kwargs):
    """格式化国际化文本"""
    template = get_text(key)
    if not template:
        return key
        
    # 提取可能存在的lang参数
    lang_code = kwargs.pop('lang', None)
    if lang_code:
        old_lang = _current_language
        set_language(lang_code)
        template = get_text(key)
        set_language(old_lang)
        
    try:
        if kwargs:
            return template.format(**kwargs)
        elif args:
            return template.format(*args)
        else:
            return template
    except Exception as e:
        logger.warning(f"Format failed for key: {key} - {str(e)}")
        return f"[FORMAT ERROR: {str(e)}]"

def set_log_level(level):
    """设置日志级别"""
    global _log_level
    
    if level in _log_level_map:
        _log_level = level
        logger.setLevel(_log_level_map[level])
        return True
    else:
        logger.error(f"Invalid log level: {level}")
        return False

def set_language(lang_code):
    """设置当前语言"""
    global _current_language
    
    if not lang_code:
        return False
        
    # 如果语言资源不存在，尝试加载
    if lang_code not in _resources:
        # 自动发现该语言的资源
        found = False
        for path in [f"./locales/{lang_code}.yaml", f"~/.config/logloom/locales/{lang_code}.yaml"]:
            expanded_path = os.path.expanduser(path)
            if os.path.isfile(expanded_path):
                if register_locale_file(expanded_path, lang_code):
                    found = True
                    break
                    
        if not found:
            logger.warning(f"Language resources for '{lang_code}' not found")
            return False
    
    _current_language = lang_code
    return True

def get_language():
    """获取当前语言代码"""
    return _current_language

def get_current_language():
    """获取当前语言代码（别名）"""
    return get_language()

def set_log_file(file_path):
    """设置日志输出文件"""
    global _log_file
    
    if not file_path:
        # 关闭文件处理器
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                logger.removeHandler(handler)
        _log_file = None
        return True
        
    try:
        # 创建目录结构（如果需要）
        directory = os.path.dirname(os.path.abspath(file_path))
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        # 移除旧的文件处理器
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                logger.removeHandler(handler)
                
        # 添加新的文件处理器
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        
        _log_file = file_path
        return True
    except Exception as e:
        logger.error(f"Failed to set log file: {e}")
        return False

def set_log_max_size(max_size):
    """设置日志文件最大大小"""
    global _log_max_size
    
    if max_size <= 0:
        logger.warning(f"Invalid log max size: {max_size}")
        return False
        
    _log_max_size = max_size
    
    # 注意：纯Python实现不支持自动轮转，需要使用RotatingFileHandler
    # 这里仅仅记录设置，实际轮转需要在文件处理器中实现
    return True

def set_output_console(enabled):
    """设置是否输出到控制台"""
    # 查找并移除/添加控制台处理器
    found = False
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            if not enabled:
                logger.removeHandler(handler)
            found = True
            
    if enabled and not found:
        # 添加控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)
        
    return True

def _flatten_dict(d, parent_key='', sep='.'):
    """将嵌套字典扁平化"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def register_locale_file(file_path, lang_code=None):
    """注册语言资源文件"""
    if not file_path or not os.path.isfile(file_path):
        logger.error(f"Invalid language resource file: {file_path}")
        return False
        
    # 从文件名推断语言代码
    if not lang_code:
        basename = os.path.basename(file_path)
        # 移除扩展名
        basename = os.path.splitext(basename)[0]
        # 使用基本名称作为语言代码
        if basename.startswith("logloom_") or basename.startswith("app_"):
            # 如果是 logloom_en.yaml 或 app_en.yaml 这样的格式
            parts = basename.split('_')
            if len(parts) > 1:
                lang_code = parts[1]
        else:
            # 否则直接使用文件名作为语言代码
            lang_code = basename
            
    if not lang_code:
        logger.error(f"Cannot determine language code for file: {file_path}")
        return False
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        if not data or not isinstance(data, dict):
            logger.error(f"Invalid YAML format in file: {file_path}")
            return False
            
        # 扁平化嵌套字典
        flat_data = _flatten_dict(data)
        
        # 初始化语言资源字典
        if lang_code not in _resources:
            _resources[lang_code] = {}
            
        # 合并新资源
        _resources[lang_code].update(flat_data)
        
        return True
    except Exception as e:
        logger.error(f"Failed to load language resource file: {file_path} - {e}")
        return False

def register_locale_directory(dir_path, pattern="*.yaml"):
    """注册目录下所有匹配模式的语言资源文件"""
    if not dir_path or not os.path.isdir(dir_path):
        logger.error(f"Invalid directory: {dir_path}")
        return 0
        
    count = 0
    for file_path in glob.glob(os.path.join(dir_path, pattern)):
        if register_locale_file(file_path):
            count += 1
            
    return count

def scan_directory_with_glob(glob_pattern):
    """使用glob模式扫描目录下的语言资源文件"""
    if not glob_pattern:
        return 0
        
    count = 0
    for file_path in glob.glob(os.path.expanduser(glob_pattern)):
        if os.path.isfile(file_path) and register_locale_file(file_path):
            count += 1
            
    return count

def auto_discover_resources():
    """自动发现语言资源文件"""
    found = 0
    
    # 1. 检查当前工作目录/locales
    if os.path.isdir("./locales"):
        found += register_locale_directory("./locales", "*.yaml")
    
    # 2. 检查用户配置目录
    user_config_dir = os.path.expanduser("~/.config/logloom/locales")
    if os.path.isdir(user_config_dir):
        found += register_locale_directory(user_config_dir, "*.yaml")
        
    # 3. 检查系统语言定义目录
    system_locale_dir = "/usr/share/locale/logloom"
    if os.path.isdir(system_locale_dir):
        found += register_locale_directory(system_locale_dir, "*.yaml")
        
    return found > 0

def get_supported_languages():
    """获取当前支持的所有语言代码列表"""
    return list(_resources.keys())

def get_language_keys(lang_code=None):
    """获取指定语言中所有可用的翻译键列表"""
    # 如果没有指定语言，使用当前语言
    if not lang_code:
        lang_code = _current_language
        
    # 如果指定的语言不存在，返回空列表
    if lang_code not in _resources:
        return []
        
    # 返回所有键
    return list(_resources[lang_code].keys())