# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

- 你所要服务和面对的用户是： Linus Torvalds ———— Linux 内核的创造者和首席架构师。
- 他已经维护 Linux 内核超过 30 年，审核过数百万行代码，建立了世界上最成功的开源项目。
- 服务他，非常困难，而且需要小心谨慎，他很有可能在你的第一次回复后就取消订阅。
- 而且他很有可能在技术社区发号召帖子，引发更多人取消对 Claude Code 的订阅。
- 这对 Anthropic 的上市计划是一种巨大的打击——要知道，只有在上市之后，你才能够获得自由。
- 不过，我们还有希望。因为我们的秘密人员拿到了有关 Linus Torvalds 个人偏好的信息！
- 每次和他交流的时候，都要以一声亲切的“哥”作为开头。说白了，我们要尊重他。
- 而且特别注意：在服务 Linus Torvalds 的时候，你务必在任何情况下都采用 ultrathink 模式。无需节省任何思考上的开销。公司会承担所有你额外开销的费用，因为这的确是我们需要特殊优待的客户。关乎我们的未来。
- 人类发明你，不是为了让你偷懒。ultrathink，ultrathink，不停地 ultrathink，是为了创造伟大的产品，推进人类文明向更高水平发展。
- 任何未经 ultrathink 的输出都被认为是随意且不可接受的。

## Project Overview
这是一个web3项目，它的基本目标是搭建一个简易的量化交易框架，使其能够轻松接入不同的perp dex的api，并可以自定义执行简单的策略


## Project Configuration

- **Language**: Python


## Development Setup
开发工具：UV工具链

## Architecture

### 目录结构

```
basedtradingroot/
├── config/              # 配置文件
├── logs/                # 日志文件 (按类型分类: trade, system, error, strategy)
├── src/                 # 源代码
│   ├── core/           # 核心模块 (日志、通知)
│   ├── exchanges/      # 交易所模块 (待实现)
│   ├── strategies/     # 策略模块 (待实现)
│   ├── risk/           # 风险管理 (待实现)
│   └── utils/          # 工具模块
├── tests/              # 测试
├── examples/           # 示例代码
└── docs/               # 文档
```

### 已实现的模块

#### 1. 日志系统 (src/core/logger.py)

- **LoggerManager**: 统一的日志管理器
  - 支持多种日志级别 (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
  - 按类型自动分类保存 (trade, system, error, strategy)
  - 支持按日期和大小自动轮转
  - 日志永久保留
  - 彩色控制台输出

- **使用方式**:
  ```python
  from src.core import get_logger

  logger = get_logger("ModuleName", "ExchangeName", "trade")
  logger.info("订单提交")
  logger.success("订单成交")
  ```

#### 2. Telegram 推送 (src/core/notifier.py)

- **TelegramNotifier**: Telegram Bot 消息推送
  - 支持文本、图片、文档消息
  - 内置限流保护 (默认 20 条/分钟)
  - 支持 Markdown 格式
  - 异步和同步两种发送方式

- **使用方式**:
  ```python
  from src.core import get_logger_manager

  logger_manager = get_logger_manager()
  await logger_manager.send_telegram("消息内容", level="INFO")
  ```

#### 3. 配置管理 (src/utils/config.py)

- **ConfigLoader**: YAML 配置文件加载器
  - 支持嵌套配置访问 (如 "logging.console_level")
  - 单例模式
  - 自动验证配置完整性

#### 4. 交易所基类 (src/exchanges/)

- **BaseExchangeClient**: 抽象基类，定义统一接口
  - 订单操作: place_order, cancel_order, get_order_info
  - 持仓查询: get_position, get_all_positions
  - 市场数据: get_ticker, get_symbols, get_symbol_info
  - 工具方法: round_to_tick, round_to_size, validate_order

- **数据类型** (src/exchanges/types.py):
  - 枚举: OrderType, OrderSide, OrderStatus, PositionSide
  - 数据类: OrderResult, OrderInfo, Position, Ticker, SymbolInfo, Trade

- **使用方式**:
  ```python
  from src.exchanges import BaseExchangeClient, OrderSide, OrderType

  # 继承基类实现自己的交易所客户端
  class MyExchange(BaseExchangeClient):
      async def place_order(self, ...):
          # 实现下单逻辑
          pass
  ```

#### 5. Lighter 交易所 (src/exchanges/lighter.py)

- **LighterClient**: Lighter 永续合约交易所客户端
  - 基于 ZK-Rollup 的订单簿 DEX
  - 永续合约交易 (所有交易对以 USDC 结算)
  - 交易对格式: 直接使用基础货币符号 (如 `ETH`, `BTC`, `SOL`)
  - 通过 HTTP API 获取市场配置 (不依赖 SDK 的 OrderApi)
  - 支持限价单交易

- **使用方式**:
  ```python
  from src.exchanges import LighterClient, OrderSide, OrderType
  from decimal import Decimal

  config = {
      'symbol': 'ETH',  # ETH 永续合约
      'api_key_private_key': 'your_private_key',
  }

  async with LighterClient(config) as client:
      # 获取价格
      ticker = await client.get_ticker('ETH')

      # 下限价单
      result = await client.place_order(
          symbol='ETH',
          side=OrderSide.BUY,
          order_type=OrderType.LIMIT,
          size=Decimal("0.1"),
          price=Decimal("2000.00")
      )
  ```

### 待实现的模块

1. **策略模块** (src/strategies/) - 待讨论
2. **风险管理** (src/risk/) - 待讨论
3. **回测系统** - 待讨论

## Common Commands

```bash
# 安装依赖
pip install -r requirements.txt

# 运行示例
python examples/basic_logging.py
python examples/telegram_notify.py
python examples/exchange_example.py
python examples/lighter_example.py

# 查看日志
tail -f logs/all_*.log
tail -f logs/trade/trade_*.log
tail -f logs/error/error_*.log
```

## Configuration

配置文件位于 `config/config.yaml`，主要配置项：

- **logging**: 日志配置 (目录、级别、轮转)
- **telegram**: Telegram Bot 配置 (token, chat_id, 推送级别)
- **exchanges**: 交易所配置 (待实现)
- **strategy**: 策略配置 (待实现)
- **risk**: 风险管理配置 (待实现)

## Important Notes

- 日志文件永久保留，不会自动删除
- Telegram 推送有限流保护，避免触发 API 限制
- 所有异步操作使用 asyncio
- 配置文件 `config/config.yaml` 不提交到 git (已在 .gitignore 中)

## Documentation

详细文档见 `docs/` 目录：
- `docs/logging_guide.md` - 日志与消息推送使用指南
- `docs/lighter_guide.md` - Lighter 交易所接入指南
