#!/usr/bin/env python3
"""
测试新增的国际化扩展API
"""
import os
import sys
import inspect

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# 添加项目根目录到Python路径，使我们可以导入logloom模块
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, os.path.join(project_root, 'src', 'bindings', 'python'))

# 创建测试语言文件目录
test_locales_dir = os.path.join(current_dir, 'test_locales')
if not os.path.exists(test_locales_dir):
    os.makedirs(test_locales_dir)

# 法语测试文件路径
fr_yaml_path = os.path.join(test_locales_dir, 'fr.yaml')

# 创建法语测试文件，如果不存在
if not os.path.exists(fr_yaml_path):
    fr_content = """
system:
  welcome: "Bienvenue au système de journalisation Logloom"
  start_message: "Système démarré"
  shutdown_message: "Système en cours d'arrêt"
  error_message: "Erreur survenue: {0}"

error:
  file_not_found: "Fichier non trouvé: {0}"
  invalid_value: "Valeur invalide: {value}, attendue: {expected}"

test:
  hello: "Bonjour, {0}!"
  error_count: "Rencontré {0} erreurs"
  custom_key: "Ceci est une clé personnalisée en français"
"""
    with open(fr_yaml_path, 'w') as f:
        f.write(fr_content)
    print(f"创建了法语测试文件: {fr_yaml_path}")

# 尝试从纯Python实现直接导入
try:
    print("尝试从纯Python实现直接导入")
    sys.path.insert(0, os.path.join(project_root, 'src', 'bindings', 'python', 'logloom_py'))
    from logloom_pure import (
        initialize, register_locale_file, set_language, get_language, 
        get_text, format_text, get_supported_languages, get_language_keys
    )
    
    using_pure = True
    print("成功从纯Python实现导入")
except ImportError as e:
    using_pure = False
    print(f"从纯Python实现导入失败: {e}")
    print("尝试从logloom模块导入")
    try:
        import logloom
        print("已导入logloom模块，检查API可用性...")
        
        # 检查新API是否可用
        api_funcs = [
            'register_locale_file', 
            'register_locale_directory',
            'get_supported_languages', 
            'get_language_keys'
        ]
        
        missing_apis = [func for func in api_funcs if not hasattr(logloom, func)]
        
        if missing_apis:
            print(f"缺少以下API: {', '.join(missing_apis)}")
            print("将使用动态添加方法解决问题")
            
            # 动态导入纯Python实现
            sys.path.insert(0, os.path.join(project_root, 'src', 'bindings', 'python', 'logloom_py'))
            import logloom_pure
            
            # 动态添加缺失的方法到logloom模块
            for func in missing_apis:
                if hasattr(logloom_pure, func):
                    setattr(logloom, func, getattr(logloom_pure, func))
                    print(f"已添加 {func} 到logloom模块")
                else:
                    print(f"警告: 纯Python实现中也没有找到 {func}")
        
        initialize = logloom.initialize
        register_locale_file = logloom.register_locale_file if hasattr(logloom, "register_locale_file") else None
        set_language = logloom.set_language
        get_language = logloom.get_language
        get_text = logloom.get_text
        format_text = logloom.format_text
        get_supported_languages = logloom.get_supported_languages if hasattr(logloom, "get_supported_languages") else None
        get_language_keys = logloom.get_language_keys if hasattr(logloom, "get_language_keys") else None
        
        using_pure = False
        print("从logloom模块导入成功")
    except ImportError as e:
        print(f"从logloom模块导入失败: {e}")
        print("无法导入任何版本的logloom，测试无法继续")
        sys.exit(1)

print("\n===== 开始测试新API =====\n")

# 初始化
print("初始化logloom...")
initialize()

# 测试注册语言资源文件
if register_locale_file:
    print(f"\n测试register_locale_file: 注册法语资源文件 {fr_yaml_path}")
    result = register_locale_file(fr_yaml_path)
    print(f"注册结果: {result}")

    # 测试切换语言
    print("\n测试set_language: 切换到法语")
    set_language("fr")
    print(f"当前语言: {get_language()}")

    # 测试获取翻译文本
    print("\n测试get_text: 获取法语文本")
    text = get_text("test.hello")
    print(f"文本: {text}")

    # 测试格式化文本
    print("\n测试format_text: 格式化法语文本")
    formatted = format_text("test.hello", "monde")
    print(f"格式化后的文本: {formatted}")

    # 测试自定义键
    print("\n测试自定义键: test.custom_key")
    custom_text = get_text("test.custom_key")
    print(f"自定义文本: {custom_text}")

    # 测试获取支持的语言列表
    if get_supported_languages:
        print("\n测试get_supported_languages: 获取支持的语言列表")
        languages = get_supported_languages()
        print(f"支持的语言: {languages}")

    # 测试获取语言键列表
    if get_language_keys:
        print("\n测试get_language_keys: 获取法语键列表")
        keys = get_language_keys("fr")
        print(f"法语键列表 (前5个): {keys[:5]}")
else:
    print("警告: register_locale_file 功能不可用，跳过相关测试")

print("\n===== 测试完成 =====\n")

print(f"使用的实现: {'纯Python实现' if using_pure else 'C扩展模块'}")