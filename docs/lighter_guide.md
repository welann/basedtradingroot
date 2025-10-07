## Lighter 交易所接入指南

本文档介绍如何使用 basedtradingroot 框架连接 Lighter 交易所进行交易。

## 目录
- [简介](#简介)
- [环境准备](#环境准备)
- [配置](#配置)
- [基础使用](#基础使用)
- [API 参考](#api-参考)
- [常见问题](#常见问题)

---

## 简介

Lighter 是一个基于 ZK-Rollup 的去中心化订单簿交易所，提供低手续费和高性能的永续合约交易体验。

### 特点

- ✅ 基于 ZK-Rollup 技术
- ✅ 订单簿交易模式
- ✅ 永续合约 (Perpetual Futures) - 所有交易对均为 USDC 结算
- ✅ 低手续费
- ✅ 支持限价单
- ✅ 实时持仓和订单查询

### 交易对说明

Lighter 提供的是永续合约交易，不是现货交易：
- 符号格式：直接使用基础货币符号（如 `ETH`、`BTC`、`SOL`）
- 所有合约以 USDC 作为保证金和结算货币
- 示例：`ETH` 代表 ETH/USDC 永续合约

---

## 环境准备

### 1. 安装依赖

```bash
pip install lighter-v2-python websockets
```

或使用项目的 requirements.txt：

```bash
pip install -r requirements.txt
```

### 2. 获取 API 凭证

1. 访问 [Lighter](https://lighter.xyz) 官网
2. 创建账户并完成身份验证
3. 获取您的 API 私钥（Private Key）
4. 记录账户索引（Account Index）和 API 密钥索引（API Key Index）

---

## 配置

### 方式一：环境变量（推荐）

```bash
export API_KEY_PRIVATE_KEY=your_private_key_here
export LIGHTER_ACCOUNT_INDEX=0
export LIGHTER_API_KEY_INDEX=0
```

### 方式二：配置文件

编辑 `config/config.yaml`:

```yaml
exchanges:
  lighter:
    enabled: true
    symbol: "ETH"                          # 交易对 (永续合约)
    api_key_private_key: "your_key_here"   # API 私钥
    account_index: 0                       # 账户索引
    api_key_index: 0                       # API 密钥索引
    base_url: "https://mainnet.zklighter.elliot.ai"
```

### 方式三：代码中配置

```python
config = {
    'symbol': 'ETH',  # 永续合约交易对
    'api_key_private_key': 'your_private_key',
    'account_index': 0,
    'api_key_index': 0,
}
```

---

## 基础使用

### 1. 创建客户端

```python
from src.exchanges import LighterClient

config = {
    'symbol': 'ETH',  # ETH 永续合约
    'api_key_private_key': 'your_private_key',
}

client = LighterClient(config)
```

### 2. 连接交易所

```python
# 使用异步上下文管理器
async with client:
    # 执行交易操作...
    pass

# 或手动连接/断开
await client.connect()
# ... 执行操作 ...
await client.disconnect()
```

### 3. 获取市场信息

```python
# 获取交易对信息
symbol_info = await client.get_symbol_info('ETH')
print(f"价格精度: {symbol_info.price_precision}")
print(f"Tick Size: {symbol_info.tick_size}")

# 获取最新价格
ticker = await client.get_ticker('ETH')
print(f"最新价: ${ticker.last_price}")
print(f"买一价: ${ticker.bid_price}")
print(f"卖一价: ${ticker.ask_price}")

# 获取所有可用交易对
symbols = await client.get_symbols()
print(f"可用交易对: {symbols}")  # ['ETH', 'BTC', 'SOL', ...]
```

### 4. 查询持仓和订单

```python
# 获取所有持仓
positions = await client.get_all_positions()
for pos in positions:
    print(f"{pos.symbol}: {pos.side.value} {pos.size} @ ${pos.entry_price}")

# 获取特定交易对的持仓
position = await client.get_position('ETH')
if position:
    print(f"持仓: {position.size}, 盈亏: {position.unrealized_pnl}")

# 获取活跃订单
orders = await client.get_active_orders('ETH')
for order in orders:
    print(f"订单 {order.order_id}: {order.side.value} {order.size} @ ${order.price}")
```

### 5. 下单交易

```python
from decimal import Decimal
from src.exchanges import OrderSide, OrderType

# 下限价买单 - 买入 0.1 ETH @ $2000
result = await client.place_order(
    symbol='ETH',
    side=OrderSide.BUY,
    order_type=OrderType.LIMIT,
    size=Decimal("0.1"),
    price=Decimal("2000.00")
)

if result.success:
    print(f"订单提交成功: {result.order_id}")

    # 查询订单状态
    order_info = await client.get_order_info(result.order_id)
    if order_info:
        print(f"订单状态: {order_info.status.value}")
        print(f"已成交: {order_info.filled_size}")
else:
    print(f"订单失败: {result.error_message}")
```

### 6. 取消订单

```python
# 取消单个订单
cancel_result = await client.cancel_order(order_id)

if cancel_result.success:
    print("订单已取消")
else:
    print(f"取消失败: {cancel_result.error_message}")
```

---

## API 参考

### LighterClient

#### 连接管理

```python
async def connect() -> None
async def disconnect() -> None
```

#### 订单操作

```python
async def place_order(
    symbol: str,
    side: OrderSide,
    order_type: OrderType,
    size: Decimal,
    price: Optional[Decimal] = None
) -> OrderResult

async def cancel_order(order_id: str) -> OrderResult

async def get_order_info(order_id: str) -> Optional[OrderInfo]

async def get_active_orders(symbol: Optional[str] = None) -> List[OrderInfo]
```

#### 持仓查询

```python
async def get_position(symbol: str) -> Optional[Position]

async def get_all_positions() -> List[Position]
```

#### 市场数据

```python
async def get_ticker(symbol: str) -> Ticker

async def get_symbols() -> List[str]

async def get_symbol_info(symbol: str) -> SymbolInfo
```

#### 工具方法

```python
def round_to_tick(symbol: str, price: Decimal) -> Decimal

def round_to_size(symbol: str, size: Decimal) -> Decimal

async def validate_order(
    symbol: str,
    side: OrderSide,
    size: Decimal,
    price: Optional[Decimal]
) -> tuple[bool, str]
```

---

## 完整示例

```python
import asyncio
from decimal import Decimal
from src.exchanges import LighterClient, OrderSide, OrderType

async def main():
    # 配置
    config = {
        'symbol': 'ETH',  # ETH 永续合约
        'api_key_private_key': 'your_private_key',
    }

    # 创建客户端
    client = LighterClient(config)

    async with client:
        # 获取市场信息
        ticker = await client.get_ticker('ETH')
        print(f"当前价格: ${ticker.last_price}")

        # 下单
        result = await client.place_order(
            symbol='ETH',
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            size=Decimal("0.1"),
            price=ticker.bid_price  # 买一价
        )

        if result.success:
            print(f"订单成功: {result.order_id}")

            # 等待一会儿
            await asyncio.sleep(5)

            # 取消订单（如果还未成交）
            cancel_result = await client.cancel_order(result.order_id)
            if cancel_result.success:
                print("订单已取消")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 常见问题

### Q1: 如何获取 API 私钥？

A: 访问 Lighter 官网，在账户设置中生成 API 密钥。注意妥善保管私钥，不要泄露。

### Q2: 支持哪些订单类型？

A: 目前框架集成的 LighterClient 支持限价单（LIMIT）。市价单和其他订单类型可以通过修改代码添加。

### Q3: 如何处理订单成交通知？

A: 可以定期轮询 `get_order_info()` 或 `get_active_orders()` 来检查订单状态。WebSocket 实时推送功能待实现。

### Q4: 报错 "Lighter SDK not installed" 怎么办？

A: 运行 `pip install lighter-v2-python` 安装 Lighter SDK。

### Q5: 如何切换到测试网？

A: 修改配置中的 `base_url` 为测试网地址（如果 Lighter 提供测试网）。

### Q6: 订单精度如何处理？

A: 框架会自动调用 `round_to_tick()` 和 `round_to_size()` 进行精度处理，无需手动舍入。

---

## 下一步

- 查看 [日志与消息推送指南](logging_guide.md)
- 查看 [策略开发指南](strategy_guide.md)（待编写）
- 查看完整示例: `examples/lighter_example.py`

---

## 安全提示

⚠️ **重要安全提示**

1. **永远不要**将 API 私钥硬编码在代码中
2. **永远不要**将包含私钥的配置文件提交到 Git
3. 使用环境变量或安全的密钥管理服务
4. 定期更换 API 密钥
5. 使用专用的交易账户，不要在主账户中存放大额资金
6. 在正式交易前，先在测试网测试代码

---

## 相关链接

- [Lighter 官网](https://lighter.xyz)
- [Lighter 文档](https://docs.lighter.xyz)
- [Lighter SDK GitHub](https://github.com/elliottech/lighter-v2-python)
