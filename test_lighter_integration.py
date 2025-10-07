"""
Integration test for Lighter client with HTTP market config
"""
import asyncio
import sys
from pathlib import Path
from decimal import Decimal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.exchanges import LighterClient, OrderSide, OrderType


async def test_market_config():
    """Test HTTP-based market configuration"""
    print("\n" + "=" * 60)
    print("Test 1: Market Configuration (HTTP)")
    print("=" * 60)

    config = {
        'symbol': 'ETH',
        'api_key_private_key': 'dummy_key',
    }

    client = LighterClient(config)
    await client._initialize_market_config()

    assert client.market_id is not None, "Market ID should be set"
    assert client.base_amount_multiplier is not None, "Base multiplier should be set"
    assert client.price_multiplier is not None, "Price multiplier should be set"
    assert client._symbol_info_cache is not None, "Symbol info should be cached"

    info = client._symbol_info_cache
    assert info.symbol == 'ETH', "Symbol should be ETH"
    assert info.base_currency == 'ETH', "Base currency should be ETH"
    assert info.quote_currency == 'USDC', "Quote currency should be USDC"
    assert info.min_order_size > 0, "Min order size should be positive"
    assert info.min_notional > 0, "Min notional should be positive"
    assert info.trading_enabled is True, "Trading should be enabled"

    print(f"✅ Market ID: {client.market_id}")
    print(f"✅ Multipliers: base={client.base_amount_multiplier}, price={client.price_multiplier}")
    print(f"✅ Symbol Info: {info.symbol} ({info.base_currency}/{info.quote_currency})")
    print(f"✅ Min order size: {info.min_order_size}")
    print(f"✅ Min notional: {info.min_notional}")


async def test_symbol_parsing():
    """Test symbol parsing for different formats"""
    print("\n" + "=" * 60)
    print("Test 2: Symbol Parsing")
    print("=" * 60)

    test_symbols = ['ETH', 'BTC', 'SOL']

    for symbol in test_symbols:
        config = {
            'symbol': symbol,
            'api_key_private_key': 'dummy_key',
        }
        client = LighterClient(config)
        await client._initialize_market_config()

        info = client._symbol_info_cache
        print(f"✅ {symbol}: ID={client.market_id}, "
              f"base={info.base_currency}, quote={info.quote_currency}")


async def test_precision_helpers():
    """Test precision rounding helpers"""
    print("\n" + "=" * 60)
    print("Test 3: Precision Helpers")
    print("=" * 60)

    config = {
        'symbol': 'ETH',
        'api_key_private_key': 'dummy_key',
    }

    client = LighterClient(config)
    await client._initialize_market_config()

    # Test price rounding
    price = Decimal("2345.6789")
    rounded_price = client.round_to_tick('ETH', price)
    print(f"✅ Price rounding: {price} -> {rounded_price}")

    # Test size rounding
    size = Decimal("0.12345")
    rounded_size = client.round_to_size('ETH', size)
    print(f"✅ Size rounding: {size} -> {rounded_size}")

    # Test validation
    is_valid, msg = await client.validate_order(
        'ETH',
        OrderSide.BUY,
        Decimal("0.01"),
        Decimal("2000.00")
    )
    print(f"✅ Validation: valid={is_valid}, msg='{msg}'")


async def main():
    print("\n" + "=" * 70)
    print(" Lighter Client Integration Tests (HTTP Market Config)")
    print("=" * 70)

    try:
        await test_market_config()
        await test_symbol_parsing()
        await test_precision_helpers()

        print("\n" + "=" * 70)
        print("✅ All tests passed!")
        print("=" * 70)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
