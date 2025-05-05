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

