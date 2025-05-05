# Logloom (MVP)

更换语言：[EN](./README_EN.md)

> **注意**: 当前版本为最小可行产品(MVP)，正在积极开发中。核心功能已实现，但更多高级特性将在后续版本添加。

---

## 📊 开发阶段（Development Status）

当前Logloom项目处于积极开发阶段：

- **当前支持**：C语言接口（同时支持纯C和C++项目）
- **开发中**：分离内核态和用户空间实现，Python绑定和API接口
- **规划中**：独立进程/容器插件系统，AI分析模块集成

### 开发里程碑

| 里程碑编号 | 名称             | 完成标志                             | 状态 |
|---------|----------------|----------------------------------|------|
| M0      | 初始化项目结构      | 完成 Makefile / 源码目录 / YAML 输入结构  | ✅ 已完成 |
| M1      | 多语言支持构建与核心  | 能够加载 YAML 并通过 `lang_get()` 取出字符串 | ✅ 已完成 |
| M2      | 日志系统初步       | 输出结构化日志到控制台 / 文件，支持多等级        | ✅ 已完成 |
| M3      | 配置加载与默认合并   | 正确加载配置 YAML 并生成头文件 / 结构体       | ✅ 已完成 |
| M4      | 日志文件轮转功能    | 日志达到最大容量后成功生成新文件               | ✅ 已完成 |
| M5      | 插件注册与运行框架   | 成功加载 `.so` 插件并执行其 process()     | ✅ 已完成 |
| M6      | 测试集成         | 所有模块能通过至少 3 条测试用例验证            | ✅ 已完成 |
| M7      | 最小可运行版本（MVP）| 执行演示程序，加载语言+配置，写入日志           | ✅ 已完成 |
| M8      | Python绑定和扩展API| 支持在Python中调用Logloom核心功能        | 🚧 开发中 |
| M9      | AI分析模块集成    | 支持智能日志分析和诊断功能                  | 📅 规划中 |

---

## 🌟 动机（Motivation）

随着软件系统规模的不断增长，不同模块、不同语言、不同平台之间的协作变得日益复杂。  
在这种环境下，**日志**成为理解、监控、诊断系统行为的最基本手段。  
然而，传统日志系统存在诸多问题：

- 缺乏统一标准，不同程序风格各异
- 语言绑定零散，难以跨语言共享日志格式
- 日志内容面向人类阅读，不适合机器智能分析
- 缺乏内置国际化支持，难以适应多语环境

**Logloom** 诞生的目标，就是要从根本上解决这些问题。

---

## 🌟 目标（Goals）

Logloom 致力于构建一个：

- **统一标准**  
  为所有程序提供一致、结构化的日志格式，无论是内核模块、自动化工具还是虚拟化平台。

- **跨语言兼容**  
  设计简单、轻量的日志协议，可以方便地在 C、Python、Shell 等多种语言中实现。

- **多语国际化**  
  日志消息与自然语言内容完全分离，支持动态多语输出，适应全球化应用需求。

- **智能可观测性**  
  日志不仅用于记录，还为后续机器分析、智能诊断、自动修复提供数据基础。

- **未来可扩展性**  
  为集成 AI 分析模块打下架构基础，使系统能够从日志中学习、推理与自我优化。

---

## 🧹 设计哲学（Design Principles）

- **结构化优先**  
  日志以标准化结构（如 JSON 行）记录，确保既可读又可解析。

- **上下文丰富**  
  除错误信息外，包含运行环境、资源状态、调用栈等上下文信息，支持深层分析。

- **语言无关**  
  日志标准与具体实现语言解耦，任何支持基本输出的环境都能使用。

- **国际化内嵌**  
  消息编码 + 语言资源管理，日志输出可根据配置即时切换语言。

- **轻量灵活**  
  不依赖重型服务（如 Fluentd/Kibana），单程序、单模块即可部署使用。

- **智能扩展**  
  设计保留足够的数据冗余，为未来引入规则引擎、机器学习模块留出空间。

---

## 🛠️ 核心模块（Core Components）

Logloom 基础系统包含以下模块：

### 1. 国际化系统（Internationalization System）

- 语言资源文件独立管理，采用 YAML 或 C 头文件形式。
- 支持运行时动态切换语言（如中文、英文等）。
- 消息文本通过统一接口调用（如 `locale_get(key)` 或 `lang_get(key)`）。
- 支持格式化字符串插值（如 `locale_getf(key, value)`）。
- 默认语言可通过配置或参数指定，未找到时回退到默认语言。

参考实现：
- Python 项目（KnowForge）使用 `LocaleManager` 类。
- C 语言项目（MoeAI-C）使用宏定义键值对 + `lang_get` 系统。

### 2. 结构化日志系统（Structured Logging System）

- 日志统一为 JSON 格式：
  ```json
  {
    "timestamp": "2025-04-29T12:00:00Z",
    "level": "INFO",
    "module": "auth",
    "message": "User login successful",
    "lang_key": "auth.login_success",
    "context": {
      "user_id": 12345,
      "ip": "192.168.1.1"
    }
  }
  ```
- 支持日志级别管理：DEBUG、INFO、WARN、ERROR、FATAL。
- 日志输出支持双通道：
  - 控制台输出（便于调试）
  - 文件持久化（便于追溯）
- 可按模块细分 Logger，独立控制各模块日志行为。

参考实现：
- Python 项目中使用 `setup_logger()` 和 `get_module_logger()`
- C 项目中使用 `moeai_log()` 和内置环形缓冲区输出。

### 3. 配置与扩展接口（Configuration and Extensibility）

- 支持通过配置文件或环境变量动态设置：
  - 默认语言
  - 日志保存路径
  - 最低日志级别
- 后续可扩展：
  - 日志轮转、清理机制
  - 日志数据导出 API
  - 日志驱动的告警与自恢复模块

---

## 🚀 典型应用场景（Typical Use Cases）

- **高性能内核模块日志**  
  （如 MoeAI-C 项目）
- **智能笔记生成工具日志**  
  （如 KnowForge 项目）
- **虚拟化环境管理与监控日志**  
  （如 AntiChatVM 项目）
- **未来 AI 系统日志数据采集与分析**

---

## 🚀 快速开始（Quick Start）

### 安装

1. 克隆仓库
   ```bash
   git clone https://github.com/yourusername/Logloom.git
   cd Logloom
   ```

2. 编译项目
   ```bash
   make
   ```

### 基本使用

1. **创建配置文件**

   创建 `config.yaml` 文件（或使用示例配置文件）:

   ```yaml
   logloom:
     language: "zh"  # 或 "en"
     log:
       level: "DEBUG"  # 可选: DEBUG, INFO, WARN, ERROR
       file: "./app.log"
       max_size: 1048576  # 1MB
       console: true
   ```

2. **在你的C程序中使用**

   ```c
   #include "include/log.h"
   #include "include/lang.h"
   
   int main() {
       // 初始化日志系统
       log_init();
       log_set_level(LOG_LEVEL_DEBUG);
       log_set_output_file("my_app.log");
       
       // 设置语言
       lang_set_language("zh");  // 或 "en"
       
       // 使用日志系统
       log_debug("LOGLOOM_LANG_DEBUG_MESSAGE", 123);
       log_info("LOGLOOM_LANG_INFO_MESSAGE");
       log_warn("LOGLOOM_LANG_WARN_WITH_PARAM", "警告参数");
       log_error("LOGLOOM_LANG_ERROR_CODE", 404);
       
       return 0;
   }
   ```

3. **编译你的程序**

   ```bash
   gcc your_program.c -I/path/to/logloom/include -L/path/to/logloom -llogloom -o yourprogram
   ```

### 运行演示

```bash
# 编译并运行示例程序
make demo
./demo
```

查看生成的日志文件或控制台输出。

---

## 📚 技术路线图（Technical Roadmap）

1. **当前 MVP**: 基础日志和国际化功能
2. 分离内核态和用户空间实现
3. 发布 Python + C 语言的完整 SDK
4. 支持更多语言扩展（新增西班牙语、法语等）
5. 增强日志安全性（敏感信息自动脱敏）
6. 引入基于日志的异常检测与告警系统
7. 集成轻量级日志智能分析模块

---

## 📖 关于命名（About the Name）

**Logloom**  
取自 "Log"（日志）与 "Loom"（织机）的结合，  
寓意将分散的日志数据织成一张连贯、可感知、可演化的智能系统之网。

---

# 📜 许可协议（License）

本项目使用 **GNU General Public License v3.0 (GPL-3.0)** 协议。  
详情请查阅 [LICENSE](./LICENSE)。
