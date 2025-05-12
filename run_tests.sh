#!/bin/bash
# Logloom 测试运行器
# 此脚本运行所有 Logloom 测试，包括 C 测试和 Python 测试

set -e

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}           Logloom 测试运行器                   ${NC}"
echo -e "${BLUE}================================================${NC}"

# 当前目录
CURRENT_DIR=$(pwd)

# 检查是否为 Logloom 目录
if [ ! -f "${CURRENT_DIR}/Makefile" ] || [ ! -d "${CURRENT_DIR}/src" ]; then
    echo -e "${RED}错误：请在 Logloom 项目根目录运行此脚本${NC}"
    exit 1
fi

# 创建所需的目录
mkdir -p tests/logs
mkdir -p tests/python/logs
mkdir -p tests/python/config

# 1. 运行 C 测试
echo -e "${YELLOW}[1/3] 运行 C 测试...${NC}"
make -f Makefile.test
if [ $? -eq 0 ]; then
    echo -e "${GREEN}C 测试通过!${NC}"
else
    echo -e "${RED}C 测试失败!${NC}"
    exit 1
fi

# 2. 编译 Python 绑定
echo -e "${YELLOW}[2/3] 编译 Python 绑定...${NC}"
cd src/bindings/python
python3 setup.py build_ext --inplace
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Python 绑定编译成功!${NC}"
else
    echo -e "${RED}Python 绑定编译失败!${NC}"
    cd $CURRENT_DIR
    exit 1
fi
cd $CURRENT_DIR

# 3. 运行 Python 测试
echo -e "${YELLOW}[3/3] 运行 Python 测试...${NC}"
cd tests/python
python3 run_tests.py
PYTHON_TEST_RESULT=$?
cd $CURRENT_DIR

if [ $PYTHON_TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}Python 测试通过!${NC}"
else
    echo -e "${RED}Python 测试失败!${NC}"
    exit 1
fi

# 总结
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}所有测试通过!${NC}"
echo -e "${BLUE}================================================${NC}"

exit 0