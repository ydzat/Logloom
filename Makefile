# Logloom Makefile

CC = gcc
CFLAGS = -Wall -Werror -g -I./include -fPIC
LDFLAGS = -ldl -pthread  # For plugin loading and threading

# 编译目标
.PHONY: all clean test dirs lang_headers config_headers kernel userspace kernel-test

# Directories
SRC_DIR = src
BUILD_DIR = build
INCLUDE_DIR = include
TEST_DIR = tests
LANG_DIR = locales
KERNEL_DIR = kernel
CORE_DIR = $(SRC_DIR)/core
USERSPACE_DIR = $(SRC_DIR)/userspace

# Source files
CORE_SRC = $(wildcard $(CORE_DIR)/*.c)
USERSPACE_SRC = $(wildcard $(USERSPACE_DIR)/*.c)

# Object files
CORE_OBJ = $(patsubst $(SRC_DIR)/%.c,$(BUILD_DIR)/%.o,$(CORE_SRC))
USERSPACE_OBJ = $(patsubst $(SRC_DIR)/%.c,$(BUILD_DIR)/%.o,$(USERSPACE_SRC))

# 默认目标 - 构建用户空间库
all: dirs lang_headers config_headers userspace demo

dirs:
	mkdir -p $(BUILD_DIR)/core $(BUILD_DIR)/userspace $(INCLUDE_DIR)/generated

# Language headers generation
lang_headers:
	python tools/generate_lang_headers.py

# Config headers generation
config_headers:
	./tools/gen_config_header.py config.yaml $(INCLUDE_DIR)/generated/config_gen.h

# 用户态静态库
userspace: $(CORE_OBJ) $(USERSPACE_OBJ)
	ar rcs liblogloom.a $^

# 内核模块
kernel: dirs lang_headers config_headers
	cd $(KERNEL_DIR) && ./build.sh build

# 内核模块测试
kernel-test: kernel
	cd $(KERNEL_DIR)/tests && $(MAKE)

# 运行内核模块测试
test-kernel: kernel-test
	cd $(KERNEL_DIR)/tests && ./test_runner.sh --all

# Demo application
demo: $(BUILD_DIR)/demo.o liblogloom.a
	$(CC) -o $@ $^ $(LDFLAGS)

# Python bindings
python: userspace
	cd $(SRC_DIR)/bindings/python && python setup.py build

# Test target
test: dirs lang_headers config_headers
	$(MAKE) -f Makefile.test

# Build rules
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD_DIR)/demo.o: demo.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -rf $(BUILD_DIR) liblogloom.a demo include/generated
	cd $(KERNEL_DIR) && ./build.sh clean
	cd $(KERNEL_DIR)/tests && $(MAKE) clean

clean-all: clean
	find . -name "*.o" -delete
	find . -name "*.ko" -delete
	find . -name "*.mod" -delete
	find . -name "*.cmd" -delete
	find . -name "modules.order" -delete
	find . -name "Module.symvers" -delete
	rm -rf $(SRC_DIR)/bindings/python/build
