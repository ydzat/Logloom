# 03\_LoggingSystemDesign.md

# Logloom 日志系统详细设计文档

---

## 1. 简介与设计目标（Purpose & Goals）

Logloom 的日志系统负责以统一的格式记录系统运行过程中的关键信息，具备高可读性、可追溯性和国际化能力，支持用户态和内核态的并发调用。设计目标如下：

* ✅ 支持多级别日志输出（debug, info, warn, error）
* ✅ 支持使用多语言 Key 作为模板进行格式化输出
* ✅ 支持控制台与文件双通道输出，可配置启用/禁用
* ✅ 支持日志文件按大小自动轮转，防止无限增长
* ✅ 接口简洁、线程安全、可嵌入内核模块使用

---

## 2. 核心接口设计（Core API）

### 2.1 多语言日志格式接口

```c
void log_debug(const char* lang_key, ...);
void log_info(const char* lang_key, ...);
void log_warn(const char* lang_key, ...);
void log_error(const char* lang_key, ...);
```

* 所有接口都使用语言系统的 key（如 `LOGLOOM_LANG_AUTH_LOGIN_FAILED`）
* 内部通过 `lang_getf()` 获取对应语言格式化文本并写入日志
* 如果语言查询失败或格式化出错，将回退为：

  ```plaintext
  [FORMAT ERROR: ...] [KEY: auth.login_failed]
  ```

### 2.2 配置与控制接口

```c
void log_set_level(int level);                    // 设置全局日志等级
void log_set_output_console(bool enabled);        // 开启/关闭控制台输出
void log_set_output_file(const char* filepath);   // 设置日志输出文件路径
void log_set_max_file_size(size_t max_bytes);     // 设置单文件最大大小，超限轮转
```

* 支持按运行时动态控制输出策略
* 文件输出可设定大小限制（如 1MB），轮转时生成新文件

---

## 3. 日志等级与模块标签设计（Levels & Tags）

### 3.1 日志等级（Log Levels）

日志等级按严重性从低到高定义为：

```c
typedef enum {
    LOG_LEVEL_DEBUG = 0,
    LOG_LEVEL_INFO  = 1,
    LOG_LEVEL_WARN  = 2,
    LOG_LEVEL_ERROR = 3
} log_level_t;
```

* `log_set_level(level)` 可设置最小输出等级，低于该等级的日志将被忽略。
* 默认等级建议为 `LOG_LEVEL_INFO`

### 3.2 模块标签（Module Tags）

每条日志应包含来源模块的标签，方便归类与分析。例如：

```c
[INFO] [CORE] 初始化完成
[WARN] [LANG] 未找到语言条目：xxx
[ERROR] [IO] 文件写入失败
```

* 模块名称建议使用大写英文字母，不超过 8 个字符
* 标签可通过注册机制或静态宏定义设定，例如：

  ```c
  #define LOG_MODULE_TAG "LANG"
  ```

  并在日志实现中自动附加

### 3.3 高级选项（可选）

* 支持运行时动态设置当前模块标签（如线程上下文绑定）
* 日志格式统一为：

  ```plaintext
  [LEVEL] [MODULE] 时间戳 消息内容
  ```

---

## 4. 输出通道与轮转逻辑（Output Channels & Rotation）

### 4.1 控制台输出

* 控制台输出通过 `stdout`（用户态）或 `printk`（内核态）实现
* 可通过 `log_set_output_console(bool)` 开启或关闭
* 每条日志带换行符，适用于实时调试与终端监控

### 4.2 文件输出

* 通过 `log_set_output_file(path)` 设置目标日志文件路径
* 所有日志写入该文件，自动追加
* 若未设置路径或路径非法，则文件输出禁用

### 4.3 日志轮转机制

* 支持按文件大小自动轮转，需配置最大文件大小：

```c
log_set_max_file_size(1024 * 1024); // 1MB 限制
```

* 当日志文件超过设定大小时：

  1. 当前文件重命名为 `log.txt.1`, `log.txt.2`（递增）
  2. 新日志写入 `log.txt`
  3. 可设置最多保留 N 个历史日志（如 5）

### 4.4 示例日志轮转流程

假设配置为：最大 1MB，保留 3 个备份。

```plaintext
log.txt        ← 当前写入文件
log.txt.1      ← 上一份
log.txt.2      ← 再上一份
log.txt.3      ← 最旧，超过后删除
```

### 4.5 文件写入性能注意

* 建议使用缓冲写入（`fwrite` + `fflush` 控制）
* 在内核态需使用 `vfs_write` 或 `kernel_write` 封装接口
* 多线程访问需加锁保护（后续设计同步策略）

---

## 5. 日志缓冲区机制与并发安全策略（Buffering & Concurrency）

### 5.1 是否启用缓冲写入

* 用户态建议使用标准输出缓冲区（如 `fwrite()` + `fflush()`）以减少 I/O 开销。
* 内核态可采用写入缓冲区 + 定时刷新（可选，需权衡内存占用与实时性）。
* 日志缓冲建议由内部维护，外部不感知，默认开启。

### 5.2 缓冲区结构建议

```c
typedef struct {
    char buffer[LOG_BUFFER_SIZE];  // 例如 4096 bytes
    size_t offset;
    bool dirty;
} log_buffer_t;
```

* 每个输出通道（控制台/文件）各维护一个缓冲结构体
* 满或强制刷新（如轮转）时自动写出

### 5.3 并发访问策略（用户态）

* 使用 `pthread_mutex_t log_mutex` 对日志输出临界区加锁
* 保护内容包括：

  * log\_level 判断
  * 多线程写 buffer 和轮转文件
  * 控制台与文件输出过程

### 5.4 并发访问策略（内核态）

* 内核模块中使用 `spinlock_t` 或 `seqlock_t`（不可睡眠上下文）
* 写入函数需避免阻塞操作，特别是在中断上下文中调用时
* 若允许 sleep 环境，可使用 `mutex` 或 `rw_semaphore`

### 5.5 接口设计建议（同步）

```c
void log_lock();    // 显式加锁（如多条连续日志）
void log_unlock();  // 解锁
```

* 对外暴露锁接口为可选项，仅在高级用户场景中暴露（如事务式日志）
* 普通日志调用无需感知锁机制，库内部自动封装

---
## 6. 配置加载与运行时控制机制（Configuration & Runtime Control）

### 6.1 启动时加载配置文件（用户态）

* 日志系统支持从配置文件中加载初始设置，如：

  ```ini
  log_level = INFO
  log_file = /var/log/logloom.log
  log_max_size = 1048576
  log_console = true
  ```
* 可选配置格式：INI / YAML / JSON（建议 INI 简洁易解析）
* 加载函数接口：

```c
void log_load_config(const char* config_path);
```

### 6.2 内核态配置策略

* 内核态不支持动态加载外部文件，可使用：

  * 编译时宏定义（如 `#define LOG_DEFAULT_LEVEL LOG_LEVEL_INFO`）
  * 初始化结构体传参（由上层驱动/模块传入）

### 6.3 运行时动态调整接口

* 日志系统允许运行时调整关键参数：

```c
void log_set_level(int level);
void log_set_output_file(const char* filepath);
void log_set_output_console(bool enabled);
void log_set_max_file_size(size_t bytes);
```

* 更改后立即生效，所有后续日志遵循新配置
* 配置修改线程安全，内部自动加锁同步

### 6.4 获取当前状态（可选接口）

* 提供查询函数获取当前状态（用于调试、状态导出）

```c
int log_get_level();
bool log_is_console_enabled();
const char* log_get_file_path();
size_t log_get_max_file_size();
```

---
## 7. 错误处理与边界行为设计（Error Handling & Edge Cases）

### 7.1 语言模板错误或格式化失败

* 当 `lang_getf()` 返回 NULL 或格式化失败时：

  * 日志内容自动替换为：

    ```plaintext
    [FORMAT ERROR] Key: <lang_key>
    ```
  * 日志系统不会崩溃，确保健壮性

### 7.2 文件写入失败

* 文件路径无权限、磁盘满或句柄失效时：

  * 控制台输出错误信息 `[LOG FILE WRITE FAILED]`
  * 自动禁用文件输出，仅保留控制台日志
  * 可在后续尝试 `log_set_output_file()` 重新开启

### 7.3 轮转失败（重命名失败或新建失败）

* 保留当前日志文件继续写入，并在日志中输出一条错误提示：

  ```plaintext
  [LOG ROTATE FAILED] Will continue appending to current log file.
  ```

### 7.4 配置文件非法 / 缺失

* 无配置文件或配置格式非法时：

  * 使用内置默认配置（等级 INFO，控制台启用，文件关闭）
  * 输出警告日志 `[CONFIG LOAD FAILED, USING DEFAULTS]`

### 7.5 多次初始化 / 重复设置

* 所有初始化函数（如 `log_load_config`, `log_set_*`）具备幂等性
* 多次调用不会重复分配资源或泄露句柄

### 7.6 线程安全异常处理

* 若锁失败（如死锁检测）或内部状态不一致：

  * 使用 `assert()` 抛出开发时警告
  * 或输出 `[INTERNAL LOGGING FAILURE]` 并忽略该条日志（保守失败）

---
## 8. 测试策略与验证流程（Testing and Validation）

### 8.1 测试目标

确保日志系统具备以下特性：

* 多语言模板格式化准确无误
* 日志等级、轮转、通道控制逻辑正常
* 并发环境下日志不丢失、无竞态
* 异常处理分支安全降级

### 8.2 测试类型与方法

| 测试类型  | 内容                                | 方法                   |
| ----- | --------------------------------- | -------------------- |
| 单元测试  | `log_info()`, `log_set_*()` 等接口行为 | 使用断言与 mock 文件系统      |
| 格式化测试 | `lang_getf()` 多参数组合测试             | 构造 YAML + 对比结果字符串    |
| 并发测试  | 多线程连续写日志轮转                        | 使用 `pthread` 模拟高并发场景 |
| 异常测试  | 写盘失败、格式错误、权限丢失                    | 注入故障点、观察 fallback 行为 |
| 性能测试  | 轮转与写入频率性能统计                       | 加入时间戳、日志吞吐量计量        |

### 8.3 自动化建议

* 提供 `make test-log` 测试入口，执行：

  * 生成测试 YAML 模板
  * 执行日志轮转与异常验证脚本
  * 输出结果统一比对（含 diff、内容校验）
* CI 集成建议（GitHub Actions/GitLab CI）：

  * 每次提交时验证日志格式、输出行为、构建可用性
  * 对比日志样本与 golden file，检查一致性
