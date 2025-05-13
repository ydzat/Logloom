# Logloom Python API 完整参考文档

本文档提供 Logloom Python 绑定的详细 API 参考，包括所有公开函数、类、配置选项和使用示例。本文档适合想要在 Python 项目中集成 Logloom 的开发者。

---

## 目录

- [初始化与配置](#初始化与配置)
- [日志记录](#日志记录)
- [国际化支持](#国际化支持)
- [异常处理](#异常处理)
- [配置格式参考](#配置格式参考)
- [插件系统](#插件系统)
- [特殊功能](#特殊功能)
- [最佳实践](#最佳实践)
- [常见问题解答](#常见问题解答)

---

## 初始化与配置

### `initialize(config_path=None)`

初始化 Logloom 系统，可选择通过配置文件或配置字典进行配置。

**参数：**
- `config_path` (str 或 dict, 可选)：配置文件路径或配置字典
  - 如果是字符串，作为配置文件路径处理
  - 如果是字典，直接作为配置使用
  - 如果不提供，尝试使用环境变量 `LOGLOOM_CONFIG` 指定的配置文件

**返回值：**
- `True`：初始化成功
- `False`：初始化失败

**示例：**

使用配置文件初始化：
```python
import logloom_py as ll

# 通过配置文件初始化
if not ll.initialize("./config.yaml"):
    print("初始化失败")
    exit(1)
```

使用字典初始化：
```python
import logloom_py as ll

# 通过字典配置初始化
config_dict = {
    "logloom": {
        "language": "zh",
        "log": {
            "level": "DEBUG",
            "file": "app.log",
            "max_size": 1048576,  # 1MB
            "console": True
        }
    }
}

ll.initialize(config_dict)
```

### `cleanup()`

清理 Logloom 系统资源，应在程序退出前调用。

**参数：** 无

**返回值：**
- `True`：清理成功
- `False`：清理失败

**示例：**
```python
import logloom_py as ll

# 初始化和使用...

# 程序退出前清理资源
ll.cleanup()
```

### `set_log_level(level)`

设置全局日志级别，控制记录哪些级别的日志。

**参数：**
- `level` (LogLevel 或 str)：日志级别
  - 如果是 LogLevel 枚举值，直接使用
  - 如果是字符串，可以是 "DEBUG"、"INFO"、"WARN"、"ERROR" 或 "FATAL"

**返回值：**
- `True`：设置成功
- `False`：设置失败

**抛出异常：**
- `ValueError`：如果提供了无效的日志级别

**示例：**
```python
import logloom_py as ll
from logloom_py import LogLevel

# 使用枚举值设置
ll.set_log_level(LogLevel.DEBUG)

# 使用字符串设置
ll.set_log_level("INFO")
```

### `set_log_file(filepath)`

设置日志输出文件路径。

**参数：**
- `filepath` (str)：日志文件路径
  - 如果路径中包含不存在的目录，会自动创建

**返回值：**
- `True`：设置成功
- `False`：设置失败

**示例：**
```python
import logloom_py as ll

# 设置日志文件
ll.set_log_file("logs/app.log")
```

### `set_log_max_size(max_bytes)`

设置日志文件的最大大小，超出后将进行轮转。

**参数：**
- `max_bytes` (int)：最大文件大小（字节）

**返回值：**
- `True`：设置成功
- `False`：设置失败

**示例：**
```python
import logloom_py as ll

# 设置最大 2MB
ll.set_log_max_size(2 * 1024 * 1024)
```

### `set_output_console(enabled)`

设置是否输出日志到控制台。

**参数：**
- `enabled` (bool)：是否启用控制台输出
  - `True`：启用控制台输出
  - `False`：禁用控制台输出

**返回值：**
- `True`：设置成功
- `False`：设置失败

**示例：**
```python
import logloom_py as ll

# 禁用控制台输出
ll.set_output_console(False)
```

## 日志记录

### 类 `LogLevel`

日志级别枚举，用于指定日志记录的严重程度。

**属性：**
- `DEBUG`：调试信息，最详细级别
- `INFO`：常规信息
- `WARN`：警告信息（有潜在问题）
- `ERROR`：错误信息（操作失败）
- `FATAL`：致命错误（程序可能无法继续）

**示例：**
```python
import logloom_py as ll
from logloom_py import LogLevel

# 设置日志级别为 DEBUG
ll.set_log_level(LogLevel.DEBUG)

# 可以比较日志级别
current_level = ll.logger.get_level()
if current_level == "DEBUG":
    print("当前是调试级别")
```

### 类 `Logger`

记录器类，用于记录日志消息。

#### `__init__(name=None)`

创建一个新的日志记录器实例。

**参数：**
- `name` (str, 可选)：记录器名称
  - 如果不提供，将尝试自动检测调用者的模块名称

**示例：**
```python
import logloom_py as ll

# 创建命名记录器
auth_logger = ll.Logger("auth")
api_logger = ll.Logger("api")

# 使用默认名称（自动检测）
logger = ll.Logger()
```

#### `debug(message, *args, **kwargs)`

记录调试级别的日志消息。

**参数：**
- `message` (str)：日志消息模板
- `*args`：用于格式化消息的位置参数
- `**kwargs`：用于格式化消息的关键字参数
  - 可以使用特殊参数 `module` 覆盖模块名称

**返回值：** 无

**示例：**
```python
# 使用位置参数
logger.debug("处理请求 #{0} 从 {1}", req_id, client_ip)

# 使用关键字参数
logger.debug("用户 {username} 尝试访问 {resource}", username="admin", resource="/api/data")

# 覆盖模块名称
logger.debug("特殊情况", module="security")
```

#### `info(message, *args, **kwargs)`

记录信息级别的日志消息。

**参数：**
- `message` (str)：日志消息模板
- `*args`：用于格式化消息的位置参数
- `**kwargs`：用于格式化消息的关键字参数

**返回值：** 无

**示例：**
```python
# 简单消息
logger.info("应用程序已启动")

# 带参数的消息
logger.info("已处理 {} 个请求，耗时 {:.2f} 秒", count, duration)
```

#### `warn(message, *args, **kwargs)`

记录警告级别的日志消息。

**参数：**
- `message` (str)：日志消息模板
- `*args`：用于格式化消息的位置参数
- `**kwargs`：用于格式化消息的关键字参数

**返回值：** 无

**示例：**
```python
logger.warn("资源使用量过高：CPU {0}%, 内存 {1}%", cpu_usage, mem_usage)
```

#### `warning(message, *args, **kwargs)`

`warn` 的别名，提供与 Python 标准库日志兼容的接口。

#### `error(message, *args, **kwargs)`

记录错误级别的日志消息。

**参数：**
- `message` (str)：日志消息模板
- `*args`：用于格式化消息的位置参数
- `**kwargs`：用于格式化消息的关键字参数

**返回值：** 无

**示例：**
```python
try:
    # 某些操作
    pass
except Exception as e:
    logger.error("操作失败：{}", str(e))
    # 或者使用异常对象
    logger.error("操作失败", exc_info=e)
```

#### `fatal(message, *args, **kwargs)`

记录致命错误级别的日志消息。

**参数：**
- `message` (str)：日志消息模板
- `*args`：用于格式化消息的位置参数
- `**kwargs`：用于格式化消息的关键字参数

**返回值：** 无

**示例：**
```python
logger.fatal("系统无法恢复，即将关闭")
```

#### `critical(message, *args, **kwargs)`

`fatal` 的别名，提供与 Python 标准库日志兼容的接口。

#### `set_level(level)`

设置此记录器实例的日志级别。

**参数：**
- `level` (LogLevel 或 str)：日志级别

**返回值：** 无

**示例：**
```python
# 只对当前记录器设置级别
auth_logger.set_level(ll.LogLevel.WARN)
```

#### `set_file(file_path)`

设置此记录器实例的输出文件。

**参数：**
- `file_path` (str)：日志文件路径

**返回值：** 无

**示例：**
```python
# 分别记录到不同文件
auth_logger.set_file("logs/auth.log")
api_logger.set_file("logs/api.log")
```

#### `set_rotation_size(size)`

设置此记录器的日志文件轮转大小。

**参数：**
- `size` (int)：最大文件大小（字节）

**返回值：** 无

**示例：**
```python
# 设置 5MB 的轮转大小
logger.set_rotation_size(5 * 1024 * 1024)
```

#### `get_level()`

获取此记录器当前的日志级别。

**参数：** 无

**返回值：**
- (str)：当前日志级别，例如 "DEBUG"、"INFO" 等

**示例：**
```python
current = logger.get_level()
print(f"当前日志级别：{current}")
```

### 全局日志记录

Logloom 提供了全局级别的直接日志记录函数。

#### `debug(module, message)`

记录调试级别的日志消息。

**参数：**
- `module` (str)：模块名称
- `message` (str)：日志消息

**返回值：** 无

**示例：**
```python
import logloom_py as ll

ll.debug("main", "初始化连接")
```

#### `info(module, message)`

记录信息级别的日志消息。

**参数：**
- `module` (str)：模块名称
- `message` (str)：日志消息

**返回值：** 无

#### `warn(module, message)`

记录警告级别的日志消息。

**参数：**
- `module` (str)：模块名称
- `message` (str)：日志消息

**返回值：** 无

#### `error(module, message)`

记录错误级别的日志消息。

**参数：**
- `module` (str)：模块名称
- `message` (str)：日志消息

**返回值：** 无

#### `fatal(module, message)`

记录致命错误级别的日志消息。

**参数：**
- `module` (str)：模块名称
- `message` (str)：日志消息

**返回值：** 无

## 国际化支持

### `set_language(lang_code)`

设置当前使用的语言代码。

**参数：**
- `lang_code` (str)：语言代码，如 "zh" 或 "en"

**返回值：**
- `True`：设置成功
- `False`：设置失败（例如提供了不支持的语言代码）

**示例：**
```python
import logloom_py as ll

# 设置中文
ll.set_language("zh")

# 设置英文
ll.set_language("en")
```

### `get_current_language()`

获取当前使用的语言代码。

**参数：** 无

**返回值：**
- (str)：当前语言代码，如 "zh" 或 "en"

**示例：**
```python
import logloom_py as ll

current_lang = ll.get_current_language()
print(f"当前使用的语言：{current_lang}")
```

### `get_text(key, *args)`

获取指定键的翻译文本，可选地应用位置参数。

**参数：**
- `key` (str)：文本键名
- `*args`：可选的格式化参数

**返回值：**
- (str)：翻译后的文本
  - 如果找不到翻译，返回键名本身

**示例：**
```python
import logloom_py as ll

# 简单文本获取
welcome_text = ll.get_text("system.welcome")

# 带参数的文本获取
error_msg = ll.get_text("error.file_not_found", "/config.json")
```

### `format_text(key, *args, **kwargs)`

获取指定键的翻译文本并应用格式化，支持位置参数和关键字参数。

**参数：**
- `key` (str)：文本键名
- `*args`：位置格式化参数
- `**kwargs`：关键字格式化参数

**返回值：**
- (str)：格式化后的翻译文本
  - 如果找不到翻译，返回键名本身

**示例：**
```python
import logloom_py as ll

# 使用位置参数
msg1 = ll.format_text("greeting", "张三")  # "你好，张三！"

# 使用关键字参数
msg2 = ll.format_text("error.invalid_value", value="123", expected="数字")
# "无效的值: 123，期望: 数字"
```

## 插件系统

Logloom提供了强大的插件系统，支持动态加载和配置插件。

### `initialize_plugins(plugin_dir=None, config_path=None)`

初始化插件系统。

**参数：**
- `plugin_dir` (str, 可选)：插件目录路径
- `config_path` (str, 可选)：插件配置文件路径

**返回值：**
- `True`：初始化成功
- `False`：初始化失败

**示例：**
```python
import logloom_py as ll

# 初始化插件系统
ll.initialize_plugins(plugin_dir="./plugins", config_path="./plugin_config.json")
```

### `load_plugins()`

加载所有可用插件。

**参数：** 无

**返回值：**
- (int)：成功加载的插件数量

**示例：**
```python
import logloom_py as ll

# 初始化插件系统
ll.initialize_plugins("./plugins")

# 加载所有插件
num_loaded = ll.load_plugins()
print(f"已加载 {num_loaded} 个插件")
```

### `register_plugin(plugin_class)`

注册自定义Python插件类。

**参数：**
- `plugin_class` (class)：符合插件接口的Python类

**返回值：**
- `True`：注册成功
- `False`：注册失败

**示例：**
```python
import logloom_py as ll

# 定义自定义插件类
class MyLogFilter:
    def __init__(self, config=None):
        self.config = config or {}
    
    def process(self, log_entry):
        # 过滤或修改日志条目
        if "password" in log_entry["message"]:
            log_entry["message"] = log_entry["message"].replace("password=123456", "password=******")
        return log_entry

# 注册插件
ll.register_plugin(MyLogFilter)
```

### `get_loaded_plugins()`

获取已加载的插件列表。

**参数：** 无

**返回值：**
- (list)：已加载插件信息的列表

**示例：**
```python
import logloom_py as ll

# 获取已加载插件
plugins = ll.get_loaded_plugins()
for plugin in plugins:
    print(f"插件名: {plugin['name']}, 类型: {plugin['type']}")
```

### `enable_plugin(plugin_name, enabled=True)`

启用或禁用特定插件。

**参数：**
- `plugin_name` (str)：插件名称
- `enabled` (bool, 可选)：是否启用，默认为True

**返回值：**
- `True`：操作成功
- `False`：操作失败

**示例：**
```python
import logloom_py as ll

# 禁用特定插件
ll.enable_plugin("sensitive_filter", False)

# 重新启用
ll.enable_plugin("sensitive_filter", True)
```

## 异常处理

Logloom 库中的异常处理策略。

### 抛出的异常

以下是 Logloom Python 绑定可能抛出的异常：

1. **`ValueError`**：当提供的参数值无效时抛出
   - 例如：无效的日志级别字符串
   - 例如：无效的配置值

2. **`IOError`/`OSError`**：当文件操作失败时抛出
   - 例如：无法创建或写入日志文件
   - 例如：无法读取配置文件

3. **`ImportError`**：当缺少必要的依赖时抛出
   - 例如：尝试使用字典配置但缺少 PyYAML 库

4. **`RuntimeError`**：当系统状态无效或操作不允许时抛出
   - 例如：在初始化前调用功能

### 错误恢复策略

Logloom 采用以下错误恢复策略：

1. **降级处理**：当 C 扩展模块不可用时，自动使用纯 Python 实现
2. **默认值回退**：当配置错误时，使用合理的默认值
3. **日志文件处理**：当无法写入日志文件时，输出警告并继续执行

## 配置格式参考

### YAML 配置文件格式

Logloom 配置文件采用 YAML 格式，支持以下配置选项：

```yaml
logloom:
  # 语言设置
  language: "zh"  # 支持 "zh" 或 "en"
  
  # 日志配置
  log:
    # 日志级别: DEBUG, INFO, WARN, ERROR, FATAL
    level: "INFO"
    
    # 日志文件路径
    file: "logs/app.log"
    
    # 日志文件最大大小（字节）
    max_size: 1048576  # 1MB
    
    # 是否输出到控制台
    console: true
    
    # 格式配置
    format: "[{timestamp}][{level}][{module}] {message}"
    
    # 时间戳格式
    timestamp_format: "%Y-%m-%d %H:%M:%S"
  
  # 国际化配置
  i18n:
    # 翻译文件目录
    lang_dir: "locales"
    
    # 默认语言
    default_language: "en"
  
  # 插件系统配置
  plugins:
    # 插件目录
    dir: "plugins"
    
    # 启用的插件列表
    enabled:
      - "filter_sensitive"
      - "sink_database"
```

### 字典配置格式

使用字典初始化时，结构与 YAML 文件相同：

```python
config = {
    "logloom": {
        "language": "zh",
        "log": {
            "level": "INFO",
            "file": "logs/app.log",
            "max_size": 1048576,
            "console": True
        },
        "plugins": {
            "dir": "plugins",
            "enabled": ["filter_sensitive", "sink_database"]
        }
    }
}
```

## 特殊功能

### 线程安全性

Logloom 的所有 API 都是线程安全的，可以在多线程环境中使用，不需要额外的同步操作。

### 日志文件轮转

当日志文件大小超过设置的最大大小时，将自动进行轮转：
1. 当前日志文件将被重命名为 `{原文件名}.1`
2. 如果已存在 `.1` 文件，则递增为 `.2`，以此类推
3. 创建新的空白日志文件继续写入

### 多语言支持

Logloom 支持在运行时动态切换语言，支持以下语言：

- `en`: 英文
- `zh`: 中文

## 最佳实践

### 合理使用日志级别

- **DEBUG**：详细的调试信息，仅在开发和故障排查时启用
- **INFO**：常规操作信息，表示正常流程
- **WARN**：潜在问题的警告，不影响程序继续运行
- **ERROR**：操作失败，但程序可以继续
- **FATAL**：严重错误，程序可能无法继续

### 日志文件管理

1. **目录结构**：将日志文件放在专门的 `logs` 目录
2. **命名约定**：使用有意义的名称，如 `app.log`、`auth.log` 等
3. **轮转策略**：在长期运行的应用中设置合理的最大大小

### 国际化最佳实践

1. **使用键名而非硬编码文本**：`get_text("welcome.user")` 而非直接使用字符串
2. **键名命名约定**：使用点号分隔的层次结构，如 `category.subcategory.name`
3. **参数顺序**：在不同语言之间保持参数顺序一致

### 插件开发最佳实践

1. **保持简单**：每个插件只做一件事，并做好它
2. **错误处理**：插件应妥善处理异常，不应导致主程序崩溃
3. **配置验证**：在插件初始化时验证配置，提供有用的错误信息
4. **性能考虑**：插件的process方法会被频繁调用，应尽量高效

### 性能优化

1. **日志级别过滤**：在性能敏感的环境中使用更高的日志级别（INFO 或更高）
2. **避免频繁调用 `get_text`**：对于重复使用的文本，获取一次并重用
3. **使用 Logger 实例**：优先使用 `Logger` 实例而非全局函数，减少上下文检测开销
4. **适当配置插件**：只启用必要的插件，减少日志处理开销

## 常见问题解答

### 使用场景问题

#### 问：如何在多个模块中使用不同的日志配置？
答：为每个模块创建单独的 `Logger` 实例，并单独配置级别和输出文件。

#### 问：如何同时输出到控制台和文件？
答：使用 `set_log_file` 设置文件输出，确保 `set_output_console(True)` 启用控制台输出。

#### 问：如何实现自定义日志处理逻辑？
答：创建自定义插件类并使用 `register_plugin` 注册，插件可以过滤、修改或重定向日志。

### 技术问题

#### 问：为什么使用 `logloom_py.format_text` 而非 Python 的 `format` 函数？
答：`format_text` 自动处理语言切换和翻译查找，更适合国际化应用。

#### 问：如何添加自定义语言支持？
答：在 `locales` 目录中添加新的语言 YAML 文件，如 `ja.yaml` 用于日语支持。

#### 问：Logloom 的 Python 绑定是否依赖 C 扩展？
答：是的，Logloom 的 Python 绑定通过 CPython 扩展实现，但提供了纯 Python 备选实现，如果 C 扩展不可用或安装失败，会自动降级使用纯 Python 实现。

#### 问：如何调试插件加载问题？
答：设置环境变量 `LOGLOOM_DEBUG=1` 可以启用插件加载的详细日志输出。

