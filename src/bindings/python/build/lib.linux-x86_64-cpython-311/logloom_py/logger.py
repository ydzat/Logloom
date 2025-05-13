"""
Logloom Logger 模块
==================

提供面向对象的日志接口
"""

import threading
import inspect
import os.path
import sys

# 尝试导入C扩展模块，如果导入失败，则使用纯Python实现
try:
    import logloom
    _has_c_extension = True
except ImportError:
    print("[WARNING] Failed to import logloom C extension module, falling back to pure Python implementation")
    _has_c_extension = False

# 全局锁用于保护日志操作
_global_log_lock = threading.RLock()

# 全局变量，跟踪当前活跃的日志文件路径
_active_log_file = None

# 全局变量，用于纯Python实现
_current_log_level = "INFO"  # 默认日志级别
_log_max_size = 1048576  # 默认日志文件大小限制(1MB)
_log_file_size = {}  # 跟踪日志文件大小

# 纯Python实现的日志函数
def _py_log(level, module, message):
    """纯Python实现的日志记录函数"""
    import time
    import os
    global _log_file_size, _log_max_size
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}][{level}][{module}] {message}\n"
    
    # 打印到控制台
    print(log_line, end='')
    
    # 如果有日志文件，写入文件
    if _active_log_file:
        # 检查是否需要轮转
        if _active_log_file in _log_file_size:
            current_size = _log_file_size[_active_log_file]
        else:
            # 如果文件存在，获取其大小
            if os.path.exists(_active_log_file):
                current_size = os.path.getsize(_active_log_file)
            else:
                current_size = 0
            _log_file_size[_active_log_file] = current_size
            
        # 检查是否需要轮转
        if current_size + len(log_line) > _log_max_size:
            # 需要轮转日志
            _rotate_log_file(_active_log_file)
            # 重置大小计数
            _log_file_size[_active_log_file] = 0
                
        try:
            with open(_active_log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
                # 更新文件大小
                _log_file_size[_active_log_file] += len(log_line)
        except Exception as e:
            print(f"[ERROR] 无法写入日志文件 {_active_log_file}: {e}")

def _rotate_log_file(file_path):
    """轮转日志文件"""
    import os
    import time
    
    if not file_path or not os.path.exists(file_path):
        return
        
    # 生成带时间戳的轮转文件名
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    rotated_name = f"{file_path}.{timestamp}"
    
    try:
        # 重命名当前日志文件
        os.rename(file_path, rotated_name)
        print(f"[INFO] 轮转日志文件: {file_path} -> {rotated_name}")
    except Exception as e:
        print(f"[ERROR] 轮转日志文件失败 {file_path}: {e}")

# Logger类定义
class Logger:
    """
    Logloom日志记录器，提供友好的Python API
    """
    
    # 保存所有创建的Logger实例
    _instances = []
    # 共享的日志文件目录锁
    _dir_lock = threading.Lock()
    
    def __init__(self, default_module=None):
        """
        创建Logger实例
        
        Parameters:
        -----------
        default_module : str, optional
            默认模块名，如果不提供，将自动从调用栈获取
        """
        self.default_module = default_module
        self._current_level = "INFO"  # 默认日志级别
        self._log_file = None  # 日志文件路径
        self._instance_lock = threading.RLock()  # 实例级别的锁
        
        # 将新实例添加到实例列表中
        with _global_log_lock:
            Logger._instances.append(self)
    
    def _get_caller_module(self):
        """
        从调用栈获取调用者的模块名
        """
        if self.default_module:
            return self.default_module
            
        # 获取调用栈
        stack = inspect.stack()
        # 第0层是当前函数，第1层是调用此函数的日志方法，第2层是用户代码
        if len(stack) >= 3:
            caller_frame = stack[2]
            module = inspect.getmodule(caller_frame[0])
            if module:
                return os.path.basename(module.__file__).split('.')[0]
        
        return "unknown"
    
    def debug(self, message, *args, **kwargs):
        """
        记录调试信息
        
        Parameters:
        -----------
        message : str
            日志消息，可以包含格式化占位符 {} 或 {name}
        *args
            位置格式化参数
        **kwargs
            关键字格式化参数，或者额外选项:
            - module: 模块名称，如果不提供则自动检测
        """
        module = kwargs.pop('module', None) or self._get_caller_module()
        
        # 如果有格式化参数，先进行格式化
        if args or kwargs:
            try:
                message = message.format(*args, **kwargs)
            except Exception as e:
                # 格式化失败，添加一个警告
                message = f"{message} (格式化失败: {e})"
        
        # 使用全局锁保护日志操作
        with _global_log_lock:
            if not self.log_to_file("DEBUG", module, message):
                # 不再直接调用logloom.debug
                _py_log("DEBUG", module, message)
    
    def info(self, message, *args, **kwargs):
        """
        记录普通信息
        
        Parameters:
        -----------
        message : str
            日志消息，可以包含格式化占位符 {} 或 {name}
        *args
            位置格式化参数
        **kwargs
            关键字格式化参数，或者额外选项:
            - module: 模块名称，如果不提供则自动检测
        """
        module = kwargs.pop('module', None) or self._get_caller_module()
        
        # 如果有格式化参数，先进行格式化
        if args or kwargs:
            try:
                message = message.format(*args, **kwargs)
            except Exception as e:
                # 格式化失败，添加一个警告
                message = f"{message} (格式化失败: {e})"
                
        # 使用全局锁保护日志操作
        with _global_log_lock:
            if not self.log_to_file("INFO", module, message):
                # 不再直接调用logloom.info
                _py_log("INFO", module, message)
    
    def warn(self, message, *args, **kwargs):
        """
        记录警告信息
        
        Parameters:
        -----------
        message : str
            日志消息，可以包含格式化占位符 {} 或 {name}
        *args
            位置格式化参数
        **kwargs
            关键字格式化参数，或者额外选项:
            - module: 模块名称，如果不提供则自动检测
        """
        module = kwargs.pop('module', None) or self._get_caller_module()
        
        # 如果有格式化参数，先进行格式化
        if args or kwargs:
            try:
                message = message.format(*args, **kwargs)
            except Exception as e:
                # 格式化失败，添加一个警告
                message = f"{message} (格式化失败: {e})"
                
        # 使用全局锁保护日志操作
        with _global_log_lock:
            if not self.log_to_file("WARN", module, message):
                # 不再直接调用logloom.warn
                _py_log("WARN", module, message)
    
    def error(self, message, *args, **kwargs):
        """
        记录错误信息
        
        Parameters:
        -----------
        message : str
            日志消息，可以包含格式化占位符 {} 或 {name}
        *args
            位置格式化参数
        **kwargs
            关键字格式化参数，或者额外选项:
            - module: 模块名称，如果不提供则自动检测
        """
        module = kwargs.pop('module', None) or self._get_caller_module()
        
        # 如果有格式化参数，先进行格式化
        if args or kwargs:
            try:
                message = message.format(*args, **kwargs)
            except Exception as e:
                # 格式化失败，添加一个警告
                message = f"{message} (格式化失败: {e})"
                
        # 使用全局锁保护日志操作
        with _global_log_lock:
            if not self.log_to_file("ERROR", module, message):
                # 不再直接调用logloom.error
                _py_log("ERROR", module, message)
    
    def fatal(self, message, *args, **kwargs):
        """
        记录致命错误信息
        
        Parameters:
        -----------
        message : str
            日志消息，可以包含格式化占位符 {} 或 {name}
        *args
            位置格式化参数
        **kwargs
            关键字格式化参数，或者额外选项:
            - module: 模块名称，如果不提供则自动检测
        """
        module = kwargs.pop('module', None) or self._get_caller_module()
        
        # 如果有格式化参数，先进行格式化
        if args or kwargs:
            try:
                message = message.format(*args, **kwargs)
            except Exception as e:
                # 格式化失败，添加一个警告
                message = f"{message} (格式化失败: {e})"
                
        # 使用全局锁保护日志操作
        with _global_log_lock:
            if not self.log_to_file("FATAL", module, message):
                # 不再直接调用logloom.fatal
                _py_log("FATAL", module, message)
    
    def set_level(self, level):
        """
        设置日志级别
        
        Parameters:
        -----------
        level : str or LogLevel
            日志级别，可以是 'DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'FATAL', 'CRITICAL' 或相应的枚举值
        
        Raises:
        -------
        ValueError
            如果日志级别无效
        """
        global _current_log_level
        
        # 如果是枚举值，获取其字符串表示
        if hasattr(level, 'value'):
            level = level.value
        
        # 处理别名
        if level == 'WARNING':
            level = 'WARN'
        elif level == 'CRITICAL':
            level = 'FATAL'
            
        # 验证日志级别的有效性
        valid_levels = ('DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL')
        if level not in valid_levels:
            raise ValueError(f"无效的日志级别: {level}, 有效值: {', '.join(valid_levels)}")
            
        self._current_level = level  # 保存当前级别以便于 get_level 使用
        _current_log_level = level   # 更新全局日志级别
        
        if _has_c_extension:
            try:
                logloom.set_log_level(level)
            except Exception as e:
                print(f"[WARNING] 设置日志级别失败: {e}")
        
    def set_file(self, file_path):
        """
        设置日志输出文件路径
        
        Parameters:
        -----------
        file_path : str
            日志文件的路径
        
        Returns:
        --------
        bool
            操作是否成功
        """
        global _active_log_file
        
        # 如果已经设置了相同的文件路径，不需要重复设置
        if self._log_file == file_path:
            return True
            
        # 使用实例锁保护更改
        with self._instance_lock:
            import os
            
            # 提前检查目录是否存在，如果不存在则创建
            if file_path:
                log_dir = os.path.dirname(file_path)
                if log_dir:
                    with Logger._dir_lock:
                        try:
                            if not os.path.exists(log_dir):
                                os.makedirs(log_dir, exist_ok=True)
                        except (OSError, IOError) as e:
                            print(f"[WARNING] 设置日志文件失败 - 无法创建目录 {log_dir}: {e}")
                            return False
            
            # 保存新的文件路径
            self._log_file = file_path
            
            # 在全局锁保护下更新日志文件路径
            with _global_log_lock:
                # 更新当前活动的日志文件为这个实例的文件
                _active_log_file = file_path
                
                if _has_c_extension:
                    try:
                        logloom.set_log_file(file_path or "")
                    except Exception as e:
                        print(f"[ERROR] 设置日志文件失败: {e}")
                        # 即使C扩展调用失败，我们仍然使用纯Python实现
                
                return True
        
    def set_rotation_size(self, size):
        """
        设置日志文件轮转大小
        
        Parameters:
        -----------
        size : int
            日志文件大小上限（字节）
        """
        global _log_max_size
        _log_max_size = size
        
        if _has_c_extension:
            try:
                logloom.set_log_max_size(size)
            except Exception as e:
                print(f"[WARNING] 设置日志文件轮转大小失败: {e}")
                
    def warning(self, message, *args, **kwargs):
        """
        记录警告信息（别名，与 warn 相同）
        
        Parameters:
        -----------
        message : str
            日志消息，可以包含格式化占位符 {} 或 {name}
        *args
            位置格式化参数
        **kwargs
            关键字格式化参数，或者额外选项:
            - module: 模块名称，如果不提供则自动检测
        """
        self.warn(message, *args, **kwargs)
        
    def critical(self, message, *args, **kwargs):
        """
        记录严重错误信息（别名，与 fatal 相同）
        
        Parameters:
        -----------
        message : str
            日志消息
        *args
            位置格式化参数
        **kwargs
            关键字格式化参数，或者额外选项:
            - module: 模块名称，如果不提供则自动检测
        """
        self.fatal(message, *args, **kwargs)
        
    def log_to_file(self, level, module, message):
        """
        直接将消息写入此Logger的日志文件
        
        Parameters:
        -----------
        level : str
            日志级别
        module : str
            模块名称
        message : str
            日志消息
        """
        # 如果没有设置日志文件，使用默认日志行为
        if not self._log_file:
            return False
            
        import os
        
        # 使用类的目录锁保护目录创建操作
        with Logger._dir_lock:
            # 创建日志文件目录（如果不存在）
            log_dir = os.path.dirname(self._log_file)
            if log_dir:
                try:
                    if not os.path.exists(log_dir):
                        os.makedirs(log_dir, exist_ok=True)
                except (OSError, IOError) as e:
                    # 如果无法创建目录，记录错误但继续执行
                    print(f"[WARNING] 无法创建日志目录 {log_dir}: {e}")
                    
                # 确保目录存在后，检查是否可以写入
                if not os.path.exists(log_dir):
                    print(f"[WARNING] 日志目录 {log_dir} 不存在且无法创建")
                    return False
                if not os.access(log_dir, os.W_OK):
                    print(f"[WARNING] 日志目录 {log_dir} 没有写入权限")
                    return False
            
        # 使用实例锁保护日志文件操作
        with self._instance_lock:
            # 全局跟踪当前活跃的日志文件路径
            global _active_log_file
            prev_log_file = _active_log_file
            _active_log_file = self._log_file
            
            # 检查日志级别是否需要记录
            # DEBUG < INFO < WARN < ERROR < FATAL
            level_order = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3, "FATAL": 4}
            if level_order.get(level, 0) < level_order.get(_current_log_level, 1):
                # 如果当前日志级别低于全局设置，则忽略此日志
                return True
            
            # 使用全局锁保护日志操作
            with _global_log_lock:
                try:
                    if _has_c_extension:
                        # 设置当前的日志文件为此Logger实例的文件
                        try:
                            logloom.set_log_file(self._log_file)
                        except Exception as e:
                            print(f"[ERROR] 设置日志文件失败: {e}")
                            # 使用Python实现继续
                        
                        try:
                            # 根据级别调用相应的日志函数
                            if level == "DEBUG":
                                logloom.debug(module, message)
                            elif level == "INFO":
                                logloom.info(module, message)
                            elif level == "WARN" or level == "WARNING":
                                logloom.warn(module, message)
                            elif level == "ERROR":
                                logloom.error(module, message)
                            elif level == "FATAL" or level == "CRITICAL":
                                logloom.fatal(module, message)
                        except Exception:
                            # 如果C扩展调用失败，回退到纯Python实现
                            _py_log(level, module, message)
                    else:
                        # 纯Python实现
                        _py_log(level, module, message)
                        
                finally:
                    # 恢复之前的日志文件路径
                    _active_log_file = prev_log_file
                    if _has_c_extension:
                        try:
                            logloom.set_log_file(prev_log_file or "")
                        except Exception:
                            pass  # 忽略错误
        
        return True

    # 添加将WARN转换为WARNING的辅助方法
    def _convert_log_level(self, level):
        """
        转换日志级别为测试期望的格式
        这是为了适配测试用例期望的格式，在实际日志中WARN会显示为WARNING
        """
        if level == "WARN":
            return "WARNING"
        elif level == "FATAL":
            return "CRITICAL"
        return level
    
    def get_level(self):
        """
        获取当前日志级别
        
        Returns:
        --------
        str
            当前日志级别
        """
        return self._current_level