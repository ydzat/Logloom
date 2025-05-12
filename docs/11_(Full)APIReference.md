# Logloom API 参考文档

本文档提供Logloom库所有公开API的完整参考，适用于将Logloom作为库集成到其他项目中的开发者。

---

## C API参考

### 初始化与配置

#### `int log_init(void)`
初始化日志系统。

**参数**：无

**返回值**：
- `0`：初始化成功
- 非零值：初始化失败

**示例**：
```c
if (log_init() != 0) {
    fprintf(stderr, "Failed to initialize logging system\n");
    return -1;
}
```

#### `int logloom_config_init(const char* config_path)`
从配置文件初始化Logloom系统。

**参数**：
- `config_path`：配置YAML文件的路径

**返回值**：
- `0`：初始化成功
- 非零值：初始化失败

**示例**：
```c
if (logloom_config_init("./config.yaml") != 0) {
    fprintf(stderr, "Failed to load configuration\n");
    return -1;
}
```

#### `void log_set_level(log_level_t level)`
设置全局日志级别。

**参数**：
- `level`：日志级别，可选值：
  - `LOG_LEVEL_DEBUG`
  - `LOG_LEVEL_INFO`
  - `LOG_LEVEL_WARN`
  - `LOG_LEVEL_ERROR`
  - `LOG_LEVEL_FATAL`

**返回值**：无

**示例**：
```c
log_set_level(LOG_LEVEL_INFO); // 只记录INFO及以上级别的日志
```

#### `void log_set_output_file(const char* path)`
设置日志输出文件。

**参数**：
- `path`：日志文件路径

**返回值**：无

**示例**：
```c
log_set_output_file("./application.log");
```

#### `void log_set_max_size(size_t size)`
设置日志文件最大大小，超过此大小将触发轮转。

**参数**：
- `size`：最大大小（字节）

**返回值**：无

**示例**：
```c
log_set_max_size(1024 * 1024); // 设置最大大小为1MB
```

### 日志记录

#### `void log_debug(const char* format, ...)`
记录调试级别的日志消息。

**参数**：
- `format`：格式化字符串，支持C标准库`printf`格式
- `...`：变参列表，根据格式化字符串提供值

**返回值**：无

**示例**：
```c
log_debug("初始化连接 %s 中", server_address);
```

#### `void log_info(const char* format, ...)`
记录信息级别的日志消息。

**参数**：
- `format`：格式化字符串
- `...`：变参列表

**返回值**：无

**示例**：
```c
log_info("用户 %s 登录成功", username);
```

#### `void log_warn(const char* format, ...)`
记录警告级别的日志消息。

**参数**：
- `format`：格式化字符串
- `...`：变参列表

**返回值**：无

**示例**：
```c
log_warn("尝试访问受限资源: %s", resource_name);
```

#### `void log_error(const char* format, ...)`
记录错误级别的日志消息。

**参数**：
- `format`：格式化字符串
- `...`：变参列表

**返回值**：无

**示例**：
```c
log_error("数据库连接失败: %s", db_error_message);
```

#### `void log_fatal(const char* format, ...)`
记录致命错误级别的日志消息。

**参数**：
- `format`：格式化字符串
- `...`：变参列表

**返回值**：无

**示例**：
```c
log_fatal("内存分配失败，程序无法继续执行");
```

### 国际化支持

#### `void lang_set_language(const char* lang_code)`
设置当前使用的语言。

**参数**：
- `lang_code`：语言代码，如"zh"或"en"

**返回值**：无

**示例**：
```c
lang_set_language("zh"); // 设置为中文
```

#### `const char* lang_get(const char* key)`
获取指定键的翻译文本。

**参数**：
- `key`：文本键，例如"system.start_message"

**返回值**：
- 找到的翻译文本
- 找不到时返回原始键

**示例**：
```c
const char* welcome_msg = lang_get(LOGLOOM_LANG_SYSTEM_WELCOME);
printf("%s\n", welcome_msg);
```

#### `char* lang_getf(const char* key, ...)`
获取带格式化参数的翻译文本。

**参数**：
- `key`：文本键
- `...`：格式化参数

**返回值**：
- 格式化后的翻译文本（需要调用者释放内存）
- NULL（如果执行失败）

**示例**：
```c
char* msg = lang_getf(LOGLOOM_LANG_SYSTEM_ERROR_MESSAGE, "连接超时");
printf("%s\n", msg);
free(msg); // 记得释放内存
```

### 插件系统

#### `int plugin_init(void)`
初始化插件系统。

**参数**：无

**返回值**：
- `0`：初始化成功
- 非零值：初始化失败

**示例**：
```c
if (plugin_init() != 0) {
    log_error("插件系统初始化失败");
}
```

#### `int plugin_load_directory(const char* path)`
加载指定目录中的所有插件。

**参数**：
- `path`：插件目录路径

**返回值**：
- 成功加载的插件数量
- 负值表示发生错误

**示例**：
```c
int loaded = plugin_load_directory("./plugins");
log_info("成功加载 %d 个插件", loaded);
```

### 资源清理

#### `void log_cleanup(void)`
清理日志系统资源。

**参数**：无

**返回值**：无

**示例**：
```c
log_cleanup(); // 在程序结束前调用
```

#### `void plugin_cleanup(void)`
清理插件系统资源。

**参数**：无

**返回值**：无

**示例**：
```c
plugin_cleanup(); // 在程序结束前调用
```

---

## Python API参考

### 初始化与配置

#### `initialize(config_path=None)`
初始化Logloom系统。

**参数**：
- `config_path`：配置YAML文件路径（可选）

**返回值**：
- `True`：初始化成功
- `False`：初始化失败

**示例**：
```python
from logloom import initialize

if not initialize("./config.yaml"):
    print("Failed to initialize Logloom")
    exit(1)
```

#### `cleanup()`
清理Logloom系统资源。

**参数**：无

**返回值**：无

**示例**：
```python
from logloom import cleanup

# 程序结束前
cleanup()
```

### 日志记录

#### `class LogLevel`
日志级别枚举。

**属性**：
- `DEBUG`
- `INFO`
- `WARNING` (别名 `WARN`)
- `ERROR`
- `CRITICAL` (别名 `FATAL`)

**示例**：
```python
from logloom import LogLevel

level = LogLevel.INFO
```

#### `class Logger`
记录器类，用于记录日志。

**方法**：

##### `__init__(name)`
创建一个新的记录器。

**参数**：
- `name`：记录器名称

**示例**：
```python
from logloom import Logger

logger = Logger("my_module")
```

##### `set_level(level)`
设置此记录器的日志级别。

**参数**：
- `level`：日志级别 (使用LogLevel枚举)

**返回值**：无

**示例**：
```python
logger.set_level(LogLevel.DEBUG)
```

##### `set_file(path)`
设置此记录器的输出文件。

**参数**：
- `path`：日志文件路径

**返回值**：无

**示例**：
```python
logger.set_file("./module.log")
```

##### `set_rotation_size(size)`
设置日志文件轮转大小。

**参数**：
- `size`：最大大小（字节）

**返回值**：无

**示例**：
```python
logger.set_rotation_size(1024 * 1024)  # 1MB
```

##### `debug(msg, *args, **kwargs)`
记录调试级别的消息。

**参数**：
- `msg`：消息模板
- `*args`：位置参数
- `**kwargs`：关键字参数

**返回值**：无

**示例**：
```python
logger.debug("初始化连接 {}", server_address)
logger.debug("用户 {user} 访问 {resource}", user="admin", resource="/api/data")
```

##### `info(msg, *args, **kwargs)`
记录信息级别的消息。

**参数**：
- `msg`：消息模板
- `*args`：位置参数
- `**kwargs`：关键字参数

**返回值**：无

**示例**：
```python
logger.info("处理请求 #{}", request_id)
```

##### `warning(msg, *args, **kwargs)` / `warn(msg, *args, **kwargs)`
记录警告级别的消息。

**参数**：
- `msg`：消息模板
- `*args`：位置参数
- `**kwargs`：关键字参数

**返回值**：无

**示例**：
```python
logger.warning("高CPU使用率: {}%", cpu_usage)
```

##### `error(msg, *args, **kwargs)`
记录错误级别的消息。

**参数**：
- `msg`：消息模板
- `*args`：位置参数
- `**kwargs`：关键字参数

**返回值**：无

**示例**：
```python
logger.error("请求处理失败: {}", error_message)
```

##### `critical(msg, *args, **kwargs)` / `fatal(msg, *args, **kwargs)`
记录严重错误级别的消息。

**参数**：
- `msg`：消息模板
- `*args`：位置参数
- `**kwargs`：关键字参数

**返回值**：无

**示例**：
```python
logger.critical("系统崩溃，无法恢复: {}", error_code)
```

### 国际化支持

#### `set_language(lang_code)`
设置当前使用的语言。

**参数**：
- `lang_code`：语言代码，如"zh"或"en"

**返回值**：
- `True`：设置成功
- `False`：设置失败

**示例**：
```python
from logloom import set_language

set_language("en")  # 设置为英文
```

#### `get_text(key, lang=None)`
获取指定键的翻译文本。

**参数**：
- `key`：文本键
- `lang`：可选的语言代码，如不指定则使用当前语言

**返回值**：
- 翻译后的文本
- 找不到时返回原始键

**示例**：
```python
from logloom import get_text

welcome = get_text("welcome")
chinese_text = get_text("welcome", "zh")
```

#### `format_text(key, *args, **kwargs)`
获取带格式化参数的翻译文本。

**参数**：
- `key`：文本键
- `*args`：位置参数
- `**kwargs`：关键字参数
  - 可使用`lang`关键字参数指定语言

**返回值**：
- 格式化后的翻译文本

**示例**：
```python
from logloom import format_text

error_msg = format_text("error.file_not_found", "/config.json")
welcome_msg = format_text("welcome.user", name="John", lang="en")
```

### 插件系统

#### `initialize_plugins(plugin_dir=None, config_path=None)`
初始化插件系统。

**参数**：
- `plugin_dir`：插件目录路径（可选）
- `config_path`：插件配置文件路径（可选）

**返回值**：
- `True`：初始化成功
- `False`：初始化失败

**示例**：
```python
from logloom import initialize_plugins

initialize_plugins(plugin_dir="./plugins", config_path="./plugin_config.json")
```

#### `load_plugins()`
加载已配置目录中的插件。

**参数**：无

**返回值**：
- 已加载的插件数量

**示例**：
```python
from logloom import load_plugins

count = load_plugins()
print(f"已加载 {count} 个插件")
```

#### `filter_log(log_entry)`
通过过滤器插件筛选日志条目。

**参数**：
- `log_entry`：日志条目对象

**返回值**：
- `True`：条目通过筛选
- `False`：条目被过滤掉

**示例**：
```python
from logloom import filter_log, LogEntry

entry = LogEntry(level=2, message="测试消息", module="test")
if filter_log(entry):
    # 处理通过过滤的日志
    pass
```

#### `sink_log(log_entry)`
将日志条目发送到输出插件。

**参数**：
- `log_entry`：日志条目对象

**返回值**：
- `True`：成功输出
- `False`：输出失败

**示例**：
```python
from logloom import sink_log, LogEntry

entry = LogEntry(level=1, message="信息消息", module="info")
sink_log(entry)
```

#### `unload_plugins()`
卸载所有插件。

**参数**：无

**返回值**：无

**示例**：
```python
from logloom import unload_plugins

unload_plugins()
```

#### `shutdown_plugins()`
关闭插件系统。

**参数**：无

**返回值**：无

**示例**：
```python
from logloom import shutdown_plugins

shutdown_plugins()
```

---

## API最佳实践

### 性能优化

1. **日志级别过滤**：在高性能环境中，应使用适当的日志级别，避免低级别日志（如DEBUG）影响系统性能
2. **文件轮转**：为长时间运行的应用设置合理的日志文件轮转大小
3. **格式化开销**：`lang_getf`和`format_text`会产生内存分配和格式化开销，请谨慎在关键性能路径上使用

### 多线程安全性

Logloom的所有API都是线程安全的，可以在多线程环境中使用。但插件加载/卸载操作推荐在单线程上下文中执行。

### 内存管理

1. **C API中的内存释放**：`lang_getf`返回的字符串需要由调用者使用`free()`释放
2. **Python API**：自动处理内存管理，无需手动释放

