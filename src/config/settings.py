"""
配置管理模块
支持配置文件、环境变量和命令行参数
"""
import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path
from .constants import *


class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        self._config = {}
        self._load_default_config()

        if config_path and os.path.exists(config_path):
            self._load_config_file(config_path)

        self._load_env_vars()

    def _load_default_config(self):
        """加载默认配置"""
        self._config = {
            'scraper': {
                'base_url': BASE_URL,
                'events_url': EVENTS_URL,
                'delay': DEFAULT_DELAY,
                'timeout': DEFAULT_TIMEOUT,
                'max_retries': MAX_RETRIES,
                'retry_delay': RETRY_DELAY,
            },
            'downloader': {
                'output_dir': DEFAULT_OUTPUT_DIR,
                'max_download': DEFAULT_MAX_DOWNLOAD,
                'download_abstracts': True,
                'create_year_dirs': True,
                'create_venue_dirs': True,
                'max_filename_length': 100,
            },
            'cli': {
                'supported_venues': SUPPORTED_VENUES,
                'show_progress': True,
                'verbose': False,
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': None,
            }
        }

    def _load_config_file(self, config_path: str):
        """从配置文件加载配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)

            if file_config:
                self._merge_config(file_config)

        except Exception as e:
            print(f"警告: 无法加载配置文件 {config_path}: {e}")

    def _load_env_vars(self):
        """从环境变量加载配置"""
        env_mappings = {
            'ACL_OUTPUT_DIR': ('downloader', 'output_dir'),
            'ACL_MAX_DOWNLOAD': ('downloader', 'max_download'),
            'ACL_DELAY': ('scraper', 'delay'),
            'ACL_TIMEOUT': ('scraper', 'timeout'),
            'ACL_LOG_LEVEL': ('logging', 'level'),
            'ACL_VERBOSE': ('cli', 'verbose'),
        }

        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # 尝试转换数据类型
                if key in ['max_download', 'delay', 'timeout']:
                    try:
                        value = int(value)
                    except ValueError:
                        continue
                elif key == 'verbose':
                    value = value.lower() in ('true', '1', 'yes', 'on')

                self.set(section, key, value)

    def _merge_config(self, new_config: Dict[str, Any]):
        """合并配置"""
        def merge_dict(base: Dict, update: Dict):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value

        merge_dict(self._config, new_config)

    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """
        获取配置值
        Args:
            section: 配置节名称
            key: 配置键名称，如果为None则返回整个节的配置
            default: 默认值
        Returns:
            配置值
        """
        if key is None:
            return self._config.get(section, default)

        return self._config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any):
        """
        设置配置值
        Args:
            section: 配置节名称
            key: 配置键名称
            value: 配置值
        """
        if section not in self._config:
            self._config[section] = {}

        self._config[section][key] = value

    def update(self, config_dict: Dict[str, Any]):
        """
        批量更新配置
        Args:
            config_dict: 配置字典
        """
        self._merge_config(config_dict)

    def save(self, config_path: str):
        """
        保存配置到文件
        Args:
            config_path: 配置文件路径
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False,
                         allow_unicode=True, indent=2)

        except Exception as e:
            print(f"错误: 无法保存配置文件 {config_path}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._config.copy()

    def __str__(self) -> str:
        return yaml.dump(self._config, default_flow_style=False, allow_unicode=True)


# 全局配置实例
default_config = Config()


def get_config(config_path: Optional[str] = None) -> Config:
    """
    获取配置实例
    Args:
        config_path: 配置文件路径
    Returns:
        Config实例
    """
    if config_path:
        return Config(config_path)
    return default_config


def create_default_config_file(config_path: str = "config/default.yaml"):
    """
    创建默认配置文件
    Args:
        config_path: 配置文件路径
    """
    config = Config()
    config.save(config_path)
    print(f"默认配置文件已创建: {config_path}")


if __name__ == "__main__":
    # 创建默认配置文件
    create_default_config_file()