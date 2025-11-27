"""Symbol detection and mapping utilities for trading signals"""

import json
import os
from loguru import logger
import Configure


class SymbolDetector:
    """Handles symbol detection and mapping for trading instruments"""

    @staticmethod
    def read_symbol_list():
        """Read available symbols from JSON file"""
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        json_file_path = os.path.join(root_dir, "data", "Symbols.json")

        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)
                return data.get('SymbolList', [])
        except Exception as e:
            logger.exception("Error reading symbol list JSON file")
            return []

    @staticmethod
    def find_similar_word(word, symbol_list):
        """Find similar symbols in the available list"""
        if not word or not symbol_list:
            return None

        word_upper = word.upper()
        matches = [symbol for symbol in symbol_list if word_upper in symbol]

        if not matches:
            return None

        # Check for custom mappings first
        from Configure.settings.Settings import Settings
        mappings = Settings.mt_symbol_mappings()

        if word_upper in mappings:
            exact = mappings[word_upper]
            if exact in symbol_list:
                return exact

        # Prefer symbols without ! or # suffixes
        no_suffix = [s for s in matches if '!' not in s and '#' not in s]
        if no_suffix:
            return no_suffix[0]

        # Return first match as fallback
        return matches[0]

    @staticmethod
    def detect_symbol(sentence):
        """Detect trading symbol from sentence"""
        if not sentence:
            return None

        # Get available symbols
        symbol_list = SymbolDetector._get_symbols()
        if not symbol_list:
            return None

        words = sentence.split()

        # First pass: Direct symbol matches
        for word in words:
            word = word.replace("/", "").replace("-", "")
            if word.upper() in symbol_list:
                return SymbolDetector.find_similar_word(word, symbol_list)

        # Second pass: Special symbol mappings
        for word in words:
            word_normalized = word.replace("/", "").replace("-", "").upper()

            # Gold detection
            if any(keyword in word_normalized for keyword in [
                'طلا', 'GOLD', 'GLD', '#XAUUSD', 'انس', 'گلد', '𝐗𝐀𝐔𝐔𝐒𝐃', 'XAUUSD', 'اونس'
            ]):
                return SymbolDetector.find_similar_word('XAUUSD', symbol_list)

            # Dow Jones/US30 detection
            if any(keyword in word_normalized for keyword in ['US30', 'داوجونز']):
                return SymbolDetector.find_similar_word('DJIUSD', symbol_list)

            # EURUSD detection
            if any(keyword in word_normalized for keyword in ['یورو', 'EURUSD']):
                return SymbolDetector.find_similar_word('EURUSD', symbol_list)

            # NASDAQ detection
            if 'NASDAQ' in word_normalized:
                return SymbolDetector.find_similar_word('NDAQ', symbol_list)

            # Oil detection
            if 'OIL' in word_normalized:
                return SymbolDetector.find_similar_word('OIL', symbol_list)

        # Default fallback
        return SymbolDetector.find_similar_word('XAUUSD', symbol_list)

    @staticmethod
    def _get_symbols():
        """Get symbols from MetaTrader or cache"""
        try:
            from MetaTrader import MetaTrader
            return MetaTrader.GetSymbols()
        except Exception:
            # Fallback to JSON file
            return SymbolDetector.read_symbol_list()