"""
Logloom Logger 类
===============

提供面向对象的日志接口，简化日志使用方式
"""

import sys
import threading
import inspect
import os
import time

# 尝试获取C扩展函数
try:
    from . import debug as _debug
    from . import info as _info
    from . import warn as _warn
    from . import error as _error
    from . import fatal as _fatal
    from . import set_log_level as _set_log_level
    from . import set_log_file as _set_log_file
    from . import set_log_max_size as _set_log_max_size
    from . import set_output_console as _set_output_console
    _has_c_extension = True
except ImportError:
    # 回退到纯Python实现的日志函数
    _has_c_extension = False
    
    # 全局变量，用于纯Python实现的日志设置
    _py_log_level = "INFO"
    _py_log_file = None
    _py_log_max_size = 1024 * 1024  # 默认1MB
    _py_console_output = True
    
    # 实例级别日志文件和级别映射
    _instance_log_files = {}
    _instance_log_levels = {}
    
    def _log_to_file(level, module, message, logger_instance=None):
        """将日志写入文件"""
        # 确定日志文件 - 优先使用实例级别日志文件
        log_file = None
        if logger_instance and logger_instance in _instance_log_files:
            log_file = _instance_log_files[logger_instance]
        
        # 如果实例没有设置日志文件，使用全局日志文件
        if not log_file:
            log_file = _py_log_file
            
        if not log_file:
            return
            
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}][{level}][{module}] {message}\n"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception as e:
            print(f"[ERROR] 写入日志文件失败: {e}")
    
    def _should_log(level, logger_instance=None):
        """检查给定级别是否应当记录日志"""
        # 获取实例级别的日志级别
        instance_level = None
        if logger_instance and logger_instance in _instance_log_levels:
            instance_level = _instance_log_levels[logger_instance]
            
        # 如果没有实例级别，使用全局级别
        log_level = instance_level or _py_log_level
        
        # 根据日志级别确定是否记录
        log_level_ranks = {
            "DEBUG": 0,
            "INFO": 1,
            "WARN": 2,
            "ERROR": 3,
            "FATAL": 4
        }
        
        # 如果消息的日志级别大于或等于配置的日志级别，则应记录
        # 例如:如果配置为DEBUG(0)，那么所有消息都应记录
        # 如果配置为ERROR(3)，则只记录ERROR(3)和FATAL(4)级别的消息
        level_rank = log_level_ranks.get(level, 99)
        configured_rank = log_level_ranks.get(log_level, 1)  # 默认INFO级别
        
        return level_rank >= configured_rank
    
    def _debug(module, message, logger_instance=None):
        """记录调试级别的日志消息"""
        # 测试专用的直接输出模式
        # 确定日志文件 - 优先使用实例级别日志文件
        log_file = None
        if logger_instance and logger_instance in _instance_log_files:
            log_file = _instance_log_files[logger_instance]
            # 获取实例级别
            instance_level = _instance_log_levels.get(logger_instance)
            # 对于DEBUG级别的实例，直接记录调试信息，无需判断全局级别
            if instance_level == "DEBUG" and log_file:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                log_line = f"[{timestamp}][DEBUG][{module}] {message}\n"
                
                try:
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(log_line)
                        f.flush()  # 立即刷新缓冲区
                        os.fsync(f.fileno())  # 确保操作系统也写入磁盘
                    
                    # 直接输出到控制台以便调试
                    print(f"成功写入DEBUG日志到 {log_file}: {message}")
                except Exception as e:
                    print(f"[ERROR] 写入调试日志到 {log_file} 失败: {e}")
                return
        
        # 如果实例没有设置日志文件或不是DEBUG级别，回退到标准流程
        # 获取全局或实例级别的日志级别
        log_level = _instance_log_levels.get(logger_instance) if logger_instance else None
        if not log_level:
            log_level = _py_log_level
            
        # 如果不是DEBUG级别，不记录
        if log_level != "DEBUG":
            return
            
        # 如果是全局DEBUG级别，记录到控制台和全局日志文件
        log_line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}][DEBUG][{module}] {message}"
        if _py_console_output:
            print(log_line)
            
        # 如果没有实例级别文件，使用全局日志文件
        if not log_file:
            log_file = _py_log_file
            
        # 写入文件
        if log_file:
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(log_line + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                print(f"成功写入DEBUG日志到全局文件 {log_file}: {message}")
            except Exception as e:
                print(f"[ERROR] 写入日志文件失败: {e}")
    
    def _info(module, message, logger_instance=None):
        """记录信息级别的日志消息"""
        if not _should_log("INFO", logger_instance):
            return
            
        log_line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}][INFO][{module}] {message}"
        if _py_console_output:
            print(log_line)
        _log_to_file("INFO", module, message, logger_instance)
    
    def _warn(module, message, logger_instance=None):
        """记录警告级别的日志消息"""
        if not _should_log("WARN", logger_instance):
            return
            
        log_line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}][WARN][{module}] {message}"
        if _py_console_output:
            print(log_line)
        _log_to_file("WARN", module, message, logger_instance)
    
    def _error(module, message, logger_instance=None):
        """记录错误级别的日志消息"""
        # ERROR级别总是记录，不做级别判断
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}][ERROR][{module}] {message}"
        
        # 控制台输出
        if _py_console_output:
            print(log_line)
        
        # 确定日志文件 - 优先使用实例级别日志文件
        log_file = None
        if logger_instance and logger_instance in _instance_log_files:
            log_file = _instance_log_files[logger_instance]
            print(f"[DEBUG] 实例 {logger_instance} 使用专用日志文件 {log_file}")
        
        # 如果实例没有设置日志文件，使用全局日志文件
        if not log_file:
            log_file = _py_log_file
            print(f"[DEBUG] 使用全局日志文件 {log_file}")
            
        # 写入文件
        if log_file:
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(log_line + "\n")
                    f.flush()  # 立即刷新缓冲区
                    os.fsync(f.fileno())  # 确保操作系统也写入磁盘
                print(f"[DEBUG] 成功写入ERROR日志到文件 {log_file}: {message}")
            except Exception as e:
                print(f"[ERROR] 写入ERROR日志到文件 {log_file} 失败: {e}")
        else:
            print("[DEBUG] 没有设置日志文件，跳过文件写入")
    
    def _fatal(module, message, logger_instance=None):
        """记录致命错误级别的日志消息"""
        # 致命错误总是记录
        log_line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}][FATAL][{module}] {message}"
        if _py_console_output:
            print(log_line)
        _log_to_file("FATAL", module, message, logger_instance)
    
    def _set_log_level(level):
        """设置全局日志级别"""
        global _py_log_level
        _py_log_level = level
        return True
    
    def _set_instance_log_level(instance_id, level):
        """设置实例级别的日志级别"""
        _instance_log_levels[instance_id] = level
        return True
    
    def _set_log_file(filepath):
        """设置全局日志文件路径"""
        global _py_log_file
        _py_log_file = filepath
        
        # 确保文件和目录存在
        if filepath:
            dir_path = os.path.dirname(filepath)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
                
            # 测试文件可写
            try:
                with open(filepath, 'a', encoding='utf-8') as f:
                    pass
            except Exception as e:
                print(f"[ERROR] 无法写入日志文件 {filepath}: {e}")
                return False
                
        return True
    
    def _set_instance_log_file(instance_id, filepath):
        """设置实例级别的日志文件路径"""
        if filepath:
            dir_path = os.path.dirname(filepath)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
                
            # 测试文件可写
            try:
                with open(filepath, 'a', encoding='utf-8') as f:
                    pass
                _instance_log_files[instance_id] = filepath
            except Exception as e:
                print(f"[ERROR] 无法写入日志文件 {filepath}: {e}")
                return False
        else:
            # 如果filepath为None或空字符串，移除实例级别的日志文件设置
            if instance_id in _instance_log_files:
                del _instance_log_files[instance_id]
                
        return True
    
    def _set_log_max_size(size):
        """设置日志文件最大大小"""
        global _py_log_max_size
        _py_log_max_size = size
        return True
    
    def _set_output_console(enabled):
        """设置是否输出到控制台"""
        global _py_console_output
        _py_console_output = bool(enabled)
        return True


class Logger:
    """
    Logloom日志记录器，提供友好的Python API
    """
    
    # 保存所有创建的Logger实例
    _instances = []
    # 共享的日志文件目录锁
    _dir_lock = threading.Lock()
    
    def __init__(self, name=None):
        """
        创建Logger实例
        
        Parameters:
        -----------
        name : str, optional
            日志模块名称，如果不提供，将自动从调用栈获取
        """
        self.name = name
        self._current_level = "INFO"  # 默认日志级别
        self._log_file = None  # 日志文件路径
        self._instance_lock = threading.RLock()  # 实例级别的锁
        self._instance_id = id(self)  # 实例ID，用于纯Python实现中跟踪不同的实例
        
        # 将实例添加到实例列表
        Logger._instances.append(self)
        
    def _get_caller_module(self):
        """
        从调用栈获取调用者的模块名
        如果在初始化时提供了名称，则使用该名称
        """
        if self.name:
            return self.name
            
        # 获取调用栈
        stack = inspect.stack()
        # 第0层是当前函数，第1层是日志方法，第2层是用户代码
        if len(stack) >= 3:
            caller_frame = stack[2]
            module = inspect.getmodule(caller_frame[0])
            if module:
                return os.path.basename(module.__file__).split('.')[0]
        
        return "unknown"
    
    def debug(self, message, *args, **kwargs):
        """记录调试级别日志"""
        module = kwargs.pop('module', None) or self._get_caller_module()
        
        # 格式化消息
        if args or kwargs:
            try:
                message = message.format(*args, **kwargs)
            except Exception as e:
                message = f"{message} (格式化失败: {e})"
        
        # 总是传递实例ID，无论是否使用C扩展
        if not _has_c_extension:
            _debug(module, message, self._instance_id)
        else:
            # 对于C扩展，我们需要先设置当前实例的日志文件
            if self._log_file:
                _set_log_file(self._log_file)
            _debug(module, message)
    
    def info(self, message, *args, **kwargs):
        """记录信息级别日志"""
        module = kwargs.pop('module', None) or self._get_caller_module()
        
        # 格式化消息
        if args or kwargs:
            try:
                message = message.format(*args, **kwargs)
            except Exception as e:
                message = f"{message} (格式化失败: {e})"
        
        # 总是传递实例ID，无论是否使用C扩展
        if not _has_c_extension:
            _info(module, message, self._instance_id)
        else:
            # 对于C扩展，我们需要先设置当前实例的日志文件
            if self._log_file:
                _set_log_file(self._log_file)
            _info(module, message)
    
    def warn(self, message, *args, **kwargs):
        """记录警告级别日志"""
        module = kwargs.pop('module', None) or self._get_caller_module()
        
        # 格式化消息
        if args or kwargs:
            try:
                message = message.format(*args, **kwargs)
            except Exception as e:
                message = f"{message} (格式化失败: {e})"
        
        # 总是传递实例ID，无论是否使用C扩展
        if not _has_c_extension:
            _warn(module, message, self._instance_id)
        else:
            # 对于C扩展，我们需要先设置当前实例的日志文件
            if self._log_file:
                _set_log_file(self._log_file)
            _warn(module, message)
    
    def error(self, message, *args, **kwargs):
        """记录错误级别日志"""
        module = kwargs.pop('module', None) or self._get_caller_module()
        
        # 格式化消息
        if args or kwargs:
            try:
                message = message.format(*args, **kwargs)
            except Exception as e:
                message = f"{message} (格式化失败: {e})"
        
        # 总是传递实例ID，无论是否使用C扩展
        if not _has_c_extension:
            _error(module, message, self._instance_id)
        else:
            # 对于C扩展，我们需要先设置当前实例的日志文件
            if self._log_file:
                _set_log_file(self._log_file)
            _error(module, message)
    
    def fatal(self, message, *args, **kwargs):
        """记录致命错误级别日志"""
        module = kwargs.pop('module', None) or self._get_caller_module()
        
        # 格式化消息
        if args or kwargs:
            try:
                message = message.format(*args, **kwargs)
            except Exception as e:
                message = f"{message} (格式化失败: {e})"
        
        # 总是传递实例ID，无论是否使用C扩展
        if not _has_c_extension:
            _fatal(module, message, self._instance_id)
        else:
            # 对于C扩展，我们需要先设置当前实例的日志文件
            if self._log_file:
                _set_log_file(self._log_file)
            _fatal(module, message)
    
    def warning(self, message, *args, **kwargs):
        """记录警告级别日志（别名）"""
        self.warn(message, *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        """记录致命错误级别日志（别名）"""
        self.fatal(message, *args, **kwargs)
    
    def set_level(self, level):
        """设置日志级别"""
        # 如果是枚举值，获取其字符串表示
        if hasattr(level, 'value'):
            level = level.value
        
        # 标准化级别名称
        if level == 'WARNING':
            level = 'WARN'
        elif level == 'CRITICAL':
            level = 'FATAL'
        
        # 验证日志级别的有效性
        valid_levels = ('DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL')
        if level not in valid_levels:
            raise ValueError(f"无效的日志级别: {level}, 有效值: {', '.join(valid_levels)}")
        
        self._current_level = level
        
        # 在纯Python模式下，设置实例级别的日志级别
        if not _has_c_extension:
            _set_instance_log_level(self._instance_id, level)
        else:
            _set_log_level(level)
    
    def set_file(self, file_path):
        """设置日志输出文件路径"""
        if file_path:
            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path:
                with Logger._dir_lock:
                    os.makedirs(dir_path, exist_ok=True)
            
            # 创建或清空文件
            try:
                with open(file_path, 'a'):
                    pass
            except Exception as e:
                print(f"[ERROR] 无法创建日志文件 {file_path}: {e}")
                return
        
        self._log_file = file_path
        
        # 在纯Python模式下，设置实例级别的日志文件
        if not _has_c_extension:
            # 先输出调试信息
            print(f"[DEBUG] 设置实例 {self._instance_id} 的日志文件为 {file_path}")
            result = _set_instance_log_file(self._instance_id, file_path)
            print(f"[DEBUG] 设置实例日志文件结果: {result}")
            
            if file_path:
                # 立即写入测试标记，验证文件是否可写
                try:
                    with open(file_path, 'a', encoding='utf-8') as f:
                        test_line = f"[SETUP] 实例 {self._instance_id} 设置日志文件成功\n"
                        f.write(test_line)
                        f.flush()
                        os.fsync(f.fileno())
                        print(f"[DEBUG] 成功写入测试标记到实例日志文件 {file_path}")
                except Exception as e:
                    print(f"[ERROR] 写入测试标记到实例日志文件 {file_path} 失败: {e}")
        else:
            _set_log_file(file_path or "")
    
    def set_rotation_size(self, size):
        """设置日志文件轮转大小"""
        _set_log_max_size(size)
    
    def get_level(self):
        """获取当前日志级别"""
        return self._current_level