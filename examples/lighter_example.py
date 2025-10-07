"""
Lighter 交易所使用示例

注意：运行此示例需要：
1. 安装 Lighter SDK: pip install lighter-v2-python
2. 设置环境变量或配置文件
"""
import sys
import asyncio
from pathlib import Path
from decimal import Decimal

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.exchanges import LighterClient, OrderSide, OrderType
from src.core import get_logger


async def main():
    """主函数"""
    print("=" * 60)
    print("Lighter 交易所使用示例")
    print("=" * 60)

    # 配置 Lighter 客户端
    # 注意：实际使用时请从环境变量或安全的配置文件读取
    config = {
        'symbol': 'ETH',  # 交易对 (永续合约)
        'api_key_private_key': 'YOUR_PRIVATE_KEY',  # 或从环境变量读取
        'account_index': 0,
        'api_key_index': 0,
        'base_url': 'https://mainnet.zklighter.elliot.ai',
    }

    # 检查是否配置了私钥
    if config['api_key_private_key'] == 'YOUR_PRIVATE_KEY':
        print("\n⚠️  请先配置您的 Lighter API 私钥！")
        print("方式1: 在配置文件中设置 api_key_private_key")
        print("方式2: 设置环境变量 API_KEY_PRIVATE_KEY")
        print("\n示例命令:")
        print("export API_KEY_PRIVATE_KEY=your_private_key_here")
        print("export LIGHTER_ACCOUNT_INDEX=0")
        print("export LIGHTER_API_KEY_INDEX=0")
        return

    try:
        # 创建客户端
        print("\n【1】创建 Lighter 客户端")
        client = LighterClient(config)
        print(f"✅ 客户端创建成功 - 交易对: {config['symbol']}")

        # 连接交易所
        print("\n【2】连接到 Lighter")
        async with client:
            # 获取市场信息
            print("\n【3】获取市场信息")
            symbol_info = await client.get_symbol_info(config['symbol'])
            print(f"交易对: {symbol_info.symbol}")
            print(f"基础货币: {symbol_info.base_currency}")
            print(f"计价货币: {symbol_info.quote_currency}")
            print(f"价格精度: {symbol_info.price_precision} 位")
            print(f"数量精度: {symbol_info.quantity_precision} 位")
            print(f"Tick Size: {symbol_info.tick_size}")

            # 获取最新价格
            print("\n【4】获取最新价格")
            ticker = await client.get_ticker(config['symbol'])
            print(f"最新价: ${ticker.last_price}")
            if ticker.bid_price and ticker.ask_price:
                print(f"买一价: ${ticker.bid_price}")
                print(f"卖一价: ${ticker.ask_price}")
                print(f"价差: ${ticker.spread}")

            # 获取持仓
            print("\n【5】获取持仓信息")
            positions = await client.get_all_positions()
            if positions:
                for pos in positions:
                    print(f"持仓: {pos.symbol}")
                    print(f"  方向: {pos.side.value}")
                    print(f"  数量: {pos.size}")
                    print(f"  开仓价: ${pos.entry_price}")
                    if pos.unrealized_pnl:
                        print(f"  未实现盈亏: ${pos.unrealized_pnl}")
            else:
                print("当前无持仓")

            # 获取活跃订单
            print("\n【6】获取活跃订单")
            active_orders = await client.get_active_orders(config['symbol'])
            if active_orders:
                for order in active_orders:
                    print(f"订单 {order.order_id}:")
                    print(f"  {order.side.value} {order.size} @ ${order.price}")
                    print(f"  状态: {order.status.value}")
                    print(f"  已成交: {order.filled_size}")
            else:
                print("当前无活跃订单")

            # 模拟下单（注释掉以避免实际交易）
            print("\n【7】模拟下单流程")
            print("⚠️  以下代码已注释，取消注释以执行实际交易")
            print("""
            # 下限价单示例
            result = await client.place_order(
                symbol=config['symbol'],
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                size=Decimal("0.01"),
                price=Decimal("2000.00"),
            )

            if result.success:
                print(f"✅ 订单提交成功: {result.order_id}")

                # 查询订单状态
                order_info = await client.get_order_info(result.order_id)
                if order_info:
                    print(f"订单状态: {order_info.status.value}")

                # 取消订单
                cancel_result = await client.cancel_order(result.order_id)
                if cancel_result.success:
                    print(f"✅ 订单已取消")
            """)

            # 获取所有可用交易对
            print("\n【8】获取所有可用交易对")
            all_symbols = await client.get_symbols()
            print(f"可用交易对数量: {len(all_symbols)}")
            print(f"示例: {', '.join(all_symbols[:5])}...")

    except ValueError as e:
        print(f"\n❌ 配置错误: {e}")
        print("请检查您的配置参数")
    except Exception as e:
        print(f"\n❌ 错误: {e}")

    print("\n" + "=" * 60)
    print("示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
