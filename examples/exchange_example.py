"""
交易所模块使用示例 - 演示如何继承 BaseExchangeClient
"""
import sys
import asyncio
from pathlib import Path
from decimal import Decimal
from typing import Dict, Any, Optional, List

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.exchanges import (
    BaseExchangeClient,
    OrderResult,
    OrderInfo,
    Position,
    Ticker,
    SymbolInfo,
    OrderType,
    OrderSide,
    OrderStatus,
    PositionSide,
)
from src.core import get_logger


class MockExchangeClient(BaseExchangeClient):
    """
    模拟交易所客户端（用于演示）

    这是一个示例实现，展示如何继承 BaseExchangeClient
    实际的交易所实现需要对接真实的 API
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = get_logger("MockExchange", "MOCK", "trade")
        self.connected = False
        # 模拟数据存储
        self.orders: Dict[str, OrderInfo] = {}
        self.positions: Dict[str, Position] = {}
        self.order_counter = 1

    def _validate_config(self) -> None:
        """验证配置"""
        required_keys = ['api_key', 'api_secret']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"配置缺少必需字段: {key}")

    async def connect(self) -> None:
        """连接到交易所"""
        self.logger.info("正在连接到模拟交易所...")
        await asyncio.sleep(0.5)  # 模拟连接延迟
        self.connected = True
        self.logger.success("连接成功！")

    async def disconnect(self) -> None:
        """断开连接"""
        self.logger.info("正在断开连接...")
        self.connected = False
        self.logger.info("已断开连接")

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        size: Decimal,
        price: Optional[Decimal] = None,
        **kwargs
    ) -> OrderResult:
        """下单"""
        if not self.connected:
            return OrderResult(success=False, error_message="未连接到交易所")

        # 验证订单
        is_valid, error_msg = await self.validate_order(symbol, side, size, price)
        if not is_valid:
            self.logger.error(f"订单验证失败: {error_msg}")
            return OrderResult(success=False, error_message=error_msg)

        # 生成订单ID
        order_id = f"MOCK_{self.order_counter:06d}"
        self.order_counter += 1

        # 创建订单信息
        order_info = OrderInfo(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            size=size,
            price=price or Decimal("0"),
            status=OrderStatus.FILLED,  # 模拟立即成交
            filled_size=size,
            remaining_size=Decimal("0"),
            average_price=price or Decimal("42000"),  # 模拟成交价
        )

        # 保存订单
        self.orders[order_id] = order_info

        self.logger.success(
            f"订单已成交: {symbol} {side.value} {size} @ {price or '市价'}"
        )

        return OrderResult(
            success=True,
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            size=size,
            price=price,
            status=OrderStatus.FILLED,
            filled_size=size,
        )

    async def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> OrderResult:
        """取消订单"""
        if order_id not in self.orders:
            return OrderResult(success=False, error_message=f"订单不存在: {order_id}")

        order = self.orders[order_id]
        if order.status == OrderStatus.FILLED:
            return OrderResult(success=False, error_message="订单已成交，无法取消")

        order.status = OrderStatus.CANCELLED
        self.logger.info(f"订单已取消: {order_id}")

        return OrderResult(success=True, order_id=order_id, status=OrderStatus.CANCELLED)

    async def get_order_info(self, order_id: str, symbol: Optional[str] = None) -> Optional[OrderInfo]:
        """查询订单信息"""
        return self.orders.get(order_id)

    async def get_active_orders(self, symbol: Optional[str] = None) -> List[OrderInfo]:
        """查询活跃订单"""
        active_orders = [
            order for order in self.orders.values()
            if order.is_open and (symbol is None or order.symbol == symbol)
        ]
        return active_orders

    async def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓"""
        return self.positions.get(symbol)

    async def get_all_positions(self) -> List[Position]:
        """获取所有持仓"""
        return list(self.positions.values())

    async def get_ticker(self, symbol: str) -> Ticker:
        """获取最新价格"""
        # 模拟返回价格数据
        return Ticker(
            symbol=symbol,
            last_price=Decimal("42000"),
            bid_price=Decimal("41995"),
            ask_price=Decimal("42005"),
            high_24h=Decimal("43000"),
            low_24h=Decimal("41000"),
            volume_24h=Decimal("1000"),
        )

    async def get_symbols(self) -> List[str]:
        """获取所有交易对"""
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

    async def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """获取交易对信息"""
        # 模拟返回交易对信息
        return SymbolInfo(
            symbol=symbol,
            base_currency="BTC",
            quote_currency="USDT",
            price_precision=2,
            quantity_precision=6,
            tick_size=Decimal("0.01"),
            min_order_size=Decimal("0.0001"),
            max_order_size=Decimal("100"),
            min_notional=Decimal("10"),
            trading_enabled=True,
        )

    def get_exchange_name(self) -> str:
        """获取交易所名称"""
        return "MockExchange"


async def main():
    """主函数"""
    print("=" * 60)
    print("交易所模块使用示例")
    print("=" * 60)

    # 1. 创建交易所客户端
    print("\n【1】创建交易所客户端")
    config = {
        'api_key': 'mock_api_key',
        'api_secret': 'mock_api_secret',
    }
    exchange = MockExchangeClient(config)

    # 2. 连接交易所（使用异步上下文管理器）
    print("\n【2】连接交易所")
    async with exchange:
        # 3. 获取交易对列表
        print("\n【3】获取交易对列表")
        symbols = await exchange.get_symbols()
        print(f"可交易的交易对: {', '.join(symbols)}")

        # 4. 获取交易对信息
        print("\n【4】获取交易对信息")
        symbol = "BTC/USDT"
        symbol_info = await exchange.get_symbol_info(symbol)
        print(f"交易对: {symbol_info.symbol}")
        print(f"价格精度: {symbol_info.price_precision} 位")
        print(f"数量精度: {symbol_info.quantity_precision} 位")
        print(f"最小下单量: {symbol_info.min_order_size}")
        print(f"Tick Size: {symbol_info.tick_size}")

        # 5. 获取最新价格
        print("\n【5】获取最新价格")
        ticker = await exchange.get_ticker(symbol)
        print(f"最新价: ${ticker.last_price:,.2f}")
        print(f"买一价: ${ticker.bid_price:,.2f}")
        print(f"卖一价: ${ticker.ask_price:,.2f}")
        print(f"价差: ${ticker.spread:,.2f}")

        # 6. 下限价单
        print("\n【6】下限价单")
        result = await exchange.place_order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            size=Decimal("0.1"),
            price=Decimal("42000"),
        )

        if result.success:
            print(f"✅ 订单成功: {result.order_id}")
            print(f"   交易对: {result.symbol}")
            print(f"   方向: {result.side}")
            print(f"   数量: {result.size}")
            print(f"   价格: ${result.price}")
            print(f"   状态: {result.status}")

            # 7. 查询订单信息
            print("\n【7】查询订单信息")
            order_info = await exchange.get_order_info(str(result.order_id))
            if order_info:
                print(f"订单ID: {order_info.order_id}")
                print(f"状态: {order_info.status.value}")
                print(f"已成交: {order_info.filled_size}")
                print(f"成交率: {order_info.fill_percentage:.2f}%")
        else:
            print(f"❌ 订单失败: {result.error_message}")

        # 8. 测试订单验证
        print("\n【8】测试订单验证")
        # 测试数量过小
        is_valid, error = await exchange.validate_order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            size=Decimal("0.00001"),  # 小于最小下单量
            price=Decimal("42000"),
        )
        print(f"测试小数量订单: {'✅ 有效' if is_valid else f'❌ 无效 - {error}'}")

        # 9. 测试价格和数量舍入
        print("\n【9】测试价格和数量舍入")
        test_price = Decimal("42000.12345")
        test_size = Decimal("0.123456789")

        rounded_price = exchange.round_to_tick("BTC/USDT", test_price)
        rounded_size = exchange.round_to_size("BTC/USDT", test_size)

        print(f"原始价格: {test_price} -> 舍入后: {rounded_price}")
        print(f"原始数量: {test_size} -> 舍入后: {rounded_size}")

    print("\n" + "=" * 60)
    print("示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
