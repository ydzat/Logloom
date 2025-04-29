# 01_HighLevelDesign.md

# Logloom 高层设计文档（正式版）

## 1. 简介（Purpose）
本文件旨在描述 Logloom 项目的整体系统架构、模块划分、主要数据流动与交互方式，为后续各模块详细设计与开发提供统一指导。

## 2. 背景（Background）
随着软件系统规模扩大，传统日志方式暴露出诸多问题（如：缺乏标准、跨语言兼容性差、国际化不足、机器分析难）。Logloom 项目希望通过统一的结构化日志协议和多语支持，打造轻量、可扩展、跨语言的日志系统，为未来智能日志分析奠定基础。

## 3. 总体架构概览（System Overview）

Logloom 系统划分为以下核心模块：

- **国际化模块 (i18n System)**
- **结构化日志模块 (Structured Logging System)**
- **配置管理模块 (Configuration System)**
- **扩展与接入层 (Extensibility Layer)**

各模块之间通过明确定义的接口进行通信与协作。

## 4. 核心模块划分（Modules）

### 4.1 国际化模块（i18n System）
**职责**：提供统一的多语言资源加载与查询接口。

**子模块**：
- 语言资源管理（Language Resource Management）
- 运行时语言切换（Runtime Language Switching）

**关键接口**：
- `lang_get(key: str) -> const char*`
- `lang_getf(key: str, ...) -> char*`

**语言资源格式**：
- 源格式为 YAML 文件，便于维护和扩展多语言。
- 构建阶段通过脚本工具自动生成静态数组形式的 C 头文件。
- 生成的 C 宏统一采用 `LOGLOOM_LANG_` 前缀，所有 Key 规范为大写字母、使用下划线连接多层级，例如：
  - YAML Key `system.start_message` → 宏名 `LOGLOOM_LANG_SYSTEM_START_MESSAGE`

---

### 4.2 结构化日志模块（Structured Logging System）
**职责**：负责生成符合标准结构的日志条目，并根据配置输出到控制台、文件等渠道。

**子模块**：
- 日志条目生成（Log Entry Generation）
- 日志级别控制（Log Level Control）
- 多通道输出（Console and File Output）

**关键接口**：
- `log_debug(const char* module, const char* fmt, ...)`
- `log_info(const char* module, const char* fmt, ...)`
- `log_warn(const char* module, const char* fmt, ...)`
- `log_error(const char* module, const char* fmt, ...)`

**日志格式**：使用简单 C 结构体存储，序列化输出。无 JSON/Protobuf 等外部依赖。

示例结构体：
```c
struct log_entry {
    uint64_t timestamp;
    uint8_t level;
    char module[16];
    char message[128];
};
```

---

### 4.3 配置管理模块（Configuration System）
**职责**：统一管理项目的动态参数（如语言设置、日志级别、日志输出目录等）。

**关键接口**：
- `config_get(const char* key)`
- `config_set(const char* key, const void* value)`

**配置源**：静态配置文件或模块参数，初始化时加载，不支持运行时热更新。

---

### 4.4 扩展与接入层（Extensibility Layer）
**职责**：提供标准接口，允许外部系统接入、扩展 Logloom 能力（如日志轮转、告警模块、AI分析模块）。

**示例扩展**：
- 日志轮转子系统（Log Rotation）
- 日志异常检测（Anomaly Detection）
- 日志智能总结（Intelligent Summarization）


## 5. 数据流与交互（Data Flow & Interaction）

1. 业务模块调用日志接口，传入日志内容及可选上下文。
2. 日志模块根据当前配置，生成结构化日志条目。
3. 日志条目关联语言 Key（如果需要国际化展示）。
4. 日志模块根据输出通道配置，将日志写入控制台和/或文件。
5. 配置模块在系统初始化阶段提供参数支持。


## 6. 开发语言与目标平台（Languages and Target Platforms）

- 开发语言：C、Python（后续可扩展至 Shell、Rust 等）
- 目标平台：Linux 系统为主，兼容内核态（C）、用户态（Python）环境。


## 7. 关键设计决策（Key Design Decisions）

- 国际化资源采用 YAML 维护，构建阶段生成静态数组 C 头文件，宏名统一前缀为 `LOGLOOM_LANG_`。
- 日志存储格式使用结构体序列化输出，不使用 JSON、Protobuf 等格式。
- 日志输出默认启用控制台 + 文件双通道，允许通过配置关闭任一通道。
- 配置系统仅在模块初始化时加载，运行时不支持动态热更新。


## 8. 未来扩展预留（Future Extension）

- 支持多租户日志隔离（Multi-tenant Logging）
- 支持标准远程日志聚合（Remote Logging via gRPC/HTTP）
- 集成基于规则引擎的告警系统
- 引入基于日志数据的机器学习分析模块


## 9. 与内核模块集成注意事项（Kernel Module Integration Notes）

- 必须避免动态内存泄漏，所有分配的内存需及时释放。
- 日志写入需确保不会阻塞内核主路径，应使用环形缓冲区（Ring Buffer）。
- 需考虑并发访问同步问题（如使用 spinlock 保证缓冲区线程安全）。
- 资源初始化和清理（如语言系统、日志系统）需严格遵循 `init -> exit` 生命周期规范。
