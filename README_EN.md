# Logloom

Change Language: [CN](./README.md)

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/yourusername/Logloom)
[![Version](https://img.shields.io/badge/version-1.2.1-blue)](https://github.com/yourusername/Logloom/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **Note**: This is a Minimum Viable Product (MVP) version under active development. Core functionalities are implemented, but more advanced features will be added in future releases.

---

## 📊 Development Status

Logloom is currently in active development:

- **Currently Supported**: C language interface (for both pure C and C++ projects), Python basic bindings, API consistency automation, Python plugin system
- **In Development**: AI analysis module integration
- **Planned**: Advanced security features

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
| M8        | Python Bindings and Extended API | Support Logloom core functionality from Python         | ✅ Completed |
| M9        | C Library and Python API Alignment | Ensure C library API matches Python bindings         | ✅ Completed |
| M10       | High Concurrency Stability      | Normal operation in multi-threaded environment         | ✅ Completed |
| M11       | API Consistency Checker Tool     | Automatically verify header and implementation consistency | ✅ Completed |
| M12       | Python Plugin System Implementation | Feature parity with C plugin system & plugin discovery | ✅ Completed |
| M13       | AI Analysis Module Integration   | Support intelligent log analysis and diagnostics       | 📅 Planned |

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

### 4. API Consistency Checker

- Automatically detects and reports API inconsistencies:
  - Mismatches between header declarations and implementation definitions
  - Return type inconsistencies
  - Parameter type, count, or name mismatches
- Supports multiple output formats (text, JSON, HTML)
- Uses libclang for precise AST analysis
- Customizable checking rules via YAML configuration file

Usage example:

```bash
# Run API consistency check
./tools/api_consistency_check.py --include-dir include --src-dir src --rules tools/api_consistency_rules.yaml

# Generate HTML report
./tools/api_consistency_check.py --include-dir include --src-dir src --output html --output-file api_report.html
```

### 5. Python Bindings and Test Adapters

Logloom provides comprehensive Python language support, including:

- **Core functionality interface**: Logging, internationalization, and configuration management
- **Modular loggers**: Each module can independently control log levels
- **Test adapter system**: Provides mock implementations when real modules are unavailable

Key features of the test adapter:

```python
# Using the test adapter
from tests.python.test_adapter import logger, Logger, LogLevel

# Create a logger
logger = Logger("my_module")
logger.set_level(LogLevel.DEBUG)
logger.set_file("my_logs.log")

# Set log rotation
logger.set_rotation_size(1024)  # 1KB

# Log at different levels
logger.debug("This is debug info: {}", 123)
logger.info("This is information")
logger.warning("This is a warning: {warning}", warning="Warning content")
logger.error("This is an error")
logger.critical("This is a critical error")
```

The test adapter supports:

- Log level filtering
- Formatting positional and keyword arguments
- Log file rotation
- Multi-language support
- Module-specific settings

---

## 🚀 Quick Start

### Requirements

Basic requirements for the Logloom library:

- **Operating System**:
  - Linux: Fedora 41 (tested)
  - Other Linux distributions (theoretically supported)
  - macOS or Windows (theoretically supported, via WSL)
- **Compiler**: GCC 5.0+ or Clang 5.0+
- **Build Tools**: Make
- **Python**: Python 3.13 (version in virtual environment, tested) (other versions may be supported but compatibility should be considered)
- **Dependencies**:
  - libyaml-dev (for YAML config parsing)
  - pkg-config (for build system)
  - python3-dev (required for Python bindings)

Install dependencies on Fedora 41:
```bash
sudo dnf install make gcc libyaml-devel pkgconfig python3-devel
```

Install dependencies on Debian/Ubuntu:
```bash
sudo apt-get update
sudo apt-get install build-essential libyaml-dev pkg-config python3-dev
```

Recommended to use Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
# Install development dependencies
pip install -r requirements-dev.txt
```

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/Logloom.git
   cd Logloom
   ```

2. Build the core library
   ```bash
   make
   ```

3. Install the library (optional)
   ```bash
   sudo make install
   ```

4. Build and install Python bindings (optional)
   ```bash
   cd src/bindings/python
   pip install -e .
   ```

### Version Management

Logloom uses a centralized version management system that maintains version consistency across all project components.

#### Version Management Commands

```bash
# Check version consistency across the project
make version-check

# Update all version references from the central version file
make version-update

# Set a new version number (interactive prompt)
make version-set

# Directly set a specific version number
./tools/version_manager.py --set 1.3.0
```

#### How the Version System Works

1. A central version file (`version/VERSION`) serves as the single source of truth
2. The version management tool (`tools/version_manager.py`) automatically updates:
   - C header file (`include/generated/version.h`)
   - Kernel module version declarations
   - Python bindings version numbers
   - Version tags in README files

When developing or releasing new versions, simply update the central version file, and all other files will be automatically synchronized to maintain version consistency.

### Verify Installation

Run the test suite to confirm successful installation:

```bash
# C library tests
./run_tests.sh

# Python binding tests
cd tests/python
python run_tests.py
```

### Using in C/C++ Projects

1. **Create a Configuration File**

   Create a `config.yaml` file:

   ```yaml
   logloom:
     language: "en"  # or "zh"
     log:
       level: "DEBUG"  # Options: DEBUG, INFO, WARN, ERROR, FATAL
       file: "./app.log"
       max_size: 1048576  # 1MB
       console: true
   ```

2. **Include Headers and Initialize**

   ```c
   #include <logloom/log.h>
   #include <logloom/lang.h>
   #include <logloom/config.h>

   int main() {
       // Initialize configuration
       logloom_config_init("./config.yaml");
       
       // Initialize logging system
       log_init();
       
       // Use settings from config, or set manually
       // log_set_level(LOG_LEVEL_DEBUG);
       // log_set_output_file("my_app.log");
       
       // Set language
       lang_set_language("en");  // or "zh"
       
       // ...your application code...
       
       return 0;
   }
   ```

3. **Log Messages**

   ```c
   // Different log levels
   log_debug("Initializing application"); // Debug info
   log_info("User %s logged in", username);
   log_warn("Unusual access pattern detected");
   log_error("Failed to connect to database: %s", db_error);
   log_fatal("System crash: %d", error_code);
   
   // With internationalization support
   log_info("LOGLOOM_USER_LOGIN", username); // Will look up text from language resources
   ```

4. **Compile Your Program**

   Using pkg-config (if Logloom was installed):
   ```bash
   gcc your_program.c $(pkg-config --cflags --libs logloom) -o yourprogram
   ```

   Or specify paths directly:
   ```bash
   gcc your_program.c -I/path/to/logloom/include -L/path/to/logloom -llogloom -o yourprogram
   ```

### Using in Python Projects

1. **Import Modules**

   ```python
   import logloom_py as ll
   ```

2. **Initialize the System**

   ```python
   # Initialize with config file
   ll.initialize("./config.yaml")
   
   # Or configure manually
   root_logger = ll.Logger("app")
   root_logger.set_level(ll.LogLevel.DEBUG)
   root_logger.set_file("app.log")
   ```

3. **Use Modular Logging**

   ```python
   # Create loggers for specific modules
   db_logger = ll.Logger("database")
   auth_logger = ll.Logger("auth")
   
   # Set different log levels
   db_logger.set_level(ll.LogLevel.INFO)
   auth_logger.set_level(ll.LogLevel.DEBUG)
   
   # Log messages
   db_logger.info("Database connection successful")
   auth_logger.debug("Validation request: {}", request_id)
   auth_logger.warning("User {user} login failed: {reason}", user="admin", reason="password incorrect")
   ```

4. **Log Rotation**

   ```python
   # Set log rotation (when file size exceeds 1MB)
   db_logger.set_rotation_size(1024 * 1024)  # 1MB
   ```

5. **Internationalization Support**

   ```python
   # Set current language
   ll.set_language("en")  # or "zh"
   
   # Get translated text
   welcome_text = ll.get_text("welcome")
   
   # Format text with parameters
   error_text = ll.format_text("error.file_not_found", "/data/config.json")
   user_text = ll.format_text("user.profile", name="John", age=30)
   ```

   **Dynamic Language Resource Registration (New in 1.2.0)**
   
   ```python
   # Register a single language resource file
   # Language code can be inferred from filename (e.g., "fr.yaml" for French)
   ll.register_locale_file("/path/to/fr.yaml")
   # Or explicitly specified
   ll.register_locale_file("/path/to/custom_translations.yaml", "de")
   
   # Register all language resource files in a directory
   count = ll.register_locale_directory("/app/translations")
   print(f"Registered {count} language files")
   
   # Query supported languages
   languages = ll.get_supported_languages()
   print(f"Supported languages: {', '.join(languages)}")  # e.g.: en, zh, fr, de
   
   # Get all translation keys for a specific language
   zh_keys = ll.get_language_keys("zh")
   print(f"Chinese translation keys count: {len(zh_keys)}")
   
   # Use newly registered language
   ll.set_language("fr")
   welcome = ll.get_text("system.welcome")  # Get welcome message in French
   ```
   
   **Multi-language Environment Configuration**
   
   The configuration file can specify default language and resource paths:
   
   ```yaml
   logloom:
     # Language setting
     language: "en"  # Default language
     
     # Internationalization config (new in 1.2.0)
     i18n:
       # Language resource paths list, supports glob patterns
       locale_paths:
         - "./locales/*.yaml"
         - "./custom_translations/*.yaml"
       
       # Auto-discover resource directories (defaults to true if not specified)
       auto_discover: true
   ```

### Advanced Usage

1. **Enable the Plugin System**

   ```c
   // Loading plugins in C
   plugin_init();
   plugin_load_directory("./plugins");
   
   // Logs will automatically be processed by loaded plugins
   log_info("This log will go through all loaded filters and output plugins");
   ```

   ```python
   # Loading plugins in Python
   from logloom import initialize_plugins, load_plugins
   
   initialize_plugins(plugin_dir="./plugins", config_path="./plugin_config.json")
   load_plugins()
   ```

2. **Custom Log Formats**

   ```c
   // Set custom format (if supported)
   log_set_format("[%level%][%time%] %message%");
   ```

3. **Multi-threaded Environment**

   Logloom is thread-safe and requires no additional locking:

   ```c
   // Log from any thread
   log_info("Thread %d is processing task %s", thread_id, task_name);
   ```

### Running the Demo

```bash
# Compile and run the example program
make demo
./demo
```

Check the generated log file (`logloom.log`) or console output.

---

## 📚 About the Name

**Logloom** combines "Log" and "Loom," symbolizing weaving dispersed log data into coherent system insights, supporting the evolution of future intelligent systems.

---

## 📚 Technical Roadmap

1. **Current MVP**: Basic logging and internationalization functionality ✅
2. **Python Bindings and Extended API**: Provide Python language interface ✅
3. **API Consistency Checking and Validation**: Ensure API stability and consistency ✅
4. Separate kernel-space and user-space implementations 🚧
5. Enhance log security (automatic sensitive information masking)
6. Introduce log-based anomaly detection and alerting system
7. Integrate lightweight log intelligent analysis module

---

# 📊 License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

For details, please refer to the [LICENSE](LICENSE) file.
