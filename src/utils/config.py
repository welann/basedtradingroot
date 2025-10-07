"""
配置文件加载器
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from loguru import logger


class ConfigLoader:
    """配置文件加载器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径，默认为 config/config.yaml
        """
        if config_path is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self._config: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: YAML 解析错误
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"配置文件不存在: {self.config_path}\n"
                f"请复制 config.example.yaml 为 config.yaml 并填入实际值"
            )

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)

            logger.debug(f"成功加载配置文件: {self.config_path}")
            return self._config

        except yaml.YAMLError as e:
            logger.error(f"解析配置文件失败: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项（支持点号访问嵌套配置）

        Args:
            key: 配置键，支持 "logging.console_level" 这样的嵌套访问
            default: 默认值

        Returns:
            配置值
        """
        if self._config is None:
            self.load()

        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get('logging', {})

    def get_telegram_config(self) -> Dict[str, Any]:
        """获取 Telegram 配置"""
        return self.get('telegram', {})

    def get_exchange_config(self, exchange_name: str) -> Dict[str, Any]:
        """获取指定交易所的配置"""
        return self.get(f'exchanges.{exchange_name}', {})

    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置"""
        if self._config is None:
            self.load()
        return self._config


# 全局配置实例
_global_config: Optional[ConfigLoader] = None


def get_config(config_path: Optional[str] = None) -> ConfigLoader:
    """
    获取全局配置实例

    Args:
        config_path: 配置文件路径

    Returns:
        ConfigLoader 实例
    """
    global _global_config

    if _global_config is None:
        _global_config = ConfigLoader(config_path)
        _global_config.load()

    return _global_config
