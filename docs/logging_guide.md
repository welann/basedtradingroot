# 日志与消息推送使用指南

本文档介绍如何使用 basedtradingroot 框架的日志系统和 Telegram 消息推送功能。

## 目录
- [快速开始](#快速开始)
- [日志系统](#日志系统)
- [Telegram 推送](#telegram-推送)
- [高级用法](#高级用法)
- [常见问题](#常见问题)

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置文件

复制配置文件模板：

```bash
cp config/config.example.yaml config/config.yaml
```

编辑 `config/config.yaml`，根据需要修改配置。

### 3. 基础使用

```python
from src.utils import get_config
from src.core import get_logger_manager, get_logger

# 加载配置
config = get_config()

# 初始化日志管理器
logger_manager = get_logger_manager(config.config)

# 获取 logger
logger = get_logger("MyModule", "Binance", "trade")

# 记录日志
logger.info("交易开始")
logger.success("订单成交")
logger.error("订单失败")
```

---

## 日志系统

### 日志级别

框架支持以下日志级别（从低到高）：

- **TRACE**: 详细的调试信息
- **DEBUG**: 调试信息
- **INFO**: 一般信息
- **SUCCESS**: 成功操作
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

### 日志分类

日志会自动分类保存到不同的文件：

1. **交易日志** (`logs/trade/trade_YYYY-MM-DD.log`)
   - 订单提交、成交、取消
   - 持仓变化
   - 盈亏记录

2. **系统日志** (`logs/system/system_YYYY-MM-DD.log`)
   - 启动/停止
   - 连接状态
   - 配置加载

3. **错误日志** (`logs/error/error_YYYY-MM-DD.log`)
   - 所有 ERROR 和 CRITICAL 级别
   - 异常堆栈信息

4. **策略日志** (`logs/strategy/strategy_YYYY-MM-DD.log`)
   - 策略信号
   - 策略决策过程
   - 参数调整

5. **完整日志** (`logs/all_YYYY-MM-DD.log`)
   - 所有日志的完整记录

### 获取不同类型的 Logger

```python
from src.core import get_logger

# 系统日志
system_logger = get_logger("System", "N/A", "system")
system_logger.info("系统启动")

# 交易日志
trade_logger = get_logger("Trade", "Binance", "trade")
trade_logger.info("提交订单")

# 策略日志
strategy_logger = get_logger("Strategy", "MyStrategy", "strategy")
strategy_logger.info("策略信号触发")
```

### 日志格式

日志格式为：
```
[时间] [级别] [模块] [交易所] - 消息内容
```

示例：
```
[2025-01-15 10:30:45.123] [INFO] [Exchange] [Binance] - 订单提交成功
```

### 日志配置

在 `config/config.yaml` 中配置：

```yaml
logging:
  log_dir: "logs"                # 日志目录
  console_level: "INFO"          # 控制台输出级别
  file_level: "DEBUG"            # 文件输出级别

  rotation:
    time: "00:00"                # 每天凌晨轮转
    size: 100                    # 单文件最大 100MB

  # 模块级别配置（可选）
  module_levels:
    exchange: "DEBUG"
    strategy: "INFO"
```

---

## Telegram 推送

### 配置 Telegram Bot

1. **创建 Bot**
   - 在 Telegram 中找到 [@BotFather](https://t.me/BotFather)
   - 发送 `/newbot` 创建新 Bot
   - 按提示设置 Bot 名称
   - 获取 Bot Token（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

2. **获取 Chat ID**
   - 在 Telegram 中找到 [@userinfobot](https://t.me/userinfobot)
   - 发送任意消息获取您的 Chat ID
   - 或者将 Bot 添加到群组，使用 [@RawDataBot](https://t.me/RawDataBot) 获取群组 ID

3. **配置文件**
   ```yaml
   telegram:
     enabled: true
     bot_token: "YOUR_BOT_TOKEN"
     chat_id: "YOUR_CHAT_ID"
     min_level: "WARNING"           # 最小推送级别
     notify_on_trade: true          # 推送交易通知
     notify_on_error: true          # 推送错误
     rate_limit: 20                 # 限流：20 条/分钟
     batch_interval: 5              # 批量间隔：5 秒
   ```

### 发送消息

#### 基础用法

```python
from src.core import get_logger_manager

logger_manager = get_logger_manager()

# 异步发送
await logger_manager.send_telegram("Hello from Bot!", level="INFO")

# 同步发送（非异步环境）
logger_manager.send_telegram_sync("Hello from Bot!")
```

#### 发送交易通知

```python
# 使用格式化方法
trade_msg = logger_manager.format_trade_message(
    exchange="Binance",
    symbol="BTC/USDT",
    side="BUY",
    size=0.1,
    price=42000.0,
    total=4200.0,
    fee=4.2,
    order_id="12345"
)

await logger_manager.send_telegram(trade_msg, level="INFO")
```

输出示例：
```
🔔 订单成交通知

交易所: Binance
交易对: BTC/USDT
方向: 🟢 买入
数量: 0.1
价格: $42,000.00
总额: $4,200.00
手续费: $4.20
时间: 2025-01-15 10:30:45

订单ID: #12345
```

#### 发送告警消息

```python
alert_msg = logger_manager.format_alert_message(
    level="WARNING",
    module="Exchange",
    exchange="OKX",
    message="WebSocket 连接断开，正在重连..."
)

await logger_manager.send_telegram(alert_msg, level="WARNING")
```

输出示例：
```
⚠️ 系统告警

级别: WARNING
模块: Exchange
交易所: OKX
消息: WebSocket 连接断开，正在重连...
时间: 2025-01-15 10:35:00
```

#### 自定义消息

您可以发送任意格式的消息，支持 Markdown：

```python
custom_msg = """💡 **自定义提醒**

📊 今日数据
- 交易次数: 15
- 总盈亏: +$1,250 (📈 +5.2%)

🎯 下单信号
- 交易对: `BTC/USDT`
- 操作: **买入**
"""

await logger_manager.send_telegram(custom_msg, level="INFO")
```

### 限流保护

Telegram API 有速率限制，框架内置了限流保护：

- 默认限制：20 条消息/分钟
- 超过限制时会自动等待
- 可在配置文件中调整 `rate_limit` 参数

---

## 高级用法

### 直接使用 TelegramNotifier

```python
from src.core import TelegramNotifier

notifier = TelegramNotifier(
    bot_token="YOUR_BOT_TOKEN",
    chat_id="YOUR_CHAT_ID",
    config={
        'rate_limit': 20,
        'batch_interval': 5
    }
)

# 发送文本消息
await notifier.send_message("Hello!")

# 发送图片
await notifier.send_photo("chart.png", caption="今日K线图")

# 发送文档
await notifier.send_document("report.pdf", caption="日报")

# 测试连接
is_ok = await notifier.test_connection()
```

### 单例模式

`LoggerManager` 使用单例模式，确保全局只有一个实例：

```python
from src.core import get_logger_manager

# 第一次调用会初始化
logger_manager1 = get_logger_manager(config)

# 后续调用返回同一实例
logger_manager2 = get_logger_manager()

assert logger_manager1 is logger_manager2  # True
```

---

## 常见问题

### Q1: 日志文件在哪里？

A: 默认在项目根目录的 `logs/` 文件夹下，按类型分类：
- `logs/trade/` - 交易日志
- `logs/system/` - 系统日志
- `logs/error/` - 错误日志
- `logs/strategy/` - 策略日志
- `logs/` - 完整日志

### Q2: 如何修改日志级别？

A: 编辑 `config/config.yaml`：

```yaml
logging:
  console_level: "DEBUG"  # 控制台显示 DEBUG 及以上
  file_level: "TRACE"     # 文件记录所有级别
```

### Q3: Telegram 消息发送失败怎么办？

A: 检查以下几点：
1. Bot Token 是否正确
2. Chat ID 是否正确
3. 是否已与 Bot 进行过对话（发送 `/start`）
4. 网络连接是否正常
5. 查看错误日志：`logs/error/error_*.log`

### Q4: 如何关闭 Telegram 推送？

A: 在 `config/config.yaml` 中设置：

```yaml
telegram:
  enabled: false
```

### Q5: 日志文件太多怎么办？

A: 日志文件默认永久保留。如果需要定期清理，可以：

1. 手动删除旧日志
2. 使用系统定时任务（cron/Windows Task Scheduler）
3. 修改 loguru 配置添加 retention 参数（需要修改源码）

### Q6: 如何在策略中使用日志？

A: 在您的策略类中：

```python
from src.core import get_logger

class MyStrategy:
    def __init__(self):
        self.logger = get_logger("MyStrategy", "Binance", "strategy")

    def on_signal(self):
        self.logger.info("MA 交叉信号触发")
        self.logger.debug(f"MA_fast: 42000, MA_slow: 41000")
```

---

## 示例代码

完整示例代码位于 `examples/` 目录：

- `examples/basic_logging.py` - 基础日志示例
- `examples/telegram_notify.py` - Telegram 推送示例

运行示例：

```bash
# 基础日志
python examples/basic_logging.py

# Telegram 推送（需要先配置）
python examples/telegram_notify.py
```

---

## 下一步

- 阅读 [交易所接入指南](exchange_guide.md)（待编写）
- 阅读 [策略开发指南](strategy_guide.md)（待编写）
- 查看 [API 文档](api_reference.md)（待编写）
