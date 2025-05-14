"""
Logloom Python Bindings
=======================

Python interface for the Logloom logging and internationalization library.
"""
import sys
import os
import importlib.util
import warnings
import enum

# 定义在全局命名空间中的变量，以确保所有测试都能访问到
initialize = None
cleanup = None
debug = None
info = None
warn = None
warning = None
error = None
fatal = None
critical = None
get_text = None
format_text = None
set_log_level = None
set_language = None
get_language = None
get_current_language = None
set_log_file = None
set_log_max_size = None
set_output_console = None
# 新增的国际化扩展功能API
register_locale_file = None
register_locale_directory = None
scan_directory_with_glob = None
auto_discover_resources = None
get_supported_languages = None
get_language_keys = None

# LogLevel枚举 - 测试套件会查找这个
class LogLevel(enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"

# 尝试导入C扩展模块
_has_c_extension = False
try:
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 查找.so文件
    for filename in os.listdir(current_dir):
        if filename.startswith('logloom') and filename.endswith('.so'):
            so_path = os.path.join(current_dir, filename)
            spec = importlib.util.spec_from_file_location("logloom_c_ext", so_path)
            logloom_c_ext = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(logloom_c_ext)
            
            # 从C扩展模块导入所有函数
            for name in dir(logloom_c_ext):
                if not name.startswith('_'):
                    globals()[name] = getattr(logloom_c_ext, name)
            
            _has_c_extension = True
            break
    
    if not _has_c_extension:
        raise ImportError("无法找到C扩展模块")
        
except ImportError as e:
    warnings.warn(f"无法加载Logloom C扩展模块: {e}. 将使用纯Python实现 (功能有限).", ImportWarning)
    
    # 使用纯Python实现
    try:
        # 添加logloom_py目录到Python路径
        logloom_py_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logloom_py')
        if logloom_py_dir not in sys.path:
            sys.path.insert(0, logloom_py_dir)
        
        # 尝试导入纯Python实现
        import logloom_py.logloom_pure as pure

        # 将纯Python实现的函数添加到全局命名空间
        initialize = pure.initialize
        cleanup = pure.cleanup
        debug = pure.debug
        info = pure.info
        warn = pure.warn
        warning = pure.warning
        error = pure.error
        fatal = pure.fatal
        critical = pure.critical
        get_text = pure.get_text
        format_text = pure.format_text
        set_log_level = pure.set_log_level
        set_language = pure.set_language
        get_language = pure.get_language
        get_current_language = pure.get_current_language
        set_log_file = pure.set_log_file
        set_log_max_size = pure.set_log_max_size
        set_output_console = pure.set_output_console
        
        # 新增的国际化扩展功能API
        register_locale_file = pure.register_locale_file
        register_locale_directory = pure.register_locale_directory
        scan_directory_with_glob = pure.scan_directory_with_glob
        auto_discover_resources = pure.auto_discover_resources
        get_supported_languages = pure.get_supported_languages
        get_language_keys = pure.get_language_keys
        
        # 导入Logger类
        try:
            from logloom_py.logger import Logger
        except ImportError:
            # 如果无法导入，创建一个模拟的Logger类
            class Logger:
                def __init__(self, name="default"):
                    self.name = name
                def debug(self, message): debug(message)
                def info(self, message): info(message)
                def warn(self, message): warn(message)
                def warning(self, message): warning(message)
                def error(self, message): error(message)
                def fatal(self, message): fatal(message)
                def critical(self, message): critical(message)
    
    except ImportError as e:
        # 如果纯Python实现也无法导入，提供详细的错误信息
        raise ImportError(f"无法导入Logloom C扩展模块也无法导入纯Python实现: {e}")

# 模块版本号
__version__ = "1.1.0"