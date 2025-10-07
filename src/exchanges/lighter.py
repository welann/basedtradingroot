"""
Lighter exchange client implementation
"""
import os
import asyncio
import time
import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .base import BaseExchangeClient
from .types import (
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
from ..core import get_logger

from lighter import SignerClient, ApiClient, Configuration
import lighter
import aiohttp


# Suppress Lighter SDK debug logs
logging.getLogger('lighter').setLevel(logging.WARNING)


class LighterClient(BaseExchangeClient):
    """Lighter exchange client implementation"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Lighter client

        Args:
            config: Configuration dictionary containing:
                - symbol: Trading pair (e.g. "ETH", "BTC", "SOL")
                - api_key_private_key: Private key for API authentication
                - account_index: Lighter account index (default: 0)
                - api_key_index: Lighter API key index (default: 0)
                - base_url: Lighter API base URL (default: mainnet)
        """
        # Initialize Lighter-specific attributes BEFORE calling super().__init__
        # because base class __init__ will call _validate_config()

        # Lighter credentials
        self.api_key_private_key = config.get(
            'api_key_private_key',
            os.getenv('API_KEY_PRIVATE_KEY')
        )
        self.account_index = config.get(
            'account_index',
            int(os.getenv('LIGHTER_ACCOUNT_INDEX', '0'))
        )
        self.api_key_index = config.get(
            'api_key_index',
            int(os.getenv('LIGHTER_API_KEY_INDEX', '0'))
        )
        self.base_url = config.get(
            'base_url',
            "https://mainnet.zklighter.elliot.ai"
        )

        # Get symbol from config
        self.symbol = config.get('symbol')

        # Initialize clients (will be set in connect)
        self.lighter_client: Optional[SignerClient] = None
        self.api_client: Optional[ApiClient] = None

        # Market configuration
        self.market_id: Optional[int] = None
        self.base_amount_multiplier: Optional[int] = None
        self.price_multiplier: Optional[int] = None
        self._symbol_info_cache: Optional[SymbolInfo] = None

        # Order tracking
        self.orders_cache: Dict[str, Dict[str, Any]] = {}
        self._order_update_handler = None

        # Now call base class __init__ which will call _validate_config()
        super().__init__(config)

        # Initialize logger after base init
        self.logger = get_logger("LighterClient", "Lighter", "trade")

    def _validate_config(self) -> None:
        """Validate Lighter configuration"""
        if not self.api_key_private_key:
            raise ValueError("api_key_private_key is required")
        if not self.symbol:
            raise ValueError("symbol is required")

    async def connect(self) -> None:
        """Connect to Lighter exchange"""
        try:
            self.logger.info(f"Connecting to Lighter ({self.base_url})...")

            # Initialize shared API client
            self.api_client = ApiClient(
                configuration=Configuration(host=self.base_url)
            )

            # Initialize Lighter signer client
            self.lighter_client = SignerClient(
                url=self.base_url,
                private_key=self.api_key_private_key,
                account_index=self.account_index,
                api_key_index=self.api_key_index,
            )

            # Check client
            err = self.lighter_client.check_client()
            if err is not None:
                raise Exception(f"Lighter client check failed: {err}")

            # Get market configuration
            await self._initialize_market_config()

            self.logger.success(
                f"Connected to Lighter - Market: {self.symbol} (ID: {self.market_id})"
            )

        except Exception as e:
            self.logger.error(f"Failed to connect to Lighter: {e}")
            raise

    async def _initialize_market_config(self) -> None:
        """Initialize market configuration for the trading symbol"""
        try:
            # Fetch order books data via HTTP
            url = f"{self.base_url}/api/v1/orderBooks"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}: {await response.text()}")

                    data = await response.json()

                    if data.get('code') != 200:
                        raise Exception(f"API error: {data}")

            # Find market by symbol
            market_info = None
            for market in data.get('order_books', []):
                if market['symbol'] == self.symbol:
                    market_info = market
                    break

            if not market_info:
                raise ValueError(f"Market {self.symbol} not found")

            # Store market configuration
            self.market_id = market_info['market_id']
            self.base_amount_multiplier = pow(10, market_info['supported_size_decimals'])
            self.price_multiplier = pow(10, market_info['supported_price_decimals'])

            # Parse base/quote currencies
            # Lighter uses simple symbols like "ETH", "BTC" for perpetual contracts
            # All contracts are settled in USDC
            base_currency = self.symbol
            quote_currency = "USDC"

            # Calculate tick size from price precision
            tick_size = Decimal("1") / (Decimal("10") ** market_info['supported_price_decimals'])

            # Create SymbolInfo with complete information from API
            self._symbol_info_cache = SymbolInfo(
                symbol=self.symbol,
                base_currency=base_currency,
                quote_currency=quote_currency,
                price_precision=market_info['supported_price_decimals'],
                quantity_precision=market_info['supported_size_decimals'],
                tick_size=tick_size,
                min_order_size=Decimal(str(market_info['min_base_amount'])),
                max_order_size=None,
                min_notional=Decimal(str(market_info['min_quote_amount'])),
                trading_enabled=(market_info['status'] == 'active'),
            )

            self.logger.debug(
                f"Market config: ID={self.market_id}, "
                f"Base multiplier={self.base_amount_multiplier}, "
                f"Price multiplier={self.price_multiplier}, "
                f"Tick size={tick_size}, "
                f"Min base: {market_info['min_base_amount']}, "
                f"Min quote: {market_info['min_quote_amount']}, "
                f"Status: {market_info['status']}"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize market config: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Lighter"""
        try:
            if self.api_client:
                await self.api_client.close()
                self.api_client = None

            self.lighter_client = None
            self.logger.info("Disconnected from Lighter")

        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        size: Decimal,
        price: Optional[Decimal] = None,
        **kwargs
    ) -> OrderResult:
        """
        Place an order on Lighter

        Args:
            symbol: Trading pair
            side: Order side (BUY/SELL)
            order_type: Order type (LIMIT/MARKET)
            size: Order size
            price: Order price (required for LIMIT orders)
            **kwargs: Additional parameters

        Returns:
            OrderResult
        """
        if not self.lighter_client:
            return OrderResult(
                success=False,
                error_message="Not connected to Lighter"
            )

        if symbol != self.symbol:
            return OrderResult(
                success=False,
                error_message=f"Invalid symbol {symbol}, expected {self.symbol}"
            )

        # Only support LIMIT orders for now
        if order_type != OrderType.LIMIT:
            return OrderResult(
                success=False,
                error_message=f"Order type {order_type.value} not supported"
            )

        if price is None:
            return OrderResult(
                success=False,
                error_message="Price is required for LIMIT orders"
            )

        try:
            # Validate order
            is_valid, error_msg = await self.validate_order(symbol, side, size, price)
            if not is_valid:
                return OrderResult(success=False, error_message=error_msg)

            # Round price and size
            price = self.round_to_tick(symbol, price)
            size = self.round_to_size(symbol, size)

            # Generate unique client order ID
            client_order_id = int(time.time() * 1000) % 1000000

            # Prepare order parameters
            order_params = {
                'market_index': self.market_id,
                'client_order_index': client_order_id,
                'base_amount': int(size * self.base_amount_multiplier),
                'price': int(price * self.price_multiplier),
                'is_ask': (side == OrderSide.SELL),
                'order_type': self.lighter_client.ORDER_TYPE_LIMIT,
                'time_in_force': self.lighter_client.ORDER_TIME_IN_FORCE_GOOD_TILL_TIME,
                'reduce_only': kwargs.get('reduce_only', False),
                'trigger_price': 0,
            }

            # Create order
            create_order, tx_hash, error = await self.lighter_client.create_order(
                **order_params
            )

            if error is not None:
                self.logger.error(f"Order creation failed: {error}")
                return OrderResult(
                    success=False,
                    order_id=str(client_order_id),
                    error_message=str(error)
                )

            self.logger.success(
                f"Order placed: {side.value} {size} {symbol} @ {price}"
            )

            return OrderResult(
                success=True,
                order_id=str(client_order_id),
                symbol=symbol,
                side=side,
                order_type=order_type,
                size=size,
                price=price,
                status=OrderStatus.OPEN,
                timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return OrderResult(
                success=False,
                error_message=str(e)
            )

    async def cancel_order(
        self,
        order_id: str,
        symbol: Optional[str] = None
    ) -> OrderResult:
        """Cancel an order"""
        if not self.lighter_client:
            return OrderResult(
                success=False,
                error_message="Not connected to Lighter"
            )

        try:
            # Cancel order
            cancel_order, tx_hash, error = await self.lighter_client.cancel_order(
                market_index=self.market_id,
                order_index=int(order_id)
            )

            if error is not None:
                self.logger.error(f"Cancel order failed: {error}")
                return OrderResult(
                    success=False,
                    error_message=str(error)
                )

            if tx_hash:
                self.logger.info(f"Order {order_id} cancelled")
                return OrderResult(success=True, order_id=order_id)
            else:
                return OrderResult(
                    success=False,
                    error_message="Failed to send cancellation transaction"
                )

        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return OrderResult(
                success=False,
                error_message=str(e)
            )

    async def get_order_info(
        self,
        order_id: str,
        symbol: Optional[str] = None
    ) -> Optional[OrderInfo]:
        """Get order information"""
        # Lighter doesn't have a direct API for single order query
        # We need to get all orders and filter
        active_orders = await self.get_active_orders(symbol)

        for order in active_orders:
            if order.order_id == order_id:
                return order

        return None

    async def get_active_orders(
        self,
        symbol: Optional[str] = None
    ) -> List[OrderInfo]:
        """Get active orders"""
        if not self.lighter_client or not self.api_client:
            return []

        try:
            # Generate auth token
            auth_token, error = self.lighter_client.create_auth_token_with_expiry()
            if error is not None:
                self.logger.error(f"Failed to create auth token: {error}")
                return []

            # Get active orders
            order_api = lighter.OrderApi(self.api_client)
            orders_response = await order_api.account_active_orders(
                account_index=self.account_index,
                market_id=self.market_id,
                auth=auth_token
            )

            if not orders_response or not orders_response.orders:
                return []

            # Convert to OrderInfo
            order_list = []
            for order in orders_response.orders:
                side = OrderSide.SELL if order.is_ask else OrderSide.BUY

                order_info = OrderInfo(
                    order_id=str(order.order_index),
                    symbol=self.symbol,
                    side=side,
                    order_type=OrderType.LIMIT,
                    size=Decimal(str(order.initial_base_amount)),
                    price=Decimal(str(order.price)),
                    status=OrderStatus(order.status.upper()),
                    filled_size=Decimal(str(order.filled_base_amount)),
                    remaining_size=Decimal(str(order.remaining_base_amount)),
                )

                # Only include orders with remaining size
                if order_info.remaining_size > 0:
                    order_list.append(order_info)

            return order_list

        except Exception as e:
            self.logger.error(f"Error getting active orders: {e}")
            return []

    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a symbol"""
        positions = await self.get_all_positions()

        for position in positions:
            if position.symbol == symbol:
                return position

        return None

    async def get_all_positions(self) -> List[Position]:
        """Get all positions"""
        if not self.api_client:
            return []

        try:
            account_api = lighter.AccountApi(self.api_client)
            account_data = await account_api.account(
                by="index",
                value=str(self.account_index)
            )

            if not account_data or not account_data.accounts:
                return []

            positions = []
            for pos in account_data.accounts[0].positions:
                # Skip zero positions
                position_amt = abs(float(pos.position))
                if position_amt < 0.0001:
                    continue

                position = Position(
                    symbol=pos.symbol,
                    side=PositionSide.LONG if float(pos.position) > 0 else PositionSide.SHORT,
                    size=Decimal(str(position_amt)),
                    entry_price=Decimal(str(pos.avg_price)),
                    unrealized_pnl=Decimal(str(pos.unrealized_pnl)) if hasattr(pos, 'unrealized_pnl') else None,
                )

                positions.append(position)

            return positions

        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []

    async def get_ticker(self, symbol: str) -> Ticker:
        """Get ticker information"""
        if symbol != self.symbol:
            raise ValueError(f"Invalid symbol {symbol}")

        if not self.api_client:
            raise ConnectionError("Not connected to Lighter")

        try:
            order_api = lighter.OrderApi(self.api_client)
            market_summary = await order_api.order_book_details(
                market_id=self.market_id
            )

            details = market_summary.order_book_details[0]

            return Ticker(
                symbol=symbol,
                last_price=Decimal(str(details.last_price)) if hasattr(details, 'last_price') else Decimal("0"),
                bid_price=Decimal(str(details.best_bid)) if hasattr(details, 'best_bid') else None,
                ask_price=Decimal(str(details.best_ask)) if hasattr(details, 'best_ask') else None,
                timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error getting ticker: {e}")
            raise

    async def get_symbols(self) -> List[str]:
        """Get all available trading pairs"""
        if not self.api_client:
            return []

        try:
            order_api = lighter.OrderApi(self.api_client)
            order_books = await order_api.order_books()

            return [market.symbol for market in order_books.order_books]

        except Exception as e:
            self.logger.error(f"Error getting symbols: {e}")
            return []

    async def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Get symbol information"""
        if symbol != self.symbol:
            raise ValueError(f"Invalid symbol {symbol}")

        if self._symbol_info_cache:
            return self._symbol_info_cache

        # Re-initialize if not cached
        await self._initialize_market_config()
        return self._symbol_info_cache

    def get_exchange_name(self) -> str:
        """Get exchange name"""
        return "Lighter"

    def round_to_tick(self, symbol: str, price: Decimal) -> Decimal:
        """
        Round price to tick size

        Args:
            symbol: Trading pair
            price: Price to round

        Returns:
            Rounded price
        """
        if symbol != self.symbol:
            raise ValueError(f"Invalid symbol {symbol}, expected {self.symbol}")

        if not isinstance(price, Decimal):
            price = Decimal(str(price))

        if self._symbol_info_cache:
            return self._symbol_info_cache.round_price(price)

        # Fallback to default tick size
        tick_size = Decimal("0.01")
        from decimal import ROUND_HALF_UP
        return (price / tick_size).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * tick_size

    def round_to_size(self, symbol: str, size: Decimal) -> Decimal:
        """
        Round size to quantity precision

        Args:
            symbol: Trading pair
            size: Size to round

        Returns:
            Rounded size
        """
        if symbol != self.symbol:
            raise ValueError(f"Invalid symbol {symbol}, expected {self.symbol}")

        if not isinstance(size, Decimal):
            size = Decimal(str(size))

        if self._symbol_info_cache:
            return self._symbol_info_cache.round_quantity(size)

        # Fallback to default precision
        precision = 4
        return size.quantize(Decimal(f"1e-{precision}"), rounding=ROUND_HALF_UP)
