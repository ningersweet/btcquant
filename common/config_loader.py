"""
通用配置加载器

从 YAML 文件加载配置，支持环境变量覆盖
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigLoader:
    """配置加载器"""
    
    _instance: Optional['ConfigLoader'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._config:
            self._load_config()
    
    def _find_config_file(self) -> Path:
        """查找配置文件"""
        search_paths = [
            Path(os.getenv("CONFIG_PATH", "")),
            Path.cwd() / "config.yaml",
            Path.cwd().parent / "config.yaml",
            Path("/app/config.yaml"),
            Path(__file__).parent / "config.yaml",
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        
        return Path.cwd() / "config.yaml"
    
    def _load_config(self) -> None:
        """加载配置文件"""
        config_path = self._find_config_file()
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        支持点号分隔的嵌套键，如 "data.binance.base_url"
        环境变量优先级高于配置文件
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        env_key = key.upper().replace(".", "_")
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_type(env_value, default)
        
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def _convert_type(self, value: str, default: Any) -> Any:
        """根据默认值类型转换环境变量值"""
        if default is None:
            return value
        
        if isinstance(default, bool):
            return value.lower() in ('true', '1', 'yes')
        if isinstance(default, int):
            return int(value)
        if isinstance(default, float):
            return float(value)
        if isinstance(default, list):
            return [x.strip() for x in value.split(',')]
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取配置节
        
        Args:
            section: 节名称
            
        Returns:
            配置字典
        """
        return self._config.get(section, {})
    
    def reload(self) -> None:
        """重新加载配置"""
        self._config = {}
        self._load_config()


config_loader = ConfigLoader()


def get_config(key: str, default: Any = None) -> Any:
    """便捷函数：获取配置值"""
    return config_loader.get(key, default)


def get_section(section: str) -> Dict[str, Any]:
    """便捷函数：获取配置节"""
    return config_loader.get_section(section)
