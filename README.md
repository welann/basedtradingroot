# basedtradingroot

一个简易的 Python 量化交易框架，支持快速接入多个交易所进行自动化交易。

## ✨ 特性

- 📊 **统一的日志系统** - 基于 loguru，支持分类存储、自动轮转
- 📱 **Telegram 消息推送** - 实时接收交易通知和系统告警
- 🔌 **灵活的交易所接入** - 抽象基类设计，轻松对接不同交易所
- 🛡️ **风险管理** - 仓位控制、止损止盈 (开发中)
- 📈 **策略框架** - 支持自定义交易策略 (开发中)

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone <repository-url>
cd basedtradingroot

# 安装依赖
pip install -r requirements.txt
```

### 配置

```bash
# 复制配置文件模板
cp config/config.example.yaml config/config.yaml

# 编辑配置文件，填入您的配置
nano config/config.yaml
```

### 运行示例

```bash
# 测试日志系统
python examples/basic_logging.py

# 测试 Telegram 推送 (需要先配置 Bot Token)
python examples/telegram_notify.py

# 测试交易所模块
python examples/exchange_example.py
```

## 📖 文档

- [日志与消息推送指南](docs/logging_guide.md)
- [交易所接入指南](docs/exchange_guide.md) (待编写)
- [策略开发指南](docs/strategy_guide.md) (待编写)

## 🏗️ 项目结构

```
basedtradingroot/
├── config/              # 配置文件
├── logs/                # 日志输出 (自动生成)
├── src/                 # 源代码
│   ├── core/           # 核心模块 (日志、通知)
│   ├── exchanges/      # 交易所接口
│   ├── strategies/     # 交易策略
│   ├── risk/           # 风险管理
│   └── utils/          # 工具函数
├── tests/              # 单元测试
├── examples/           # 示例代码
└── docs/               # 项目文档
```

## 📝 开发状态

- ✅ 日志系统 - 已完成
- ✅ Telegram 推送 - 已完成
- ✅ 交易所基类 - 已完成
- 🚧 策略框架 - 规划中
- 🚧 风险管理 - 规划中
- 🚧 回测系统 - 规划中

详见 [todos.md](todos.md)

 