"""
Telegram 消息推送模块
"""
import asyncio
import time
from typing import Optional, Dict, Any
from collections import deque

from telegram import Bot
from telegram.error import TelegramError
from loguru import logger


class TelegramNotifier:
    """Telegram 消息推送器"""

    def __init__(self, bot_token: str, chat_id: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化 Telegram 推送器

        Args:
            bot_token: Telegram Bot Token
            chat_id: 接收消息的 Chat ID
            config: 额外配置
                - rate_limit: 每分钟最多发送消息数 (默认: 20)
                - batch_interval: 批量发送间隔秒数 (默认: 5)
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.config = config or {}

        # 限流配置
        self.rate_limit = self.config.get('rate_limit', 20)
        self.batch_interval = self.config.get('batch_interval', 5)

        # 限流跟踪: 使用双端队列记录最近的发送时间戳
        self._send_timestamps = deque(maxlen=self.rate_limit)

        # 初始化 Bot
        self._bot: Optional[Bot] = None
        self._init_bot()

        logger.debug(
            f"TelegramNotifier 初始化完成 - "
            f"Chat ID: {self.chat_id}, "
            f"限流: {self.rate_limit}条/分钟"
        )

    def _init_bot(self) -> None:
        """初始化 Telegram Bot 实例"""
        try:
            self._bot = Bot(token=self.bot_token)
            logger.debug("Telegram Bot 初始化成功")
        except Exception as e:
            logger.error(f"初始化 Telegram Bot 失败: {e}")
            raise

    def _check_rate_limit(self) -> bool:
        """
        检查是否触发限流

        Returns:
            True 表示可以发送, False 表示需要等待
        """
        current_time = time.time()

        # 清理 60 秒之前的时间戳
        while self._send_timestamps and current_time - self._send_timestamps[0] > 60:
            self._send_timestamps.popleft()

        # 检查是否超过限流
        if len(self._send_timestamps) >= self.rate_limit:
            logger.warning(
                f"Telegram 推送触发限流 "
                f"({len(self._send_timestamps)}/{self.rate_limit}条/分钟)"
            )
            return False

        return True

    async def send_message(
        self,
        text: str,
        parse_mode: str = "Markdown",
        disable_notification: bool = False
    ) -> bool:
        """
        发送文本消息

        Args:
            text: 消息内容
            parse_mode: 解析模式 ("Markdown", "HTML", None)
            disable_notification: 是否静默发送（不通知用户）

        Returns:
            发送成功返回 True，失败返回 False
        """
        if not self._bot:
            logger.error("Telegram Bot 未初始化")
            return False

        # 检查限流
        if not self._check_rate_limit():
            # 等待一段时间后重试
            await asyncio.sleep(self.batch_interval)
            if not self._check_rate_limit():
                logger.error("Telegram 推送限流，跳过此消息")
                return False

        try:
            await self._bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_notification=disable_notification
            )

            # 记录发送时间
            self._send_timestamps.append(time.time())

            logger.debug(f"Telegram 消息发送成功: {text[:50]}...")
            return True

        except TelegramError as e:
            logger.error(f"发送 Telegram 消息失败: {e}")
            return False
        except Exception as e:
            logger.error(f"发送 Telegram 消息时发生未知错误: {e}")
            return False

    async def send_photo(
        self,
        photo: str,
        caption: Optional[str] = None,
        parse_mode: str = "Markdown"
    ) -> bool:
        """
        发送图片消息

        Args:
            photo: 图片文件路径或 URL
            caption: 图片说明
            parse_mode: 解析模式

        Returns:
            发送成功返回 True，失败返回 False
        """
        if not self._bot:
            logger.error("Telegram Bot 未初始化")
            return False

        # 检查限流
        if not self._check_rate_limit():
            await asyncio.sleep(self.batch_interval)
            if not self._check_rate_limit():
                logger.error("Telegram 推送限流，跳过此消息")
                return False

        try:
            await self._bot.send_photo(
                chat_id=self.chat_id,
                photo=photo,
                caption=caption,
                parse_mode=parse_mode
            )

            # 记录发送时间
            self._send_timestamps.append(time.time())

            logger.debug(f"Telegram 图片发送成功: {caption or '(无说明)'}")
            return True

        except TelegramError as e:
            logger.error(f"发送 Telegram 图片失败: {e}")
            return False
        except Exception as e:
            logger.error(f"发送 Telegram 图片时发生未知错误: {e}")
            return False

    async def send_document(
        self,
        document: str,
        caption: Optional[str] = None,
        filename: Optional[str] = None
    ) -> bool:
        """
        发送文档消息

        Args:
            document: 文档文件路径
            caption: 文档说明
            filename: 文件名（可选）

        Returns:
            发送成功返回 True，失败返回 False
        """
        if not self._bot:
            logger.error("Telegram Bot 未初始化")
            return False

        # 检查限流
        if not self._check_rate_limit():
            await asyncio.sleep(self.batch_interval)
            if not self._check_rate_limit():
                logger.error("Telegram 推送限流，跳过此消息")
                return False

        try:
            await self._bot.send_document(
                chat_id=self.chat_id,
                document=document,
                caption=caption,
                filename=filename
            )

            # 记录发送时间
            self._send_timestamps.append(time.time())

            logger.debug(f"Telegram 文档发送成功: {filename or document}")
            return True

        except TelegramError as e:
            logger.error(f"发送 Telegram 文档失败: {e}")
            return False
        except Exception as e:
            logger.error(f"发送 Telegram 文档时发生未知错误: {e}")
            return False

    def send_message_sync(self, text: str, parse_mode: str = "Markdown") -> bool:
        """
        同步方式发送消息（用于非异步环境）

        Args:
            text: 消息内容
            parse_mode: 解析模式

        Returns:
            发送成功返回 True，失败返回 False
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环已在运行，创建新任务
                future = asyncio.ensure_future(self.send_message(text, parse_mode))
                return True
            else:
                # 否则直接运行
                return loop.run_until_complete(self.send_message(text, parse_mode))
        except Exception as e:
            logger.error(f"同步发送消息失败: {e}")
            return False

    async def test_connection(self) -> bool:
        """
        测试连接是否正常

        Returns:
            连接正常返回 True，否则返回 False
        """
        try:
            me = await self._bot.get_me()
            logger.info(f"Telegram Bot 连接成功: @{me.username}")
            return True
        except TelegramError as e:
            logger.error(f"Telegram Bot 连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"测试 Telegram 连接时发生未知错误: {e}")
            return False
