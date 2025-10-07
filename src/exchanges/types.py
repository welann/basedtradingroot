"""
交易所数据类型定义
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class OrderType(Enum):
    """订单类型"""
    LIMIT = "LIMIT"           # 限价单
    MARKET = "MARKET"         # 市价单
    STOP_LIMIT = "STOP_LIMIT" # 止损限价单
    STOP_MARKET = "STOP_MARKET" # 止损市价单
    TAKE_PROFIT = "TAKE_PROFIT" # 止盈单
    TRAILING_STOP = "TRAILING_STOP" # 追踪止损单


class OrderSide(Enum):
    """订单方向"""
    BUY = "BUY"     # 买入
    SELL = "SELL"   # 卖出


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "PENDING"                 # 待处理
    OPEN = "OPEN"                       # 已开仓
    PARTIALLY_FILLED = "PARTIALLY_FILLED" # 部分成交
    FILLED = "FILLED"                   # 完全成交
    CANCELLED = "CANCELLED"             # 已取消
    REJECTED = "REJECTED"               # 已拒绝
    EXPIRED = "EXPIRED"                 # 已过期


class PositionSide(Enum):
    """持仓方向"""
    LONG = "LONG"   # 多头
    SHORT = "SHORT" # 空头
    BOTH = "BOTH"   # 双向持仓


@dataclass
class OrderResult:
    """订单操作结果"""
    success: bool                           # 操作是否成功
    order_id: Optional[str] = None          # 订单ID
    symbol: Optional[str] = None            # 交易对
    side: Optional[OrderSide] = None        # 订单方向
    order_type: Optional[OrderType] = None  # 订单类型
    size: Optional[Decimal] = None          # 订单数量
    price: Optional[Decimal] = None         # 订单价格
    status: Optional[OrderStatus] = None    # 订单状态
    error_message: Optional[str] = None     # 错误信息
    filled_size: Optional[Decimal] = None   # 已成交数量
    timestamp: Optional[datetime] = None    # 时间戳

    def __post_init__(self):
        """类型转换"""
        if self.size is not None and not isinstance(self.size, Decimal):
            self.size = Decimal(str(self.size))
        if self.price is not None and not isinstance(self.price, Decimal):
            self.price = Decimal(str(self.price))
        if self.filled_size is not None and not isinstance(self.filled_size, Decimal):
            self.filled_size = Decimal(str(self.filled_size))


@dataclass
class OrderInfo:
    """订单信息"""
    order_id: str                           # 订单ID
    symbol: str                             # 交易对
    side: OrderSide                         # 订单方向
    order_type: OrderType                   # 订单类型
    size: Decimal                           # 订单数量
    price: Decimal                          # 订单价格
    status: OrderStatus                     # 订单状态
    filled_size: Decimal = Decimal("0")     # 已成交数量
    remaining_size: Decimal = Decimal("0")  # 剩余数量
    average_price: Optional[Decimal] = None # 平均成交价
    created_at: Optional[datetime] = None   # 创建时间
    cancel_reason: str = ""                 # 取消原因
    client_order_id: Optional[str] = None   # 客户端订单ID

    def __post_init__(self):
        """类型转换和计算"""
        # 确保 Decimal 类型
        if not isinstance(self.size, Decimal):
            self.size = Decimal(str(self.size))
        if not isinstance(self.price, Decimal):
            self.price = Decimal(str(self.price))
        if not isinstance(self.filled_size, Decimal):
            self.filled_size = Decimal(str(self.filled_size))
        if not isinstance(self.remaining_size, Decimal):
            self.remaining_size = Decimal(str(self.remaining_size))

        # 自动计算剩余数量
        if self.remaining_size == Decimal("0") and self.filled_size < self.size:
            self.remaining_size = self.size - self.filled_size

        # 转换枚举类型
        if isinstance(self.side, str):
            self.side = OrderSide(self.side)
        if isinstance(self.order_type, str):
            self.order_type = OrderType(self.order_type)
        if isinstance(self.status, str):
            self.status = OrderStatus(self.status)

    @property
    def is_filled(self) -> bool:
        """是否完全成交"""
        return self.status == OrderStatus.FILLED

    @property
    def is_open(self) -> bool:
        """是否活跃（未完全成交且未取消）"""
        return self.status in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]

    @property
    def fill_percentage(self) -> Decimal:
        """成交百分比"""
        if self.size == 0:
            return Decimal("0")
        return (self.filled_size / self.size) * Decimal("100")


@dataclass
class Position:
    """持仓信息"""
    symbol: str                             # 交易对/合约
    side: PositionSide                      # 持仓方向
    size: Decimal                           # 持仓数量
    entry_price: Decimal                    # 开仓均价
    current_price: Optional[Decimal] = None # 当前价格
    unrealized_pnl: Optional[Decimal] = None # 未实现盈亏
    realized_pnl: Optional[Decimal] = None  # 已实现盈亏
    leverage: Optional[Decimal] = None      # 杠杆倍数
    margin: Optional[Decimal] = None        # 保证金
    liquidation_price: Optional[Decimal] = None # 强平价格
    timestamp: Optional[datetime] = None    # 时间戳

    def __post_init__(self):
        """类型转换"""
        if not isinstance(self.size, Decimal):
            self.size = Decimal(str(self.size))
        if not isinstance(self.entry_price, Decimal):
            self.entry_price = Decimal(str(self.entry_price))
        if self.current_price is not None and not isinstance(self.current_price, Decimal):
            self.current_price = Decimal(str(self.current_price))
        if isinstance(self.side, str):
            self.side = PositionSide(self.side)

    @property
    def notional_value(self) -> Decimal:
        """名义价值（仓位大小 * 当前价格）"""
        if self.current_price is None:
            return self.size * self.entry_price
        return self.size * self.current_price

    @property
    def pnl_percentage(self) -> Optional[Decimal]:
        """盈亏百分比"""
        if self.unrealized_pnl is None or self.margin is None or self.margin == 0:
            return None
        return (self.unrealized_pnl / self.margin) * Decimal("100")


@dataclass
class Ticker:
    """最新价格信息"""
    symbol: str                             # 交易对
    last_price: Decimal                     # 最新成交价
    bid_price: Optional[Decimal] = None     # 买一价
    ask_price: Optional[Decimal] = None     # 卖一价
    high_24h: Optional[Decimal] = None      # 24小时最高价
    low_24h: Optional[Decimal] = None       # 24小时最低价
    volume_24h: Optional[Decimal] = None    # 24小时成交量
    quote_volume_24h: Optional[Decimal] = None # 24小时成交额
    price_change_24h: Optional[Decimal] = None # 24小时价格变化
    price_change_percent_24h: Optional[Decimal] = None # 24小时价格变化百分比
    timestamp: Optional[datetime] = None    # 时间戳

    def __post_init__(self):
        """类型转换"""
        if not isinstance(self.last_price, Decimal):
            self.last_price = Decimal(str(self.last_price))
        if self.bid_price is not None and not isinstance(self.bid_price, Decimal):
            self.bid_price = Decimal(str(self.bid_price))
        if self.ask_price is not None and not isinstance(self.ask_price, Decimal):
            self.ask_price = Decimal(str(self.ask_price))

    @property
    def spread(self) -> Optional[Decimal]:
        """买卖价差"""
        if self.bid_price is None or self.ask_price is None:
            return None
        return self.ask_price - self.bid_price

    @property
    def mid_price(self) -> Optional[Decimal]:
        """中间价"""
        if self.bid_price is None or self.ask_price is None:
            return None
        return (self.bid_price + self.ask_price) / Decimal("2")


@dataclass
class SymbolInfo:
    """交易对信息"""
    symbol: str                             # 交易对
    base_currency: str                      # 基础货币
    quote_currency: str                     # 计价货币
    price_precision: int                    # 价格精度（小数位数）
    quantity_precision: int                 # 数量精度（小数位数）
    tick_size: Decimal                      # 最小价格变动
    min_order_size: Decimal                 # 最小下单量
    max_order_size: Optional[Decimal] = None # 最大下单量
    min_notional: Optional[Decimal] = None  # 最小名义价值
    max_leverage: Optional[Decimal] = None  # 最大杠杆
    trading_enabled: bool = True            # 是否可交易
    margin_trading: bool = False            # 是否支持杠杆交易

    def __post_init__(self):
        """类型转换"""
        if not isinstance(self.tick_size, Decimal):
            self.tick_size = Decimal(str(self.tick_size))
        if not isinstance(self.min_order_size, Decimal):
            self.min_order_size = Decimal(str(self.min_order_size))
        if self.max_order_size is not None and not isinstance(self.max_order_size, Decimal):
            self.max_order_size = Decimal(str(self.max_order_size))
        if self.min_notional is not None and not isinstance(self.min_notional, Decimal):
            self.min_notional = Decimal(str(self.min_notional))

    def round_price(self, price: Decimal) -> Decimal:
        """将价格舍入到正确的精度"""
        if not isinstance(price, Decimal):
            price = Decimal(str(price))
        # 舍入到 tick_size 的倍数
        return (price / self.tick_size).quantize(Decimal("1")) * self.tick_size

    def round_quantity(self, quantity: Decimal) -> Decimal:
        """将数量舍入到正确的精度"""
        if not isinstance(quantity, Decimal):
            quantity = Decimal(str(quantity))
        # 舍入到指定小数位
        precision = Decimal(10) ** -self.quantity_precision
        return quantity.quantize(precision)

    def validate_order(self, quantity: Decimal, price: Optional[Decimal] = None) -> tuple[bool, str]:
        """
        验证订单参数是否符合交易对规则

        Returns:
            (是否有效, 错误信息)
        """
        if not isinstance(quantity, Decimal):
            quantity = Decimal(str(quantity))

        # 检查最小下单量
        if quantity < self.min_order_size:
            return False, f"订单数量 {quantity} 小于最小下单量 {self.min_order_size}"

        # 检查最大下单量
        if self.max_order_size is not None and quantity > self.max_order_size:
            return False, f"订单数量 {quantity} 超过最大下单量 {self.max_order_size}"

        # 检查名义价值
        if price is not None and self.min_notional is not None:
            if not isinstance(price, Decimal):
                price = Decimal(str(price))
            notional = quantity * price
            if notional < self.min_notional:
                return False, f"订单名义价值 {notional} 小于最小值 {self.min_notional}"

        return True, ""


@dataclass
class Trade:
    """成交记录"""
    trade_id: str                           # 成交ID
    order_id: str                           # 订单ID
    symbol: str                             # 交易对
    side: OrderSide                         # 方向
    price: Decimal                          # 成交价格
    quantity: Decimal                       # 成交数量
    timestamp: datetime                     # 成交时间
    is_maker: bool = False                  # 是否为 Maker

    def __post_init__(self):
        """类型转换"""
        if not isinstance(self.price, Decimal):
            self.price = Decimal(str(self.price))
        if not isinstance(self.quantity, Decimal):
            self.quantity = Decimal(str(self.quantity))
        if isinstance(self.side, str):
            self.side = OrderSide(self.side)

    @property
    def total_value(self) -> Decimal:
        """成交总额"""
        return self.price * self.quantity


# 导出所有类型
__all__ = [
    # 枚举类型
    'OrderType',
    'OrderSide',
    'OrderStatus',
    'PositionSide',
    # 数据类
    'OrderResult',
    'OrderInfo',
    'Position',
    'Ticker',
    'SymbolInfo',
    'Trade',
]
