"""
Logloom 配置模块
=============

提供配置文件的访问和修改功能
"""

import yaml
import os
import logloom

class Config:
    """Logloom配置管理类"""
    
    def __init__(self):
        """初始化配置对象"""
        self._config = {
            # 使用测试期望的结构
            'logging': {
                'default_level': 'INFO',
                'output_path': 'log.txt',
                'max_file_size': 10485760  # 10MB
            },
            'i18n': {
                'default_language': 'zh',
                'language_files': {
                    'zh': 'locales/zh.yaml',
                    'en': 'locales/en.yaml'
                }
            },
            'plugins': {
                'enabled': True,
                'search_paths': ['plugins']
            },
            # 同时保留兼容原始配置文件的结构
            'logloom': {
                'language': 'zh',
                'log': {
                    'level': 'INFO',
                    'file': 'log.txt',
                    'max_size': 10485760,
                    'console': True
                },
                'plugin': {
                    'paths': ['plugins'],
                    'enabled': []
                }
            }
        }
        self._config_path = None
    
    def load(self, config_path=None):
        """
        从文件加载配置
        
        Parameters:
        -----------
        config_path : str, optional
            配置文件路径，如果不提供则使用默认配置
        
        Returns:
        --------
        bool
            是否成功加载配置
        """
        if not config_path:
            # 使用默认配置
            return True
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
                if loaded_config:
                    # 递归更新配置，保留默认值
                    self._update_dict(self._config, loaded_config)
                    
                    # 如果加载的是原始结构，同步到测试需要的结构
                    if 'logloom' in loaded_config:
                        logloom_cfg = loaded_config.get('logloom', {})
                        
                        # 同步日志配置
                        log_cfg = logloom_cfg.get('log', {})
                        if log_cfg:
                            self._config['logging']['default_level'] = log_cfg.get('level', 'INFO')
                            self._config['logging']['output_path'] = log_cfg.get('file', 'log.txt')
                            self._config['logging']['max_file_size'] = log_cfg.get('max_size', 10485760)
                        
                        # 同步国际化配置
                        self._config['i18n']['default_language'] = logloom_cfg.get('language', 'zh')
                        
                # 同样，如果使用的是测试结构，同步到原始结构
                if 'logging' in loaded_config:
                    log_cfg = loaded_config.get('logging', {})
                    self._config['logloom']['log']['level'] = log_cfg.get('default_level', 'INFO')
                    self._config['logloom']['log']['file'] = log_cfg.get('output_path', 'log.txt')
                    self._config['logloom']['log']['max_size'] = log_cfg.get('max_file_size', 10485760)
                
                if 'i18n' in loaded_config:
                    i18n_cfg = loaded_config.get('i18n', {})
                    self._config['logloom']['language'] = i18n_cfg.get('default_language', 'zh')
                    
                self._config_path = config_path
                return True
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return False
    
    def save(self, config_path=None):
        """
        保存配置到文件
        
        Parameters:
        -----------
        config_path : str, optional
            配置文件路径，如果不提供则使用加载时的路径
        
        Returns:
        --------
        bool
            是否成功保存配置
        """
        path = config_path or self._config_path
        if not path:
            print("无法保存配置：未指定配置文件路径")
            return False
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key, default=None):
        """
        获取配置值
        
        Parameters:
        -----------
        key : str
            配置键，可以是点分隔的路径，如 'logging.default_level'
        default : any, optional
            如果键不存在时返回的默认值
        
        Returns:
        --------
        any
            配置值或默认值
        """
        parts = key.split('.')
        value = self._config
        
        for part in parts:
            if part not in value:
                return default
            value = value[part]
        
        return value
    
    def set(self, key, value):
        """
        设置配置值
        
        Parameters:
        -----------
        key : str
            配置键，可以是点分隔的路径，如 'logging.default_level'
        value : any
            要设置的值
        """
        parts = key.split('.')
        target = self._config
        
        # 导航到最后一个部分的父级
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]
        
        # 设置值
        target[parts[-1]] = value
        
        # 如果修改了关键配置，应用到运行时
        if key == 'logging.default_level':
            logloom.set_log_level(value)
        elif key == 'logging.output_path':
            logloom.set_log_file(value)
        elif key == 'i18n.default_language':
            logloom.set_language(value)
    
    def _update_dict(self, target, source):
        """
        递归更新字典，保留原有键
        
        Parameters:
        -----------
        target : dict
            目标字典
        source : dict
            源字典
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_dict(target[key], value)
            else:
                target[key] = value
    
    def __getitem__(self, key):
        """
        通过字典风格访问配置
        
        Parameters:
        -----------
        key : str
            配置分组键名，如 'logging'
        
        Returns:
        --------
        dict
            配置分组
        
        Raises:
        -------
        KeyError
            如果键不存在
        """
        if key in self._config:
            return self._config[key]
        raise KeyError(f"配置键 '{key}' 不存在")
    
    def __setitem__(self, key, value):
        """
        通过字典风格设置配置
        
        Parameters:
        -----------
        key : str
            配置分组键名，如 'logging'
        value : dict
            配置分组值
        """
        self._config[key] = value
    
    def __contains__(self, key):
        """
        检查配置键是否存在
        
        Parameters:
        -----------
        key : str
            配置键
        
        Returns:
        --------
        bool
            键是否存在
        """
        return key in self._config

# 创建全局配置实例
config = Config()