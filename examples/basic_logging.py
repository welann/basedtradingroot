"""
基础日志使用示例
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import get_config
from src.core import get_logger_manager, get_logger


def main():
    """主函数"""
    # 1. 加载配置
    print("加载配置文件...")
    try:
        config = get_config()
    except FileNotFoundError:
        print("配置文件不存在，使用默认配置")
        config_dict = {
            'logging': {
                'log_dir': 'logs',
                'console_level': 'INFO',
                'file_level': 'DEBUG',
            }
        }
        from src.core import LoggerManager
        logger_manager = LoggerManager(config_dict)
    else:
        # 2. 初始化日志管理器
        logger_manager = get_logger_manager(config.config)

    print("日志管理器初始化完成\n")

    # 3. 获取不同类型的 logger
    system_logger = get_logger("System", "N/A", "system")
    trade_logger = get_logger("Trade", "Binance", "trade")
    strategy_logger = get_logger("Strategy", "N/A", "strategy")

    # 4. 测试不同级别的日志
    print("=== 测试系统日志 ===")
    system_logger.debug("这是一条 DEBUG 日志")
    system_logger.info("系统启动成功")
    system_logger.success("连接交易所成功")
    system_logger.warning("网络延迟较高")
    system_logger.error("连接失败，正在重试")

    print("\n=== 测试交易日志 ===")
    trade_logger.info("提交买入订单 BTC/USDT 0.1 @ 42000")
    trade_logger.success("订单完全成交 #12345 BTC/USDT 0.1 @ 42000")

    print("\n=== 测试策略日志 ===")
    strategy_logger.info("MA 交叉信号触发")
    strategy_logger.debug("计算 RSI 指标: 35.2")

    print("\n=== 测试格式化消息 ===")
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
    print("交易消息格式:")
    print(trade_msg)

    print("\n=== 测试告警消息 ===")
    alert_msg = logger_manager.format_alert_message(
        level="WARNING",
        module="Exchange",
        exchange="OKX",
        message="WebSocket 连接断开，正在重连..."
    )
    print("告警消息格式:")
    print(alert_msg)

    print("\n✅ 日志测试完成！")
    print(f"日志文件保存在: {logger_manager.log_dir}")


if __name__ == "__main__":
    main()
