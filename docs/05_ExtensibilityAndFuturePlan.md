# 05\_ExtensibilityDesign.md

# Logloom 扩展与接入层设计文档

---

## 1. 简介与目标（Purpose & Goals）

Logloom 的架构设计支持模块化与可插拔能力，允许用户在不修改核心代码的前提下扩展其功能。
扩展机制不仅适用于语言与日志的增强，也包括 AI 分析、远程通信、格式导出等高级功能。

扩展目标如下：

* ✅ 支持用户态模块的 **插件式接入**（C语言 `.so` 动态库 + Python 脚本）
* ✅ 支持**独立进程/容器插件**，与主程序通过 socket / IPC 交互
* ✅ 接口标准化，便于版本管理与插件兼容性维护
* ✅ 内核态禁止动态扩展，仅允许静态构建绑定模块
* ✅ 支持典型扩展如：日志导出、AI 总结、语言工具链、远程日志聚合等

---

## 2. 扩展机制分类（Extension Types）

Logloom 支持如下三类插件扩展机制，按生命周期与隔离等级划分：

### 2.1 `.so` 动态库插件（C 插件）

* 主程序通过 `dlopen()` + `dlsym()` 方式加载动态库
* 每个插件需实现标准初始化与处理接口，如：

```c
int plugin_init();
int plugin_process(const log_entry_t* entry);
```

* 适用于：日志过滤器、导出器、多语言模块注册器等高性能插件

### 2.2 Python 插件（脚本插件）

* 使用嵌入式 Python 或子进程 `python3 script.py` 方式加载
* 适用于轻量分析器、AI 模块（如 log summary、异常检测）
* 可通过 `subprocess`, `socket` 或 `jsonrpc` 进行通信

### 2.3 独立进程/容器插件

* 插件以服务形式运行，主程序通过 IPC、TCP、UNIX socket 等协议通信
* 适用于安全隔离、跨语言（如 Rust, Go, Java）或云端部署场景
* 推荐插件类型：`log_aggregator`, `log_ai_recommender`, `lang_sync_service`

---

## 3. 扩展接口设计（Extension Interfaces）

为了保证插件的可管理性、跨语言兼容性与功能扩展性，Logloom 定义了一套统一的插件接口标准。
接口设计遵循以下核心原则：

* 接口尽可能稳定、可版本化
* 插件行为应可声明（描述能力、用途、钩子类型）
* 插件数据结构统一、具备 JSON 映射能力

---

### 3.1 插件分类与职责

| 插件类型     | 典型用途        | 接口风格                    |
| -------- | ----------- | ----------------------- |
| `filter` | 日志预处理、关键字筛选 | 同步调用 `filter(entry)`    |
| `sink`   | 导出日志到文件/远程  | 批处理 `flush(entries[])`  |
| `ai`     | AI 总结、异常检测  | 请求-响应 `analyze(entry)`  |
| `lang`   | 提供动态语言资源    | 查询型 `resolve(lang_key)` |

插件可声明其 `type` 与支持的 `capability`，主程序根据类型注册合适钩子。

---

### 3.2 通用接口规范（语言无关）

所有插件均应遵守以下通用接口原型（以伪代码表示）：

```text
init() → int
process(payload: object) → int / object
shutdown() → void
info() → PluginInfo  // 可选
```

* `init()`：初始化资源、配置环境
* `process(payload)`：根据插件类型处理日志或请求
* `shutdown()`：释放资源，正常退出
* `info()`：返回插件元信息（结构见下）

---

### 3.3 插件元信息（PluginInfo）结构

用于主程序识别插件能力、版本与用途：

```json
{
  "name": "log_exporter_kafka",
  "version": "1.2.0",
  "author": "Logloom Team",
  "type": "sink",
  "capability": ["json", "batch"]
}
```

---

### 3.4 日志数据结构标准

所有插件处理的输入都应遵循如下结构（等价于 C 中的 `log_entry_t`）：

```json
{
  "timestamp": "2025-04-30T12:00:00Z",
  "level": "INFO",
  "module": "CORE",
  "message": "User logged in",
  "lang_key": "auth.login"
}
```

> 插件不得修改原始日志内容，仅可读取、复制、转发

---

### 3.5 C 插件接口映射（动态库）

```c
int plugin_init();
int plugin_process(const log_entry_t* entry);  // 或 batch variant
void plugin_shutdown();
const plugin_info_t* plugin_info();            // 可选
```

* 插件通过 `dlopen()` 动态加载，使用 `dlsym()` 解析函数符号
* 插件需使用 C ABI，避免 C++ name mangling 问题

---

### 3.6 Python 插件接口映射（子进程 / 嵌入）

```python
def plugin_init():
    ...

def plugin_process(entry: dict) -> Union[int, dict]:
    ...

def plugin_shutdown():
    ...

def plugin_info() -> dict:
    ...
```

* 主程序通过 `subprocess.Popen()` 或嵌入式解释器启动插件
* 通信协议为 `stdin/stdout`（行分隔 JSON）或 socket

---

## 4. 模块注册与发现机制（Registration & Discovery）

### 4.1 插件目录扫描机制

* 主程序在启动时从默认插件目录加载所有可用模块：

  * Linux: `/usr/lib/logloom/plugins/`
  * Windows: `C:\\Program Files\\Logloom\\plugins\\`
* 插件以命名规范识别类型：如 `filter_*.so`、`sink_*.py`
* 支持通过配置文件指定插件加载路径列表

### 4.2 静态注册方式（可选）

* 在资源受限场景（如嵌入式）可使用编译期注册表机制：

```c
extern plugin_entry_t plugin_example;
register_plugin(&plugin_example);
```

* 静态注册机制通过链接器集或初始化列表完成聚合

### 4.3 插件加载验证流程

加载每个插件时需验证：

* 所有必要函数是否导出（`init`, `process`, `shutdown`）
* 插件元信息合法（字段完整、版本可识别）
* 插件类型是否与系统注册钩子匹配

加载失败时应输出如下警告：

```text
[WARN] Failed to load plugin 'log_exporter_kafka.so': missing plugin_process()
```

### 4.4 插件启用控制

* 插件是否启用由配置文件控制，如：

```yaml
plugins:
  enabled:
    - log_exporter_kafka
    - log_summary_ai
```

* 支持在运行时动态禁用某类插件（如 debug-only 工具）

---

## 5. 插件通信与调用方式（Plugin Invocation & Communication）

### 5.1 同步与异步调用模型

| 调用模式        | 适用插件             | 描述                       |
| ----------- | ---------------- | ------------------------ |
| 同步调用（Sync）  | `filter`, `lang` | 调用后立即返回处理结果，主程序阻塞等待      |
| 异步调用（Async） | `ai`, `sink`     | 插件处理任务后异步通知或写入队列，主程序继续执行 |

> 插件类型需在元信息中标明其调用方式：`"mode": "sync" / "async"`

---

### 5.2 通信协议（跨语言插件）

#### 5.2.1 Python 插件（子进程模式）

* 使用 `stdin/stdout` 传输 JSON 格式日志数据
* 主程序每次发送一行 JSON 请求，插件输出响应 JSON
* 推荐使用“行分隔 JSON”（LDJSON）格式

```bash
主程序：{"entry": {"message": "..."}}
插件返回：{"status": 0}
```

#### 5.2.2 独立进程插件

* 支持通过以下传输协议之一：

  * Unix socket（默认推荐）
  * TCP socket（远程插件）
  * gRPC / JSON-RPC（如需结构化服务定义）

> 插件启动后监听预定义端口或 socket 文件路径

---

### 5.3 插件容错与失败处理

* 若插件通信失败（子进程崩溃、socket 断开）：

  * 主程序记录 `[ERROR] Plugin communication failed` 日志
  * 可设定超时重试机制，或将插件标记为失效

* 若插件返回非法格式 / 空响应：

  * 视为插件错误，主程序不采用其结果

* 插件可在响应中主动返回状态码，如：

```json
{"status": 0, "message": "ok"}
{"status": 1, "error": "invalid input"}
```

---

### 5.4 批处理与流式处理支持

* `sink` 类型插件可支持批量传输多个日志条目：

```json
{"batch": [log1, log2, log3]}
```

* `ai` 插件可选择“流式响应”模式（逐条返回分析结果）

---

### 5.5 Python插件系统详细设计（Python Plugin System Design）

Python插件系统是Logloom的核心扩展机制之一，允许用户使用Python编写插件，无需编译即可扩展系统功能。本节详细说明Python插件的设计、加载机制、通信协议、资源管理和安全策略。

#### 5.5.1 Python插件架构

Python插件系统由以下组件组成：

1. **Python解释器接口**：负责初始化、管理和与Python解释器交互
   - 嵌入式模式：使用C API嵌入Python解释器到Logloom进程
   - 子进程模式：独立Python进程，通过管道或套接字通信

2. **插件发现与加载器**：扫描指定目录，加载符合规范的Python脚本
   - 支持热加载、重载和卸载
   - 自动处理依赖关系

3. **类型转换与桥接层**：在C/C++与Python之间转换数据结构
   - 日志项转换为Python字典
   - 异常转换与处理

4. **生命周期管理器**：控制Python插件的初始化、执行和销毁
   - 启动时加载
   - 按需执行
   - 优雅关闭

#### 5.5.2 Python插件标准接口

每个Python插件必须实现以下标准接口：

```python
"""Logloom插件模板"""
# 插件元信息
PLUGIN_INFO = {
    "name": "example_python_plugin",
    "version": "1.0.0",
    "type": "filter",  # 可选值: filter, sink, ai, lang
    "capability": ["text", "json"],
    "author": "Logloom Team",
    "description": "示例Python插件"
}

def plugin_init():
    """初始化插件，设置必要资源"""
    # 返回0表示成功，非0表示失败
    return 0

def plugin_process(entry):
    """处理日志条目
    
    参数:
        entry: dict - 日志条目字典
        
    返回:
        处理结果，取决于插件类型:
        - filter: bool（是否保留日志）
        - sink: int（成功为0，失败为错误码）
        - ai: dict（分析结果）
        - lang: str（翻译结果）
    """
    # 示例：过滤掉DEBUG级别的日志
    if entry.get('level') == 'DEBUG':
        return False
    return True

def plugin_shutdown():
    """清理插件资源"""
    # 释放所有资源
    pass
```

#### 5.5.3 Python插件加载与生命周期

Python插件的完整生命周期如下：

1. **发现阶段**:
   - 扫描`plugins/python/`目录下的所有`.py`文件
   - 读取每个文件的`PLUGIN_INFO`字典验证合法性
   - 将有效插件添加到注册表

2. **初始化阶段**:
   - 导入Python模块
   - 调用`plugin_init()`
   - 检查返回值确认初始化成功

3. **执行阶段**:
   - 根据插件类型，在适当时机调用`plugin_process()`
   - 对调用结果进行验证和类型转换
   - 在子进程模式下使用JSON序列化消息传递

4. **卸载阶段**:
   - 调用`plugin_shutdown()`
   - 清理Python对象引用
   - 释放解释器资源（嵌入式模式）或终止子进程

#### 5.5.4 通信模式与数据交换

##### 嵌入式模式

```c
// C库中的嵌入式Python插件调用示例
PyObject *pModule, *pFunc, *pArgs, *pValue;
// ...初始化Python解释器...

// 构造日志条目字典
PyObject *py_entry = PyDict_New();
PyDict_SetItemString(py_entry, "level", PyUnicode_FromString(entry->level));
PyDict_SetItemString(py_entry, "message", PyUnicode_FromString(entry->message));

// 调用插件处理函数
pFunc = PyObject_GetAttrString(pModule, "plugin_process");
pArgs = PyTuple_Pack(1, py_entry);
pValue = PyObject_CallObject(pFunc, pArgs);

// 处理返回值
if (PyBool_Check(pValue)) {
    return PyObject_IsTrue(pValue) ? 1 : 0;
}
```

##### 子进程模式

```python
# 子进程模式中的通信协议（伪代码）
def plugin_subprocess_main():
    while True:
        # 从stdin读取JSON数据
        input_line = sys.stdin.readline().strip()
        if not input_line:
            break
            
        try:
            # 解析输入
            request = json.loads(input_line)
            entry = request.get("entry", {})
            
            # 处理日志
            result = plugin_process(entry)
            
            # 返回结果
            response = {"status": 0, "result": result}
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except Exception as e:
            # 错误处理
            error_response = {"status": 1, "error": str(e)}
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()
```

#### 5.5.5 资源管理与性能优化

1. **缓存机制**:
   - 保持Python解释器实例长期运行（嵌入式模式）
   - 批处理多个日志条目减少进程切换开销（子进程模式）
   - 预编译频繁执行的Python函数

2. **内存管理**:
   - 定期调用`Py_DecRef`和垃圾回收防止内存泄漏
   - 限制Python堆内存使用（通过`sys.setrecursionlimit`和资源限制）

3. **性能监控**:
   - 记录每个插件的执行时间和资源消耗
   - 对超时或高资源消耗插件发出警告

#### 5.5.6 安全与沙箱机制

为确保Python插件不影响系统安全性和稳定性，实现以下安全措施：

1. **权限控制**:
   - 使用`RestrictedPython`或类似库限制Python代码访问系统资源
   - 移除危险模块(`os.system`, `subprocess`, `socket`等)
   - 限制文件系统访问范围

2. **资源限制**:
   - 设置执行超时（默认500ms）
   - 内存使用上限（默认100MB）
   - CPU时间限制

3. **沙箱执行**:
   - 子进程模式下使用低权限用户执行
   - 可选容器化运行环境（Docker或系统容器）

4. **代码审查**:
   - 插件可选静态分析检测潜在风险
   - 自动检测无限循环、阻塞I/O等问题

#### 5.5.7 Python插件注册与配置

Python插件使用YAML配置启用和配置，集成到Logloom主配置中：

```yaml
# config.yaml - Python插件配置示例
plugins:
  python:
    enabled: true
    mode: "subprocess"  # 'embedded'或'subprocess'
    path: "plugins/python"
    enabled_plugins:
      - "log_filter_severity"
      - "log_ai_summary"
    timeout: 500  # 毫秒
    max_memory: 100  # MB
    sandbox: true
```

每个Python插件可以有自己的配置文件：
```yaml
# plugins/python/log_ai_summary.yaml
model: "local-llm"
batch_size: 100
summary_interval: 3600  # 每小时生成一次摘要
```

#### 5.5.8 Python插件开发工具链

为方便用户开发Python插件，提供以下工具和资源：

1. **插件模板生成器**:
   ```bash
   logloom-cli create-plugin --type python --name "my_plugin"
   ```

2. **插件开发环境**:
   - 提供虚拟环境设置脚本
   - 包含类型提示和接口定义

3. **调试工具**:
   - 独立测试工具模拟Logloom环境
   - 日志记录和性能分析功能

4. **文档与示例**:
   - 常见插件模式库
   - 最佳实践文档

#### 5.5.9 实现示例

##### 日志过滤器插件示例

```python
# plugins/python/log_filter_severity.py
"""基于严重性过滤日志的插件"""

PLUGIN_INFO = {
    "name": "log_filter_severity",
    "version": "1.0.0",
    "type": "filter",
    "capability": ["text"],
    "author": "Logloom Team",
    "description": "根据日志级别过滤日志条目"
}

# 插件配置：默认过滤掉DEBUG级别的日志
config = {
    "min_level": "INFO"  # 可选值: DEBUG, INFO, WARN, ERROR, FATAL
}

# 日志级别映射到数值
LEVEL_MAP = {
    "DEBUG": 0,
    "INFO": 1,
    "WARN": 2,
    "ERROR": 3,
    "FATAL": 4
}

def plugin_init():
    """初始化插件"""
    # 这里可以加载自定义配置文件
    return 0

def plugin_process(entry):
    """
    根据配置的最低日志级别过滤日志
    返回True表示保留日志，False表示过滤掉
    """
    entry_level = entry.get("level", "INFO")
    min_level = config.get("min_level", "INFO")
    
    # 将级别转换为数值进行比较
    entry_level_value = LEVEL_MAP.get(entry_level, 1)
    min_level_value = LEVEL_MAP.get(min_level, 1)
    
    # 只保留级别大于等于最低级别的日志
    return entry_level_value >= min_level_value

def plugin_shutdown():
    """清理资源"""
    pass
```

##### AI分析插件示例

```python
# plugins/python/log_ai_summary.py
"""日志AI摘要插件"""

PLUGIN_INFO = {
    "name": "log_ai_summary",
    "version": "1.0.0",
    "type": "ai",
    "capability": ["json", "batch"],
    "author": "Logloom Team",
    "description": "使用AI分析日志并生成摘要"
}

import json
import time
from collections import deque

# 保存最近的日志
log_buffer = deque(maxlen=1000)
last_summary_time = 0
summary_interval = 3600  # 默认每小时生成一次摘要

def plugin_init():
    """初始化插件，加载AI模型"""
    global summary_interval
    
    try:
        # 尝试加载配置
        with open("plugins/python/log_ai_summary.yaml", "r") as f:
            import yaml
            config = yaml.safe_load(f)
            if "summary_interval" in config:
                summary_interval = config["summary_interval"]
                
        # 初始化AI模型（示例）
        # model = load_ai_model()
        return 0
    except Exception as e:
        print(f"初始化AI摘要插件失败: {e}")
        return 1

def plugin_process(entry):
    """处理日志条目，定期生成摘要"""
    global log_buffer, last_summary_time
    
    # 将日志加入缓冲区
    log_buffer.append(entry)
    
    current_time = time.time()
    # 检查是否应该生成摘要
    if current_time - last_summary_time >= summary_interval and len(log_buffer) > 0:
        return generate_summary(list(log_buffer))
    
    # 返回空结果表示暂不生成摘要
    return {"summary": None}

def generate_summary(logs):
    """生成日志摘要"""
    # 实际实现中，这里会调用LLM或其他AI模型
    # 简化示例：统计不同级别的日志数量
    level_counts = {}
    for log in logs:
        level = log.get("level", "INFO")
        level_counts[level] = level_counts.get(level, 0) + 1
    
    # 检测异常模式
    error_count = level_counts.get("ERROR", 0) + level_counts.get("FATAL", 0)
    has_errors = error_count > 0
    
    # 更新最后摘要时间
    global last_summary_time
    last_summary_time = time.time()
    
    # 返回摘要
    return {
        "summary": f"过去{summary_interval//60}分钟内共记录{len(logs)}条日志",
        "statistics": level_counts,
        "has_errors": has_errors,
        "error_count": error_count,
        "timestamp": last_summary_time
    }

def plugin_shutdown():
    """清理资源"""
    global log_buffer
    log_buffer.clear()
    # 释放AI模型资源
    # unload_ai_model()
    pass
```

#### 5.5.10 Python插件系统与现有C插件系统的互操作

Python插件系统与现有C插件系统完全兼容，并可进行互操作：

1. **链式处理**:
   - Python插件可与C插件组成处理链
   - 定义明确的执行顺序，例如`filter_c → filter_python → sink_c`

2. **混合模式集成**:
   - Python插件可调用C插件（通过Python绑定）
   - C插件可触发Python回调（嵌入式模式）

3. **数据格式兼容**:
   - 保持日志条目结构一致性
   - 统一错误码和状态报告

4. **资源协调**:
   - 统一的插件管理接口
   - 共享配置系统

---

## 6. 扩展场景示例（Examples of Extensibility）

以下展示几种典型插件的实现与接入方式，用于说明 Logloom 插件机制的可行性与灵活性。

---

### 6.1 日志导出插件：`log_exporter_kafka`

* 类型：`sink`
* 功能：将日志以 JSON 格式写入 Kafka 队列中
* 接入方式：

  * C 插件，编译为 `liblog_exporter_kafka.so`
  * 主程序通过配置启用插件并批量传输日志数据
* 示例接口实现：

```c
int plugin_process(const log_entry_t* entry) {
    kafka_send(entry_to_json(entry));
    return 0;
}
```

---

### 6.2 AI 总结插件：`log_summary_ai`

* 类型：`ai`
* 功能：分析最近日志内容，生成关键摘要或异常提示
* 接入方式：

  * Python 插件（子进程），读取日志 JSON 数据，调用 LLM 模型处理
  * 与主程序通过 stdin/stdout 或 socket 通信
* 示例响应：

```json
{
  "status": 0,
  "summary": "Multiple auth failures from IP 192.168.0.5"
}
```

---

### 6.3 多语言热加载工具：`lang_hot_reload`

* 类型：`lang`
* 功能：支持通过插件动态提供翻译条目，配合在线编辑器实时修改语言包
* 接入方式：

  * Python 插件，监听文件系统或 REST API 修改
  * 实现 `resolve(lang_key)` 方法，根据 key 查找对应翻译

---

### 6.4 远程聚合服务：`log_aggregator_remote`

* 类型：`sink`
* 功能：收集各个 Logloom 节点的日志并聚合上传至中央服务器
* 接入方式：

  * 独立进程或容器，通过 TCP 与主程序通信
  * 支持断线重连与离线缓存

---

### 6.5 插件调试工具：`plugin_logger`

* 类型：`filter`
* 功能：记录插件传入与输出数据，协助开发与调试
* 接入方式：

  * C 插件或 Python 插件，作为透明中间层插入管道
  * 自动记录每条日志调用链上下文与执行耗时

---

## 7. 插件安全性与资源隔离设计（Security & Isolation）

为了保证主程序的稳定性与安全性，Logloom 插件系统在设计时需考虑：

* 插件运行的失败隔离（防止崩溃影响主程序）
* 插件的执行资源限制（防止卡死或过载）
* 插件访问系统资源的权限控制

---

### 7.1 错误与崩溃隔离

| 插件类型      | 隔离策略                        |
| --------- | --------------------------- |
| `.so` 动态库 | 每次调用插件前捕获异常状态（如信号）并恢复主程序流程  |
| Python 插件 | 运行在独立子进程中，主程序监控其退出状态        |
| 独立进程      | 与主程序物理隔离，使用 socket 通信，崩溃无影响 |

---

### 7.2 执行资源限制

* **执行时间限制**：主程序对每次插件调用设置最大超时时间（如 500ms）
* **内存限制**：对于 Python 插件或外部进程可使用 cgroup / ulimit 设定最大内存
* **并发数量限制**：防止插件批量请求造成拥塞，限制最大调用线程数或队列长度

---

### 7.3 脚本型插件安全沙箱

* 禁用 Python 中危险模块（如 `os`, `subprocess`, `socket`）
* 运行 Python 插件时使用降权用户（如 `nobody`）执行
* 建议使用 `Pyodide`、`MicroPython` 等嵌入式解释器构建插件沙箱（可选）

---

### 7.4 独立服务插件隔离建议

* 使用容器化部署（如 Docker）限制插件资源与网络权限
* 插件使用私有端口或 Unix Socket 与主程序通信，避免暴露端口
* 插件输出均需经主程序验签或格式校验，避免日志注入等攻击

---

### 7.5 插件签名与验证（可选功能）

* 支持为插件 `.so` 文件或 `.py` 脚本生成 SHA256 签名
* 主程序加载前校验插件签名，防止篡改与注入
* 支持公钥签名机制以实现发布认证链（需构建工具链支持）

---

## 8. 测试与验证策略（Testing & Validation）

为保障插件机制的正确性、兼容性与安全性，需构建完备的测试流程，涵盖单元测试、集成测试、动态行为验证与异常场景模拟。

---

### 8.1 测试目标

* 验证插件加载、初始化、处理、卸载流程是否正常
* 验证插件间行为独立性与数据一致性
* 验证跨语言插件接口规范一致性
* 验证通信协议、超时机制、资源限制是否生效
* 验证主程序在插件崩溃、异常响应等场景下的容错能力

---

### 8.2 测试类型与策略

| 测试类型 | 内容                          | 工具/方式                    |
| ---- | --------------------------- | ------------------------ |
| 单元测试 | `plugin_process()` 返回值与行为测试 | GTest / Pytest           |
| 接口测试 | 跨语言插件通信协议、字段校验              | mock 插件 / socket stub    |
| 崩溃模拟 | 插件崩溃或返回非法 JSON              | 信号注入 / 断开 socket         |
| 性能测试 | 批量调用性能、插件处理延迟               | benchmark harness        |
| 并发测试 | 多线程并发调用插件                   | thread stress test       |
| 沙箱测试 | 限权执行插件行为验证                  | Docker / ulimit / cgroup |

---

### 8.3 自动化测试建议

* 提供统一测试入口脚本 `make test-plugins`
* 所有测试用例应覆盖：

  * 至少一个 `.so` 插件、一个 Python 插件、一个 socket 服务插件
  * 正常执行 + 失败回退 + 限权执行等场景
* 集成测试用例使用虚拟插件模拟插件注册/卸载/替换流程
* 测试时动态生成日志输入，验证输出内容一致性

---

### 8.4 CI/CD 集成建议

* 所有插件在合入主干前应通过插件接口一致性测试
* 提供构建后插件签名验证测试（签名校验通过）
* 插件仓库应定义：

  * `plugin.yaml` 描述插件元信息与入口点
  * 自动发布测试容器镜像 / `.so` 文件

---

## 9. Python插件开发与部署指南（Python Plugin Development Guide）

为了便于开发者快速上手Python插件开发，本节提供了完整的开发流程、最佳实践和部署指南。

### 9.1 Python插件开发环境设置

开发Python插件前，建议按以下步骤设置开发环境：

1. **安装依赖**:
   ```bash
   # 创建虚拟环境
   python -m venv logloom-plugin-env
   source logloom-plugin-env/bin/activate
   
   # 安装开发依赖
   pip install pyyaml pytest mock
   ```

2. **获取接口定义**:
   ```bash
   # 克隆或下载Logloom插件开发包
   git clone https://github.com/logloom/plugin-sdk.git
   cd plugin-sdk/python
   pip install -e .
   ```

3. **使用插件模板**:
   ```bash
   # 生成插件模板
   logloom-plugin-sdk create --type filter --name "my_custom_filter"
   ```

### 9.2 Python插件结构与规范

一个完整的Python插件项目应包含以下文件：

```
my_plugin/
│
├── __init__.py          # 主插件代码
├── plugin.yaml          # 插件配置
├── requirements.txt     # 依赖项
├── README.md            # 文档
└── tests/               # 测试代码
    └── test_plugin.py
```

#### 插件包命名约定

- 不同类型的插件应使用特定前缀：
  - `filter_*` - 过滤器插件
  - `sink_*` - 输出插件
  - `ai_*` - AI分析插件
  - `lang_*` - 多语言插件

#### 版本控制规范

使用语义化版本控制（SemVer）：
- MAJOR.MINOR.PATCH
- 主要版本号变化表示不兼容的API变更
- 次要版本号变化表示向后兼容的功能性新增
- 修订号变化表示向后兼容的问题修正

### 9.3 Python插件测试

#### 单元测试

```python
# tests/test_filter_plugin.py
import unittest
import sys
from unittest import mock

# 导入插件模块
sys.path.insert(0, '..')
import my_custom_filter

class TestMyCustomFilter(unittest.TestCase):
    
    def setUp(self):
        # 初始化插件
        my_custom_filter.plugin_init()
    
    def tearDown(self):
        # 清理资源
        my_custom_filter.plugin_shutdown()
    
    def test_filter_debug_logs(self):
        # 准备测试数据
        debug_log = {"level": "DEBUG", "message": "Debug message"}
        info_log = {"level": "INFO", "message": "Info message"}
        
        # 验证过滤器行为
        self.assertFalse(my_custom_filter.plugin_process(debug_log))
        self.assertTrue(my_custom_filter.plugin_process(info_log))
    
    def test_plugin_info(self):
        # 验证插件元信息
        self.assertIn("name", my_custom_filter.PLUGIN_INFO)
        self.assertIn("version", my_custom_filter.PLUGIN_INFO)
        self.assertEqual("filter", my_custom_filter.PLUGIN_INFO["type"])

if __name__ == '__main__':
    unittest.main()
```

#### 集成测试

```python
# tests/test_integration.py
import unittest
import subprocess
import json
import os

class TestPluginIntegration(unittest.TestCase):
    
    def test_subprocess_mode(self):
        """测试子进程模式下的插件响应"""
        test_log = {"level": "INFO", "message": "Test message"}
        
        # 启动插件子进程
        proc = subprocess.Popen(
            ['python', '../my_custom_filter.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        
        # 发送测试数据
        proc.stdin.write(json.dumps({"entry": test_log}) + "\n")
        proc.stdin.flush()
        
        # 读取响应
        response = proc.stdout.readline()
        result = json.loads(response)
        
        # 验证结果
        self.assertEqual(0, result.get("status"))
        self.assertTrue(result.get("result"))
        
        # 清理
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    unittest.main()
```

### 9.4 部署与分发指南

#### 插件打包

```bash
# 创建Python wheel包
pip install wheel
python setup.py sdist bdist_wheel
```

#### 插件安装

```bash
# 全局安装
pip install logloom-plugin-myfilter-1.0.0.whl

# 或复制到Logloom插件目录
cp -r my_custom_filter/ /usr/lib/logloom/plugins/python/
```

#### 容器化部署

```dockerfile
# Dockerfile - 插件容器
FROM python:3.9-slim

WORKDIR /plugin
COPY . /plugin/

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "my_custom_filter.py"]
```

### 9.5 故障排查与调试

#### 常见问题解决方案

1. **插件未被加载**:
   - 检查配置中是否启用了该插件
   - 验证插件位置是否正确
   - 检查`PLUGIN_INFO`字典是否完整

2. **插件执行错误**:
   - 启用日志调试模式: `LOG_LEVEL=DEBUG`
   - 检查Python版本兼容性
   - 验证所有依赖是否已安装

#### 调试技巧

1. **独立测试**:
   ```bash
   # 独立运行插件进行测试
   echo '{"entry":{"level":"INFO","message":"test"}}' | python my_plugin.py
   ```

2. **使用日志**:
   ```python
   # 在插件中添加日志
   import logging
   logging.basicConfig(filename="plugin_debug.log", level=logging.DEBUG)
   logging.debug("处理日志条目: %s", entry)
   ```

3. **检查内存使用**:
   ```python
   # 在插件中监控内存使用
   import resource
   def log_memory_usage():
       usage = resource.getrusage(resource.RUSAGE_SELF)
       return f"内存使用: {usage.ru_maxrss / 1024} MB"
   ```

### 9.6 最佳实践

1. **性能优化**:
   - 避免每次处理时导入重量级库
   - 利用缓存减少重复计算
   - 处理批量日志而不是单条处理

2. **可靠性**:
   - 捕获所有可能的异常
   - 设置超时限制防止长时间运行
   - 实现优雅的失败处理

3. **兼容性**:
   - 支持Python 3.6+
   - 显式声明所有依赖
   - 使用标准库优先，减少第三方依赖

4. **可维护性**:
   - 遵循PEP 8编码风格
   - 添加完整的类型注解
   - 编写详细文档

---

## 10. 插件生态系统与社区贡献（Plugin Ecosystem）

### 10.1 官方与社区插件

Logloom维护一个插件仓库，包含官方提供和社区贡献的插件。插件分类包括：

- **官方核心插件**：由Logloom团队维护的基础功能插件
- **官方扩展插件**：由Logloom团队维护的高级功能插件
- **认证社区插件**：经过审核的高质量社区插件
- **实验性插件**：新特性和实验性功能

### 10.2 插件发布与共享

社区成员可通过以下流程贡献插件：

1. 使用标准模板开发插件
2. 提供完整文档和测试
3. 提交插件到Logloom插件仓库
4. 通过审核后发布到插件目录

### 10.3 插件版本管理与兼容性策略

为确保系统稳定和插件生态健康，Logloom采用以下版本管理策略：

- Logloom核心API使用语义化版本控制
- 明确每个API的稳定性级别（稳定、测试中、实验性）
- 废弃的API保持向后兼容至少一个主要版本周期
- 插件声明支持的Logloom版本范围

### 10.4 插件生态系统路线图

Logloom计划逐步扩展插件生态系统的能力：

- 插件市场：一键发现与安装插件
- 插件评分与评论系统
- 插件互操作性框架：允许插件之间协作
- 插件健康监控：自动检测性能问题和兼容性

