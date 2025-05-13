#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python 版本的 Logloom 国际化支持模块

本模块实现了 Logloom Python 绑定的国际化支持功能，
确保与 C 版本的国际化功能一致，包括：
- 获取本地化字符串
- 格式化本地化字符串
- 支持多种语言和区域

此模块设计为直接使用 C 版本的国际化库，通过 ctypes 绑定实现。
也可以在纯 Python 环境中使用 YAML 文件作为后端。
"""

import os
import sys
import yaml
import ctypes
from typing import Dict, Optional, Any
import logging
import locale

# 配置日志记录器
logger = logging.getLogger("logloom.lang")

# 默认语言文件路径
DEFAULT_LOCALE_PATHS = [
    "./locales",  # 相对路径，便于开发
    os.path.expanduser("~/.local/share/logloom/locales"),  # 用户级语言文件
    "/usr/share/logloom/locales"  # 系统级语言文件
]

# 全局变量
_lang_initialized = False
_current_locale = "en"
_locale_data = {}
_c_lib = None


def _try_load_c_lib():
    """尝试加载 C 版本的国际化库"""
    global _c_lib
    
    if _c_lib:
        return True
        
    lib_paths = [
        "./liblogloom.so",
        os.path.expanduser("~/.local/lib/liblogloom.so"),
        "/usr/lib/liblogloom.so"
    ]
    
    for path in lib_paths:
        if os.path.exists(path):
            try:
                _c_lib = ctypes.cdll.LoadLibrary(path)
                logger.debug(f"已加载 C 库: {path}")
                
                # 配置函数参数和返回类型
                _c_lib.lang_get.argtypes = [ctypes.c_char_p]
                _c_lib.lang_get.restype = ctypes.c_char_p
                
                _c_lib.lang_getf.argtypes = [ctypes.c_char_p]  # 变参函数，只指定第一个参数
                _c_lib.lang_getf.restype = ctypes.c_void_p     # 返回堆上分配的字符串
                
                _c_lib.lang_free.argtypes = [ctypes.c_void_p]
                _c_lib.lang_free.restype = None
                
                return True
            except Exception as e:
                logger.debug(f"加载 C 库失败: {path}, {str(e)}")
    
    logger.debug("未找到 Logloom C 库，将使用纯 Python 实现")
    return False


def _load_locale_file(locale_name):
    """加载指定区域的语言文件"""
    global _locale_data
    
    _locale_data.clear()
    
    for locale_path in DEFAULT_LOCALE_PATHS:
        file_path = os.path.join(locale_path, f"{locale_name}.yaml")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and isinstance(data, dict):
                        _locale_data.update(data)
                        logger.debug(f"已加载语言文件: {file_path}")
                        break
            except Exception as e:
                logger.error(f"加载语言文件失败: {file_path}, {str(e)}")
    
    if not _locale_data:
        logger.warning(f"未找到区域 {locale_name} 的语言文件，将使用键名作为文本")


def initialize(locale_name=None):
    """
    初始化国际化系统
    
    Args:
        locale_name: 区域名称，如 'en' 或 'zh'，如果为 None 则使用系统设置
    
    Returns:
        初始化是否成功
    """
    global _lang_initialized, _current_locale
    
    if _lang_initialized:
        return True
    
    # 如果未指定区域，则尝试从环境变量获取
    if not locale_name:
        try:
            # 从环境变量获取区域
            system_locale, _ = locale.getdefaultlocale()
            if system_locale:
                locale_name = system_locale.split('_')[0]
            else:
                locale_name = "en"
            logger.debug(f"从系统获取区域设置: {locale_name}")
        except Exception:
            locale_name = "en"
            logger.warning("获取系统区域设置失败，使用默认值: en")
    
    _current_locale = locale_name
    
    # 尝试加载 C 库，如果失败则使用纯 Python 实现
    if not _try_load_c_lib():
        _load_locale_file(locale_name)
    
    _lang_initialized = True
    logger.info(f"国际化系统已初始化，当前区域: {_current_locale}")
    return True


def get(key):
    """
    获取本地化字符串
    
    Args:
        key: 字符串键名
    
    Returns:
        本地化的字符串，如果未找到则返回键名
    """
    if not _lang_initialized:
        initialize()
    
    # 如果有 C 库，优先使用 C 库实现
    if _c_lib:
        try:
            c_key = ctypes.c_char_p(key.encode('utf-8'))
            result = _c_lib.lang_get(c_key)
            if result:
                return result.decode('utf-8')
            return key
        except Exception as e:
            logger.debug(f"使用 C 库获取本地化字符串失败: {str(e)}")
    
    # 纯 Python 实现
    try:
        # 点号分隔的键支持层次化访问
        if '.' in key:
            parts = key.split('.')
            value = _locale_data
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return key
            
            if isinstance(value, str):
                return value
        
        # 单层键
        elif key in _locale_data:
            return _locale_data[key]
    except Exception:
        pass
    
    return key


def getf(format_key, *args):
    """
    获取并格式化本地化字符串
    
    Args:
        format_key: 格式化字符串的键名
        *args: 要插入到格式化字符串中的参数
    
    Returns:
        格式化后的本地化字符串，如果未找到则使用键名作为格式化字符串
    """
    if not _lang_initialized:
        initialize()
    
    # 获取格式化字符串
    format_str = get(format_key)
    
    # 执行格式化
    try:
        return format_str.format(*args)
    except Exception as e:
        logger.debug(f"格式化字符串失败: {format_key}, {str(e)}")
        return format_key


def set_locale(locale_name):
    """
    切换当前区域
    
    Args:
        locale_name: 区域名称，如 'en' 或 'zh'
    
    Returns:
        是否成功切换
    """
    global _current_locale
    
    if not _lang_initialized:
        return initialize(locale_name)
    
    if _c_lib:
        try:
            # 使用 C 库实现
            c_locale = ctypes.c_char_p(locale_name.encode('utf-8'))
            result = _c_lib.lang_set_locale(c_locale)
            if result:
                _current_locale = locale_name
                return True
            return False
        except Exception as e:
            logger.debug(f"使用 C 库切换区域失败: {str(e)}")
    
    # 纯 Python 实现
    _current_locale = locale_name
    _load_locale_file(locale_name)
    return True


def get_current_locale():
    """
    获取当前区域
    
    Returns:
        当前区域名称
    """
    if not _lang_initialized:
        initialize()
    
    return _current_locale


# 初始化模块
if not _lang_initialized:
    initialize()