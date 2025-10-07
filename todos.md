# 量化交易框架开发任务清单

## 1. 交易所基类模块 (Exchange Base Module)

### 1.1 数据类型设计

#### 需要实现的数据类 (DataClasses)
- [ ] **OrderType** - 订单类型枚举
  - LIMIT (限价单)
  - MARKET (市价单)
  - 其他类型待定

- [ ] **OrderSide** - 订单方向枚举
  - BUY (买入)
  - SELL (卖出)

- [ ] **OrderStatus** - 订单状态枚举
  - PENDING (待处理)
  - OPEN (已开仓)
  - PARTIALLY_FILLED (部分成交)
  - FILLED (完全成交)
  - CANCELLED (已取消)
  - REJECTED (已拒绝)

- [ ] **OrderResult** - 订单操作结果（优化版）
  - success: bool
  - order_id: Optional[str]
  - side: Optional[str]
  - size: Optional[Decimal]
  - price: Optional[Decimal]
  - status: Optional[str]
  - error_message: Optional[str]
  - filled_size: Optional[Decimal]
  - timestamp: Optional[datetime]

- [ ] **OrderInfo** - 订单信息（增强版）
  - order_id: str
  - symbol: str (交易对)
  - side: str
  - order_type: str
  - size: Decimal
  - price: Decimal
  - status: str
  - filled_size: Decimal
  - remaining_size: Decimal
  - average_price: Optional[Decimal] (平均成交价)
  - fee: Optional[Decimal] (手续费)
  - created_at: Optional[datetime]
  - updated_at: Optional[datetime]
  - cancel_reason: str

- [ ] **Position** - 持仓信息
  - symbol: str (交易对/合约)
  - side: str (LONG/SHORT)
  - size: Decimal (持仓数量)
  - entry_price: Decimal (开仓均价)
  - current_price: Optional[Decimal] (当前价格)
  - unrealized_pnl: Optional[Decimal] (未实现盈亏)
  - realized_pnl: Optional[Decimal] (已实现盈亏)
  - leverage: Optional[Decimal] (杠杆倍数)

- [ ] **Ticker** - 最新价格信息
  - symbol: str
  - last_price: Decimal (最新成交价)
  - bid_price: Optional[Decimal] (买一价)
  - ask_price: Optional[Decimal] (卖一价)
  - volume_24h: Optional[Decimal] (24小时成交量)
  - timestamp: datetime

- [ ] **SymbolInfo** - 交易对信息
  - symbol: str
  - base_currency: str (基础货币)
  - quote_currency: str (计价货币)
  - price_precision: int (价格精度)
  - quantity_precision: int (数量精度)
  - tick_size: Decimal (最小价格变动)
  - min_order_size: Decimal (最小下单量)
  - max_order_size: Optional[Decimal] (最大下单量)
  - min_notional: Optional[Decimal] (最小名义价值)

### 1.2 BaseExchangeClient 抽象基类

#### 需要保留的方法
- [ ] `__init__(config: Dict[str, Any])` - 初始化
- [ ] `_validate_config() -> None` - 配置验证
- [ ] `connect() -> None` - 连接交易所
- [ ] `disconnect() -> None` - 断开连接
- [ ] `cancel_order(order_id: str) -> OrderResult` - 取消订单
- [ ] `get_order_info(order_id: str) -> Optional[OrderInfo]` - 查询订单信息
- [ ] `get_active_orders(symbol: str) -> List[OrderInfo]` - 查询活跃订单
- [ ] `setup_order_update_handler(handler) -> None` - 设置订单更新回调
- [ ] `get_exchange_name() -> str` - 获取交易所名称
- [ ] `round_to_tick(price) -> Decimal` - 价格精度处理

#### 需要修改的方法
- [ ] ~~`place_open_order()`~~ → `place_order(symbol: str, side: OrderSide, order_type: OrderType, size: Decimal, price: Optional[Decimal]) -> OrderResult` - 统一下单接口
- [ ] ~~`place_close_order()`~~ → 合并到 `place_order()`
- [ ] ~~`get_account_positions() -> Decimal`~~ → `get_position(symbol: str) -> Optional[Position]` - 获取指定合约持仓

#### 需要新增的方法
- [ ] `round_to_size(size: Decimal) -> Decimal` - 数量精度处理
- [ ] `validate_order(symbol: str, side: OrderSide, size: Decimal, price: Optional[Decimal]) -> bool` - 订单参数验证
- [ ] `get_ticker(symbol: str) -> Ticker` - 获取最新价格
- [ ] `get_symbols() -> List[str]` - 获取所有交易对
- [ ] `get_symbol_info(symbol: str) -> SymbolInfo` - 获取交易对详细信息
- [ ] `modify_order(order_id: str, new_price: Optional[Decimal], new_size: Optional[Decimal]) -> OrderResult` - 修改订单（可选，如果交易所支持）

#### 当前阶段不需要的功能
- ~~`get_orderbook()` - 获取订单簿~~
- ~~`get_klines()` - 获取K线数据~~
- ~~`get_balance()` - 获取账户余额（假设余额充足）~~
- ~~`cancel_all_orders()` - 批量取消订单~~
- ~~`get_order_history()` - 获取历史订单~~

### 1.3 实现任务
- [x] 创建项目目录结构
- [x] 实现所有数据类和枚举类型 (src/exchanges/types.py)
- [x] 实现 BaseExchangeClient 抽象基类 (src/exchanges/base.py)
- [ ] 编写单元测试
- [x] 编写使用文档和示例 (examples/exchange_example.py)

---

## 2. 日志与消息推送模块 (Logging & Notification Module)

### 2.1 日志系统设计 (基于 loguru)

#### 日志级别
- **TRACE** - 详细的调试信息
- **DEBUG** - 调试信息
- **INFO** - 一般信息（订单提交、成交等）
- **SUCCESS** - 成功操作（交易成功、连接成功等）
- **WARNING** - 警告信息（网络波动、重试等）
- **ERROR** - 错误信息（订单失败、API错误等）
- **CRITICAL** - 严重错误（连接断开、资金异常等）

#### 日志格式设计
```
[时间] [级别] [模块] [交易所] - 消息内容
例如：
[2025-01-15 10:30:45.123] [INFO] [Exchange] [Binance] - 订单提交成功 BTC/USDT BUY 0.1 @ 42000
[2025-01-15 10:30:46.456] [SUCCESS] [Exchange] [Binance] - 订单完全成交 #12345 BTC/USDT 0.1 @ 42000
[2025-01-15 10:30:50.789] [ERROR] [Exchange] [OKX] - 订单提交失败: 余额不足
```

#### 日志配置要求
- [ ] 支持按日期自动轮转（每天一个文件）
- [ ] 支持按大小轮转（单文件最大100MB）
- [ ] 永久保留所有日志文件（不自动删除）
- [ ] 控制台输出彩色日志
- [ ] 文件输出纯文本日志
- [ ] 支持不同模块使用不同的日志级别

#### 日志内容分类
- [ ] **交易日志** (trade.log)
  - 订单提交、成交、取消
  - 持仓变化
  - 盈亏记录

- [ ] **系统日志** (system.log)
  - 启动/停止
  - 连接状态
  - 配置加载

- [ ] **错误日志** (error.log)
  - 所有 ERROR 和 CRITICAL 级别
  - 异常堆栈信息

- [ ] **策略日志** (strategy.log)
  - 策略信号
  - 策略决策过程
  - 参数调整

### 2.2 Telegram Bot 消息推送

#### 推送消息类型
- [ ] **交易通知**
  - 开仓/平仓通知
  - 订单成交通知
  - 止损/止盈触发

- [ ] **系统通知**
  - 策略启动/停止
  - 连接异常告警
  - 严重错误告警

- [ ] **自定义消息**
  - 支持自由定义消息内容和格式
  - 支持Markdown格式
  - 支持添加自定义emoji和格式化

#### Telegram 消息格式设计

**交易通知格式**
```
🔔 订单成交通知

交易所: Binance
交易对: BTC/USDT
方向: 🟢 买入 / 🔴 卖出
数量: 0.1 BTC
价格: $42,000
总额: $4,200
手续费: $4.2
时间: 2025-01-15 10:30:45

订单ID: #12345
```

**系统告警格式**
```
⚠️ 系统告警

级别: ERROR
模块: Exchange
交易所: OKX
消息: WebSocket连接断开，正在重连...
时间: 2025-01-15 10:35:00
```

**自定义消息格式**
```
支持任意自定义格式，例如：

💰 盈亏提醒
当前总盈亏: +$500 (📈 +2.5%)

🎯 策略信号
交易对: BTC/USDT
信号: 买入
理由: MA交叉 + RSI超卖

⚡ 快速通知
任意自定义内容...
```

#### Telegram Bot 配置
- [ ] **基础配置**
  - bot_token: str (Bot Token)
  - chat_id: str (接收消息的 Chat ID)
  - enabled: bool (是否启用推送)

- [ ] **推送级别过滤**
  - min_level: str (最小推送级别，如 "WARNING" 以上才推送)
  - notify_on_trade: bool (是否推送所有交易)
  - notify_on_error: bool (是否推送错误)

- [ ] **限流保护**
  - rate_limit: int (每分钟最多发送消息数)
  - batch_interval: int (批量发送间隔，秒)

### 2.3 日志管理器实现

#### LoggerManager 类设计
- [ ] `__init__(config: Dict)` - 初始化日志系统
- [ ] `get_logger(module_name: str) -> Logger` - 获取特定模块的logger
- [ ] `log_trade(exchange: str, symbol: str, side: str, size: Decimal, price: Decimal, ...)` - 记录交易日志
- [ ] `log_order(order_info: OrderInfo)` - 记录订单信息
- [ ] `log_position(position: Position)` - 记录持仓信息
- [ ] `log_error(module: str, error: Exception)` - 记录错误
- [ ] `send_telegram(message: str, parse_mode: str = "Markdown")` - 发送自定义Telegram消息
- [ ] `format_trade_message(order_info: OrderInfo) -> str` - 格式化交易消息（可选）
- [ ] `format_alert_message(level: str, module: str, message: str) -> str` - 格式化告警消息（可选）

#### TelegramNotifier 类设计 (使用 python-telegram-bot)
- [ ] `__init__(bot_token: str, chat_id: str, config: Dict)` - 初始化
- [ ] `async send_message(text: str, parse_mode: str = "Markdown")` - 发送自定义消息
- [ ] `async send_photo(photo: str, caption: str)` - 发送图片消息（可选）
- [ ] `_check_rate_limit() -> bool` - 检查限流
- [ ] `_init_bot() -> Application` - 初始化telegram bot实例

### 2.4 实现任务
- [ ] 安装依赖: loguru, python-telegram-bot
- [ ] 配置 loguru 日志系统（多文件、轮转、格式化、永久保留）
- [ ] 实现 LoggerManager 统一日志管理
- [ ] 实现 TelegramNotifier 消息推送（基于 python-telegram-bot）
- [ ] 实现日志与Telegram的双向输出（可选）
- [ ] 实现限流保护机制
- [ ] 编写配置文件模板
- [ ] 编写使用示例和文档

### 2.5 依赖包
```bash
pip install loguru python-telegram-bot
```

---

## 待讨论的其他模块

3. **策略模块** - 交易策略的定义和执行
4. **风险管理模块** - 仓位管理、止损止盈
5. **回测分析模块** - 性能指标计算和可视化
6. **配置管理模块** - 统一的配置文件管理

---

## 设计决策待确认

- [ ] 是否需要同时支持 WebSocket 和 REST API？
- [ ] 错误处理策略：重试机制、异常类型定义
- [ ] 日志记录规范
- [ ] 异步/同步接口选择（当前设计为 async）
