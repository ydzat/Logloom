"""
Logloom Logger 模块
==================

提供面向对象的日志接口
"""

import logloom
import inspect
import os.path
import threading

# 全局锁用于保护日志操作
_global_log_lock = threading.RLock()

# 全局变量，跟踪当前活跃的日志文件路径
_active_log_file = None

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
                logloom.debug(module, message)
    
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
                logloom.info(module, message)
    
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
                logloom.warn(module, message)
    
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
                logloom.error(module, message)
    
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
                logloom.fatal(module, message)
    
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
        # 如果是枚举值，获取其字符串表示
        if hasattr(level, 'value'):
            level = level.value
        
        # 处理别名
        if level == 'WARNING':
            level = 'WARN'
        elif level == 'CRITICAL':
            level = 'FATAL'
            
        self._current_level = level  # 保存当前级别以便于 get_level 使用
        logloom.set_log_level(level)
        
    def get_level(self):
        """
        获取当前日志级别
        
        Returns:
        --------
        str
            当前日志级别
        """
        return self._current_level
        
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
                try:
                    logloom.set_log_file(file_path or "")
                    return True
                except Exception as e:
                    print(f"[ERROR] 设置日志文件失败: {e}")
                    return False
        
    def set_rotation_size(self, size):
        """
        设置日志文件轮转大小
        
        Parameters:
        -----------
        size : int
            日志文件大小上限（字节）
        """
        logloom.set_log_max_size(size)
        
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
            
        import logloom
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
            
            # 使用全局锁保护C函数的调用，防止并发问题
            with _global_log_lock:
                # 设置当前的日志文件为此Logger实例的文件
                logloom.set_log_file(self._log_file)
                
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
                finally:
                    # 恢复之前的日志文件路径
                    if prev_log_file:
                        _active_log_file = prev_log_file
                        logloom.set_log_file(prev_log_file)
        
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