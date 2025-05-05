# Logloom (MVP)

Change Language: [CN](./README.md)

> **Note**: This is a Minimum Viable Product (MVP) version under active development. Core functionalities are implemented, but more advanced features will be added in future releases.

---

## 📊 Development Status

Logloom is currently in active development:

- **Currently Supported**: C language interface (for both pure C and C++ projects)
- **In Development**: Separation of kernel and user space implementations, Python bindings and API
- **Planned**: Standalone process/container plugin system, AI analysis module integration

### Development Milestones

| Milestone | Name                             | Completion Indicator                               | Status |
|-----------|----------------------------------|---------------------------------------------------|--------|
| M0        | Initialize Project Structure     | Complete Makefile / source dirs / YAML input structure | ✅ Completed |
| M1        | Multilingual Support Core        | Can load YAML and extract strings via `lang_get()`     | ✅ Completed |
| M2        | Basic Logging System             | Output structured logs to console/file with multiple levels | ✅ Completed |
| M3        | Config Loading & Default Merging | Correctly load config YAML and generate headers/structs | ✅ Completed |
| M4        | Log File Rotation                | Successfully create new log files when max size reached | ✅ Completed |
| M5        | Plugin Registration Framework    | Successfully load `.so` plugins and execute process()  | ✅ Completed |
| M6        | Test Integration                 | All modules pass at least 3 test cases                 | ✅ Completed |
| M7        | Minimum Viable Product (MVP)     | Run demo program, load language+config, write logs     | ✅ Completed |
| M8        | Python Bindings and Extended API | Support Logloom core functionality from Python         | 🚧 In Progress |
| M9        | AI Analysis Module Integration   | Support intelligent log analysis and diagnostics       | 📅 Planned |

---

## 🌟 Motivation

As software systems grow in scale, collaboration between different modules, languages, and platforms becomes increasingly complex. In this environment, **logs** are the most fundamental tool for understanding, monitoring, and diagnosing system behavior. However, traditional logging systems often:

- Lack a unified standard, leading to inconsistent styles across programs.
- Have scattered language bindings, making cross-language log sharing difficult.
- Are human-oriented and unsuitable for machine intelligence analysis.
- Lack built-in internationalization support, making them hard to adapt for multilingual environments.

**Logloom** was created to address these challenges fundamentally.

---

## 🌟 Goals

Logloom aims to build a system that:

- **Unified Standard**  
  Provides a consistent, structured logging format for all programs, whether kernel modules, automation tools, or virtualization platforms.

- **Cross-Language Compatibility**  
  Designs a simple, lightweight logging protocol that can be easily implemented in C, Python, Shell, and more.

- **Multilingual Internationalization**  
  Completely separates log messages from natural language content, supporting dynamic multilingual output for global applications.

- **Intelligent Observability**  
  Uses logs not only for recording but also as the foundation for machine analysis, intelligent diagnostics, and automatic repair.

- **Future Scalability**  
  Lays the architectural foundation for integrating AI analysis modules, enabling systems to learn, reason, and self-optimize from logs.

---

## 🚀 Vision

Logloom will serve as a unified, general-purpose logging infrastructure for multiple future systems, including:

- **moeai-c** — High-performance Linux kernel applications
- **knowforge** — Automated note-taking and knowledge generation tools
- **AntiChatVM** — Linux-based virtual Windows platform
- **More future planned intelligent systems**

In the future, Logloom will support:

- **Anomaly detection and alerting** driven by logs
- **AI diagnostics and repair suggestion generation** based on logs
- **Adaptive system tuning and optimization** through logs

---

## 🧹 Design Principles

- **Structured First**  
  Logs are recorded in a standardized structure (such as JSON lines), ensuring they are both readable and parseable.

- **Rich Context**  
  Logs include runtime environment, resource status, call stack, and more, supporting deep analysis.

- **Language Agnostic**  
  The log standard is decoupled from implementation languages, usable in any environment supporting basic output.

- **Built-in Internationalization**  
  Message codes plus translation resource management allow dynamic language switching in log output.

- **Lightweight and Flexible**  
  No dependency on heavy services (like Fluentd/Kibana); single program or module can deploy and use it.

- **Intelligent Expandability**  
  Retains enough data redundancy to accommodate future integration of rule engines and machine learning modules.

---

## 🛠️ Core Components

Logloom base system includes the following modules:

### 1. Internationalization System

- Language resource files managed separately, using YAML or C header files.
- Support for runtime dynamic language switching (e.g., Chinese, English).
- Message text retrieved through unified interfaces (e.g., `locale_get(key)` or `lang_get(key)`).
- Support for formatted string interpolation (e.g., `locale_getf(key, value)`).
- Default language can be specified via configuration or parameters, with fallback mechanism.

Reference implementations:
- Python projects (KnowForge) use the `LocaleManager` class.
- C language projects (MoeAI-C) use macro-defined key-value pairs + `lang_get` system.

### 2. Structured Logging System

- Logs unified in JSON format:
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
- Support for log level management: DEBUG, INFO, WARN, ERROR, FATAL.
- Log output supports dual channels:
  - Console output (for debugging)
  - File persistence (for tracing)
- Loggers can be divided by module, controlling log behavior independently.

Reference implementations:
- In Python projects, using `setup_logger()` and `get_module_logger()`
- In C projects, using `moeai_log()` and built-in ring buffer output.

### 3. Configuration and Extensibility

- Support for dynamic settings via configuration file or environment variables:
  - Default language
  - Log storage path
  - Minimum log level
- Future extensions:
  - Log rotation and cleanup mechanisms
  - Log data export API
  - Log-driven alerting and self-recovery modules

---

## 🚀 Quick Start

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/Logloom.git
   cd Logloom
   ```

2. Compile the project
   ```bash
   make
   ```

### Basic Usage

1. **Create a configuration file**

   Create a `config.yaml` file (or use the example configuration file):

   ```yaml
   logloom:
     language: "en"  # or "zh"
     log:
       level: "DEBUG"  # Options: DEBUG, INFO, WARN, ERROR
       file: "./app.log"
       max_size: 1048576  # 1MB
       console: true
   ```

2. **Use in your C program**

   ```c
   #include "include/log.h"
   #include "include/lang.h"
   
   int main() {
       // Initialize logging system
       log_init();
       log_set_level(LOG_LEVEL_DEBUG);
       log_set_output_file("my_app.log");
       
       // Set language
       lang_set_language("en");  // or "zh"
       
       // Use the logging system
       log_debug("LOGLOOM_LANG_DEBUG_MESSAGE", 123);
       log_info("LOGLOOM_LANG_INFO_MESSAGE");
       log_warn("LOGLOOM_LANG_WARN_WITH_PARAM", "warning parameter");
       log_error("LOGLOOM_LANG_ERROR_CODE", 404);
       
       return 0;
   }
   ```

3. **Compile your program**

   ```bash
   gcc your_program.c -I/path/to/logloom/include -L/path/to/logloom -llogloom -o yourprogram
   ```

### Running the Demo

```bash
# Compile and run the example program
make demo
./demo
```

Check the generated log file or console output.

---

## 📚 About the Name

**Logloom** combines "Log" and "Loom," symbolizing weaving dispersed log data into coherent system insights, supporting the evolution of future intelligent systems.

---

## 📚 Technical Roadmap

1. **Current MVP**: Basic logging and internationalization functionality
2. Separate kernel-space and user-space implementations
3. Release complete SDK for Python + C languages
4. Support more language extensions (adding Spanish, French, etc.)
5. Enhance log security (automatic sensitive information masking)
6. Introduce log-based anomaly detection and alerting system
7. Integrate lightweight log intelligent analysis module

---

# 📊 License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

For details, please refer to the [LICENSE](LICENSE) file.
