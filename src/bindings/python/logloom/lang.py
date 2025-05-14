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
import glob
from typing import Dict, Optional, Any, List
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
_resources = {}  # 用于存储动态加载的语言资源 {language_code: {key: value}}


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
        # 检查当前语言的动态加载资源
        if _current_locale in _resources and key in _resources[_current_locale]:
            return _resources[_current_locale][key]
            
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


def register_locale_file(file_path, lang_code=None):
    """
    注册额外的语言资源文件
    
    Args:
        file_path: YAML语言资源文件的路径
        lang_code: 语言代码，如"en", "zh"，如果为None，则从文件名推断
    
    Returns:
        bool: 注册是否成功
    """
    global _resources
    
    if not file_path or not os.path.isfile(file_path):
        logger.error(f"无效的语言资源文件: {file_path}")
        return False
    
    # 如果有C库，先尝试使用C库的实现
    if _c_lib and hasattr(_c_lib, 'lang_register_file'):
        try:
            c_file_path = ctypes.c_char_p(file_path.encode('utf-8'))
            c_lang_code = None
            if lang_code:
                c_lang_code = ctypes.c_char_p(lang_code.encode('utf-8'))
            result = _c_lib.lang_register_file(c_file_path, c_lang_code)
            return bool(result)
        except Exception as e:
            logger.debug(f"使用C库注册语言资源文件失败: {str(e)}")
    
    # 纯Python实现
    # 从文件名推断语言代码
    if not lang_code:
        basename = os.path.basename(file_path)
        # 移除扩展名
        basename = os.path.splitext(basename)[0]
        # 使用基本名称作为语言代码
        lang_code = basename
    
    if not lang_code:
        logger.error(f"无法确定文件的语言代码: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        if not data or not isinstance(data, dict):
            logger.error(f"无效的YAML格式: {file_path}")
            return False
            
        # 初始化语言资源字典
        if lang_code not in _resources:
            _resources[lang_code] = {}
            
        # 扁平化嵌套字典
        def flatten_dict(d, parent_key='', sep='.'):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)
            
        flat_data = flatten_dict(data)
        _resources[lang_code].update(flat_data)
        
        logger.info(f"成功注册语言资源文件: {file_path} (语言: {lang_code})")
        return True
    except Exception as e:
        logger.error(f"加载语言资源文件失败: {file_path} - {e}")
        return False


def register_locale_directory(dir_path, pattern="*.yaml"):
    """
    注册目录中所有匹配模式的语言资源文件
    
    Args:
        dir_path: 包含语言资源文件的目录路径
        pattern: 文件匹配模式（默认为"*.yaml"）
    
    Returns:
        int: 成功注册的文件数量
    """
    if not dir_path or not os.path.isdir(dir_path):
        logger.error(f"无效的目录: {dir_path}")
        return 0
    
    # 如果有C库，先尝试使用C库的实现
    if _c_lib and hasattr(_c_lib, 'lang_scan_directory'):
        try:
            c_dir_path = ctypes.c_char_p(dir_path.encode('utf-8'))
            c_pattern = ctypes.c_char_p(pattern.encode('utf-8'))
            return _c_lib.lang_scan_directory(c_dir_path, c_pattern)
        except Exception as e:
            logger.debug(f"使用C库注册语言资源目录失败: {str(e)}")
    
    # 纯Python实现
    count = 0
    for file_path in glob.glob(os.path.join(dir_path, pattern)):
        if register_locale_file(file_path):
            count += 1
            
    logger.info(f"从目录 {dir_path} 注册了 {count} 个语言资源文件")
    return count


def get_supported_languages():
    """
    获取当前支持的所有语言代码列表
    
    Returns:
        list: 语言代码列表
    """
    if _c_lib and hasattr(_c_lib, 'lang_get_supported_languages'):
        try:
            count = ctypes.c_int()
            langs_ptr = _c_lib.lang_get_supported_languages(ctypes.byref(count))
            if not langs_ptr or count.value <= 0:
                return ["en"]
                
            langs = []
            for i in range(count.value):
                lang = ctypes.string_at(ctypes.cast(langs_ptr + i * ctypes.sizeof(ctypes.c_char_p), 
                                                 ctypes.POINTER(ctypes.c_char_p))[0]).decode('utf-8')
                langs.append(lang)
                
            # 释放C分配的内存
            _c_lib.free(langs_ptr)
            return langs
        except Exception as e:
            logger.debug(f"使用C库获取支持的语言列表失败: {str(e)}")
    
    # 纯Python实现
    # 合并预设语言和资源中的语言
    default_languages = ["en", "zh"]
    resource_languages = list(_resources.keys())
    all_languages = list(set(default_languages + resource_languages))
    return all_languages


def get_language_keys(lang_code=None):
    """
    获取指定语言中所有可用的翻译键列表
    
    Args:
        lang_code: 语言代码，默认为当前语言
    
    Returns:
        list: 翻译键列表
    """
    # 如果没有指定语言，使用当前语言
    if not lang_code:
        lang_code = _current_locale
        
    if _c_lib and hasattr(_c_lib, 'lang_get_language_keys'):
        try:
            c_lang_code = ctypes.c_char_p(lang_code.encode('utf-8'))
            count = ctypes.c_int()
            keys_ptr = _c_lib.lang_get_language_keys(c_lang_code, ctypes.byref(count))
            if not keys_ptr or count.value <= 0:
                return []
                
            keys = []
            for i in range(count.value):
                key = ctypes.string_at(ctypes.cast(keys_ptr + i * ctypes.sizeof(ctypes.c_char_p), 
                                               ctypes.POINTER(ctypes.c_char_p))[0]).decode('utf-8')
                keys.append(key)
                
            # 释放C分配的内存
            _c_lib.free(keys_ptr)
            return keys
        except Exception as e:
            logger.debug(f"使用C库获取语言键列表失败: {str(e)}")
    
    # 纯Python实现
    # 如果指定的语言在资源中存在，返回其所有键
    if lang_code in _resources:
        return list(_resources[lang_code].keys())
    
    # 否则返回预设的一些键
    if lang_code == "en":
        return ["system.welcome", "system.error", "system.warning", "auth.login", "auth.logout"]
    elif lang_code == "zh":
        return ["system.welcome", "system.error", "system.warning", "auth.login", "auth.logout"]
        
    # 默认返回空列表
    return []


def scan_directory_with_glob(glob_pattern):
    """
    使用glob模式扫描目录查找语言资源文件
    
    Args:
        glob_pattern: glob模式字符串，如 "./locales/*.yaml"
    
    Returns:
        int: 成功注册的文件数量
    """
    if _c_lib and hasattr(_c_lib, 'lang_scan_directory_with_glob'):
        try:
            c_pattern = ctypes.c_char_p(glob_pattern.encode('utf-8'))
            return _c_lib.lang_scan_directory_with_glob(c_pattern)
        except Exception as e:
            logger.debug(f"使用C库进行glob扫描失败: {str(e)}")
    
    # 纯Python实现
    count = 0
    for file_path in glob.glob(glob_pattern):
        if os.path.isfile(file_path) and register_locale_file(file_path):
            count += 1
    
    return count


def auto_discover_resources():
    """
    自动发现并加载语言资源文件
    
    Returns:
        bool: 是否找到并加载了资源
    """
    if _c_lib and hasattr(_c_lib, 'lang_auto_discover_resources'):
        try:
            return bool(_c_lib.lang_auto_discover_resources())
        except Exception as e:
            logger.debug(f"使用C库进行资源自动发现失败: {str(e)}")
    
    # 纯Python实现
    found = 0
    
    # 1. 检查当前工作目录/locales
    if os.path.isdir("./locales"):
        found += register_locale_directory("./locales")
    
    # 2. 检查用户配置目录
    user_config = os.path.expanduser("~/.config/logloom/locales")
    if os.path.isdir(user_config):
        found += register_locale_directory(user_config)
    
    # 3. 检查系统级目录
    if os.path.isdir("/usr/share/logloom/locales"):
        found += register_locale_directory("/usr/share/logloom/locales")
    
    return found > 0


# 初始化模块
if not _lang_initialized:
    initialize()