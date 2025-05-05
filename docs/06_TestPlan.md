# 06\_TestPlan.md

# Logloom 测试计划与验证方案

---

## 1. 测试目标（Objectives）

本测试计划旨在确保 Logloom 系统在功能性、稳定性、兼容性与可扩展性等方面达到预期目标。目标包括：

* 验证国际化系统是否能准确加载语言资源并格式化输出
* 验证日志系统是否能正确记录结构化信息、按等级与模块分类输出
* 验证配置系统能安全加载、正确注入参数，并在缺失配置下使用默认值
* 验证插件系统能正确注册、调用、隔离运行时异常
* 验证系统在边界条件下的稳定性与容错能力

---

## 2. 测试范围划分（Scope Overview）

Logloom 的测试工作分为以下五大范围，覆盖用户态与内核态的不同模块：

### 2.1 单元测试（Unit Testing）

* 范围：函数级别的行为验证，覆盖核心模块逻辑，如日志格式构造、语言查找、配置解析等
* 工具：GTest（C）、Unity（嵌入式）、Pytest（Python 插件）

### 2.2 集成测试（Integration Testing）

* 范围：验证多个模块协同工作行为，如日志模块调用语言模块输出格式化信息、插件读取配置等
* 用例：

  * 语言模块 + 配置模块联合验证默认语言回退逻辑
  * 插件加载 + 日志模块调用数据通路是否通畅

### 2.3 边界与异常测试（Edge & Fault Testing）

* 范围：测试系统在极限条件、配置缺失、IO 错误等场景下的表现
* 场景示例：

  * 加载无效 YAML 文件 / 缺少关键字段
  * 插件处理超时 / 返回格式不合法
  * 日志文件写入权限丢失 / 日志轮转失败

### 2.4 性能与压力测试（Performance & Stress Testing）

* 范围：测量日志吞吐量、插件响应延迟、配置加载时间等关键指标
* 工具建议：valgrind、perf、custom stress harness（可与日志系统对接）
* 场景：并发写日志 + 插件并发处理 1000 条每秒

### 2.5 用户态与内核态测试区分

| 模块   | 用户态测试                | 内核态测试                      |
| ---- | -------------------- | -------------------------- |
| 配置系统 | ✅ 动态加载 YAML、合并默认值    | ✅ 编译期头文件值正确性               |
| 日志系统 | ✅ 控制台/文件输出格式与等级测试    | ✅ 内核 printk 替换与 buffer 正确性 |
| 语言系统 | ✅ 多语言查找与 fallback 测试 | ❌ （依赖用户态资源加载）              |
| 插件系统 | ✅ Python/C 插件加载与交互测试 | ❌ 禁止动态插件（不适用）              |

---

## 3. 测试用例设计规范（Test Case Design Guideline）

### 3.1 用例命名规范

* 格式：`[模块]_[功能]_[条件]_[预期结果]`
* 示例：

  * `lang_load_zh_valid_success`
  * `log_file_append_no_permission_fallback_console`
  * `plugin_python_timeout_trigger_recovery`

### 3.2 测试用例结构

每个测试用例应包含如下字段：

```yaml
test_id: TC_LOG_001
title: 日志等级过滤测试
description: 验证 INFO 等级日志不会打印 DEBUG 内容
module: logging
precondition:
  - 设置等级为 INFO
steps:
  - log_debug("should be skipped")
  - log_info("should be kept")
expected:
  - 日志文件中只包含 INFO 内容
```

### 3.3 输入输出规范

* 输入文件命名格式：`test_<模块>_<用例ID>.in.yaml`
* 输出比对文件：`test_<模块>_<用例ID>.out.log`
* 支持 golden file 对比机制：测试通过 = 输出与 golden 完全一致

### 3.4 用例分类标签

每个用例可打标签以便自动筛选运行：

```yaml
tags:
  - integration
  - plugin
  - linux-only
```

* 支持 make 过滤：如 `make test TAGS=plugin`

---

## 4. 测试执行与自动化策略（Execution & Automation）

### 4.1 测试入口与目录结构

建议标准化如下目录结构：

```
tests/
├── unit/
│   ├── test_config.c
│   ├── test_lang.c
├── integration/
│   ├── config_lang/
│   ├── log_plugin/
├── data/
│   ├── test_logging_TC_LOG_001.in.yaml
│   ├── test_logging_TC_LOG_001.out.log
```

* 所有测试均可通过 `make test` 统一入口执行
* 支持 `make test-unit`, `make test-integration`, `make test TAGS=ai`

### 4.2 自动化执行机制

* 使用 Python/C 测试驱动程序执行测试用例：

  * 加载输入 → 初始化模块 → 执行步骤 → 捕获输出 → 比对结果
* 支持增量测试：按 Git diff 判断受影响模块自动运行相关用例
* 支持输出 JUnit 格式结果用于 CI 展示

### 4.3 CI/CD 集成建议

* 集成 GitHub Actions / GitLab CI：

  * 步骤：编译 → 构建插件 → 执行测试 → 上传覆盖率 → 发布产物
* 关键 hook 阶段：

  * `pre-merge`：运行所有单元与集成测试
  * `nightly`：运行全量边界测试与性能回归

### 4.4 模拟与沙箱支持

* 内核态测试支持通过 QEMU/虚拟机或 Linux Test Project (LTP)
* 插件测试支持容器隔离执行（Docker）
* 所有自动化测试必须默认运行在沙箱/CI 安全环境中

