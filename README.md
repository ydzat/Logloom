# Logloom

一个轻量级的、国际化友好的、可扩展的日志系统，具备多平台支持能力，可用于用户空间应用和Linux内核模块。

[![构建状态](https://img.shields.io/badge/构建-通过-brightgreen)](https://github.com/yourusername/Logloom)
[![版本](https://img.shields.io/badge/版本-1.0.0-blue)](https://github.com/yourusername/Logloom/releases)
[![许可证](https://img.shields.io/badge/许可证-MIT-green)](LICENSE)

## 特性

- **C语言核心库**：高效且轻量级
- **多语言绑定**：支持Python、C++（规划中）
- **国际化支持**：内置多语言支持，易于拓展新语言
- **日志分级**：标准的DEBUG、INFO、WARN、ERROR和FATAL级别
- **多目标输出**：同时输出到控制台、文件，易于扩展新输出目标
- **自动日志轮转**：基于大小的日志文件轮转
- **可配置格式**：可自定义日志格式和时间戳格式
- **上下文追踪**：支持模块/组件级别的上下文标记
- **Linux内核支持**：可作为内核模块使用
- **线程安全**：所有操作都是线程安全的
- **插件系统**：支持动态加载自定义插件（过滤器、处理器等）
- **配置灵活**：支持文件配置和编程API配置

## 快速开始

### 在C语言中使用

```c
#include "log.h"
#include "lang.h"
#include "config.h"

int main() {
    // 初始化配置
    logloom_config_init("config.yaml");
    
    // 设置语言（可选，默认使用配置文件中的设置）
    logloom_set_language("zh");
    
    // 记录不同级别的日志
    LOG_INFO("main", "应用程序已启动");
    LOG_DEBUG("main", "调试信息: %s", "some details");
    LOG_WARN("main", "警告: 资源使用率高");
    LOG_ERROR("main", "发生错误: %d", errno);
    
    // 使用国际化文本
    const char* welcome = logloom_get_text("app.welcome");
    printf("%s\n", welcome);
    
    // 清理资源
    logloom_cleanup();
    return 0;
}
```

### 在Python中使用

```python
import logloom_py as ll

# 初始化配置
ll.initialize("config.yaml")

# 创建记录器
logger = ll.Logger("example")

# 记录不同级别的日志
logger.info("应用程序已启动")
logger.debug("调试信息: {}", "一些详细信息") 
logger.warn("警告: 资源使用率高: {}%", 85)
logger.error("发生错误: {}", "连接中断")

# 使用国际化文本
welcome = ll.get_text("app.welcome")
print(welcome)

# 带参数的国际化文本
msg = ll.format_text("app.hello", "用户")
print(msg)  # 输出：你好，用户！

# 清理资源
ll.cleanup()
```

### 在Linux内核中使用

```c
#include <linux/module.h>
#include <linux/kernel.h>
#include "kernel/include/log.h"
#include "kernel/include/lang.h"

static int __init logloom_test_init(void)
{
    // 初始化（配置通过参数传递）
    logloom_kernel_init();
    
    // 记录不同级别的日志
    KLOG_INFO("test", "内核模块已加载");
    KLOG_DEBUG("test", "调试信息");
    KLOG_WARN("test", "警告信息");
    
    // 使用国际化消息
    const char* msg = logloom_kernel_get_text("module.loaded");
    printk(KERN_INFO "%s\n", msg);
    
    return 0;
}

static void __exit logloom_test_exit(void)
{
    KLOG_INFO("test", "内核模块已卸载");
    logloom_kernel_cleanup();
}

module_init(logloom_test_init);
module_exit(logloom_test_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("作者");
MODULE_DESCRIPTION("Logloom内核模块示例");
```

## 配置

### 配置文件示例 (config.yaml)

```yaml
logloom:
  # 语言设置
  language: "zh"  # 支持 "zh" 或 "en"
  
  # 日志配置
  log:
    # 日志级别: DEBUG, INFO, WARN, ERROR, FATAL
    level: "INFO"
    
    # 日志文件路径
    file: "logs/app.log"
    
    # 日志文件最大大小（字节）
    max_size: 1048576  # 1MB
    
    # 是否输出到控制台
    console: true
    
    # 格式配置
    format: "[{timestamp}][{level}][{module}] {message}"
    
    # 时间戳格式
    timestamp_format: "%Y-%m-%d %H:%M:%S"
  
  # 插件系统配置
  plugins:
    # 插件目录
    dir: "plugins"
    
    # 启用的插件列表
    enabled:
      - "filter_sensitive"
      - "sink_database"
```

## 国际化支持

### 添加新语言

1. 在 `locales` 目录下创建新的YAML文件，如 `ja.yaml` 用于日语
2. 运行翻译生成工具: `python tools/generate_lang_headers.py`
3. 重新编译项目

### 语言文件示例 (locales/zh.yaml)

```yaml
system:
  start: "系统启动"
  shutdown: "系统关闭"
  error: "发生错误: {0}"
  
app:
  welcome: "欢迎使用Logloom"
  hello: "你好，{0}！"
  
errors:
  file_not_found: "找不到文件: {0}"
  permission: "权限不足"
```

## 插件系统

### 创建自定义插件 (C语言)

```c
#include "plugin.h"

// 初始化函数
static int sensitive_filter_init(const char* config_json) {
    // 解析配置...
    return 0; // 成功返回0
}

// 处理函数
static int sensitive_filter_process(log_entry_t* entry) {
    // 处理或修改日志条目...
    // 例如，替换敏感信息
    return 0; // 成功返回0
}

// 清理函数
static void sensitive_filter_cleanup(void) {
    // 清理资源...
}

// 导出插件定义
LOGLOOM_PLUGIN_DEFINE(
    "filter_sensitive",    // 插件名称
    "敏感信息过滤器",      // 插件描述
    PLUGIN_TYPE_FILTER,    // 插件类型
    sensitive_filter_init,
    sensitive_filter_process,
    sensitive_filter_cleanup
)
```

### 创建自定义插件 (Python)

```python
import logloom_py as ll

# 定义自定义插件类
class SensitiveFilter:
    def __init__(self, config=None):
        self.config = config or {}
        self.patterns = self.config.get("patterns", ["password", "credit_card"])
    
    def process(self, log_entry):
        # 过滤或修改日志条目
        for pattern in self.patterns:
            if pattern in log_entry["message"]:
                # 替换敏感信息
                log_entry["message"] = log_entry["message"].replace(
                    pattern + "=", pattern + "=******"
                )
        return log_entry

# 注册插件
ll.register_plugin(SensitiveFilter)
```

## 构建与安装

### 预备条件

- C编译器 (GCC 4.8+)
- Python 3.6+ (用于Python绑定)
- CMake 3.10+ (构建系统)
- Linux内核头文件 (用于内核模块)

### 构建指令

```bash
# 克隆仓库
git clone https://github.com/yourusername/Logloom.git
cd Logloom

# 构建库和用户空间组件
make

# 构建内核模块
cd kernel
make

# 构建Python绑定
cd ../src/bindings/python
python setup.py build

# 安装Python包
python setup.py install
```

## 文档

完整的API参考和示例可在以下位置找到：

- [API参考](docs/08_APIReference.md)
- [完整API参考](docs/11_(Full)APIReference.md)
- [高层设计](docs/01_HighLevelDesign.md)
- [国际化设计](docs/02_InternationalizationDesign.md)
- [日志系统设计](docs/03_LoggingSystemDesign.md)
- [配置设计](docs/04_ConfigurationDesign.md)
- [构建与部署指南](docs/07_BuildAndDeploymentGuide.md)
- [Python插件系统](docs/10_PythonPluginSystem.md)

## 贡献

欢迎贡献！请查看[贡献指南](CONTRIBUTING.md)了解详情。

## 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件。
