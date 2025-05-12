# Logloom

更换语言：[EN](./README_EN.md)

> **注意**: 当前版本为最小可行产品(MVP)，正在积极开发中。核心功能已实现，但更多高级特性将在后续版本添加。

---

## 📊 开发阶段（Development Status）

当前Logloom项目处于积极开发阶段：

- **当前支持**：C语言接口（同时支持纯C和C++项目）、Python基础绑定、API一致性自动化检查、Python插件系统
- **开发中**：AI分析模块集成
- **规划中**：高级安全特性

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
| M8      | Python绑定和扩展API| 支持在Python中调用Logloom核心功能        | ✅ 已完成 |
| M9      | C库与Python绑定API匹配 | 确保C库API与Python绑定功能一致      | ✅ 已完成 |
| M10     | 高并发稳定性验证    | 多线程环境下正常运行无数据竞争               | ✅ 已完成 |
| M11     | API一致性自动检查工具 | 能够自动验证头文件与实现的API一致性          | ✅ 已完成 |
| M12     | Python插件系统实现 | 与C插件系统功能等效且支持插件发现和加载          | ✅ 已完成 |
| M13     | AI分析模块集成     | 支持智能日志分析和诊断功能                  | 📅 规划中 |

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

### 4. API一致性检查工具（API Consistency Checker）

- 自动检测和报告API不一致问题：
  - 头文件声明与实现文件定义不匹配
  - 返回类型不一致
  - 参数类型、数量或名称不匹配
- 支持多种输出格式（文本、JSON、HTML）
- 使用libclang进行精确的AST分析
- 可自定义检查规则，通过YAML配置文件设置

使用示例：

```bash
# 运行API一致性检查
./tools/api_consistency_check.py --include-dir include --src-dir src --rules tools/api_consistency_rules.yaml

# 生成HTML格式报告
./tools/api_consistency_check.py --include-dir include --src-dir src --output html --output-file api_report.html
```

### 5. Python 绑定与测试适配器（Python Bindings and Test Adapters）

Logloom 提供了完整的 Python 语言支持，包括：

- **核心功能接口**：日志记录、国际化、配置管理
- **模块化日志记录器**：每个模块可独立控制日志级别
- **测试适配器系统**：当真实模块不可用时提供模拟实现

测试适配器的关键特性：

```python
# 使用测试适配器
from tests.python.test_adapter import logger, Logger, LogLevel

# 创建日志记录器
logger = Logger("my_module")
logger.set_level(LogLevel.DEBUG)
logger.set_file("my_logs.log")

# 设置日志轮转
logger.set_rotation_size(1024)  # 1KB

# 记录不同级别的日志
logger.debug("这是调试信息: {}", 123)
logger.info("这是信息")
logger.warning("这是警告: {warning}", warning="警告内容")
logger.error("这是错误")
logger.critical("这是严重错误")
```

测试适配器支持：

- 日志级别过滤
- 格式化位置参数和关键字参数
- 日志文件轮转功能
- 多语言支持
- 模块独立设置

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

### 环境需求

Logloom库的基本要求：

- **操作系统**：
  - Linux: Fedora 41（已测试）
  - 其他Linux发行版（理论上支持）
  - macOS或Windows（理论上支持，通过WSL）
- **编译器**：GCC 5.0+或Clang 5.0+
- **构建工具**：Make
- **Python**：Python 3.13（虚拟环境中的版本，已测试）（其他版本可能支持，需要注意兼容性）
- **其他依赖**：
  - libyaml-dev（用于YAML配置解析）
  - pkg-config（构建系统依赖）
  - python3-dev（Python绑定需要）

在Fedora 41上安装依赖：
```bash
sudo dnf install make gcc libyaml-devel pkgconfig python3-devel
```

在Debian/Ubuntu上安装依赖：
```bash
sudo apt-get update
sudo apt-get install build-essential libyaml-dev pkg-config python3-dev
```

推荐使用Python虚拟环境：
```bash
python3 -m venv venv
source venv/bin/activate
# 安装开发依赖
pip install -r requirements-dev.txt
```

### 安装

1. 克隆仓库
   ```bash
   git clone https://github.com/yourusername/Logloom.git
   cd Logloom
   ```

2. 编译核心库
   ```bash
   make
   ```

3. 安装库（可选）
   ```bash
   sudo make install
   ```

4. 编译并安装Python绑定（可选）
   ```bash
   cd src/bindings/python
   pip install -e .
   ```

### 验证安装

运行测试套件确认安装成功：

```bash
# C库测试
./run_tests.sh

# Python绑定测试
cd tests/python
python run_tests.py
```

### 在C/C++项目中使用

1. **创建配置文件**

   创建 `config.yaml` 文件:

   ```yaml
   logloom:
     language: "zh"  # 或 "en"
     log:
       level: "DEBUG"  # 可选: DEBUG, INFO, WARN, ERROR, FATAL
       file: "./app.log"
       max_size: 1048576  # 1MB
       console: true
   ```

2. **引入头文件并初始化**

   ```c
   #include <logloom/log.h>
   #include <logloom/lang.h>
   #include <logloom/config.h>

   int main() {
       // 初始化配置
       logloom_config_init("./config.yaml");
       
       // 初始化日志系统
       log_init();
       
       // 使用从配置中加载的设置，或手动设置
       // log_set_level(LOG_LEVEL_DEBUG);
       // log_set_output_file("my_app.log");
       
       // 设置语言
       lang_set_language("zh");  // 或 "en"
       
       // ...应用代码...
       
       return 0;
   }
   ```

3. **记录日志**

   ```c
   // 不同级别的日志
   log_debug("初始化应用程序"); // 调试信息
   log_info("用户 %s 登录系统", username);
   log_warn("检测到异常访问模式");
   log_error("无法连接到数据库: %s", db_error);
   log_fatal("系统崩溃: %d", error_code);
   
   // 带有国际化支持的日志
   log_info("LOGLOOM_USER_LOGIN", username); // 会从语言资源中查找对应的文本
   ```

4. **编译你的程序**

   使用pkg-config（如果已安装Logloom）：
   ```bash
   gcc your_program.c $(pkg-config --cflags --libs logloom) -o yourprogram
   ```

   或者直接指定路径：
   ```bash
   gcc your_program.c -I/path/to/logloom/include -L/path/to/logloom -llogloom -o yourprogram
   ```

### 在Python项目中使用

1. **导入模块**

   ```python
   from logloom import logger, Logger, LogLevel, initialize
   ```

2. **初始化系统**

   ```python
   # 使用配置文件初始化
   initialize("./config.yaml")
   
   # 或手动配置
   root_logger = Logger("app")
   root_logger.set_level(LogLevel.DEBUG)
   root_logger.set_file("app.log")
   ```

3. **使用模块化日志记录**

   ```python
   # 创建特定模块的日志记录器
   db_logger = Logger("database")
   auth_logger = Logger("auth")
   
   # 设置不同的日志级别
   db_logger.set_level(LogLevel.INFO)
   auth_logger.set_level(LogLevel.DEBUG)
   
   # 记录日志
   db_logger.info("数据库连接成功")
   auth_logger.debug("验证请求: {}", request_id)
   auth_logger.warning("用户 {user} 登录失败: {reason}", user="admin", reason="密码错误")
   ```

4. **日志轮转**

   ```python
   # 设置日志轮转（文件大小超过1MB时）
   db_logger.set_rotation_size(1024 * 1024)  # 1MB
   ```

5. **国际化支持**

   ```python
   from logloom import set_language, get_text, format_text
   
   # 设置当前语言
   set_language("zh")  # 或 "en" 
   
   # 获取翻译文本
   welcome_text = get_text("welcome")
   
   # 格式化带参数的文本
   error_text = format_text("error.file_not_found", "/data/config.json")
   user_text = format_text("user.profile", name="张三", age=30)
   ```

### 高级使用

1. **启用插件系统**

   ```c
   // C语言中加载插件
   plugin_init();
   plugin_load_directory("./plugins");
   
   // 处理日志时会自动应用已加载的插件
   log_info("这条日志会经过所有已加载的过滤器和输出插件处理");
   ```

   ```python
   # Python中加载插件
   from logloom import initialize_plugins, load_plugins
   
   initialize_plugins(plugin_dir="./plugins", config_path="./plugin_config.json")
   load_plugins()
   ```

2. **自定义日志格式**

   ```c
   // 设置自定义格式（如果支持）
   log_set_format("[%level%][%time%] %message%");
   ```

3. **多线程环境**

   Logloom在多线程环境中是安全的，不需要额外的锁：

   ```c
   // 在任意线程中记录日志
   log_info("线程 %d 正在处理任务 %s", thread_id, task_name);
   ```

### 运行演示程序

```bash
# 编译并运行示例程序
make demo
./demo
```

查看生成的日志文件（`logloom.log`）或控制台输出。

---

## 📚 技术路线图（Technical Roadmap）

1. **当前 MVP**: 基础日志和国际化功能 ✅
2. **Python绑定与扩展API**: 提供Python语言接口 ✅
3. **API一致性检查与验证**: 确保API稳定性和一致性 ✅
4. 分离内核态和用户空间实现 🚧
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
