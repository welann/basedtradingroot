"""
日志管理模块
"""
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from loguru import logger

from .notifier import TelegramNotifier


class LoggerManager:
    """日志管理器 - 统一管理日志输出和 Telegram 推送"""

    _instance: Optional['LoggerManager'] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化日志管理器

        Args:
            config: 配置字典，包含 logging 和 telegram 配置
        """
        # 避免重复初始化
        if self._initialized:
            return

        self.config = config or {}
        self.logging_config = self.config.get('logging', {})
        self.telegram_config = self.config.get('telegram', {})

        # 日志目录
        self.log_dir = Path(self.logging_config.get('log_dir', 'logs'))
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        (self.log_dir / 'trade').mkdir(exist_ok=True)
        (self.log_dir / 'system').mkdir(exist_ok=True)
        (self.log_dir / 'error').mkdir(exist_ok=True)
        (self.log_dir / 'strategy').mkdir(exist_ok=True)

        # 日志级别
        self.console_level = self.logging_config.get('console_level', 'INFO')
        self.file_level = self.logging_config.get('file_level', 'DEBUG')

        # Telegram 推送器
        self.telegram_notifier: Optional[TelegramNotifier] = None
        self._init_telegram()

        # 配置 loguru
        self._setup_loguru()

        self._initialized = True
        logger.info("LoggerManager 初始化完成")

    def _init_telegram(self) -> None:
        """初始化 Telegram 推送"""
        if not self.telegram_config.get('enabled', False):
            logger.debug("Telegram 推送未启用")
            return

        bot_token = self.telegram_config.get('bot_token')
        chat_id = self.telegram_config.get('chat_id')

        if not bot_token or not chat_id:
            logger.warning("Telegram 配置不完整，跳过初始化")
            return

        try:
            self.telegram_notifier = TelegramNotifier(
                bot_token=bot_token,
                chat_id=chat_id,
                config={
                    'rate_limit': self.telegram_config.get('rate_limit', 20),
                    'batch_interval': self.telegram_config.get('batch_interval', 5),
                }
            )
            logger.info("Telegram 推送器初始化成功")
        except Exception as e:
            logger.error(f"初始化 Telegram 推送器失败: {e}")

    def _setup_loguru(self) -> None:
        """配置 loguru 日志系统"""
        # 移除默认的 handler
        logger.remove()

        # 日志格式
        def format_with_extra(record):
            """添加默认的 extra 字段"""
            if 'module' not in record['extra']:
                record['extra']['module'] = 'N/A'
            if 'exchange' not in record['extra']:
                record['extra']['exchange'] = 'N/A'
            if 'log_type' not in record['extra']:
                record['extra']['log_type'] = 'system'
            return True

        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[module]}</cyan> | "
            "<cyan>{extra[exchange]}</cyan> | "
            "<level>{message}</level>"
        )

        # 控制台输出 - 彩色
        logger.add(
            sys.stdout,
            format=log_format,
            level=self.console_level,
            colorize=True,
            backtrace=True,
            diagnose=True,
            filter=format_with_extra,
        )

        # 获取轮转配置
        rotation_config = self.logging_config.get('rotation', {})
        rotation_time = rotation_config.get('time', '00:00')
        rotation_size = f"{rotation_config.get('size', 100)} MB"

        # 交易日志
        logger.add(
            self.log_dir / 'trade' / 'trade_{time:YYYY-MM-DD}.log',
            format=log_format,
            level=self.file_level,
            rotation=rotation_time,
            retention=None,  # 永久保留
            compression=None,
            encoding='utf-8',
            filter=lambda record: format_with_extra(record) and record["extra"].get("log_type") == "trade",
        )

        # 系统日志
        logger.add(
            self.log_dir / 'system' / 'system_{time:YYYY-MM-DD}.log',
            format=log_format,
            level=self.file_level,
            rotation=rotation_time,
            retention=None,
            compression=None,
            encoding='utf-8',
            filter=lambda record: format_with_extra(record) and record["extra"].get("log_type") == "system",
        )

        # 错误日志 - 记录所有 ERROR 和 CRITICAL
        logger.add(
            self.log_dir / 'error' / 'error_{time:YYYY-MM-DD}.log',
            format=log_format,
            level='ERROR',
            rotation=rotation_time,
            retention=None,
            compression=None,
            encoding='utf-8',
            backtrace=True,
            diagnose=True,
            filter=format_with_extra,
        )

        # 策略日志
        logger.add(
            self.log_dir / 'strategy' / 'strategy_{time:YYYY-MM-DD}.log',
            format=log_format,
            level=self.file_level,
            rotation=rotation_time,
            retention=None,
            compression=None,
            encoding='utf-8',
            filter=lambda record: format_with_extra(record) and record["extra"].get("log_type") == "strategy",
        )

        # 通用日志 - 记录所有日志
        logger.add(
            self.log_dir / 'all_{time:YYYY-MM-DD}.log',
            format=log_format,
            level=self.file_level,
            rotation=rotation_time,
            retention=None,
            compression=None,
            encoding='utf-8',
            filter=format_with_extra,
        )

    def get_logger(self, module_name: str, exchange: str = "N/A", log_type: str = "system"):
        """
        获取带有上下文信息的 logger

        Args:
            module_name: 模块名称
            exchange: 交易所名称
            log_type: 日志类型 (trade, system, error, strategy)

        Returns:
            配置好的 logger 对象
        """
        return logger.bind(module=module_name, exchange=exchange, log_type=log_type)

    async def send_telegram(
        self,
        message: str,
        parse_mode: str = "Markdown",
        level: str = "INFO"
    ) -> bool:
        """
        发送 Telegram 消息

        Args:
            message: 消息内容
            parse_mode: 解析模式
            level: 日志级别（用于过滤）

        Returns:
            发送成功返回 True，否则返回 False
        """
        if not self.telegram_notifier:
            logger.debug("Telegram 推送未启用")
            return False

        # 检查是否需要推送此级别
        min_level = self.telegram_config.get('min_level', 'WARNING')
        level_priority = {
            'TRACE': 0, 'DEBUG': 1, 'INFO': 2, 'SUCCESS': 3,
            'WARNING': 4, 'ERROR': 5, 'CRITICAL': 6
        }

        if level_priority.get(level, 0) < level_priority.get(min_level, 4):
            logger.debug(f"消息级别 {level} 低于最小推送级别 {min_level}，跳过推送")
            return False

        try:
            return await self.telegram_notifier.send_message(message, parse_mode)
        except Exception as e:
            logger.error(f"发送 Telegram 消息失败: {e}")
            return False

    def send_telegram_sync(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        同步方式发送 Telegram 消息

        Args:
            message: 消息内容
            parse_mode: 解析模式

        Returns:
            发送成功返回 True，否则返回 False
        """
        if not self.telegram_notifier:
            return False

        return self.telegram_notifier.send_message_sync(message, parse_mode)

    def format_trade_message(
        self,
        exchange: str,
        symbol: str,
        side: str,
        size: float,
        price: float,
        total: Optional[float] = None,
        fee: Optional[float] = None,
        order_id: Optional[str] = None,
    ) -> str:
        """
        格式化交易消息

        Args:
            exchange: 交易所名称
            symbol: 交易对
            side: 方向 (BUY/SELL)
            size: 数量
            price: 价格
            total: 总额
            fee: 手续费
            order_id: 订单ID

        Returns:
            格式化后的消息
        """
        side_emoji = "🟢" if side.upper() == "BUY" else "🔴"
        side_text = "买入" if side.upper() == "BUY" else "卖出"

        message = f"""🔔 **订单成交通知**

交易所: `{exchange}`
交易对: `{symbol}`
方向: {side_emoji} **{side_text}**
数量: `{size}`
价格: `${price:,.2f}`"""

        if total is not None:
            message += f"\n总额: `${total:,.2f}`"

        if fee is not None:
            message += f"\n手续费: `${fee:,.2f}`"

        message += f"\n时间: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"

        if order_id:
            message += f"\n\n订单ID: `#{order_id}`"

        return message

    def format_alert_message(
        self,
        level: str,
        module: str,
        exchange: str,
        message: str,
    ) -> str:
        """
        格式化告警消息

        Args:
            level: 级别 (WARNING, ERROR, CRITICAL)
            module: 模块名称
            exchange: 交易所名称
            message: 消息内容

        Returns:
            格式化后的消息
        """
        emoji_map = {
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨',
        }

        emoji = emoji_map.get(level, '📢')

        formatted_message = f"""{emoji} **系统告警**

级别: `{level}`
模块: `{module}`
交易所: `{exchange}`
消息: {message}
时间: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"""

        return formatted_message


# 全局实例
_global_logger_manager: Optional[LoggerManager] = None


def get_logger_manager(config: Optional[Dict[str, Any]] = None) -> LoggerManager:
    """
    获取全局 LoggerManager 实例

    Args:
        config: 配置字典

    Returns:
        LoggerManager 实例
    """
    global _global_logger_manager

    if _global_logger_manager is None:
        _global_logger_manager = LoggerManager(config)

    return _global_logger_manager


def get_logger(module_name: str, exchange: str = "N/A", log_type: str = "system"):
    """
    便捷函数：获取 logger

    Args:
        module_name: 模块名称
        exchange: 交易所名称
        log_type: 日志类型

    Returns:
        logger 对象
    """
    manager = get_logger_manager()
    return manager.get_logger(module_name, exchange, log_type)
