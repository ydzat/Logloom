#!/usr/bin/env python3

import os
import yaml
import re
import sys

INCLUDE_DIR = "include/generated"
LOCALE_DIR = "locales"

def create_dir_if_not_exists(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def validate_key(key):
    """验证键名是否合法"""
    if not re.match(r'^[a-z0-9_]+(\.[a-z0-9_]+)*$', key):
        return False
    return True

def flatten_yaml(yaml_data, prefix=""):
    """将嵌套的YAML结构平铺为键值对"""
    items = []
    for key, value in yaml_data.items():
        new_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            items.extend(flatten_yaml(value, new_key))
        else:
            items.append((new_key, value))
    return items

def generate_header_file(lang_code, lang_data):
    """为特定语言生成C头文件"""
    output_file = f"{INCLUDE_DIR}/lang_{lang_code}.h"
    
    with open(output_file, 'w') as f:
        f.write(f"// 自动生成的语言头文件: {lang_code}\n")
        f.write(f"// 请勿手动修改\n\n")
        
        f.write("#ifndef LOGLOOM_LANG_" + lang_code.upper() + "_H\n")
        f.write("#define LOGLOOM_LANG_" + lang_code.upper() + "_H\n\n")
        
        # 引入公共类型定义
        f.write('#include "lang_types.h"\n\n')
        
        # 写入静态数组
        f.write(f"static const lang_entry_t {lang_code}_lang_table[] = {{\n")
        
        # 平铺所有键值对
        entries = flatten_yaml(lang_data)
        for key, value in entries:
            if not validate_key(key):
                print(f"警告: 非法键名 '{key}', 已跳过")
                continue
            f.write(f'    {{"{key}", "{value}"}},\n')
        
        # 结束数组
        f.write("    {NULL, NULL}\n")
        f.write("};\n\n")
        
        # 生成宏定义
        f.write("// 语言键宏定义\n")
        for key, _ in entries:
            if not validate_key(key):
                continue
            macro_name = "LOGLOOM_LANG_" + key.upper().replace(".", "_")
            f.write(f'#define {macro_name} "{key}"\n')
        
        f.write("\n#endif // LOGLOOM_LANG_" + lang_code.upper() + "_H\n")
    
    print(f"生成语言头文件: {output_file}")

def generate_registry_header(lang_codes):
    """生成语言注册表头文件"""
    registry_file = f"{INCLUDE_DIR}/lang_registry.h"
    
    with open(registry_file, 'w') as f:
        f.write("// 自动生成的语言注册表头文件\n")
        f.write("// 请勿手动修改\n\n")
        
        f.write("#ifndef LOGLOOM_LANG_REGISTRY_H\n")
        f.write("#define LOGLOOM_LANG_REGISTRY_H\n\n")
        
        # 引入公共类型定义
        f.write('#include "lang_types.h"\n')
        f.write('#include <string.h>  // 为 strcmp 函数\n\n')
        
        # 包含所有语言头文件
        for lang in lang_codes:
            f.write(f'#include "lang_{lang}.h"\n')
        
        f.write("\n")
        
        # 生成注册表函数
        f.write("static inline const lang_entry_t* get_lang_table(const char* lang_code) {\n")
        for lang in lang_codes:
            f.write(f'    if (strcmp(lang_code, "{lang}") == 0) return {lang}_lang_table;\n')
        f.write("    return NULL;\n")
        f.write("}\n\n")
        
        f.write("#endif // LOGLOOM_LANG_REGISTRY_H\n")
    
    print(f"生成语言注册表: {registry_file}")

def main():
    # 创建输出目录
    create_dir_if_not_exists(INCLUDE_DIR)
    
    # 查找所有语言文件
    lang_files = []
    for file in os.listdir(LOCALE_DIR):
        if file.endswith('.yaml'):
            lang_files.append(file)
    
    if not lang_files:
        print(f"错误: 在 {LOCALE_DIR} 目录下没有找到语言文件")
        return 1
        
    lang_codes = []
    
    # 处理每个语言文件
    for file in lang_files:
        lang_code = file.replace('.yaml', '')
        lang_codes.append(lang_code)
        
        # 加载YAML文件
        yaml_file = os.path.join(LOCALE_DIR, file)
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                lang_data = yaml.safe_load(f)
                if not lang_data or not isinstance(lang_data, dict):
                    print(f"错误: {yaml_file} 格式不正确")
                    continue
                
                # 生成头文件
                generate_header_file(lang_code, lang_data)
        except Exception as e:
            print(f"处理 {yaml_file} 时发生错误: {e}")
    
    # 生成注册表文件
    generate_registry_header(lang_codes)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
