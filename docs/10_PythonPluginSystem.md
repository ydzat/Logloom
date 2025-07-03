# Logloom Python 插件系统

本文档介绍了 Logloom 的 Python 插件系统，该系统与 C 插件系统功能等效，允许开发者通过 Python 编写处理日志的插件。

## 概述

Logloom Python 插件系统提供了与 C 插件系统相同的功能，但通过 Python 接口实现，使得开发者可以更便捷地编写日志处理插件。该系统支持：

- 过滤器插件 (FilterPlugin)：过滤和选择日志条目
- 输出插件 (SinkPlugin)：将日志输出到不同目标
- AI 分析插件 (AIPlugin)：通过人工智能分析日志
- 语言资源插件 (LangPlugin)：提供额外的语言资源

## 插件开发指南

### 1. 插件类型

Logloom Python 插件系统定义了四种基本插件类型，对应 C 插件系统中的类型：

- `FilterPlugin`：过滤器插件，用于过滤日志条目
- `SinkPlugin`：输出插件，用于将日志输出到不同目标
- `AIPlugin`：AI 分析插件，用于分析和处理日志
- `LangPlugin`：语言资源插件，用于提供额外的本地化资源

### 2. 编写插件

要创建一个 Logloom Python 插件，你需要继承其中一个基本插件类并实现三个必要的方法：

```python
from logloom.plugin import FilterPlugin, PluginResult

class MyFilter(FilterPlugin):
    def __init__(self):
        super().__init__(
            name="my_filter",           # 插件名称
            version="1.0.0",            # 插件版本
            author="Your Name",         # 插件作者
            description="插件描述"       # 插件描述
        )
    
    def init(self, helpers):
        """初始化插件"""
        self._helpers = helpers
        # 从配置中读取值
        some_value = self.get_config_int("some_key", 0)
        return 0  # 返回 0 表示成功
    
    def process(self, log_entry):
        """处理日志条目"""
        # 插件处理逻辑
        if log_entry.level <= 1:  # 过滤 DEBUG 级别
            return PluginResult.SKIP
        return PluginResult.OK
    
    def shutdown(self):
        """关闭插件"""
        # 释放资源
        pass
```

### 3. 插件接口

所有插件必须实现以下三个方法：

- `init(helpers)`：初始化插件，接收辅助函数对象
- `process(log_entry)`：处理日志条目
- `shutdown()`：关闭插件，释放资源

### 4. 配置访问

插件可以通过辅助函数访问配置值：

- `self.get_config_int(key, default_value)`：获取整数配置
- `self.get_config_string(key, default_value)`：获取字符串配置
- `self.get_config_bool(key, default_value)`：获取布尔值配置
- `self.get_config_array(key)`：获取字符串数组配置

### 5. 日志条目结构

`LogEntry` 对象包含以下属性：

- `level`：日志级别（整数）
- `timestamp`：UNIX 时间戳
- `message`：日志消息
- `module`：模块名
- `file`：源文件名
- `line`：行号
- `context`：上下文信息（字典）

### 6. 返回值

处理函数应该返回以下值之一：

- `PluginResult.OK`：处理成功
- `PluginResult.ERROR`：处理失败
- `PluginResult.SKIP`：跳过处理
- `PluginResult.RETRY`：重试请求

## 使用 Python 插件系统

### 1. 初始化插件系统

```python
from logloom import initialize_plugins, load_plugins

# 初始化插件系统
initialize_plugins(plugin_dir="/path/to/plugins", config_path="/path/to/config.json")

# 加载插件
loaded_count = load_plugins()
print(f"已加载 {loaded_count} 个插件")
```

### 2. 处理日志

```python
from logloom import filter_log, sink_log, LogEntry

# 创建日志条目
log_entry = LogEntry(
    level=2,  # WARN
    timestamp=time.time(),
    message="这是一条警告日志",
    module="my_module",
    file="my_file.py",
    line=42,
    context={"warning": True}
)

# 使用过滤器插件过滤
if filter_log(log_entry):
    # 如果通过过滤，使用输出插件输出
    sink_log(log_entry)
```

### 3. 关闭插件系统

```python
from logloom import unload_plugins, shutdown_plugins

# 卸载所有插件
unload_plugins()

# 关闭插件系统
shutdown_plugins()
```

## 示例插件

### 示例 1：级别过滤器

```python
# level_filter.py
from logloom.plugin import FilterPlugin, PluginResult

class LevelFilterPlugin(FilterPlugin):
    def __init__(self):
        super().__init__(
            name="level_filter",
            version="1.0.0",
            author="Logloom Team",
            description="过滤低于指定级别的日志消息"
        )
        self._min_level = 0
    
    def init(self, helpers):
        self._helpers = helpers
        self._min_level = self.get_config_int("min_level", 0)
        return 0
    
    def process(self, log_entry):
        if log_entry.level < self._min_level:
            return PluginResult.SKIP
        return PluginResult.OK
    
    def shutdown(self):
        pass
```

### 示例 2：JSON 输出器

```python
# json_sink.py
import json
import os
from datetime import datetime
from logloom.plugin import SinkPlugin, PluginResult, PluginCapability

class JsonSinkPlugin(SinkPlugin):
    def __init__(self):
        super().__init__(
            name="json_sink",
            version="1.0.0",
            author="Logloom Team",
            capabilities=PluginCapability.JSON,
            description="将日志条目输出为 JSON 格式"
        )
        self._output_file = None
    
    def init(self, helpers):
        self._helpers = helpers
        file_path = self.get_config_string("file_path", "logs/output.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        try:
            self._output_file = open(file_path, "a", encoding="utf-8")
            return 0
        except Exception:
            return 1
    
    def process(self, log_entry):
        if not self._output_file:
            return PluginResult.ERROR
        
        log_record = {
            "timestamp": log_entry.timestamp,
            "datetime": datetime.fromtimestamp(log_entry.timestamp).isoformat(),
            "level": log_entry.level,
            "message": log_entry.message,
            "module": log_entry.module,
            "context": log_entry.context
        }
        
        try:
            json_line = json.dumps(log_record)
            self._output_file.write(json_line + "\n")
            self._output_file.flush()
            return PluginResult.OK
        except Exception:
            return PluginResult.ERROR
    
    def shutdown(self):
        if self._output_file:
            self._output_file.close()
```

## 配置插件

插件系统使用 JSON 文件进行配置：

```json
{
  "plugin_paths": [
    "./plugins",
    "~/.local/lib/logloom/plugins"
  ],
  "enabled_plugins": [
    "level_filter", 
    "json_sink"
  ],
  "plugin_order": [
    "level_filter",
    "json_sink"
  ],
  "plugin_configs": {
    "level_filter": {
      "min_level": 2
    },
    "json_sink": {
      "file_path": "logs/output.json"
    }
  }
}
```

## 与 C 插件系统的关系

Python 插件系统设计为与 C 插件系统功能等效，但通过 Python 接口实现。两个系统共享相同的概念：

- 插件类型（过滤器、输出、AI、语言）
- 生命周期函数（初始化、处理、关闭）
- 插件配置机制
- 日志条目结构

这种设计确保了开发者可以根据需要选择适合的语言实现插件，而不会影响系统的整体功能。

## 插件发现和加载机制

Python 插件系统会在指定的目录中搜索插件。它支持两种形式的插件：

1. 单个 Python 文件（`.py`）
2. 包含 `__init__.py` 的 Python 包目录

在加载过程中，系统会：

1. 从配置的目录中发现潜在的插件文件
2. 动态加载每个插件模块
3. 在模块中查找继承自 `Plugin` 基类的类
4. 实例化插件类并初始化
5. 将插件添加到系统的插件注册表中

插件可以通过配置文件中的 `enabled_plugins` 和 `disabled_plugins` 列表来控制启用状态。

## 线程安全

Python 插件系统使用线程锁来确保在多线程环境中的安全操作。这确保了在并发处理日志条目或加载/卸载插件时不会发生数据竞争。

## 测试适配器系统（Test Adapter System）

除了Python插件系统外，Logloom还提供了完整的测试适配器机制，用于在实际Logloom模块不可用时提供模拟实现。这对于以下场景特别有用：

1. 单元测试Python代码，无需依赖实际的Logloom库
2. 在没有Logloom核心库的环境中开发和测试应用程序
3. 模拟特定条件下的库行为

### 适配器工作原理

测试适配器（`test_adapter.py`）使用动态检测机制尝试加载实际的`logloom_py`模块，如果模块不可用，则提供完全模拟实现。关键特性包括：

```python
try:
    # 尝试导入实际的logloom_py模块
    import logloom_py
    # 使用实际模块的实现...
except ImportError:
    # 提供模拟实现
    print("[TEST][INFO] 未找到logloom_py模块，使用测试模拟实现")
    # 模拟实现代码...
```

### 日志记录

测试适配器提供了与实际Logloom库完全兼容的日志记录功能：

```python
# 使用测试适配器的Logger类
logger = Logger("my_module")
logger.set_level(LogLevel.DEBUG)
logger.set_file("my_logs.log")
logger.set_rotation_size(1024)  # 配置日志轮转大小（字节）

# 记录不同级别的日志
logger.debug("调试信息: {}", 123)
logger.info("信息消息")
logger.warning("警告信息: {}", "警告内容")
logger.error("错误: {}", "出错了")
logger.critical("严重错误: {code}", code=500)
```

### 字符串格式化

测试适配器实现了强大的字符串格式化功能，支持位置参数和关键字参数：

```python
def format_text(key, *args, **kwargs):
    """格式化文本，支持位置参数和关键字参数替换"""
    text = get_text(key, kwargs.pop('lang', None))
    try:
        # 先处理位置参数
        if args:
            try:
                text = text.format(*args)
            except Exception as e:
                print(f"[TEST][ERROR] 格式化位置参数失败: {e}")
            
        # 然后处理关键字参数
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception as e:
                print(f"[TEST][ERROR] 格式化关键字参数失败: {e}")
            
        return text
    except Exception as e:
        print(f"[TEST][ERROR] 格式化文本失败: {e}")
        return text
```

### 日志轮转功能

测试适配器还提供了完整的日志轮转功能，模拟实际系统的文件轮转行为：

```python
def _rotate_log(self):
    """执行日志文件轮转"""
    if not self._file or not os.path.exists(self._file):
        return
        
    try:
        # 构建轮转后的文件名 - 使用原始文件名作为前缀
        import time
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        
        # 确保轮转后的文件名与测试期望匹配：以原始文件名开头
        rotated_file = f"{self._file}.{timestamp}"
        
        # 重命名当前日志文件
        os.rename(self._file, rotated_file)
        print(f"[INFO][{self.name}] 日志文件已轮转: {self._file} -> {rotated_file}")
        
        # 创建新的空日志文件
        with open(self._file, 'w', encoding='utf-8') as f:
            f.write(f"# New log file created after rotation at {timestamp}\n")
            
        return rotated_file
    except Exception as e:
        print(f"[ERROR] 日志轮转失败: {e}")
        import traceback
        traceback.print_exc()
```

### 环境变量和配置

测试适配器支持通过环境变量和配置文件控制其行为：

```python
# 通过环境变量设置日志级别
LOG_LEVEL = os.environ.get("LOGLOOM_LOG_LEVEL", "INFO")

# 从配置文件加载设置
def initialize(config_path=None):
    """初始化Logloom系统"""
    print(f"[TEST][INFO] 初始化模拟Logloom系统，配置文件: {config_path}")
    
    if config_path:
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                # 处理配置...
        except Exception as e:
            print(f"[TEST][ERROR] 读取配置文件失败: {e}")
    
    return True
```

### 使用测试适配器进行单元测试

测试适配器设计用于支持单元测试，以下是一个测试示例：

```python
import unittest
from tests.python.test_adapter import Logger, LogLevel

class LoggingTest(unittest.TestCase):
    def setUp(self):
        self.logger = Logger("test_module")
        self.logger.set_file("test.log")
        
    def test_log_levels(self):
        self.logger.set_level(LogLevel.INFO)
        self.logger.debug("不应该被记录")
        self.logger.info("应该被记录")
        
        # 检查日志文件
        with open("test.log", 'r') as f:
            content = f.read()
            self.assertNotIn("不应该被记录", content)
            self.assertIn("应该被记录", content)
    
    def tearDown(self):
        import os
        if os.path.exists("test.log"):
            os.remove("test.log")
```

### 注意事项和最佳实践

1. **模块重定向**：测试适配器创建和注册`logloom`模块，使得测试代码可以直接`import logloom`

2. **错误处理**：当使用测试适配器时，错误和警告会带有`[TEST]`前缀，以区分实际系统消息

3. **配置限制**：测试适配器可能不支持所有实际Logloom系统的高级配置选项

4. **性能考量**：测试适配器优先考虑功能正确性而非性能，不适用于性能测试

5. **多线程安全**：测试适配器支持多线程环境，但可能不如实际系统稳定

测试适配器系统是Logloom Python生态系统中的重要组成部分，它使开发人员能够在各种环境中进行开发和测试，而无需依赖完整的Logloom库实现。