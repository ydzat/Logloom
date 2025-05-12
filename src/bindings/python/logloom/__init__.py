"""
Logloom Python Package
======================

A Python interface for the Logloom logging and internationalization library.
"""

# 从 logloom_py 中导入所有 API
try:
    from logloom_py import *
except ImportError:
    # 在安装之前可能无法导入，所以这里我们提供一个提示
    import sys
    sys.stderr.write("Warning: logloom_py module not found. Make sure Logloom is properly installed.\n")

# 版本信息
__version__ = '0.1.0'