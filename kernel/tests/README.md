# Logloom内核模块测试指南

本目录包含Logloom内核模块的测试代码和辅助工具。

## 测试架构

Logloom内核模块测试采用以下架构：

1. **主Logloom内核模块**：提供核心功能，包括日志记录、国际化支持和配置管理
2. **独立测试模块**：作为一个单独的内核模块加载，它依赖于主Logloom模块，并使用其公开的API
3. **通过proc文件系统交互**：测试结果可通过`/proc/logloom_test`查看

## 测试覆盖范围

当前测试覆盖以下方面：

- 日志级别设置和查询
- 日志输出到文件
- 控制台日志开关
- 多语言文本获取
- 格式化国际化文本
- 语言切换功能

## 运行测试

### 方法一：使用自动化测试脚本

最简单的方式是使用提供的测试运行脚本：

```bash
# 运行完整测试流程（构建、加载、测试、清理）
./test_runner.sh --all

# 仅构建测试模块
./test_runner.sh --build

# 仅运行测试（假设模块已加载）
./test_runner.sh --run

# 清理测试环境
./test_runner.sh --clean
```

### 方法二：使用Makefile

也可以通过项目根目录下的Makefile运行测试：

```bash
# 在项目根目录下
make test-kernel
```

### 方法三：手动测试

如果需要手动测试，请按以下步骤操作：

1. 构建并加载Logloom内核模块：
   ```bash
   cd ../
   ./build.sh build
   sudo insmod logloom.ko
   ```

2. 构建并加载测试模块：
   ```bash
   make
   sudo insmod logloom_test.ko
   ```

3. 查看测试结果：
   ```bash
   cat /proc/logloom_test
   ```

4. 手动触发测试：
   ```bash
   echo run > /proc/logloom_test
   cat /proc/logloom_test
   ```

5. 卸载模块：
   ```bash
   sudo rmmod logloom_test
   sudo rmmod logloom
   ```

## 查看日志

测试产生的日志文件位于`/tmp/logloom_kernel_test.log`，可以通过以下命令查看：

```bash
cat /tmp/logloom_kernel_test.log
```

## 错误排查

如果测试失败，请检查以下几点：

1. 确保以root权限（或使用sudo）运行测试
2. 检查内核模块是否成功加载，运行`lsmod | grep logloom`
3. 查看内核日志获取更多信息：`dmesg | tail -n 50`
4. 确保内核版本支持，最低要求为Linux 5.4+