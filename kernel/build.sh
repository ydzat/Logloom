#!/bin/bash
# Logloom 内核模块构建脚本

# 设置颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo -e "${GREEN}Logloom 内核模块构建脚本${NC}"
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  build    - 构建内核模块"
    echo "  clean    - 清理构建文件"
    echo "  install  - 安装内核模块"
    echo "  uninstall - 卸载内核模块"
    echo "  help     - 显示此帮助信息"
}

# 确保生成目录存在
ensure_dirs() {
    if [ ! -d "generated" ]; then
        mkdir -p include/generated
    fi
}

# 生成配置头文件
generate_config() {
    echo -e "${YELLOW}生成配置头文件...${NC}"
    
    # 检查配置头文件是否已经存在
    if [ -f "include/generated/config_gen.h" ]; then
        echo -e "${GREEN}配置头文件已存在，跳过生成步骤${NC}"
        return 0
    fi
    
    # 尝试运行生成脚本
    if [ -f "../tools/gen_config_header.py" ]; then
        ../tools/gen_config_header.py ../config.yaml > include/generated/config_gen.h
        if [ $? -ne 0 ]; then
            echo -e "${RED}生成配置头文件失败${NC}"
            echo -e "${YELLOW}将使用默认配置头文件${NC}"
            
            # 如果仍然不存在，创建一个简单的默认配置
            if [ ! -f "include/generated/config_gen.h" ]; then
                cat > include/generated/config_gen.h << EOL
/**
 * 默认生成的内核配置头文件
 */
#ifndef LOGLOOM_CONFIG_GEN_H
#define LOGLOOM_CONFIG_GEN_H

#define LOGLOOM_CONFIG_LANG "en"
#define LOGLOOM_CONFIG_LOG_LEVEL "INFO"
#define LOGLOOM_CONFIG_LOG_FILE "/var/log/logloom.log"
#define LOGLOOM_CONFIG_LOG_MAX_SIZE 1048576
#define LOGLOOM_CONFIG_LOG_CONSOLE 1

#endif /* LOGLOOM_CONFIG_GEN_H */
EOL
            fi
        fi
    else
        echo -e "${YELLOW}配置生成脚本不存在，使用默认配置${NC}"
    fi
}

# 构建内核模块
build_module() {
    echo -e "${YELLOW}构建内核模块...${NC}"
    
    # 确保目录结构
    ensure_dirs
    
    # 生成配置头文件
    generate_config
    
    # 构建内核模块
    make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}内核模块构建成功${NC}"
    else
        echo -e "${RED}内核模块构建失败${NC}"
        exit 1
    fi
}

# 清理构建文件
clean_module() {
    echo -e "${YELLOW}清理构建文件...${NC}"
    make -C /lib/modules/$(uname -r)/build M=$(pwd) clean
    echo -e "${GREEN}清理完成${NC}"
}

# 安装内核模块
install_module() {
    echo -e "${YELLOW}安装内核模块...${NC}"
    if [ ! -f "logloom.ko" ]; then
        echo -e "${RED}内核模块不存在，请先构建${NC}"
        exit 1
    fi
    sudo insmod logloom.ko
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}内核模块安装成功${NC}"
        echo "可以通过 'dmesg | tail' 查看模块日志"
    else
        echo -e "${RED}内核模块安装失败${NC}"
        exit 1
    fi
}

# 卸载内核模块
uninstall_module() {
    echo -e "${YELLOW}卸载内核模块...${NC}"
    if lsmod | grep -q "logloom"; then
        sudo rmmod logloom
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}内核模块卸载成功${NC}"
        else
            echo -e "${RED}内核模块卸载失败${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}内核模块未加载${NC}"
    fi
}

# 解析命令行参数
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

case "$1" in
    build)
        build_module
        ;;
    clean)
        clean_module
        ;;
    install)
        install_module
        ;;
    uninstall)
        uninstall_module
        ;;
    help)
        show_help
        ;;
    *)
        echo -e "${RED}未知选项: $1${NC}"
        show_help
        exit 1
        ;;
esac

exit 0