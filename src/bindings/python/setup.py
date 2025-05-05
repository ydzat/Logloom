from setuptools import setup, Extension
import os

# 获取Logloom库的路径
LOGLOOM_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
LOGLOOM_LIB = os.path.join(LOGLOOM_ROOT, 'liblogloom.a')
LOGLOOM_INCLUDE = os.path.join(LOGLOOM_ROOT, 'include')

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
    version='0.1.0',
    description='Python bindings for Logloom logging and internationalization library',
    author='Logloom Team',
    author_email='info@logloom.example',
    url='https://github.com/yourusername/logloom',
    ext_modules=[logloom_module],
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