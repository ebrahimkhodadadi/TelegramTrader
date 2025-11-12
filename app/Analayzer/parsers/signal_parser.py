"""Main signal parsing orchestration"""

from loguru import logger
from .text_processor import TextProcessor
from .action_detector import ActionDetector
from .price_extractor import PriceExtractor
from .symbol_detector import SymbolDetector


class SignalParser:
    """Main orchestrator for parsing trading signals from messages"""

    @staticmethod
    def parse_message(message):
        """Parse a complete trading signal message

        Returns:
            tuple: (action_type, symbol, first_price, second_price, take_profits, stop_loss)
        """
        try:
            if message is None or len(message) < 1:
                return None, None, None, None, None, None

            # Clean and normalize the message
            message = TextProcessor.normalize_for_parsing(message)

            # Extract components
            action_type = ActionDetector.detect_action_type(message)
            if action_type is None:
                return None, None, None, None, None, None

            first_price = PriceExtractor.extract_first_price(message)
            second_price = PriceExtractor.extract_second_price(message)
            take_profits = PriceExtractor.extract_take_profits(message)
            stop_loss = PriceExtractor.extract_stop_loss(message)
            symbol = SymbolDetector.detect_symbol(message)

            # Validate that we don't have duplicate prices
            if first_price == second_price or second_price in take_profits or second_price == stop_loss:
                second_price = None

            return action_type, symbol, first_price, second_price, take_profits, stop_loss

        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None, None, None, None, None, None

    @staticmethod
    def extract_price(message):
        """Extract a simple price with @ symbol (utility function)"""
        return PriceExtractor.extract_simple_price(message)