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

## 9. Python绑定扩展功能

为满足Python开发者在集成Logloom时的灵活性需求，Python绑定提供以下扩展功能。

### 9.1 动态语言资源注册

#### `register_locale_file(file_path, lang_code=None)`
注册额外的语言资源文件，实现应用级的翻译扩展。

**参数**：
- `file_path`：YAML语言资源文件的路径
- `lang_code`：语言代码（如果为None，则从文件名推断）

**返回值**：
- `True`：注册成功
- `False`：注册失败

**示例**：
```python
from logloom import register_locale_file

# 显式指定语言代码
register_locale_file("/path/to/app_translations.yaml", "zh")

# 从文件名推断语言代码（如fr.yaml）
register_locale_file("/path/to/fr.yaml")
```

#### `register_locale_directory(dir_path, pattern="*.yaml")`
注册目录中所有匹配模式的语言资源文件。

**参数**：
- `dir_path`：包含语言资源文件的目录路径
- `pattern`：文件匹配模式（默认为"*.yaml"）

**返回值**：
- 成功注册的文件数量

**示例**：
```python
from logloom import register_locale_directory

# 注册应用特定的翻译目录
count = register_locale_directory("/app/translations")
print(f"已注册 {count} 个语言文件")
```

### 9.2 语言资源状态查询

#### `get_supported_languages()`
获取当前支持的所有语言代码列表。

**参数**：无

**返回值**：
- 语言代码列表，如 `["en", "zh", "fr"]`

**示例**：
```python
from logloom import get_supported_languages

languages = get_supported_languages()
print(f"支持的语言: {', '.join(languages)}")
```

#### `get_language_keys(lang_code=None)`
获取指定语言中所有可用的翻译键列表。

**参数**：
- `lang_code`：语言代码，默认为当前语言

**返回值**：
- 翻译键列表

**示例**：
```python
from logloom import get_language_keys

# 获取当前语言的所有键
keys = get_language_keys()

# 获取特定语言的所有键
zh_keys = get_language_keys("zh")
```

### 9.3 自动资源发现

Python绑定在初始化时增加以下自动资源发现机制：

1. **配置文件自动关联**：
   - 从配置文件的`locale_paths`字段读取语言资源路径列表
   - 支持glob模式，如`"./locales/*.yaml"`

2. **项目自动发现**：
   - 自动搜索以下位置的语言资源文件：
     - 当前工作目录下的`locales/`
     - 应用配置目录（如`~/.config/应用名/locales/`）
     - 系统语言定义目录（如`/usr/share/locale/应用名/`）

3. **命名约定**：
   - 语言文件应命名为`<lang_code>.yaml`，如`en.yaml`
   - 或者格式为`<应用名>_<lang_code>.yaml`，如`myapp_en.yaml`

**示例配置**：
```yaml
# logloom_config.yaml
locale:
  default: "en"
  locale_paths:
    - "./locales/*.yaml"
    - "./custom_translations/*.yaml"
```

### 9.4 纯Python实现增强

为确保在无法加载C扩展模块时依然提供完整功能，纯Python实现（fallback实现）将提供以下保证：

1. 完全支持动态注册语言资源文件
2. 实现所有语言资源状态查询功能
3. 自动资源发现机制

纯Python实现将显示一条警告消息，但保持API完全兼容。

---

