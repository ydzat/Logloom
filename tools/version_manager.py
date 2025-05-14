#!/usr/bin/env python3
"""
版本管理工具

这个工具负责从中央VERSION文件获取版本号，并生成相应的版本头文件、
更新Python绑定中的版本号，以及提供版本号检查功能。

使用:
  python tools/version_manager.py --generate  # 生成所有版本相关文件
  python tools/version_manager.py --check     # 检查版本号一致性
  python tools/version_manager.py --update    # 更新项目中的所有版本号
  python tools/version_manager.py --set 1.2.1 # 设置新版本号并更新所有引用
"""

import os
import re
import sys
import argparse
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
# 版本文件路径
VERSION_FILE = PROJECT_ROOT / "version" / "VERSION"
# 版本头文件路径
VERSION_HEADER = PROJECT_ROOT / "include" / "generated" / "version.h"
# Python绑定目录
PYTHON_BIND_DIR = PROJECT_ROOT / "src" / "bindings" / "python"
# 内核模块主文件
KERNEL_MAIN = PROJECT_ROOT / "kernel" / "modules" / "logloom_main.c"
# README文件
README_MD = PROJECT_ROOT / "README.md"
README_EN_MD = PROJECT_ROOT / "README_EN.md"

def get_version():
    """获取当前版本号"""
    if not VERSION_FILE.exists():
        print(f"错误: 找不到版本文件 {VERSION_FILE}")
        sys.exit(1)
    
    with open(VERSION_FILE, 'r') as f:
        version = f.read().strip()
    
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        print(f"错误: 无效的版本号格式 '{version}'，应为 X.Y.Z")
        sys.exit(1)
    
    return version

def set_version(new_version):
    """设置新版本号"""
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print(f"错误: 无效的版本号格式 '{new_version}'，应为 X.Y.Z")
        sys.exit(1)
    
    # 更新版本文件
    os.makedirs(VERSION_FILE.parent, exist_ok=True)
    with open(VERSION_FILE, 'w') as f:
        f.write(new_version)
    
    print(f"版本号已更新为 {new_version}")
    return new_version

def generate_version_header(version):
    """生成版本头文件"""
    os.makedirs(VERSION_HEADER.parent, exist_ok=True)
    
    with open(VERSION_HEADER, 'w') as f:
        f.write(f"""/**
 * @file version.h
 * @brief Logloom版本号定义
 * 
 * 此文件由version_manager.py自动生成，请勿手动修改
 */

#ifndef _LOGLOOM_VERSION_H_
#define _LOGLOOM_VERSION_H_

/**
 * 版本号字符串（形如 "X.Y.Z"）
 */
#define LOGLOOM_VERSION "{version}"

/**
 * 主版本号
 */
#define LOGLOOM_VERSION_MAJOR {version.split('.')[0]}

/**
 * 次版本号
 */
#define LOGLOOM_VERSION_MINOR {version.split('.')[1]}

/**
 * 修订版本号
 */
#define LOGLOOM_VERSION_PATCH {version.split('.')[2]}

#endif /* _LOGLOOM_VERSION_H_ */
""")
    
    print(f"已生成版本头文件: {VERSION_HEADER}")

def update_kernel_module(version):
    """更新内核模块版本号"""
    if not KERNEL_MAIN.exists():
        print(f"警告: 找不到内核模块文件 {KERNEL_MAIN}")
        return False
    
    with open(KERNEL_MAIN, 'r') as f:
        content = f.read()
    
    # 更新MODULE_VERSION
    new_content = re.sub(
        r'MODULE_VERSION\("[\d\.]+"',
        f'MODULE_VERSION("{version}"',
        content
    )
    
    # 更新LOGLOOM_MODULE_VERSION
    new_content = re.sub(
        r'#define LOGLOOM_MODULE_VERSION "[\d\.]+"',
        f'#define LOGLOOM_MODULE_VERSION "{version}"',
        new_content
    )
    
    if new_content != content:
        with open(KERNEL_MAIN, 'w') as f:
            f.write(new_content)
        print(f"已更新内核模块版本号: {KERNEL_MAIN}")
        return True
    else:
        print(f"内核模块版本号已是最新: {version}")
        return False

def update_python_binding(version):
    """更新Python绑定版本号"""
    if not PYTHON_BIND_DIR.exists():
        print(f"警告: 找不到Python绑定目录 {PYTHON_BIND_DIR}")
        return False
    
    files_updated = 0
    
    # 更新setup.py
    setup_py = PYTHON_BIND_DIR / "setup.py"
    if setup_py.exists():
        with open(setup_py, 'r') as f:
            content = f.read()
        
        # 更新版本定义行
        new_content = re.sub(
            r"__version__ = '[\d\.]+'",
            f"__version__ = '{version}'",
            content
        )
        
        # 更新setup函数中的version参数
        new_content = re.sub(
            r"version='[\d\.]+'",
            f"version='{version}'",
            new_content
        )
        
        if new_content != content:
            with open(setup_py, 'w') as f:
                f.write(new_content)
            print(f"已更新 {setup_py}")
            files_updated += 1
    
    # 更新__init__.py文件
    for init_file in PYTHON_BIND_DIR.glob("**/__init__.py"):
        with open(init_file, 'r') as f:
            content = f.read()
        
        # 更新版本定义行
        new_content = re.sub(
            r"__version__ = ['\"][\d\.]+['\"]",
            f'__version__ = "{version}"',
            content
        )
        
        if new_content != content:
            with open(init_file, 'w') as f:
                f.write(new_content)
            print(f"已更新 {init_file}")
            files_updated += 1
    
    # 更新PKG-INFO文件（如果存在）
    pkg_info_file = PYTHON_BIND_DIR / "logloom.egg-info" / "PKG-INFO"
    if pkg_info_file.exists():
        # 读取所有行，只修改Version行
        lines = []
        modified = False
        
        with open(pkg_info_file, 'r') as f:
            for line in f:
                if line.startswith('Version:'):
                    new_line = f'Version: {version}\n'
                    if line != new_line:
                        lines.append(new_line)
                        modified = True
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
        
        if modified:
            # 写回文件
            with open(pkg_info_file, 'w') as f:
                f.writelines(lines)
            print(f"已更新 {pkg_info_file}")
            files_updated += 1
    
    print(f"Python绑定版本更新完成，共更新 {files_updated} 个文件")
    return files_updated > 0

def update_readme(version):
    """更新README中的版本标记"""
    files_updated = 0
    
    # 更新中文README
    if README_MD.exists():
        with open(README_MD, 'r') as f:
            content = f.read()
        
        new_content = re.sub(
            r'版本-[\d\.]+-blue',
            f'版本-{version}-blue',
            content
        )
        
        if new_content != content:
            with open(README_MD, 'w') as f:
                f.write(new_content)
            print(f"已更新 {README_MD}")
            files_updated += 1
    
    # 更新英文README
    if README_EN_MD.exists():
        with open(README_EN_MD, 'r') as f:
            content = f.read()
        
        new_content = re.sub(
            r'version-[\d\.]+-blue',
            f'version-{version}-blue',
            content
        )
        
        if new_content != content:
            with open(README_EN_MD, 'w') as f:
                f.write(new_content)
            print(f"已更新 {README_EN_MD}")
            files_updated += 1
    
    print(f"README版本更新完成，共更新 {files_updated} 个文件")
    return files_updated > 0

def check_version_consistency(version):
    """检查项目中的版本号一致性"""
    inconsistent_files = []
    
    # 检查内核模块
    if KERNEL_MAIN.exists():
        with open(KERNEL_MAIN, 'r') as f:
            content = f.read()
        
        module_version_match = re.search(r'MODULE_VERSION\("([\d\.]+)"', content)
        module_version = module_version_match.group(1) if module_version_match else None
        
        macro_version_match = re.search(r'#define LOGLOOM_MODULE_VERSION "([\d\.]+)"', content)
        macro_version = macro_version_match.group(1) if macro_version_match else None
        
        if module_version != version or macro_version != version:
            inconsistent_files.append((KERNEL_MAIN, f"期望 {version}, 实际 MODULE_VERSION={module_version}, LOGLOOM_MODULE_VERSION={macro_version}"))
    
    # 检查Python绑定
    for init_file in PYTHON_BIND_DIR.glob("**/__init__.py"):
        with open(init_file, 'r') as f:
            content = f.read()
        
        version_match = re.search(r"__version__ = ['\"]([^'\"]+)['\"]", content)
        if version_match:
            file_version = version_match.group(1)
            if file_version != version:
                inconsistent_files.append((init_file, f"期望 {version}, 实际 {file_version}"))
    
    # 检查setup.py
    setup_py = PYTHON_BIND_DIR / "setup.py"
    if setup_py.exists():
        with open(setup_py, 'r') as f:
            content = f.read()
        
        # 检查两处版本定义
        version_match1 = re.search(r"__version__ = '([^']+)'", content)
        version_match2 = re.search(r"version='([^']+)'", content)
        
        if version_match1:
            file_version1 = version_match1.group(1)
            if file_version1 != version:
                inconsistent_files.append((setup_py, f"期望 {version}, __version__={file_version1}"))
        
        if version_match2:
            file_version2 = version_match2.group(1)
            if file_version2 != version:
                inconsistent_files.append((setup_py, f"期望 {version}, setup version={file_version2}"))
    
    # 报告不一致
    if inconsistent_files:
        print("发现版本号不一致:")
        for file_path, message in inconsistent_files:
            print(f"  - {file_path}: {message}")
        return False
    else:
        print(f"版本号检查通过: 所有文件一致使用版本 {version}")
        return True

def main():
    parser = argparse.ArgumentParser(description="Logloom版本管理工具")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--generate", action="store_true", help="生成版本文件")
    group.add_argument("--check", action="store_true", help="检查版本号一致性")
    group.add_argument("--update", action="store_true", help="更新所有版本号")
    group.add_argument("--set", metavar="VERSION", help="设置新版本号并更新所有引用")
    
    args = parser.parse_args()
    
    if args.set:
        version = set_version(args.set)
        generate_version_header(version)
        update_kernel_module(version)
        update_python_binding(version)
        update_readme(version)
        print(f"已将所有版本号更新为 {version}")
    elif args.generate or args.update:
        version = get_version()
        generate_version_header(version)
        if args.update:
            update_kernel_module(version)
            update_python_binding(version)
            update_readme(version)
    elif args.check:
        version = get_version()
        check_version_consistency(version)
    else:
        version = get_version()
        print(f"当前版本: {version}")
        print("使用 --generate, --check, --update 或 --set 选项")

if __name__ == "__main__":
    main()