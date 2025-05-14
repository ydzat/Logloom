from setuptools import setup, Extension, find_packages
import os
import shutil

# 获取Logloom库的路径
LOGLOOM_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
LOGLOOM_LIB = os.path.join(LOGLOOM_ROOT, 'liblogloom.a')
LOGLOOM_INCLUDE = os.path.join(LOGLOOM_ROOT, 'include')

# 确保插件系统包结构正确
# 这将在构建时将插件系统模块复制到logloom.plugin包中
def ensure_plugin_structure():
    # 源目录
    plugin_src_dir = os.path.join(os.path.dirname(__file__), 'plugin')
    # 目标目录 - logloom.plugin
    plugin_logloom_dst_dir = os.path.join(os.path.dirname(__file__), 'logloom', 'plugin')
    # 目标目录 - logloom_py.plugin
    plugin_logloom_py_dst_dir = os.path.join(os.path.dirname(__file__), 'logloom_py', 'plugin')
    
    # 确保目标目录存在
    os.makedirs(plugin_logloom_dst_dir, exist_ok=True)
    os.makedirs(plugin_logloom_py_dst_dir, exist_ok=True)
    
    # 复制文件到logloom.plugin
    for item in os.listdir(plugin_src_dir):
        src_item = os.path.join(plugin_src_dir, item)
        logloom_dst_item = os.path.join(plugin_logloom_dst_dir, item)
        logloom_py_dst_item = os.path.join(plugin_logloom_py_dst_dir, item)
        
        # 如果是Python文件或包，复制到目标目录
        if os.path.isfile(src_item) and (item.endswith('.py') or item == '__init__.py'):
            shutil.copy2(src_item, logloom_dst_item)
            print(f"Copied {src_item} -> {logloom_dst_item}")
            
            # 也复制到logloom_py.plugin目录
            shutil.copy2(src_item, logloom_py_dst_item)
            print(f"Copied {src_item} -> {logloom_py_dst_item}")

# 确保logloom_py根模块存在
def create_logloom_py_module():
    logloom_py_dir = os.path.join(os.path.dirname(__file__), 'logloom_py')
    os.makedirs(logloom_py_dir, exist_ok=True)
    
    # 创建__init__.py文件
    init_file = os.path.join(logloom_py_dir, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write("""\"\"\"
Logloom Python Bindings
==================

Python bindings for Logloom logging and internationalization library.
\"\"\"

# 设置版本
__version__ = '1.1.0'

# 导入子模块
try:
    from . import plugin
except ImportError:
    import sys
    sys.stderr.write("警告: 无法导入插件子模块。\\n")
""")
        print(f"Created {init_file}")

# 确保插件系统结构正确
create_logloom_py_module()
ensure_plugin_structure()

# 定义扩展模块
logloom_module = Extension(
    'logloom',
    sources=['logloom_module.c'],
    include_dirs=[LOGLOOM_INCLUDE],
    extra_objects=[LOGLOOM_LIB],
    # 根据需要添加其他编译选项
    extra_compile_args=['-Wall', '-O2'],
)

# 设置包信息
setup(
    name='logloom',
    version='1.1.0',
    description='Python bindings for Logloom logging and internationalization library',
    author='Logloom Team',
    author_email='info@logloom.example',
    url='https://github.com/yourusername/logloom',
    ext_modules=[logloom_module],
    packages=['logloom_py', 'logloom_py.plugin', 'logloom', 'logloom.plugin'],
    package_data={
        'logloom_py': ['*.py'],
        'logloom_py.plugin': ['*.py'],
        'logloom': ['*.py'],
        'logloom.plugin': ['*.py'],
    },
    # 创建命令行工具
    entry_points={
        'console_scripts': [
            'logloom-plugin-manager=logloom_py.plugin.manager:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: C',
        'Topic :: System :: Logging',
        'Topic :: Software Development :: Internationalization',
    ],
    python_requires='>=3.6',
)