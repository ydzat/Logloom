# Logloom Makefile

CC = gcc
CFLAGS = -Wall -Werror -g -I./include 
LDFLAGS = -ldl  # For plugin loading

# Directories
SRC_DIR = src
BUILD_DIR = build
INCLUDE_DIR = include
TEST_DIR = tests
LANG_DIR = locales

# Source files
LANG_SRC = $(wildcard $(SRC_DIR)/lang/*.c)
CONFIG_SRC = $(wildcard $(SRC_DIR)/config/*.c)
LOG_SRC = $(wildcard $(SRC_DIR)/log/*.c)
PLUGIN_SRC = $(wildcard $(SRC_DIR)/plugin/*.c)

# Object files
LANG_OBJ = $(patsubst $(SRC_DIR)/%.c,$(BUILD_DIR)/%.o,$(LANG_SRC))
CONFIG_OBJ = $(patsubst $(SRC_DIR)/%.c,$(BUILD_DIR)/%.o,$(CONFIG_SRC))
LOG_OBJ = $(patsubst $(SRC_DIR)/%.c,$(BUILD_DIR)/%.o,$(LOG_SRC))
PLUGIN_OBJ = $(patsubst $(SRC_DIR)/%.c,$(BUILD_DIR)/%.o,$(PLUGIN_SRC))

# Main targets
all: dirs lang_headers config_headers liblogloom.a demo

dirs:
	mkdir -p $(BUILD_DIR)/lang $(BUILD_DIR)/config $(BUILD_DIR)/log $(BUILD_DIR)/plugin $(INCLUDE_DIR)/generated

# Language headers generation
lang_headers:
	python tools/generate_lang_headers.py

# Config headers generation
config_headers:
	./tools/gen_config_header.py config.yaml $(INCLUDE_DIR)/generated/config_gen.h

# Static library
liblogloom.a: $(LANG_OBJ) $(CONFIG_OBJ) $(LOG_OBJ) $(PLUGIN_OBJ)
	ar rcs $@ $^

# Demo application
demo: $(BUILD_DIR)/demo.o liblogloom.a
	$(CC) -o $@ $^ $(LDFLAGS)

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

.PHONY: all clean test dirs lang_headers config_headers
