# Logloom Kernel Test Module Makefile

obj-m += logloom_test.o

KERNELDIR ?= /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)
LOGLOOM_ROOT := $(PWD)/../..
LOGLOOM_INCLUDE := $(LOGLOOM_ROOT)/include
KERNEL_INCLUDE := $(PWD)/../include
KERNEL_MODULE_DIR := $(PWD)/..

# 添加构建标记，包含必要的头文件目录
ccflags-y := -I$(KERNEL_INCLUDE) -I$(LOGLOOM_INCLUDE)

# 指定依赖模块的符号表位置
KBUILD_EXTRA_SYMBOLS := $(KERNEL_MODULE_DIR)/Module.symvers

all:
	@echo "Building Logloom test module..."
	$(MAKE) -C $(KERNELDIR) M=$(PWD) modules
	@echo "Done!"

clean:
	@echo "Cleaning Logloom test module..."
	$(MAKE) -C $(KERNELDIR) M=$(PWD) clean
	@echo "Done!"

install:
	@echo "Installing Logloom test module..."
	sudo insmod logloom_test.ko
	@echo "Test module installed. Run tests by checking /proc/logloom_test"
	@echo "Or trigger tests by running: echo run > /proc/logloom_test"

uninstall:
	@echo "Uninstalling Logloom test module..."
	sudo rmmod logloom_test
	@echo "Test module uninstalled."

test:
	@echo "Running full test sequence..."
	@if lsmod | grep -q "logloom"; then \
		echo "Logloom module loaded, proceeding with tests"; \
	else \
		echo "Error: Logloom module not loaded. Please load it first."; \
		exit 1; \
	fi
	$(MAKE) all
	$(MAKE) install
	@echo "Waiting 1 second for test execution..."
	@sleep 1
	@cat /proc/logloom_test
	$(MAKE) uninstall

.PHONY: all clean install uninstall test