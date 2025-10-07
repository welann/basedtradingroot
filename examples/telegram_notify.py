"""
Telegram 推送示例
"""
import sys
import asyncio
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import get_config
from src.core import get_logger_manager, get_logger


async def main():
    """主函数"""
    # 1. 加载配置
    print("加载配置文件...")
    try:
        config = get_config()
        config_dict = config.config
    except FileNotFoundError:
        print("❌ 配置文件不存在")
        print("请复制 config/config.example.yaml 为 config/config.yaml")
        print("并填入您的 Telegram Bot Token 和 Chat ID")
        return

    # 2. 初始化日志管理器
    logger_manager = get_logger_manager(config_dict)
    logger = get_logger("TelegramTest", "N/A", "system")

    # 3. 检查 Telegram 是否启用
    if not config_dict.get('telegram', {}).get('enabled'):
        print("❌ Telegram 推送未启用")
        print("请在 config/config.yaml 中设置 telegram.enabled = true")
        return

    print("Telegram 推送已启用\n")

    # 4. 测试连接
    print("=== 测试 Telegram 连接 ===")
    if logger_manager.telegram_notifier:
        is_connected = await logger_manager.telegram_notifier.test_connection()
        if is_connected:
            print("✅ Telegram Bot 连接成功\n")
        else:
            print("❌ Telegram Bot 连接失败\n")
            return
    else:
        print("❌ Telegram 推送器未初始化\n")
        return

    # 5. 发送测试消息
    print("=== 发送测试消息 ===")
    test_message = """🎉 **Telegram 推送测试**

这是一条测试消息！

功能正常 ✅"""

    success = await logger_manager.send_telegram(test_message, level="INFO")
    if success:
        print("✅ 测试消息发送成功\n")
    else:
        print("❌ 测试消息发送失败\n")

    # 6. 发送交易通知
    print("=== 发送交易通知 ===")
    trade_msg = logger_manager.format_trade_message(
        exchange="Binance",
        symbol="BTC/USDT",
        side="BUY",
        size=0.1,
        price=42000.0,
        total=4200.0,
        fee=4.2,
        order_id="TEST_12345"
    )

    success = await logger_manager.send_telegram(trade_msg, level="INFO")
    if success:
        print("✅ 交易通知发送成功\n")
    else:
        print("❌ 交易通知发送失败\n")

    # 7. 发送告警消息
    print("=== 发送告警消息 ===")
    alert_msg = logger_manager.format_alert_message(
        level="WARNING",
        module="Exchange",
        exchange="Test Exchange",
        message="这是一条测试告警消息"
    )

    success = await logger_manager.send_telegram(alert_msg, level="WARNING")
    if success:
        print("✅ 告警消息发送成功\n")
    else:
        print("❌ 告警消息发送失败\n")

    # 8. 测试自定义消息
    print("=== 发送自定义消息 ===")
    custom_msg = """💡 **自定义消息示例**

您可以自由定义消息格式：

📊 数据统计
- 今日交易: 15 笔
- 总盈亏: +$1,250 (📈 +5.2%)

🎯 策略信号
- 交易对: BTC/USDT
- 信号: 买入
- 理由: MA 交叉 + RSI 超卖

⚡ 快速提醒
任意自定义内容都可以！"""

    success = await logger_manager.send_telegram(custom_msg, level="INFO")
    if success:
        print("✅ 自定义消息发送成功\n")
    else:
        print("❌ 自定义消息发送失败\n")

    print("✅ 所有测试完成！请检查您的 Telegram")


if __name__ == "__main__":
    asyncio.run(main())
