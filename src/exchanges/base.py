"""
交易所客户端抽象基类
"""
from abc import ABC, abstractmethod
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional, List, Callable

from .types import (
    OrderResult,
    OrderInfo,
    Position,
    Ticker,
    SymbolInfo,
    OrderType,
    OrderSide,
)


class BaseExchangeClient(ABC):
    """交易所客户端抽象基类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化交易所客户端

        Args:
            config: 交易所配置字典
        """
        self.config = config
        self._validate_config()
        self._symbol_info_cache: Dict[str, SymbolInfo] = {}

    @abstractmethod
    def _validate_config(self) -> None:
        """
        验证配置是否完整

        Raises:
            ValueError: 配置不完整或无效
        """
        pass

    @abstractmethod
    async def connect(self) -> None:
        """
        连接到交易所（WebSocket、REST API 等）

        Raises:
            ConnectionError: 连接失败
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """断开与交易所的连接"""
        pass

    # ==================== 订单操作 ====================

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        size: Decimal,
        price: Optional[Decimal] = None,
        **kwargs
    ) -> OrderResult:
        """
        下单

        Args:
            symbol: 交易对
            side: 订单方向 (BUY/SELL)
            order_type: 订单类型 (LIMIT/MARKET)
            size: 订单数量
            price: 订单价格（市价单可选）
            **kwargs: 其他参数（如 time_in_force, client_order_id 等）

        Returns:
            OrderResult: 订单结果

        Raises:
            ValueError: 参数无效
            Exception: 下单失败
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> OrderResult:
        """
        取消订单

        Args:
            order_id: 订单ID
            symbol: 交易对（某些交易所需要）

        Returns:
            OrderResult: 取消结果

        Raises:
            ValueError: 订单不存在
            Exception: 取消失败
        """
        pass

    @abstractmethod
    async def get_order_info(self, order_id: str, symbol: Optional[str] = None) -> Optional[OrderInfo]:
        """
        查询订单信息

        Args:
            order_id: 订单ID
            symbol: 交易对（某些交易所需要）

        Returns:
            OrderInfo: 订单信息，不存在则返回 None
        """
        pass

    @abstractmethod
    async def get_active_orders(self, symbol: Optional[str] = None) -> List[OrderInfo]:
        """
        查询活跃订单（未完全成交的订单）

        Args:
            symbol: 交易对，为 None 则返回所有交易对的活跃订单

        Returns:
            List[OrderInfo]: 活跃订单列表
        """
        pass

    async def modify_order(
        self,
        order_id: str,
        symbol: str,
        new_price: Optional[Decimal] = None,
        new_size: Optional[Decimal] = None
    ) -> OrderResult:
        """
        修改订单（如果交易所支持）

        Args:
            order_id: 订单ID
            symbol: 交易对
            new_price: 新价格
            new_size: 新数量

        Returns:
            OrderResult: 修改结果

        Note:
            默认实现为不支持，子类可以覆盖
        """
        return OrderResult(
            success=False,
            error_message="此交易所不支持修改订单，请先取消后重新下单"
        )

    # ==================== 持仓操作 ====================

    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Position]:
        """
        获取指定合约的持仓信息

        Args:
            symbol: 交易对/合约

        Returns:
            Position: 持仓信息，无持仓则返回 None
        """
        pass

    @abstractmethod
    async def get_all_positions(self) -> List[Position]:
        """
        获取所有持仓

        Returns:
            List[Position]: 持仓列表
        """
        pass

    # ==================== 市场数据 ====================

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker:
        """
        获取最新价格信息

        Args:
            symbol: 交易对

        Returns:
            Ticker: 价格信息

        Raises:
            ValueError: 交易对不存在
        """
        pass

    @abstractmethod
    async def get_symbols(self) -> List[str]:
        """
        获取所有可交易的交易对

        Returns:
            List[str]: 交易对列表
        """
        pass

    @abstractmethod
    async def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """
        获取交易对详细信息

        Args:
            symbol: 交易对

        Returns:
            SymbolInfo: 交易对信息

        Raises:
            ValueError: 交易对不存在
        """
        pass

    # ==================== WebSocket 订阅 ====================

    def setup_order_update_handler(self, handler: Callable[[OrderInfo], None]) -> None:
        """
        设置订单更新回调函数

        Args:
            handler: 回调函数，接收 OrderInfo 参数

        Note:
            默认实现为不支持，子类可以覆盖实现 WebSocket 订单推送
        """
        raise NotImplementedError("此交易所不支持 WebSocket 订单更新")

    # ==================== 工具方法 ====================

    def round_to_tick(self, symbol: str, price: Decimal) -> Decimal:
        """
        将价格舍入到交易对的最小价格变动单位

        Args:
            symbol: 交易对
            price: 价格

        Returns:
            Decimal: 舍入后的价格
        """
        if not isinstance(price, Decimal):
            price = Decimal(str(price))

        # 从缓存获取 symbol_info
        if symbol in self._symbol_info_cache:
            symbol_info = self._symbol_info_cache[symbol]
            return symbol_info.round_price(price)

        # 如果没有缓存，使用默认精度
        tick_size = self.config.get('tick_size', Decimal("0.01"))
        if not isinstance(tick_size, Decimal):
            tick_size = Decimal(str(tick_size))

        return (price / tick_size).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * tick_size

    def round_to_size(self, symbol: str, size: Decimal) -> Decimal:
        """
        将数量舍入到交易对的数量精度

        Args:
            symbol: 交易对
            size: 数量

        Returns:
            Decimal: 舍入后的数量
        """
        if not isinstance(size, Decimal):
            size = Decimal(str(size))

        # 从缓存获取 symbol_info
        if symbol in self._symbol_info_cache:
            symbol_info = self._symbol_info_cache[symbol]
            return symbol_info.round_quantity(size)

        # 如果没有缓存，使用默认精度
        precision = self.config.get('quantity_precision', 4)
        quantize_value = Decimal(10) ** -precision
        return size.quantize(quantize_value, rounding=ROUND_HALF_UP)

    async def validate_order(
        self,
        symbol: str,
        side: OrderSide,
        size: Decimal,
        price: Optional[Decimal] = None
    ) -> tuple[bool, str]:
        """
        验证订单参数是否合法

        Args:
            symbol: 交易对
            side: 订单方向
            size: 订单数量
            price: 订单价格（市价单可选）

        Returns:
            (是否合法, 错误信息)
        """
        try:
            # 获取交易对信息
            symbol_info = await self.get_symbol_info(symbol)

            # 缓存 symbol_info
            self._symbol_info_cache[symbol] = symbol_info

            # 检查交易对是否可交易
            if not symbol_info.trading_enabled:
                return False, f"交易对 {symbol} 当前不可交易"

            # 验证订单参数
            is_valid, error_msg = symbol_info.validate_order(size, price)
            if not is_valid:
                return False, error_msg

            return True, ""

        except Exception as e:
            return False, f"验证订单参数时发生错误: {e}"

    @abstractmethod
    def get_exchange_name(self) -> str:
        """
        获取交易所名称

        Returns:
            str: 交易所名称
        """
        pass

    # ==================== 上下文管理器支持 ====================

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.disconnect()
        return False
