#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Logloom API 一致性自动化测试系统

该工具用于自动验证头文件、实现文件和Python绑定的API一致性。
通过分析代码，它可以检测并报告以下问题：
- 头文件声明与实现文件定义的不一致
- 函数参数名称、类型或顺序的不匹配
- 返回类型的不匹配
- Python绑定中的API映射错误

使用方法:
    python3 api_consistency_check.py [选项]

选项:
    --include-dir DIR    指定头文件目录
    --src-dir DIR        指定源文件目录
    --python-dir DIR     指定Python绑定目录
    --output FORMAT      输出格式: text, json, html (默认: text)
    --rules FILE         规则配置文件
    --verbose            启用详细输出
    --fix                尝试自动修复不一致问题
"""

import argparse
import json
import os
import re
import sys
import yaml
import ctypes
from collections import defaultdict
from enum import Enum, auto
from typing import Dict, List, Set, Tuple, Optional, Any, Union

# 版本信息
__version__ = '0.1.0'

# 全局标志，控制是否使用正则表达式解析器
USE_REGEX_FALLBACK = False

try:
    # 尝试手动加载libclang库
    possible_paths = [
        '/usr/lib64/libclang.so',
        '/usr/lib/libclang.so',
        '/usr/lib64/libclang.so.19.1',
        '/usr/lib64/libclang.so.19.1.7',
        '/usr/local/lib/libclang.so'
    ]
    
    libclang = None
    for lib_path in possible_paths:
        if os.path.exists(lib_path):
            try:
                os.environ['LIBCLANG_LIBRARY_PATH'] = lib_path
                # 尝试手动加载库
                libclang = ctypes.CDLL(lib_path)
                print(f"成功加载libclang库: {lib_path}")
                break
            except Exception as e:
                print(f"尝试加载 {lib_path} 时出错: {e}")
    
    # 如果找到并加载了libclang，尝试导入Python绑定
    if libclang:
        import clang.cindex
        from clang.cindex import Index, Config, CursorKind, TypeKind
        
        # 明确指定库路径
        if 'LIBCLANG_LIBRARY_PATH' in os.environ:
            Config.set_library_file(os.environ['LIBCLANG_LIBRARY_PATH'])
        
        # 测试libclang是否真的可用
        try:
            test_index = Index.create()
            USE_REGEX_FALLBACK = False
            print("成功初始化libclang，将使用AST分析模式")
        except Exception as e:
            print(f"libclang初始化失败: {e}")
            USE_REGEX_FALLBACK = True
    else:
        print("未能找到兼容的libclang库")
        USE_REGEX_FALLBACK = True
except ImportError:
    print("警告: 未找到clang和libclang Python绑定。将使用正则表达式备选解析器。")
    print("如需更精确的解析，请安装必要的依赖: pip install clang libclang")
    USE_REGEX_FALLBACK = True
except Exception as e:
    print(f"警告: libclang加载失败: {e}")
    print("将使用正则表达式备选解析器。")
    USE_REGEX_FALLBACK = True

# 问题严重性级别
class Severity(Enum):
    INFO = auto()
    WARNING = auto()
    ERROR = auto()

# ANSI颜色代码
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    
    @classmethod
    def colorize(cls, text, color):
        return f"{color}{text}{cls.RESET}"

# API信息结构
class APIFunction:
    def __init__(self, name, return_type, params, location, is_declaration=True):
        self.name = name
        self.return_type = return_type
        self.params = params  # [(type, name), ...]
        self.location = location  # (文件, 行, 列)
        self.is_declaration = is_declaration  # 是否为声明（而非定义）
    
    def __repr__(self):
        param_str = ", ".join([f"{t} {n}" for t, n in self.params])
        return f"{self.return_type} {self.name}({param_str})"
    
    def to_dict(self):
        return {
            'name': self.name,
            'return_type': self.return_type,
            'params': self.params,
            'location': self.location,
            'is_declaration': self.is_declaration
        }

# 不一致问题记录
class InconsistencyIssue:
    def __init__(self, func_name, issue_type, severity, message, locations=None, suggestion=None):
        self.func_name = func_name
        self.issue_type = issue_type
        self.severity = severity
        self.message = message
        self.locations = locations or []  # [(文件, 行, 列), ...]
        self.suggestion = suggestion
    
    def __repr__(self):
        return f"{self.severity.name}: {self.func_name} - {self.message}"
    
    def to_dict(self):
        return {
            'func_name': self.func_name,
            'issue_type': self.issue_type,
            'severity': self.severity.name,
            'message': self.message,
            'locations': self.locations,
            'suggestion': self.suggestion
        }

class APIParser:
    """C/C++代码解析器，使用libclang提取API信息"""
    
    def __init__(self, include_dirs=None):
        self.index = Index.create()
        self.include_dirs = include_dirs or []
    
    def parse_file(self, filepath):
        """解析单个文件，提取API信息"""
        if not os.path.exists(filepath):
            print(f"错误: 文件不存在 - {filepath}")
            return []
        
        try:
            # 读取原始文件内容
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            # 预处理内容：
            # 1. 移除所有的#include行
            # 2. 添加我们自己的头文件定义
            processed_content = re.sub(r'#\s*include\s*(<[^>]*>|"[^"]*")', '//#include', original_content)
            
            # 添加我们自己的标准定义
            stub_headers = """
/* 标准类型定义 */
#ifndef _STDBOOL_H
#define _STDBOOL_H
#ifndef __cplusplus
typedef int bool;
#define true 1
#define false 0
#endif
#endif

#ifndef _STDDEF_H
#define _STDDEF_H
#define NULL ((void *)0)
typedef unsigned long size_t;
typedef long ssize_t;
#endif

#ifndef _STDARG_H
#define _STDARG_H
typedef void* va_list;
#define va_start(v,l)
#define va_end(v)
#define va_arg(v,l) ((l)0)
#define va_copy(d,s)
#endif

#ifndef _STDIO_H
#define _STDIO_H
typedef struct FILE FILE;
#define EOF (-1)
#endif

/* Python 头文件模拟 */
#ifndef _PYTHON_H
#define _PYTHON_H
typedef struct _object PyObject;
typedef PyObject *(*PyCFunction)(PyObject *, PyObject *);
typedef long Py_ssize_t;
#define PyMODINIT_FUNC PyObject*
struct PyMethodDef {
    const char* ml_name;
    PyCFunction ml_meth;
    int ml_flags;
    const char* ml_doc;
};
typedef struct PyMethodDef PyMethodDef;
#define METH_VARARGS 0x0001
#define METH_KEYWORDS 0x0002
#define Py_BuildValue(fmt, ...) NULL
#define PyModule_AddObject(m, name, o) 0
#define PyModule_AddStringConstant(m, name, s) 0
#define PyModule_AddIntConstant(m, name, i) 0
#define PyModule_AddFunctions(m, f) 0
#define PyModule_Create(d) NULL
#define Py_RETURN_NONE return NULL
#define PyArg_ParseTuple(a, fmt, ...) 0
#define Py_None NULL
#endif

/* 自定义项目头文件 */
#define LANG_EN_H_INCLUDED
#define LANG_ZH_H_INCLUDED
#define CONFIG_GEN_H_INCLUDED
#define LOGLOOM_CONFIG_H
#define LOGLOOM_LOG_H
#define LOGLOOM_LANG_H
#define LOGLOOM_LANG_TYPES_H
#define LOGLOOM_PLUGIN_H

/* GNU扩展属性 */
#define __attribute__(x)
#define __extension__
#define __inline inline
#define __asm__(x)
#define __restrict
"""
            # 组合内容
            combined_content = stub_headers + processed_content
            
            # 创建unsaved文件
            unsaved_files = [(filepath, combined_content)]
            
            # 准备解析参数
            args = [
                '-x', 'c',
                '-std=gnu11', 
                '-Wno-pragma-once-outside-header',  # 禁用警告
                '-D__linux__',
                '-D__x86_64__'
            ]
            
            # 添加include目录
            for inc_dir in self.include_dirs:
                if os.path.exists(inc_dir):
                    args.append(f'-I{inc_dir}')
            
            # 解析选项
            options = clang.cindex.TranslationUnit.PARSE_INCOMPLETE | clang.cindex.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES
            
            # 使用unsaved文件解析
            tu = self.index.parse(filepath, args=args, unsaved_files=unsaved_files, options=options)
            
            # 收集函数
            functions = []
            
            # 检查错误但继续解析
            diag_count = 0
            for diag in tu.diagnostics:
                if diag.severity >= 3:  # 错误或致命错误
                    diag_count += 1
                    if diag_count <= 1:  # 限制错误消息以免刷屏
                        print(f"解析警告 ({os.path.basename(filepath)}): {diag.spelling}")
                    
            # 处理AST
            self._process_cursors(tu.cursor, functions, filepath)
            
            # 报告结果
            if functions:
                print(f"成功从 {os.path.basename(filepath)} 中提取了 {len(functions)} 个函数")
            
            return functions
        except Exception as e:
            print(f"解析文件时出错 - {filepath}: {e}")
            import traceback
            traceback.print_exc()
            return []
        
    def _process_cursors(self, cursor, functions, source_file):
        """处理AST光标，提取函数声明和定义"""
        # 检查是否是函数声明
        if cursor.kind == CursorKind.FUNCTION_DECL:
            # 过滤掉宏定义的函数名
            name = cursor.spelling
            if name and not name.startswith('__builtin_'):
                # 获取函数返回类型
                return_type = cursor.result_type.spelling
                # 获取参数
                params = []
                for arg in cursor.get_arguments():
                    params.append((arg.type.spelling, arg.spelling or ''))
                
                # 获取位置信息
                location = (source_file, cursor.extent.start.line, cursor.extent.start.column)
                
                # 确定是声明还是定义
                is_declaration = not cursor.is_definition()
                
                functions.append(APIFunction(name, return_type, params, location, is_declaration))
        
        # 递归处理子节点
        for child in cursor.get_children():
            if child.location.file and child.location.file.name == source_file:
                self._process_cursors(child, functions, source_file)
    
    def parse_directory(self, dirpath, file_pattern=r'.*\.(h|c|cpp)$'):
        """解析目录中的所有匹配文件"""
        pattern = re.compile(file_pattern)
        functions = []
        
        # 收集所有匹配的文件
        for root, _, files in os.walk(dirpath):
            for file in files:
                if pattern.match(file):
                    filepath = os.path.join(root, file)
                    functions.extend(self.parse_file(filepath))
        
        return functions

class RegexAPIParser:
    """使用正则表达式的备选API解析器，当libclang不可用时使用"""
    
    def __init__(self, include_dirs=None):
        self.include_dirs = include_dirs or []
    
    def parse_file(self, filepath):
        """使用正则表达式解析文件中的函数声明和定义"""
        if not os.path.exists(filepath):
            print(f"错误: 文件不存在 - {filepath}")
            return []
        
        functions = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 匹配函数声明/定义
            # 捕获组: 1=返回类型, 2=函数名, 3=参数列表
            func_pattern = re.compile(
                r'(?:extern\s+)?(?:static\s+)?([a-zA-Z_][a-zA-Z0-9_\s*]+[*\s]+)'  # 返回类型
                r'([a-zA-Z_][a-zA-Z0-9_]*)'  # 函数名
                r'\s*\((.*?)\)\s*'  # 参数列表
                r'(?:;|{)',  # 以分号结尾(声明)或花括号开始(定义)
                re.MULTILINE | re.DOTALL
            )
            
            # 从文件名判断是声明还是定义
            is_header = filepath.endswith('.h')
            
            # 提取所有匹配
            for match in func_pattern.finditer(content):
                return_type = match.group(1).strip()
                func_name = match.group(2).strip()
                params_str = match.group(3).strip()
                
                # 解析参数列表
                params = []
                if params_str and params_str != "void":
                    # 分割参数列表，处理逗号在字符串或括号内的情况
                    param_parts = []
                    bracket_level = 0
                    current_part = ""
                    
                    for char in params_str:
                        if char == ',' and bracket_level == 0:
                            param_parts.append(current_part.strip())
                            current_part = ""
                        else:
                            if char == '(':
                                bracket_level += 1
                            elif char == ')':
                                bracket_level -= 1
                            current_part += char
                    
                    if current_part:
                        param_parts.append(current_part.strip())
                    
                    # 从每个参数解析类型和名称
                    for param in param_parts:
                        # 尝试分离类型和名称
                        param = param.strip()
                        if not param:
                            continue
                        
                        # 处理函数指针参数
                        if '(' in param and ')' in param and '*' in param:
                            # 这是一个简化处理，实际上函数指针解析更复杂
                            ptr_pos = param.find('*')
                            name_start = ptr_pos + 1
                            while name_start < len(param) and param[name_start] in ' \t\n*':
                                name_start += 1
                            
                            # 从括号或空格处分割名称
                            name_end = param.find('(', name_start)
                            if name_end == -1:
                                name_end = param.find(' ', name_start)
                            
                            if name_end == -1:
                                param_type = param
                                param_name = ""
                            else:
                                param_type = param[:name_start].strip() + param[name_end:]
                                param_name = param[name_start:name_end].strip()
                        else:
                            # 处理普通参数
                            parts = param.split()
                            if len(parts) == 1:
                                # 只有类型，没有名称
                                param_type = parts[0]
                                param_name = ""
                            else:
                                # 最后一部分是名称，其余是类型
                                param_name = parts[-1]
                                # 处理名称中的指针星号
                                while param_name.startswith('*'):
                                    param_name = param_name[1:]
                                    parts[-2] = parts[-2] + ' *'
                                param_type = ' '.join(parts[:-1])
                        
                        params.append((param_type, param_name))
                
                # 检查是否为定义（通过花括号位置判断）
                pos = match.end()
                is_definition = False
                while pos < len(content) and content[pos].isspace():
                    pos += 1
                if pos < len(content) and content[pos] == '{':
                    is_definition = True
                
                # 合并信息
                line_no = content[:match.start()].count('\n') + 1
                location = (filepath, line_no, 0)  # 列号设置为0，无法精确获取
                is_declaration = not is_definition if not is_header else True
                
                functions.append(APIFunction(func_name, return_type, params, location, is_declaration))
        
        except Exception as e:
            print(f"解析文件时出错 - {filepath}: {e}")
        
        return functions
    
    def parse_directory(self, dirpath, file_pattern=r'.*\.(h|c|cpp)$'):
        """解析目录中所有匹配的文件"""
        pattern = re.compile(file_pattern)
        functions = []
        
        for root, _, files in os.walk(dirpath):
            for file in files:
                if pattern.match(file):
                    filepath = os.path.join(root, file)
                    functions.extend(self.parse_file(filepath))
        
        return functions

class PythonBindingParser:
    """Python绑定代码解析器，提取C/Python API映射关系"""
    
    def __init__(self):
        self.c_to_py_mapping = {}  # C函数名到Python函数名的映射
        self.py_functions = []      # Python函数签名信息
    
    def parse_binding_file(self, filepath):
        """解析Python绑定文件"""
        if not os.path.exists(filepath):
            print(f"错误: 文件不存在 - {filepath}")
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 匹配常见的Python C API绑定模式
        # 1. PyModule_AddFunction模式
        py_module_pattern = re.compile(
            r'PyModule_Add(?:Object|Function)\s*\(\s*\w+\s*,\s*"(\w+)"\s*,\s*(?:\(PyCFunction\))?\s*(\w+)\s*,',
            re.MULTILINE
        )
        
        # 2. 函数映射表模式
        mapping_pattern = re.compile(
            r'(?:PyMethodDef|static\s+PyMethodDef)\s+\w+\[\]\s*=\s*{[^}]*{\s*"(\w+)"\s*,\s*(?:\(PyCFunction\))?\s*(\w+)\s*,',
            re.MULTILINE | re.DOTALL
        )
        
        # 匹配C函数定义
        for match in py_module_pattern.finditer(content):
            py_name, c_name = match.groups()
            self.c_to_py_mapping[c_name] = py_name
        
        for match in mapping_pattern.finditer(content):
            py_name, c_name = match.groups()
            self.c_to_py_mapping[c_name] = py_name

    def parse_directory(self, dirpath):
        """解析Python绑定目录中的所有C文件"""
        for root, _, files in os.walk(dirpath):
            for file in files:
                if file.endswith('.c'):
                    filepath = os.path.join(root, file)
                    self.parse_binding_file(filepath)

class APIComparator:
    """API一致性比较器"""
    
    def __init__(self, rules_config=None):
        self.rules = self._load_rules(rules_config)
        self.issues = []
    
    def _load_rules(self, rules_config):
        """加载规则配置"""
        default_rules = {
            'parameter_names_must_match': Severity.WARNING,
            'return_types_must_match': Severity.ERROR,
            'ignore_patterns': [],
            'type_compatibility': {}
        }
        
        if not rules_config:
            return default_rules
        
        try:
            with open(rules_config, 'r') as f:
                rules = yaml.safe_load(f) or {}
            
            # 转换规则中的严重程度字符串为枚举值
            severity_map = {
                'info': Severity.INFO,
                'warning': Severity.WARNING,
                'error': Severity.ERROR
            }
            
            result = default_rules.copy()
            
            if 'rules' in rules:
                for rule, value in rules['rules'].items():
                    if rule == 'parameter_names_must_match' or rule == 'return_types_must_match':
                        result[rule] = severity_map.get(value.lower(), Severity.WARNING)
                    elif rule == 'ignore_patterns':
                        result[rule] = value
                    elif rule == 'type_compatibility':
                        result[rule] = {}
                        for item in value:
                            source = item.get('source')
                            targets = item.get('target', [])
                            level = severity_map.get(item.get('level', 'warning').lower(), Severity.WARNING)
                            if source and targets:
                                result[rule][source] = {'targets': targets, 'level': level}
            
            return result
        except Exception as e:
            print(f"加载规则配置时出错: {e}")
            return default_rules
    
    def _should_ignore(self, func_name):
        """检查是否应该忽略函数"""
        for pattern in self.rules['ignore_patterns']:
            if re.match(pattern, func_name):
                return True
        return False
    
    def _are_types_compatible(self, type1, type2):
        """检查两个类型是否兼容"""
        if type1 == type2:
            return True
        
        # 检查自定义的类型兼容性规则
        compat = self.rules.get('type_compatibility', {})
        if type1 in compat and type2 in compat[type1].get('targets', []):
            return True
        if type2 in compat and type1 in compat[type2].get('targets', []):
            return True
        
        # 通用兼容性规则
        
        # 1. 指针兼容性
        ptr_pattern = re.compile(r'^(const\s+)?(.+?)(\s+\*+)$')
        m1 = ptr_pattern.match(type1)
        m2 = ptr_pattern.match(type2)
        if m1 and m2:
            # 如果两者都是指针，检查基础类型和是否为const
            # const char* 与 char* 是兼容的（但反向不一定）
            if m1.group(1) and not m2.group(1):  # type1是const但type2不是
                return False
            # 比较基础类型
            return self._are_types_compatible(m1.group(2), m2.group(2))
        
        # 2. 整数类型兼容性
        int_types = {
            'int', 'unsigned int', 'long', 'unsigned long',
            'long long', 'unsigned long long', 'short', 'unsigned short',
            'int32_t', 'uint32_t', 'int64_t', 'uint64_t',
            'int16_t', 'uint16_t', 'int8_t', 'uint8_t',
            'size_t', 'ssize_t', 'intptr_t', 'uintptr_t'
        }
        
        # 考虑整数类型与布尔类型的兼容性
        if (type1 in int_types and type2 == 'bool') or (type2 in int_types and type1 == 'bool'):
            return True
        
        # 其他兼容性检查可以根据需要添加
        
        return False
    
    def compare_declarations_vs_definitions(self, header_funcs, impl_funcs):
        """比较头文件声明与实现文件定义的一致性"""
        # 按函数名组织
        h_funcs_by_name = {}
        for func in header_funcs:
            if func.is_declaration:  # 只关注声明
                h_funcs_by_name[func.name] = func
        
        i_funcs_by_name = {}
        for func in impl_funcs:
            if not func.is_declaration:  # 只关注定义
                i_funcs_by_name[func.name] = func
        
        # 检查每个头文件声明是否有对应的实现
        for name, h_func in h_funcs_by_name.items():
            if self._should_ignore(name):
                continue
                
            if name not in i_funcs_by_name:
                self.issues.append(InconsistencyIssue(
                    name,
                    'missing_implementation',
                    Severity.ERROR,
                    f"函数在头文件中声明但未在实现文件中找到定义",
                    [h_func.location]
                ))
                continue
            
            i_func = i_funcs_by_name[name]
            
            # 检查返回类型
            if not self._are_types_compatible(h_func.return_type, i_func.return_type):
                severity = self.rules.get('return_types_must_match', Severity.ERROR)
                self.issues.append(InconsistencyIssue(
                    name,
                    'return_type_mismatch',
                    severity,
                    f"返回类型不匹配: 头文件为 '{h_func.return_type}'，实现为 '{i_func.return_type}'",
                    [h_func.location, i_func.location],
                    f"将实现文件中的返回类型修改为 '{h_func.return_type}'"
                ))
            
            # 检查参数数量
            if len(h_func.params) != len(i_func.params):
                self.issues.append(InconsistencyIssue(
                    name,
                    'parameter_count_mismatch',
                    Severity.ERROR,
                    f"参数数量不匹配: 头文件有 {len(h_func.params)} 个参数，实现有 {len(i_func.params)} 个",
                    [h_func.location, i_func.location]
                ))
                continue
            
            # 检查参数类型
            for i, ((h_type, h_name), (i_type, i_name)) in enumerate(zip(h_func.params, i_func.params)):
                if not self._are_types_compatible(h_type, i_type):
                    self.issues.append(InconsistencyIssue(
                        name,
                        'parameter_type_mismatch',
                        Severity.ERROR,
                        f"参数 {i+1} 类型不匹配: 头文件为 '{h_type}'，实现为 '{i_type}'",
                        [h_func.location, i_func.location],
                        f"将实现文件中的参数类型修改为 '{h_type}'"
                    ))
                
                # 检查参数名称
                if h_name and i_name and h_name != i_name:
                    severity = self.rules.get('parameter_names_must_match', Severity.WARNING)
                    self.issues.append(InconsistencyIssue(
                        name,
                        'parameter_name_mismatch',
                        severity,
                        f"参数 {i+1} 名称不匹配: 头文件为 '{h_name}'，实现为 '{i_name}'",
                        [h_func.location, i_func.location],
                        f"将实现文件中的参数名称修改为 '{h_name}'"
                    ))
        
        # 检查实现文件中是否有头文件中不存在的函数
        for name, i_func in i_funcs_by_name.items():
            if self._should_ignore(name):
                continue
                
            if name not in h_funcs_by_name:
                # 这可能是内部函数，不是严重错误
                self.issues.append(InconsistencyIssue(
                    name,
                    'undeclared_function',
                    Severity.INFO,
                    f"函数在实现文件中定义但未在头文件中声明（可能是内部函数）",
                    [i_func.location]
                ))
    
    def compare_c_vs_python_bindings(self, c_funcs, py_bindings):
        """比较C API与Python绑定的一致性"""
        # 找出所有被导出到Python的C函数
        exported_funcs = {}
        for c_name, py_name in py_bindings.c_to_py_mapping.items():
            for func in c_funcs:
                if func.name == c_name:
                    exported_funcs[c_name] = (func, py_name)
                    break
        
        # 检查每个C函数的Python绑定是否正确
        for c_name, (c_func, py_name) in exported_funcs.items():
            # 检查Python名称是否符合命名规范
            c_prefix = c_name.split('_')[0]
            py_prefix = py_name.split('_')[0] if '_' in py_name else ''
            
            if c_prefix and py_prefix and c_prefix != py_prefix:
                self.issues.append(InconsistencyIssue(
                    c_name,
                    'inconsistent_python_name',
                    Severity.WARNING,
                    f"Python绑定名称前缀与C函数不一致: '{py_name}'",
                    [c_func.location],
                    f"考虑使用一致的命名前缀"
                ))
            
            # 其他Python绑定特定的检查可以在此添加...

class Reporter:
    """结果报告生成器"""
    
    def __init__(self, format_type='text'):
        self.format = format_type
        
    def generate_report(self, issues, output_file=None):
        """生成报告"""
        if self.format == 'json':
            return self._generate_json_report(issues, output_file)
        elif self.format == 'html':
            return self._generate_html_report(issues, output_file)
        else:  # 默认为文本格式
            return self._generate_text_report(issues, output_file)
    
    def _generate_text_report(self, issues, output_file=None):
        """生成文本格式的报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("Logloom API 一致性检查报告")
        lines.append("=" * 80)
        lines.append("")
        
        if not issues:
            lines.append(Colors.colorize("恭喜！未发现任何API不一致问题。", Colors.GREEN))
        else:
            # 按严重性对问题进行排序
            severity_order = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.INFO: 2}
            sorted_issues = sorted(issues, key=lambda x: severity_order.get(x.severity, 99))
            
            lines.append(f"发现 {len(issues)} 个API不一致问题:")
            lines.append("")
            
            for i, issue in enumerate(sorted_issues, 1):
                # 为不同严重级别使用不同颜色
                severity_color = {
                    Severity.ERROR: Colors.RED,
                    Severity.WARNING: Colors.YELLOW,
                    Severity.INFO: Colors.BLUE
                }.get(issue.severity, Colors.RESET)
                
                lines.append(f"{i}. {Colors.colorize(issue.severity.name, severity_color)}: {issue.func_name}")
                lines.append(f"   问题类型: {issue.issue_type}")
                lines.append(f"   描述: {issue.message}")
                
                for file, line, col in issue.locations:
                    lines.append(f"   位置: {file}:{line}:{col}")
                
                if issue.suggestion:
                    lines.append(f"   建议: {issue.suggestion}")
                
                lines.append("")
            
            # 添加统计信息
            error_count = sum(1 for i in issues if i.severity == Severity.ERROR)
            warning_count = sum(1 for i in issues if i.severity == Severity.WARNING)
            info_count = sum(1 for i in issues if i.severity == Severity.INFO)
            
            lines.append("-" * 80)
            lines.append(f"统计: {Colors.colorize(f'{error_count} 错误', Colors.RED)}, " +
                         f"{Colors.colorize(f'{warning_count} 警告', Colors.YELLOW)}, " +
                         f"{Colors.colorize(f'{info_count} 信息', Colors.BLUE)}")
        
        report = "\n".join(lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                # 去除ANSI颜色代码用于文件输出
                clean_report = re.sub(r'\033\[\d+(;\d+)?m', '', report)
                f.write(clean_report)
        
        return report
    
    def _generate_json_report(self, issues, output_file=None):
        """生成JSON格式的报告"""
        report_data = {
            'summary': {
                'total_issues': len(issues),
                'errors': sum(1 for i in issues if i.severity == Severity.ERROR),
                'warnings': sum(1 for i in issues if i.severity == Severity.WARNING),
                'infos': sum(1 for i in issues if i.severity == Severity.INFO)
            },
            'issues': [issue.to_dict() for issue in issues]
        }
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)
        
        return json.dumps(report_data, indent=2)
    
    def _generate_html_report(self, issues, output_file=None):
        """生成HTML格式的报告"""
        # 创建HTML报告的基本结构
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Logloom API 一致性检查报告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                .summary { margin-bottom: 20px; }
                .issue { margin-bottom: 15px; border-left: 5px solid #ddd; padding-left: 15px; }
                .error { border-color: #f44336; }
                .warning { border-color: #ff9800; }
                .info { border-color: #2196f3; }
                .error-badge { background-color: #f44336; color: white; padding: 2px 6px; border-radius: 3px; }
                .warning-badge { background-color: #ff9800; color: white; padding: 2px 6px; border-radius: 3px; }
                .info-badge { background-color: #2196f3; color: white; padding: 2px 6px; border-radius: 3px; }
                .location { font-family: monospace; margin-top: 5px; }
                .suggestion { margin-top: 5px; color: #4caf50; }
            </style>
        </head>
        <body>
            <h1>Logloom API 一致性检查报告</h1>
            <div class="summary">
                <p>总计发现 {total} 个API不一致问题: 
                   <span class="error-badge">{errors} 错误</span> 
                   <span class="warning-badge">{warnings} 警告</span> 
                   <span class="info-badge">{infos} 信息</span>
                </p>
            </div>
            <div class="issues">
                {issues}
            </div>
        </body>
        </html>
        """
        
        issue_template = """
        <div class="issue {severity_class}">
            <h3>{index}. <span class="{severity_class}-badge">{severity}</span> {func_name}</h3>
            <p><strong>问题类型:</strong> {issue_type}</p>
            <p><strong>描述:</strong> {message}</p>
            <div class="locations">
                {locations}
            </div>
            {suggestion}
        </div>
        """
        
        # 如果没有问题，显示成功消息
        if not issues:
            issues_html = "<div class='issue info'><p>恭喜！未发现任何API不一致问题。</p></div>"
        else:
            # 按严重性排序
            severity_order = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.INFO: 2}
            sorted_issues = sorted(issues, key=lambda x: severity_order.get(x.severity, 99))
            
            issues_html = []
            for i, issue in enumerate(sorted_issues, 1):
                severity_class = issue.severity.name.lower()
                
                # 构建位置HTML
                locations_html = []
                for file, line, col in issue.locations:
                    locations_html.append(f"<div class='location'>{file}:{line}:{col}</div>")
                
                # 构建建议HTML
                suggestion_html = ""
                if issue.suggestion:
                    suggestion_html = f"<p class='suggestion'><strong>建议:</strong> {issue.suggestion}</p>"
                
                # 填充模板
                issues_html.append(issue_template.format(
                    index=i,
                    severity_class=severity_class,
                    severity=issue.severity.name,
                    func_name=issue.func_name,
                    issue_type=issue.issue_type,
                    message=issue.message,
                    locations="\n".join(locations_html),
                    suggestion=suggestion_html
                ))
            
            issues_html = "\n".join(issues_html)
        
        # 统计信息
        error_count = sum(1 for i in issues if i.severity == Severity.ERROR)
        warning_count = sum(1 for i in issues if i.severity == Severity.WARNING)
        info_count = sum(1 for i in issues if i.severity == Severity.INFO)
        
        # 填充主模板
        html_report = html_template.format(
            total=len(issues),
            errors=error_count,
            warnings=warning_count,
            infos=info_count,
            issues=issues_html
        )
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_report)
        
        return html_report

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Logloom API 一致性自动化测试系统")
    
    parser.add_argument('--include-dir', dest='include_dirs', action='append', default=[],
                      help='指定头文件目录 (可以指定多次)')
    parser.add_argument('--src-dir', dest='src_dirs', action='append', default=[],
                      help='指定源文件目录 (可以指定多次)')
    parser.add_argument('--python-dir', dest='python_dirs', action='append', default=[],
                      help='指定Python绑定目录 (可以指定多次)')
    parser.add_argument('--output', choices=['text', 'json', 'html'], default='text',
                      help='输出格式: text, json, html (默认: text)')
    parser.add_argument('--output-file', help='输出文件路径')
    parser.add_argument('--rules', help='规则配置文件路径')
    parser.add_argument('--verbose', action='store_true', help='启用详细输出')
    parser.add_argument('--fix', action='store_true', help='尝试自动修复不一致问题')
    parser.add_argument('--regex-parser', action='store_true', help='强制使用正则表达式解析器，即使libclang可用')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    args = parser.parse_args()
    
    # 检查是否强制使用正则表达式解析器
    global USE_REGEX_FALLBACK
    if args.regex_parser:
        USE_REGEX_FALLBACK = True
        if args.verbose:
            print("已强制使用正则表达式解析器")
    
    # 使用默认目录（如果未提供）
    if not args.include_dirs:
        args.include_dirs = ['include']
    if not args.src_dirs:
        args.src_dirs = ['src']
    if not args.python_dirs:
        args.python_dirs = ['src/bindings/python']
    
    # 初始化解析器
    if args.verbose:
        print("初始化API解析器...")
    
    if USE_REGEX_FALLBACK:
        api_parser = RegexAPIParser(include_dirs=args.include_dirs)
    else:
        api_parser = APIParser(include_dirs=args.include_dirs)
    
    # 解析头文件
    if args.verbose:
        print("解析头文件...")
    
    header_funcs = []
    for include_dir in args.include_dirs:
        if args.verbose:
            print(f"  处理目录: {include_dir}")
        if os.path.exists(include_dir):
            header_funcs.extend(api_parser.parse_directory(include_dir, r'.*\.h$'))
        else:
            print(f"警告: 目录不存在 - {include_dir}")
    
    if args.verbose:
        print(f"  从头文件中提取了 {len(header_funcs)} 个函数声明")
    
    # 解析实现文件
    if args.verbose:
        print("解析实现文件...")
    
    impl_funcs = []
    for src_dir in args.src_dirs:
        if args.verbose:
            print(f"  处理目录: {src_dir}")
        if os.path.exists(src_dir):
            impl_funcs.extend(api_parser.parse_directory(src_dir, r'.*\.c$'))
        else:
            print(f"警告: 目录不存在 - {src_dir}")
    
    if args.verbose:
        print(f"  从实现文件中提取了 {len(impl_funcs)} 个函数定义")
    
    # 解析Python绑定
    py_bindings = PythonBindingParser()
    for python_dir in args.python_dirs:
        if os.path.exists(python_dir):
            if args.verbose:
                print(f"处理Python绑定目录: {python_dir}")
            py_bindings.parse_directory(python_dir)
        else:
            if args.verbose:
                print(f"警告: Python绑定目录不存在 - {python_dir}")
    
    # 比较API一致性
    if args.verbose:
        print("比较API一致性...")
    
    comparator = APIComparator(args.rules)
    comparator.compare_declarations_vs_definitions(header_funcs, impl_funcs)
    comparator.compare_c_vs_python_bindings(header_funcs + impl_funcs, py_bindings)
    
    # 生成并显示报告
    reporter = Reporter(args.output)
    report = reporter.generate_report(comparator.issues, args.output_file)
    
    if args.output == 'text':
        print(report)
    elif args.verbose and args.output_file:
        print(f"报告已保存到: {args.output_file}")
    
    # 返回状态码
    # 如果存在错误级别的问题，返回1，否则返回0
    has_errors = any(issue.severity == Severity.ERROR for issue in comparator.issues)
    return 1 if has_errors else 0

if __name__ == "__main__":
    sys.exit(main())