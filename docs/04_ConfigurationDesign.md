# 04\_ConfigurationDesign.md

# Logloom 配置系统设计文档

---

## 1. 简介与设计目标（Purpose & Goals）

Logloom 的配置系统负责统一加载和提供运行期的参数设置，确保日志系统、国际化系统等子模块在启动时具备一致、可控的初始化行为。

设计目标如下：

* ✅ **仅支持初始化阶段加载**，不支持运行时热更新，保持行为确定性
* ✅ **用户态采用 YAML 格式配置文件**，结构清晰、支持嵌套，利于维护
* ✅ **内核态通过构建时预生成 `.h` 文件方式传递配置**，确保兼容性与静态性
* ✅ **所有配置键具备默认值**，缺失配置不会导致系统崩溃
* ✅ **与 01\~03 文档保持一致性**，支持日志模块、语言模块初始化参数注入

---

## 2. 配置作用范围与支持项（Supported Configuration Keys）

本节列出当前系统支持的 YAML 配置项，按模块分类。

### 2.1 顶级结构

```yaml
logloom:
  language: "en"
  log:
    level: "INFO"
    file: "/var/log/logloom.log"
    max_size: 1048576  # 单位：字节，默认 1MB
    console: true
```

### 2.2 配置项说明

| 路径                     | 类型      | 默认值       | 说明                               |
| ---------------------- | ------- | --------- | -------------------------------- |
| `logloom.language`     | string  | "en"      | 默认语言，用于加载对应语言资源表                 |
| `logloom.log.level`    | string  | "INFO"    | 日志等级：DEBUG / INFO / WARN / ERROR |
| `logloom.log.file`     | string  | 空（禁用文件输出） | 日志文件路径                           |
| `logloom.log.max_size` | integer | 1048576   | 单文件最大大小（单位：字节）                   |
| `logloom.log.console`  | boolean | true      | 是否启用控制台日志输出                      |

### 2.3 配置扩展策略

* 所有配置项均带默认值，缺省时系统使用内置默认参数
* 后续模块新增时，建议以模块命名空间添加子项（如 `logloom.metrics.enable`）
* 所有 key 应采用小写字母加下划线命名，不支持驼峰

---

## 3. 配置文件结构与格式（File Layout & Syntax）

### 3.1 配置文件路径建议

用户态默认配置文件路径如下：

* **Linux 系统**：

  ```bash
  /etc/logloom/config.yaml
  ```
* **Windows 系统**：

  ```cmd
  C:\\ProgramData\\logloom\\config.yaml
  ```

> 可通过环境变量 `LOGLOOM_CONFIG` 或命令行参数 `--config` 进行覆盖（仅限用户态）

### 3.2 YAML 文件结构规范

* 顶级必须为 `logloom` 键
* 支持最多两级嵌套（如 `logloom.log.level`）
* 不允许空键、重复键，值类型必须匹配

### 3.3 命名规范（Key Naming Conventions）

* 所有 key 使用小写英文字母，单词间用下划线连接
* 禁止使用驼峰（如 `logLevel`）或混合大小写
* 键名应与代码中访问路径严格对应（如 `logloom.language`）

### 3.4 注释与可读性

* 配置文件中允许使用标准 YAML 注释（`#` 开头）
* 推荐对每个主要字段添加用途注释，增强可维护性

### 3.5 示例完整配置文件

```yaml
logloom:
  language: "zh"
  log:
    level: "DEBUG"
    file: "/tmp/logloom.log"
    max_size: 2097152  # 2MB
    console: false
```

---

## 4. 配置加载机制（Configuration Loading Mechanism）

### 4.1 用户态：动态加载 YAML 配置文件

* 使用轻量 YAML 解析库（如 `libyaml` 或 `yaml-cpp`）读取配置
* 启动阶段加载配置文件并映射到结构体

```c
typedef struct {
    char language[8];
    struct {
        char file[256];
        char level[8];
        size_t max_size;
        bool console;
    } log;
} logloom_config_t;

extern logloom_config_t g_config;
```

* 提供加载函数：

```c
int config_load_from_file(const char* path);
```

* 如未提供路径，将从默认路径或环境变量读取

### 4.2 内核态：构建时生成静态头文件

* 内核模块无法动态读取 YAML，改由构建工具生成：

  ```bash
  gen_config_header.py config.yaml → include/generated/config.h
  ```

* 示例生成内容：

```c
#define LOGLOOM_LANG_DEFAULT "en"
#define LOGLOOM_LOG_LEVEL   "INFO"
#define LOGLOOM_LOG_FILE    "/var/log/logloom.log"
#define LOGLOOM_LOG_MAXSIZE 1048576
#define LOGLOOM_LOG_CONSOLE 1
```

* 内核模块可通过宏或初始化结构体静态使用配置参数，无需动态分配

### 4.3 配置校验逻辑

* 用户态加载时进行字段合法性校验：

  * level 是否为有效字符串
  * max\_size 是否大于最小阈值
* 内核态构建工具在转换 YAML 时亦进行静态合法性校验

---

## 5. 内核态配置传递机制（Kernel-Space Configuration Injection）

### 5.1 头文件集成方式

* 所有内核模块依赖的配置通过如下头文件引入：

  ```c
  #include "generated/config.h"
  ```
* 所有配置值通过 `#define` 宏形式暴露，确保无动态内存需求
* 与其他内核组件（如日志模块、国际化模块）通过编译时绑定使用

### 5.2 示例使用场景

```c
if (LOGLOOM_LOG_CONSOLE) {
    printk("[INFO] Console logging enabled\n");
}
```

```c
lang_set_language(LOGLOOM_LANG_DEFAULT);
```

### 5.3 多模块同步策略

* 构建工具需确保：

  * 所有引用配置的模块使用相同的 `config.h`
  * 在语言文件、日志模块构建前自动生成配置头文件
  * 所有配置值在构建后冻结，模块间保持一致

### 5.4 可选结构体映射

* 对于部分模块，可定义静态结构体简化访问：

  ```c
  static const struct log_config cfg = {
      .level = LOGLOOM_LOG_LEVEL,
      .console = LOGLOOM_LOG_CONSOLE,
      .max_size = LOGLOOM_LOG_MAXSIZE
  };
  ```

---
## 6. 配置访问接口与默认值注入策略（Access & Default Fallbacks）

### 6.1 用户态访问方式

* 用户态模块应统一通过全局结构体 `g_config` 读取配置：

```c
extern logloom_config_t g_config;

const char* lang = g_config.language;
bool log_to_console = g_config.log.console;
```

* 所有字段在 `config_load_from_file()` 成功后即完成初始化，
  缺省值在加载失败或 YAML 缺项时注入。

### 6.2 默认值注入策略（用户态）

* 在加载 YAML 前，`g_config` 会预置默认值：

```c
static void config_set_defaults(logloom_config_t* cfg) {
    strcpy(cfg->language, "en");
    strcpy(cfg->log.level, "INFO");
    cfg->log.file[0] = '\0';
    cfg->log.max_size = 1048576;
    cfg->log.console = true;
}
```

* 加载配置文件后对字段进行合并覆盖（partial override）

### 6.3 内核态访问方式

* 所有配置通过宏 `LOGLOOM_XXX` 访问：

```c
if (LOGLOOM_LOG_CONSOLE) { ... }
lang_set_language(LOGLOOM_LANG_DEFAULT);
```

* 宏定义在 `generated/config.h` 中由构建工具生成，
  已包含默认值逻辑，构建时缺项则使用 fallback 模板值填充。

### 6.4 安全性与静态性原则

* 不允许用户态模块修改 `g_config` 内容（只读）
* 内核模块禁止使用字符串拼接访问 key，应通过宏与结构体静态访问
* 所有访问路径应在编译时确定，禁止动态拼接访问路径

### 6.5 可选封装接口（建议）

* 提供函数封装访问部分关键字段，提高可维护性：

```c
const char* config_get_log_level();
bool config_is_console_enabled();
size_t config_get_max_log_size();
```

* 内部只读返回结构体字段，避免直接暴露实现

---

## 7. 错误处理策略与测试方案（Error Handling & Validation）

### 7.1 错误处理策略（用户态）

* 配置文件未找到或无法读取：

  * 控制台输出警告：`[WARN] Config file not found, using defaults.`
  * 启用默认配置继续运行

* YAML 格式非法、类型不匹配：

  * 输出详细错误信息（行号、字段名）
  * 仍使用默认值，避免中断

* 字段缺失：

  * 自动使用 `config_set_defaults()` 中的默认值

### 7.2 错误处理策略（内核态）

* 构建时：

  * 若缺失字段、类型错误、非法值，`gen_config_header.py` 立即终止并输出报错
  * 所有配置必须合法后才生成 `.h` 文件

* 运行时：

  * 不支持配置动态加载，所有配置为只读宏，无法出错

### 7.3 测试类型与方法

| 测试类型    | 方法与目标                     |
| ------- | ------------------------- |
| 加载测试    | 正确解析 YAML，字段值准确映射         |
| 缺失字段测试  | 模拟缺项，确认默认值自动注入            |
| 非法格式测试  | 模拟类型错误、非法缩进等，确保能 fallback |
| 文件不存在测试 | 未提供路径或路径错误是否降级            |
| 内核头生成测试 | `.h` 文件字段是否完整、类型正确、宏拼写合法  |

### 7.4 自动化测试建议

* 使用脚本运行以下测试场景：

  * 加载完整配置
  * 加载部分缺失配置
  * 加载非法 YAML（语法错）
  * 加载类型不符配置
  * 自动 diff 构建生成头文件与 golden 样本对比

* 提供 CI 集成入口：`make test-config`

