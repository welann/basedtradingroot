"""
Exchanges module
"""
from .base import BaseExchangeClient
from .types import (
    # Enums
    OrderType,
    OrderSide,
    OrderStatus,
    PositionSide,
    # Data classes
    OrderResult,
    OrderInfo,
    Position,
    Ticker,
    SymbolInfo,
    Trade,
)

# Import specific exchange implementations
try:
    from .lighter import LighterClient
    _LIGHTER_AVAILABLE = True
except ImportError:
    _LIGHTER_AVAILABLE = False
    LighterClient = None

__all__ = [
    # Base class
    'BaseExchangeClient',
    # Enums
    'OrderType',
    'OrderSide',
    'OrderStatus',
    'PositionSide',
    # Data classes
    'OrderResult',
    'OrderInfo',
    'Position',
    'Ticker',
    'SymbolInfo',
    'Trade',
]

# Add exchange implementations if available
if _LIGHTER_AVAILABLE:
    __all__.append('LighterClient')
