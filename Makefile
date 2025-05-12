# Logloom Makefile

CC = gcc
CFLAGS = -Wall -Werror -g -I./include -fPIC
LDFLAGS = -ldl -pthread  # For plugin loading and threading

# 编译目标
.PHONY: all clean test dirs lang_headers config_headers kernel userspace kernel-test api-check api-check-html api-check-regex python python-install python-test

# Directories
SRC_DIR = src
BUILD_DIR = build
INCLUDE_DIR = include
TEST_DIR = tests
LANG_DIR = locales
KERNEL_DIR = kernel
CORE_DIR = $(SRC_DIR)/core
USERSPACE_DIR = $(SRC_DIR)/userspace
PYTHON_DIR = $(SRC_DIR)/bindings/python
PYTHON_PLUGIN_DIR = $(PYTHON_DIR)/plugin
PYTHON_TEST_DIR = $(TEST_DIR)/python

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
	cd $(PYTHON_DIR) && python setup.py build

# Python安装目标 (用户级)
python-install: python
	cd $(PYTHON_DIR) && pip install --user .

# 系统级安装 (需要root权限)
install: userspace python
	# 安装C库
	install -D -m 644 liblogloom.a /usr/local/lib/liblogloom.a
	install -d /usr/local/include/logloom
	install -m 644 $(INCLUDE_DIR)/*.h /usr/local/include/logloom/
	cp -r $(INCLUDE_DIR)/generated /usr/local/include/logloom/
	# 安装Python绑定和插件系统 (系统级)
	cd $(PYTHON_DIR) && pip install .

# Python插件系统测试
python-test: python
	# 配置PYTHONPATH以包含当前构建的Python绑定
	cd $(PYTHON_DIR)/build && find . -name "*.so" -o -name "logloom*.py" | sort
	PYTHONPATH=$(PYTHON_DIR):$(PYTHON_DIR)/build/lib.linux-x86_64-cpython-312 \
	LOGLOOM_DEBUG=1 \
	python -c "import sys; print('Python路径:', sys.path); import logloom; print('Logloom已导入')"
	PYTHONPATH=$(PYTHON_DIR):$(PYTHON_DIR)/build/lib.linux-x86_64-cpython-312 \
	LOGLOOM_DEBUG=1 \
	python $(PYTHON_TEST_DIR)/test_python_plugins.py

# API一致性检查目标
api-check:
	@if [ ! -d "./venv/api_check_env" ]; then \
		echo "Creating API check virtual environment..."; \
		mkdir -p ./venv; \
		/usr/bin/python3 -m venv ./venv/api_check_env; \
		. ./venv/api_check_env/bin/activate && pip install pyyaml clang==19.1.7; \
	fi
	source ./venv/api_check_env/bin/activate && \
	./tools/api_consistency_check.py --include-dir $(INCLUDE_DIR) --src-dir $(SRC_DIR) --python-dir $(SRC_DIR)/bindings/python \
	--rules tools/api_consistency_rules.yaml --verbose

# 使用正则表达式解析器进行API一致性检查（更健壮但不太精确）
api-check-regex:
	source ./venv/api_check_env/bin/activate && \
	./tools/api_consistency_check.py --include-dir $(INCLUDE_DIR) --src-dir $(SRC_DIR) --python-dir $(SRC_DIR)/bindings/python \
	--rules tools/api_consistency_rules.yaml --verbose --regex-parser

# 生成API一致性检查HTML报告
api-check-html:
	./tools/api_consistency_check.py --include-dir $(INCLUDE_DIR) --src-dir $(SRC_DIR) --python-dir $(SRC_DIR)/bindings/python --rules tools/api_consistency_rules.yaml --output html --output-file api_consistency_report.html --verbose
	@echo "HTML报告已生成: api_consistency_report.html"

# Test target
test: dirs lang_headers config_headers
	$(MAKE) -f Makefile.test
	$(MAKE) python-test

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
	rm -rf $(PYTHON_DIR)/build $(PYTHON_DIR)/*.egg-info $(PYTHON_DIR)/dist
