# Logloom 构建与部署指南

本文档提供 Logloom 项目的详细构建、安装和部署说明，适用于开发者和用户。

## 目录

- [构建环境要求](#构建环境要求)
- [构建步骤](#构建步骤)
  - [用户空间库](#用户空间库)
  - [内核模块](#内核模块)
  - [Python绑定](#python绑定)
- [安装指南](#安装指南)
  - [系统级安装](#系统级安装)
  - [用户级安装](#用户级安装)
- [版本管理系统](#版本管理系统)
  - [版本号格式](#版本号格式)
  - [版本管理工具](#版本管理工具)
  - [使用示例](#使用示例)
  - [版本控制最佳实践](#版本控制最佳实践)
- [持续集成](#持续集成)
- [故障排除](#故障排除)

## 构建环境要求

在构建 Logloom 之前，请确保您的系统满足以下要求：

### 系统要求

- 操作系统：Linux（推荐 Fedora 41 或 Ubuntu 22.04+）
- 编译器：GCC 5.0+ 或 Clang 5.0+
- 构建工具：Make
- Python：3.6+ (推荐使用虚拟环境)

### 依赖包

在 Fedora 上安装依赖包：

```bash
sudo dnf install make gcc libyaml-devel pkgconfig python3-devel
```

在 Ubuntu/Debian 上安装依赖包：

```bash
sudo apt-get update
sudo apt-get install build-essential libyaml-dev pkg-config python3-dev
```

### 可选依赖

- 对于 API 一致性检查：需要 Python 虚拟环境和 libclang
- 对于内核模块构建：需要 Linux 内核头文件

## 构建步骤

### 用户空间库

1. 克隆代码仓库（如果尚未克隆）：

```bash
git clone https://github.com/yourusername/Logloom.git
cd Logloom
```

2. 生成所需的头文件并构建库：

```bash
make
```

这将执行以下操作：
- 创建必要的目录结构
- 生成版本头文件
- 生成国际化资源头文件
- 生成配置头文件
- 编译核心库组件
- 构建用户空间静态库 `liblogloom.a`

### 内核模块

构建内核模块：

```bash
cd kernel
./build.sh build
```

此脚本将根据当前内核头文件构建适用的内核模块。

### Python绑定

构建 Python 绑定：

```bash
# 确保用户空间库已构建
# 返回项目根目录（如果需要）
cd /path/to/Logloom

# 构建 Python 绑定
make python
```

这将在 `src/bindings/python/build` 目录下生成 Python 绑定模块。

### 运行测试

确保所有组件正常工作：

```bash
# 运行所有测试
make test

# 仅运行内核模块测试
make test-kernel

# 仅运行 Python 绑定测试
make python-test
```

## 安装指南

### 系统级安装

系统级安装（需要 root 权限）：

```bash
sudo make install
```

这将安装：
- C 库文件到 `/usr/local/lib/`
- 头文件到 `/usr/local/include/logloom/`
- Python 绑定到系统的 Python 路径

### 用户级安装

仅安装 Python 绑定（无需 root 权限）：

```bash
make python-install
```

或直接使用 pip：

```bash
cd src/bindings/python
pip install --user .
```

## 版本管理系统

Logloom 项目使用集中式版本管理系统，确保整个代码库中的版本号一致性。

### 版本号格式

项目采用语义化版本号（[Semantic Versioning](https://semver.org/)）格式：`X.Y.Z`

- **X**: 主版本号 - 当进行不兼容的 API 修改时增加
- **Y**: 次版本号 - 当增加向下兼容的功能时增加
- **Z**: 修订号 - 当进行向下兼容的缺陷修复时增加

### 版本管理工具

Logloom 使用 `tools/version_manager.py` 脚本管理整个项目的版本号。该工具实现了：

1. 集中化版本管理 - 所有版本号来源于单一的 `version/VERSION` 文件
2. 自动同步 - 将中央版本号同步至项目中的各个组件：
   - C/C++ 头文件中的版本定义
   - 内核模块的版本声明
   - Python 绑定的版本号
   - README 文件中的版本标记

#### 工具命令行选项

```
usage: version_manager.py [-h] [--generate] [--check] [--update] [--set VERSION]

Logloom版本管理工具

optional arguments:
  -h, --help     显示帮助信息并退出
  --generate     生成版本头文件
  --check        检查版本号一致性
  --update       更新所有版本号
  --set VERSION  设置新版本号并更新所有引用
```

#### Makefile 集成

项目 Makefile 已集成了版本管理命令：

```bash
# 生成版本头文件
make version-headers

# 检查版本号一致性
make version-check

# 更新项目中所有版本号
make version-update

# 设置新版本号（交互式）
make version-set
```

### 使用示例

#### 检查版本一致性

```bash
./tools/version_manager.py --check
```

输出示例：
```
版本号检查通过: 所有文件一致使用版本 1.2.1
```

#### 更新项目版本号

```bash
# 首先编辑 version/VERSION 文件修改版本号
echo "1.3.0" > version/VERSION

# 然后更新所有引用
./tools/version_manager.py --update
```

或直接使用 `--set` 参数：

```bash
./tools/version_manager.py --set 1.3.0
```

### 版本控制最佳实践

1. **版本号更新时机**
   - 主版本号 (X): 进行不兼容的 API 修改时
   - 次版本号 (Y): 添加向下兼容的新功能时
   - 修订号 (Z): 修复 bug 或进行小的改进时

2. **发布准备清单**
   - 更新版本号: `make version-set`
   - 运行全套测试: `make test`
   - 更新 CHANGELOG.md（如有）
   - 提交更改并添加版本标签: `git tag v1.2.1`

3. **持续集成注意事项**
   - 在 CI 流程中添加 `make version-check` 以验证版本一致性
   - 发布前使用 `make version-set` 设置正确的版本号

## 持续集成

Logloom 的持续集成流程包括：

1. **代码风格检查**: 确保代码符合项目编码规范
2. **编译测试**: 在多个平台和编译器上测试构建
3. **单元测试**: 运行所有的单元测试
4. **集成测试**: 测试各组件之间的协作
5. **API 一致性检查**: 使用自动化工具检查 API 一致性
6. **版本一致性检查**: 确保所有版本号同步

## 故障排除

### 常见问题

1. **编译错误**
   
   问题: 编译时出现 "xxx.h: No such file or directory"
   
   解决方法: 确保已运行 `make dirs lang_headers config_headers version-headers` 生成必要的头文件

2. **Python 绑定导入错误**
   
   问题: `ImportError: No module named logloom`
   
   解决方法: 检查 Python 包是否正确安装，可以尝试重新安装:
   ```bash
   cd src/bindings/python
   pip install -e .
   ```

3. **版本不一致警告**
   
   问题: 运行 `make version-check` 时出现不一致警告
   
   解决方法: 运行 `make version-update` 同步所有版本号

### 获取帮助

如果您遇到未在本指南中列出的问题，可以：

1. 检查项目 issues 页面查看是否有类似问题及解决方案
2. 在项目仓库中提交新的 issue
3. 查阅项目文档中的常见问题解答

## 结语

按照本指南的步骤，您应该能够成功构建、安装和部署 Logloom 库及其组件。如果有任何改进建议，欢迎贡献！