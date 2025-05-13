# 02_InternationalizationDesign.md

# Logloom 国际化模块详细设计文档

---

## 1. 简介（Purpose）
本模块为 Logloom 系统提供统一的多语言支持，确保日志与系统消息能够根据配置动态切换语言，同时兼容内核态与用户态环境。

---

## 2. 设计目标（Design Goals）
- 多语言资源维护简单（采用 YAML 源文件）
- 构建阶段自动生成 C 头文件供内核态使用
- 用户态直接加载 YAML 文件
- 支持格式化插值（如 "发生错误：%s"）
- 保持高性能（查询接口快速，支持静态编译）
- 标准化 Key 命名与访问接口

---

## 3. 语言资源格式（Language Resource Format）

### 3.1 源格式：YAML

- 每种语言单独一个 YAML 文件。
- 结构要求：
  - 一级分类表示模块（如 system、auth）
  - 二级键表示具体消息

- 示例（`locales/zh.yaml`）：
  ```yaml
  system:
    start_message: "程序启动"
    error_message: "发生错误：%s"
  auth:
    login_success: "登录成功"
    login_failed: "登录失败，请重试"
  ```

### 3.2 生成格式：静态数组 C 头文件

- 每种语言生成一个对应的 `.h` 文件（如 `lang_zh.h`, `lang_en.h`）
- 内容格式：
  - `typedef struct { const char* key; const char* value; } lang_entry_t;`
  - 静态数组 + NULL 结束
  - 自动生成宏定义，统一前缀为 `LOGLOOM_LANG_`

- 示例（`lang_zh.h`）：

```c
typedef struct {
    const char* key;
    const char* value;
} lang_entry_t;

static const lang_entry_t zh_lang_table[] = {
    {"system.start_message", "程序启动"},
    {"system.error_message", "发生错误：%s"},
    {"auth.login_success", "登录成功"},
    {"auth.login_failed", "登录失败，请重试"},
    {NULL, NULL}
};

// 自动生成宏
#define LOGLOOM_LANG_SYSTEM_START_MESSAGE "system.start_message"
#define LOGLOOM_LANG_SYSTEM_ERROR_MESSAGE "system.error_message"
#define LOGLOOM_LANG_AUTH_LOGIN_SUCCESS "auth.login_success"
#define LOGLOOM_LANG_AUTH_LOGIN_FAILED "auth.login_failed"
```

---

## 4. 核心接口（APIs）

| 接口 | 功能描述 |
|:----|:----|
| `const char* lang_get(const char* key);` | 获取指定 key 的文本 |
| `char* lang_getf(const char* key, ...);` | 获取带格式化插值的文本，动态分配内存 |
| `void lang_set_language(const char* lang_code);` | 切换当前语言环境 |

---

## 5. 查询流程（Lookup Flow）

1. 查找当前语言的静态表。
2. 线性搜索或哈希加速（后续可扩展）。
3. 找不到时返回默认提示或 NULL。
4. `lang_getf` 在内部调用 `lang_get` 后格式化字符串。

---

## 6. 语言切换与加载机制（Language Switching and Loading）

### 6.1 加载策略（Loading Strategy）

- **按需加载**：系统启动时只加载默认语言表。
- **切换语言时**：
  - 释放当前语言表占用资源（如果有需要）
  - 加载新的目标语言表
- **默认语言配置**：
  - 在初始化配置中指定，如 `zh`、`en`
  - 若切换失败（目标语言表不存在或加载失败），系统应回退到默认语言，并打印警告日志。

### 6.2 加载流程（Loading Flow）

```plaintext
启动阶段：
    - 从配置读取默认语言代码
    - 加载对应语言的静态表
    - 设置当前语言上下文指针

运行阶段：
    - 调用 lang_set_language(new_lang_code)
        - 检查当前语言是否已是目标语言
        - 如果不同：
            - 释放旧语言资源（如果需要）
            - 加载新语言表
            - 更新当前语言上下文指针
```

### 6.3 内存管理（Memory Management）

- 内核模块：
  - 语言表作为静态常量数据编译进模块，不需要动态分配/释放内存。
  - 切换语言仅切换指针，不涉及实际内存操作。
- 用户态应用：
  - 通过读取 YAML 文件动态分配内存，需要在切换时释放旧语言表占用内存，防止泄漏。

---

## 7. 字符串格式化功能（Formatted String Support）

### 7.1 支持的格式化占位符

- `%s`：字符串
- `%d`：有符号整数（十进制）
- `%u`：无符号整数（十进制）
- `%f`：浮点数（小数）
- `%x`：无符号整数（十六进制表示）

### 7.2 实现机制

- 使用 C 标准库函数 `vsnprintf()` 实现变参格式化。
- `lang_getf` 流程：
  1. 根据 key 查询模板字符串。
  2. 创建格式化缓冲区（动态分配）。
  3. 使用 `va_list` 处理可变参数并格式化输出。
  4. 返回格式化后字符串，调用者负责释放内存。

示例伪代码：
```c
char* lang_getf(const char* key, ...) {
    const char* template = lang_get(key);
    if (!template) return NULL;

    va_list args;
    va_start(args, key);

    char* buffer = kmalloc(BUFFER_SIZE, GFP_KERNEL); // 内核态使用 kmalloc
    if (!buffer) return NULL;

    vsnprintf(buffer, BUFFER_SIZE, template, args);
    va_end(args);

    return buffer;
}
```

- 用户态版本使用 `malloc()` 和同样的 `vsnprintf()` 流程。

### 7.3 注意事项

- 调用者负责释放 `lang_getf` 返回的动态内存，防止内存泄漏。
- 格式字符串必须与参数匹配，错误使用可能导致未定义行为。
- 内核态需确保缓冲区大小合理，防止缓冲区溢出。

---

## 8. 错误处理与默认回退策略（Error Handling and Fallback）

### 8.1 查找失败

- 当前语言表中找不到指定 key 时：
  - 自动回退到默认语言表（英语 `en`）查找。
  - 如果在默认语言也找不到，则返回统一字符串：
    ```plaintext
    "Unknown Error"
    ```
  - 记录一条 WARN 日志，内容如：`[WARN] Language key not found: {key}`

### 8.2 格式化失败

- 调用 `vsnprintf` 失败（返回负值）时：
  - 返回统一字符串：
    ```plaintext
    "[FORMAT ERROR: Check argument count and types!]"
    ```
  - 记录一条 WARN 日志，内容如：`[WARN] Format failed for key: {key}`，并提示可能原因包括：参数数量错误、类型不匹配或模板格式非法。

### 8.3 语言切换失败

- 切换语言失败（加载语言表失败或不支持的语言代码）：
  - 自动回退到默认语言 `en`
  - 如果连默认语言表也加载失败，则系统进入降级模式，仅输出 Key 名称本身。
  - 记录一条 ERROR 日志，内容如：`[ERROR] Failed to switch language to {lang_code}`

---

# Logloom API 参考文档

本文档提供Logloom库所有公开API的完整参考，适用于将Logloom作为库集成到其他项目中的开发者。

---

## C API参考

### 国际化模块 (lang.h)

#### 数据结构

```c
// 语言表项结构
typedef struct {
    const char* key;   // 语言键
    const char* value; // 翻译文本
} lang_entry_t;
```

#### 函数

| 函数 | 说明 |
|------|------|
| `int lang_init(const char* default_lang)` | 初始化语言模块，设置默认语言代码 |
| `bool lang_set_language(const char* lang_code)` | 设置当前语言，成功返回true，失败返回false |
| `const char* lang_get(const char* key)` | 获取指定key的不带格式化的文本，未找到则返回NULL |
| `char* lang_getf(const char* key, ...)` | 获取带格式化插值的文本，返回动态分配的内存，需调用者释放 |
| `const char* lang_get_current()` | 获取当前设置的语言代码 |
| `void lang_cleanup()` | 清理语言模块资源 |

### 日志系统 (log.h)

#### 数据结构

```c
// 日志级别定义
typedef enum {
    LOG_LEVEL_DEBUG = 0,
    LOG_LEVEL_INFO  = 1,
    LOG_LEVEL_WARN  = 2,
    LOG_LEVEL_ERROR = 3,
    LOG_LEVEL_FATAL = 4
} log_level_t;

// 日志条目结构
typedef struct {
    unsigned long timestamp;  // Unix 时间戳
    log_level_t level;        // 日志级别
    const char* module;       // 模块名称
    const char* message;      // 日志消息
    const char* lang_key;     // 对应的语言键（可选）
} log_entry_t;
```

#### 函数

| 函数 | 说明 |
|------|------|
| `int log_init(const char* level, const char* log_file)` | 初始化日志系统，设置初始日志级别和日志文件 |
| `void log_set_file(const char* filepath)` | 设置日志输出文件路径，NULL表示禁用文件输出 |
| `void log_set_level(const char* level)` | 设置日志级别，参数为级别字符串("DEBUG", "INFO", "WARN", "ERROR", "FATAL") |
| `int log_level_from_string(const char* level)` | 从字符串获取日志级别枚举值 |
| `const char* log_level_to_string(int level)` | 将日志级别枚举值转换为字符串 |
| `const char* log_get_level_string(void)` | 获取当前日志级别的字符串表示 |
| `void log_set_console_enabled(int enabled)` | 开启/关闭控制台输出 (0=禁用, 1=启用) |
| `void log_set_max_file_size(size_t max_bytes)` | 设置最大日志文件大小（超过后自动轮转） |
| `void log_set_max_backup_files(size_t count)` | 设置最大历史日志文件数量 |
| `size_t log_get_max_backup_files(void)` | 获取最大历史日志文件数量 |
| `bool log_rotate_now(void)` | 手动触发日志文件轮转 |
| `void log_debug(const char* module, const char* format, ...)` | 输出调试级别日志 |
| `void log_info(const char* module, const char* format, ...)` | 输出信息级别日志 |
| `void log_warn(const char* module, const char* format, ...)` | 输出警告级别日志 |
| `void log_error(const char* module, const char* format, ...)` | 输出错误级别日志 |
| `void log_fatal(const char* module, const char* format, ...)` | 输出严重错误级别日志 |
| `void log_with_lang(log_level_t level, const char* module, const char* lang_key, ...)` | 使用语言键输出国际化日志 |
| `int log_get_level(void)` | 获取当前日志级别枚举值 |
| `bool log_is_console_enabled(void)` | 检查控制台输出是否启用 |
| `const char* log_get_file_path(void)` | 获取当前日志文件路径，未设置则返回NULL |
| `size_t log_get_max_file_size(void)` | 获取最大日志文件大小（字节） |
| `void log_cleanup(void)` | 清理日志系统资源 |
| `void log_lock(void)` | 显式加锁日志系统（用于连续多条日志或事务） |
| `void log_unlock(void)` | 解锁日志系统 |

### 配置系统 (config.h)

#### 函数

| 函数 | 说明 |
|------|------|
| `int config_init(const char* config_file)` | 初始化配置系统并加载指定的配置文件 |
| `const char* config_get_string(const char* key, const char* default_value)` | 获取字符串配置项，未找到则返回默认值 |
| `int config_get_int(const char* key, int default_value)` | 获取整数配置项，未找到则返回默认值 |
| `float config_get_float(const char* key, float default_value)` | 获取浮点数配置项，未找到则返回默认值 |
| `int config_get_bool(const char* key, int default_value)` | 获取布尔配置项，未找到则返回默认值 |
| `void config_cleanup(void)` | 清理配置系统资源 |

### 插件系统 (plugin.h)

#### 数据结构

```c
// 插件操作结构
typedef struct {
    void* (*init)(void);  // 插件初始化函数
    void (*process)(void* ctx, log_entry_t* entry);  // 处理日志条目
    void (*cleanup)(void* ctx);  // 清理插件资源
} plugin_ops_t;

// 插件注册结构（面向实现插件的开发者）
typedef struct {
    const char* name;     // 插件名称
    const char* version;  // 插件版本
    const char* description;  // 插件描述
    plugin_ops_t ops;     // 插件操作函数
} plugin_t;
```

#### 函数

| 函数 | 说明 |
|------|------|
| `int plugin_init(void)` | 初始化插件系统 |
| `int plugin_register(plugin_t* plugin)` | 注册插件 |
| `int plugin_load(const char* path)` | 从指定路径加载单个插件 |
| `int plugin_load_directory(const char* path)` | 从指定目录加载所有插件 |
| `void plugin_process(log_entry_t* entry)` | 使用所有插件处理日志条目 |
| `void plugin_cleanup(void)` | 清理插件系统资源 |

---

## Python API参考

Python API通过C扩展提供，主要类和函数如下：

### Logger类

方法:

| 方法 | 说明 |
|------|------|
| `Logger(module_name)` | 创建指定模块的日志记录器 |
| `set_level(level)` | 设置日志级别(LogLevel枚举) |
| `set_file(file_path)` | 设置日志文件路径 |
| `set_console_enabled(enabled)` | 启用/禁用控制台输出 |
| `set_rotation_size(max_bytes)` | 设置日志文件轮转大小 |
| `set_max_backup_files(count)` | 设置最大历史日志文件数 |
| `debug(message, *args, **kwargs)` | 记录调试级别日志 |
| `info(message, *args, **kwargs)` | 记录信息级别日志 |
| `warning(message, *args, **kwargs)` | 记录警告级别日志 |
| `error(message, *args, **kwargs)` | 记录错误级别日志 |
| `critical(message, *args, **kwargs)` | 记录严重错误级别日志 |

### Internationalization (I18n)

函数:

| 函数 | 说明 |
|------|------|
| `set_language(language_code)` | 设置当前语言，如"en", "zh" |
| `get_current_language()` | 获取当前语言代码 |
| `get_text(key)` | 获取指定键的文本 |
| `format_text(key, *args, **kwargs)` | 获取指定键的格式化文本 |

### 配置管理

函数:

| 函数 | 说明 |
|------|------|
| `initialize(config_path)` | 使用配置文件初始化Logloom系统 |
| `get_config_string(key, default_value)` | 获取字符串配置 |
| `get_config_int(key, default_value)` | 获取整数配置 |
| `get_config_float(key, default_value)` | 获取浮点数配置 |
| `get_config_bool(key, default_value)` | 获取布尔值配置 |

### 枚举类型

```python
class LogLevel:
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4
```

### 示例用法

```python
import logloom_py as ll

# 初始化系统
ll.initialize("./config.yaml")

# 设置语言
ll.set_language("zh")

# 创建日志记录器
logger = ll.Logger("main")
logger.set_level(ll.LogLevel.DEBUG)
logger.set_file("app.log")
logger.set_rotation_size(1024 * 1024)  # 1MB

# 记录日志
logger.info("应用启动")
logger.debug("调试信息: {}", "测试")
logger.warning("警告信息: {msg}", msg="发现异常")

# 使用国际化文本
welcome = ll.format_text("welcome", name="张三")
logger.info(welcome)
```

---

## 插件开发参考

### C插件接口

开发C语言插件需要实现以下结构：

```c
#include <logloom/plugin.h>
#include <logloom/log.h>

// 插件上下文结构（自定义）
typedef struct {
    // 插件私有数据
} my_plugin_ctx_t;

// 初始化函数
void* my_plugin_init(void) {
    my_plugin_ctx_t* ctx = malloc(sizeof(my_plugin_ctx_t));
    // 初始化上下文
    return ctx;
}

// 处理函数
void my_plugin_process(void* ctx, log_entry_t* entry) {
    my_plugin_ctx_t* my_ctx = (my_plugin_ctx_t*)ctx;
    // 处理日志条目
}

// 清理函数
void my_plugin_cleanup(void* ctx) {
    my_plugin_ctx_t* my_ctx = (my_plugin_ctx_t*)ctx;
    // 清理资源
    free(ctx);
}

// 插件注册
plugin_t my_plugin = {
    .name = "my_plugin",
    .version = "1.0.0",
    .description = "这是一个示例插件",
    .ops = {
        .init = my_plugin_init,
        .process = my_plugin_process,
        .cleanup = my_plugin_cleanup
    }
};

// 导出插件（必须使用此名称和签名）
plugin_t* logloom_plugin_init(void) {
    return &my_plugin;
}
```

### Python插件接口

Python插件应继承基础插件类并实现所需方法：

```python
from logloom.plugin import LogPlugin

class MyPlugin(LogPlugin):
    def __init__(self):
        # 初始化插件
        pass
        
    def process(self, log_entry):
        # 处理日志条目
        # log_entry是包含timestamp, level, module, message等字段的字典
        pass
        
    def cleanup(self):
        # 清理资源
        pass
```

插件文件应放在插件目录中，并通过`plugin_info.json`注册：

```json
{
    "name": "my_plugin",
    "version": "1.0.0",
    "description": "这是一个Python示例插件",
    "module": "my_plugin", 
    "class": "MyPlugin"
}
```

