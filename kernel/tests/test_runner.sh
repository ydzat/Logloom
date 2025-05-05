#!/bin/bash
# Logloom内核模块测试运行脚本

# 设置颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo -e "${BLUE}Logloom内核模块测试运行脚本${NC}"
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  -a, --all      运行完整的测试流程（加载模块、运行测试、查看结果、清理）"
    echo "  -b, --build    仅构建Logloom内核模块和测试模块"
    echo "  -r, --run      运行测试（假设模块已加载）"
    echo "  -c, --clean    清理构建文件和测试文件"
    echo "  -h, --help     显示此帮助信息"
}

KERNEL_MODULE_PATH="../"
LOG_FILE="/tmp/logloom_kernel_test.log"

# 检查logloom内核模块是否加载
check_logloom_loaded() {
    if lsmod | grep -q "logloom"; then
        echo -e "${GREEN}[✓] Logloom内核模块已加载${NC}"
        return 0
    else
        echo -e "${RED}[✗] Logloom内核模块未加载${NC}"
        return 1
    fi
}

# 构建内核模块
build_modules() {
    echo -e "${YELLOW}[*] 构建Logloom内核模块...${NC}"
    (cd $KERNEL_MODULE_PATH && ./build.sh clean && ./build.sh build)
    if [ $? -ne 0 ]; then
        echo -e "${RED}[✗] Logloom内核模块构建失败${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}[*] 构建测试模块...${NC}"
    make clean && make
    if [ $? -ne 0 ]; then
        echo -e "${RED}[✗] 测试模块构建失败${NC}"
        return 1
    fi
    
    echo -e "${GREEN}[✓] 模块构建成功${NC}"
    return 0
}

# 加载内核模块
load_modules() {
    echo -e "${YELLOW}[*] 加载Logloom内核模块...${NC}"
    (cd $KERNEL_MODULE_PATH && sudo insmod logloom.ko)
    if [ $? -ne 0 ]; then
        echo -e "${RED}[✗] Logloom内核模块加载失败${NC}"
        return 1
    fi
    
    echo -e "${GREEN}[✓] Logloom内核模块加载成功${NC}"
    return 0
}

# 卸载内核模块
unload_modules() {
    echo -e "${YELLOW}[*] 卸载测试模块...${NC}"
    if lsmod | grep -q "logloom_test"; then
        sudo rmmod logloom_test
        if [ $? -ne 0 ]; then
            echo -e "${RED}[✗] 测试模块卸载失败${NC}"
        else
            echo -e "${GREEN}[✓] 测试模块卸载成功${NC}"
        fi
    fi
    
    echo -e "${YELLOW}[*] 卸载Logloom内核模块...${NC}"
    if lsmod | grep -q "logloom"; then
        sudo rmmod logloom
        if [ $? -ne 0 ]; then
            echo -e "${RED}[✗] Logloom内核模块卸载失败${NC}"
            return 1
        else
            echo -e "${GREEN}[✓] Logloom内核模块卸载成功${NC}"
        fi
    fi
    
    return 0
}

# 运行测试
run_tests() {
    echo -e "${BLUE}[*] 运行Logloom内核模块测试...${NC}"
    
    # 检查Logloom模块是否加载
    if ! check_logloom_loaded; then
        echo -e "${YELLOW}[!] 尝试加载Logloom模块...${NC}"
        load_modules
        if [ $? -ne 0 ]; then
            echo -e "${RED}[✗] 无法继续测试${NC}"
            return 1
        fi
    fi
    
    # 加载测试模块
    echo -e "${YELLOW}[*] 加载测试模块...${NC}"
    sudo insmod logloom_test.ko
    if [ $? -ne 0 ]; then
        echo -e "${RED}[✗] 测试模块加载失败${NC}"
        return 1
    fi
    
    # 等待测试完成
    echo -e "${YELLOW}[*] 等待测试完成...${NC}"
    sleep 2
    
    # 显示测试结果
    echo -e "${BLUE}================ 测试结果 =================${NC}"
    if [ -e "/proc/logloom_test" ]; then
        cat /proc/logloom_test
        
        # 检查测试是否通过
        if grep -q "FAIL" /proc/logloom_test; then
            echo -e "${RED}[✗] 测试发现错误${NC}"
            RESULT=1
        else
            echo -e "${GREEN}[✓] 所有测试通过${NC}"
            RESULT=0
        fi
    else
        echo -e "${RED}[✗] 无法读取测试结果，/proc/logloom_test不存在${NC}"
        RESULT=1
    fi
    
    # 检查日志文件
    if [ -e "$LOG_FILE" ]; then
        echo -e "${BLUE}================ 测试日志 =================${NC}"
        cat "$LOG_FILE"
    fi
    
    # 卸载测试模块
    sudo rmmod logloom_test
    
    return $RESULT
}

# 清理测试环境
cleanup() {
    echo -e "${YELLOW}[*] 清理测试环境...${NC}"
    
    # 卸载所有模块
    unload_modules
    
    # 清理构建文件
    make clean
    (cd $KERNEL_MODULE_PATH && ./build.sh clean)
    
    # 删除测试日志
    if [ -e "$LOG_FILE" ]; then
        rm -f "$LOG_FILE"
    fi
    
    echo -e "${GREEN}[✓] 清理完成${NC}"
}

# 运行完整测试流程
run_full_test() {
    build_modules || return 1
    load_modules || return 1
    run_tests
    TEST_RESULT=$?
    cleanup
    return $TEST_RESULT
}

# 检查参数
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

case "$1" in
    -a|--all)
        run_full_test
        exit $?
        ;;
    -b|--build)
        build_modules
        exit $?
        ;;
    -r|--run)
        run_tests
        exit $?
        ;;
    -c|--clean)
        cleanup
        exit $?
        ;;
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        echo -e "${RED}未知选项: $1${NC}"
        show_help
        exit 1
        ;;
esac