# 02\_InternationalizationDesign.md

# Logloom 国际化模块详细设计文档

---

## 1. 简介（Purpose）

本模块为 Logloom 系统提供统一的多语言支持，确保日志与系统消息能够根据配置动态切换语言，同时兼容内核态与用户态环境。

---

## 2. 设计目标（Design Goals）

* 多语言资源维护简单（采用 YAML 源文件）
* 构建阶段自动生成 C 头文件供内核态使用
* 用户态直接加载 YAML 文件
* 支持格式化插值（如 "发生错误：%s"）
* 保持高性能（查询接口快速，支持静态编译）
* 标准化 Key 命名与访问接口

---

## 3. 语言资源格式（Language Resource Format）

### 3.1 源格式：YAML

* 每种语言单独一个 YAML 文件。

* 结构要求：

  * 一级分类表示模块（如 system、auth）
  * 二级键表示具体消息

* 示例（`locales/zh.yaml`）：

  ```yaml
  system:
    start_message: "程序启动"
    error_message: "发生错误：%s"
  auth:
    login_success: "登录成功"
    login_failed: "登录失败，请重试"
  ```

### 3.2 生成格式：静态数组 C 头文件

* 每种语言生成一个对应的 `.h` 文件（如 `lang_zh.h`, `lang_en.h`）

* 内容格式：

  * `typedef struct { const char* key; const char* value; } lang_entry_t;`
  * 静态数组 + NULL 结束
  * 自动生成宏定义，统一前缀为 `LOGLOOM_LANG_`

* 示例（`lang_zh.h`）：

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

| 接口                                               | 功能描述               |
| :----------------------------------------------- | :----------------- |
| `const char* lang_get(const char* key);`         | 获取指定 key 的文本       |
| `char* lang_getf(const char* key, ...);`         | 获取带格式化插值的文本，动态分配内存 |
| `void lang_set_language(const char* lang_code);` | 切换当前语言环境           |

---

## 5. 查询流程（Lookup Flow）

1. 查找当前语言的静态表。
2. 线性搜索或哈希加速（后续可扩展）。
3. 找不到时返回默认提示或 NULL。
4. `lang_getf` 在内部调用 `lang_get` 后格式化字符串。

---

## 6. 语言切换与加载机制（Language Switching and Loading）

### 6.1 加载策略（Loading Strategy）

* **按需加载**：系统启动时只加载默认语言表。
* **切换语言时**：

  * 释放当前语言表占用资源（如果有需要）
  * 加载新的目标语言表
* **默认语言配置**：

  * 在初始化配置中指定，如 `zh`、`en`
  * 若切换失败（目标语言表不存在或加载失败），系统应回退到默认语言，并打印警告日志。

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

* 内核模块：

  * 语言表作为静态常量数据编译进模块，不需要动态分配/释放内存。
  * 切换语言仅切换指针，不涉及实际内存操作。
* 用户态应用：

  * 通过读取 YAML 文件动态分配内存，需要在切换时释放旧语言表占用内存，防止泄漏。

---

## 7. 字符串格式化功能（Formatted String Support）

### 7.1 支持的格式化占位符

* `%s`：字符串
* `%d`：有符号整数（十进制）
* `%u`：无符号整数（十进制）
* `%f`：浮点数（小数）
* `%x`：无符号整数（十六进制表示）

### 7.2 实现机制

* 使用 C 标准库函数 `vsnprintf()` 实现变参格式化。
* `lang_getf` 流程：

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

* 用户态版本使用 `malloc()` 和同样的 `vsnprintf()` 流程。

### 7.3 注意事项

* 调用者负责释放 `lang_getf` 返回的动态内存，防止内存泄漏。
* 格式字符串必须与参数匹配，错误使用可能导致未定义行为。
* 内核态需确保缓冲区大小合理，防止缓冲区溢出。

---

## 8. 错误处理与默认回退策略（Error Handling and Fallback）

### 8.1 查找失败

* 当前语言表中找不到指定 key 时：

  * 自动回退到默认语言表（英语 `en`）查找。
  * 如果在默认语言也找不到，则返回统一字符串：

    ```plaintext
    "Unknown Error"
    ```
  * 记录一条 WARN 日志，内容如：`[WARN] Language key not found: {key}`

### 8.2 格式化失败

* 调用 `vsnprintf` 失败（返回负值）时：

  * 返回统一字符串：

    ```plaintext
    "[FORMAT ERROR: Check argument count and types!]"
    ```
  * 记录一条 WARN 日志，内容如：`[WARN] Format failed for key: {key}`，并提示可能原因包括：参数数量错误、类型不匹配或模板格式非法。

### 8.3 语言切换失败

* 切换语言失败（加载语言表失败或不支持的语言代码）：

  * 自动回退到默认语言 `en`
  * 如果连默认语言表也加载失败，则系统进入降级模式，仅输出 Key 名称本身。
  * 记录一条 ERROR 日志，内容如：`[ERROR] Failed to switch language to {lang_code}`

---

## 9. 构建工具与生成流程（Build Tool and Generation Pipeline）

### 9.1 构建脚本功能

* 使用 Python 编写脚本 `generate_lang_headers.py`
* 读取 `locales/` 目录下的所有 `.yaml` 文件
* 为每个语言文件生成：

  * `include/generated/lang_<code>.h` 文件（如 `lang_zh.h`）
  * 包含静态语言数组和宏定义
* 生成统一注册头文件 `lang_registry.h`，提供注册查询接口：

```c
const lang_entry_t* get_lang_table(const char* lang_code);
```

### 9.2 注册表函数行为

* 自动生成 `get_lang_table()` 实现：

  ```c
  const lang_entry_t* get_lang_table(const char* lang_code) {
      if (strcmp(lang_code, "zh") == 0) return zh_lang_table;
      if (strcmp(lang_code, "en") == 0) return en_lang_table;
      return NULL;
  }
  ```
* 将所有语言表注册进逻辑分支中，避免手动维护
* 可供 `lang_set_language()` 内部调用实现按需加载

### 9.3 输出结构示例

```plaintext
project_root/
├── locales/
│   ├── zh.yaml
│   ├── en.yaml
├── include/
│   └── generated/
│       ├── lang_zh.h
│       ├── lang_en.h
│       └── lang_registry.h
```

### 9.4 错误检测

构建工具在生成过程中会进行以下检查：

* 重复 key 检查：同一语言下不能有重复键名
* 非法字符校验：key 仅允许 `a-z0-9_` 和 `.`
* 语法格式校验：必须是合法 YAML 格式，否则中止生成

出错时应输出清晰报错信息并中止构建。

---

## 10. 测试策略与验证流程（Testing and Validation）

### 10.1 测试目标

确保国际化模块在内核态和用户态下都能：

* 正确加载语言资源
* 正确解析和返回语言文本
* 正确进行字符串格式化
* 在异常条件下安全回退
* 构建工具生成内容无误

---

### 10.2 测试类型与方法

| 测试类型   | 内容                                         | 方法                     |
| :----- | :----------------------------------------- | :--------------------- |
| ✅ 单元测试 | `lang_get`、`lang_getf`、`lang_set_language` | 使用断言测试或嵌入式测试框架，如 Unity |
| ✅ 集成测试 | 调用 API 进行语言切换、格式化验证                        | 提供 YAML 测试样例、运行日志比对    |
| ✅ 构建测试 | 脚本是否正确生成 `.h` 文件和宏                         | 用 diff 工具与预期头文件比对      |
| ✅ 边界测试 | 模板非法、参数缺失、语言缺失                             | 手工构造 YAML 错误示例或故障用例    |
| ✅ 性能测试 | 多线程下的查询稳定性和耗时                              | 多线程压力测试 + 时间统计         |

---

### 10.3 关键验证点

| 验证点       | 说明                                   |
| :-------- | :----------------------------------- |
| 语言表解析准确性  | 检查生成的 C 文件中是否完整包含 YAML 所有 key        |
| 注册接口有效性   | `get_lang_table("zh")` 等是否返回正确静态数组指针 |
| 格式化输出一致性  | `%d`, `%s`, `%f` 等格式能否与实际参数一致        |
| 异常行为回退机制  | 包括 key 不存在、语言切换失败、格式化失败              |
| 构建时错误检测机制 | 包括重复 key、非法字符、非法 YAML 等均应终止构建        |

---

### 10.4 自动化测试建议

* 使用 Makefile 添加目标 `make test-i18n`

* 包含内容：

  * YAML 校验脚本（如 `yamllint`）
  * 构建后自动 diff 预期头文件
  * 编译运行一个 demo，调用所有接口并打印输出
  * 输出与预期对比结果，显示通过/失败

* 可选扩展：集成 GitHub Actions 或 GitLab CI，持续验证语言资源的正确性与构建产出一致性
