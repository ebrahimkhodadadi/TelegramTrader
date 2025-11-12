"""
Signal Analyzer - Main interface for parsing trading signals

This module provides the main interface for parsing trading signals from messages.
It uses modular components for text processing, action detection, price extraction, and symbol detection.
"""

from .signal_parser import SignalParser
from .action_detector import TradeType


def extract_price(message):
    """Extract a simple price with @ symbol (backward compatibility)"""
    return SignalParser.extract_price(message)


def parse_message(message):
    """Parse a trading signal message (backward compatibility)"""
    return SignalParser.parse_message(message)


# Re-export for backward compatibility
def clean_text(text):
    """Clean and normalize text (deprecated - use TextProcessor directly)"""
    from .text_processor import TextProcessor
    return TextProcessor.clean_text(text)


def get_main_word_actiontype(sentence):
    """Detect action type from sentence (deprecated - use ActionDetector directly)"""
    from .action_detector import ActionDetector
    return ActionDetector.detect_action_type(sentence)


def GetFirstPrice(message):
    """Extract first price (deprecated - use PriceExtractor directly)"""
    from .price_extractor import PriceExtractor
    return PriceExtractor.extract_first_price(message)


def GetSecondPrice(message):
    """Extract second price (deprecated - use PriceExtractor directly)"""
    from .price_extractor import PriceExtractor
    return PriceExtractor.extract_second_price(message)


def GetTakeProfits(message):
    """Extract take profits (deprecated - use PriceExtractor directly)"""
    from .price_extractor import PriceExtractor
    return PriceExtractor.extract_take_profits(message)


def GetStopLoss(message):
    """Extract stop loss (deprecated - use PriceExtractor directly)"""
    from .price_extractor import PriceExtractor
    return PriceExtractor.extract_stop_loss(message)


def GetSymbol(sentence):
    """Detect symbol (deprecated - use SymbolDetector directly)"""
    from .symbol_detector import SymbolDetector
    return SymbolDetector.detect_symbol(sentence)


# Re-export classes for backward compatibility
__all__ = [
    'parse_message',
    'extract_price',
    'TradeType',
    # Deprecated functions (kept for compatibility)
    'clean_text',
    'get_main_word_actiontype',
    'GetFirstPrice',
    'GetSecondPrice',
    'GetTakeProfits',
    'GetStopLoss',
    'GetSymbol'
]
