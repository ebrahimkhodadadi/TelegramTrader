"""Price extraction utilities for trading signals"""

import re


class PriceExtractor:
    """Extracts various price levels from trading signal messages"""

    @staticmethod
    def extract_first_price(message):
        """Extract the primary entry price from message"""
        try:
            # Replace US30 with DJIUSD for consistency
            message = message.upper().replace("US30", "DJIUSD")

            # Try different patterns for first price
            patterns = [
                r'(\d+(?:\.\d+)?)',  # General number pattern
                r'(\d+\.\d+)',       # Decimal number
                r'@ (\d+\.\d+)',     # @ symbol followed by price
            ]

            for pattern in patterns:
                match = re.findall(pattern, message)
                if match:
                    return float(match[0])

            return None
        except Exception:
            return None

    @staticmethod
    def extract_second_price(message):
        """Extract the secondary entry price from message"""
        try:
            # Multiple patterns for second price detection
            patterns = [
                (r'\b\d+\.?\d*///(\d+\.?\d*)', 1),  # pattern///second_price
                (r'@\d+\.?\d*\s*-\s*(\d+\.?\d*)', 1),  # @price - second_price
                (r'2(?:nd)?\s+limit\s*@\s*(\d+\.?\d*)', 1),  # 2nd limit @ price
                (r'\b\d+\.?\d*__+(\d+\.?\d*)', 1),  # price__+second_price
                (r'@\s*\d+\.?\d*\s*-\s*(\d+\.?\d*)', 1),  # @ price - second
                (r'@\s*\d+\.?\d*\s*-\s*(\d+\.?\d*)|:\s*\d+\.?\d*\s*-\s*(\d+\.?\d*)', [1, 2]),  # Alternative
                (r'\b\d+\.?\d*\s*-\s*(\d+\.?\d*)', 1),  # price - second
                (r'\b\d+\b\s*و\s*(\d+)\s*فروش', 1),  # Persian: number and sell
                (r'\b\d+\b\s*و\s*(\d+)\s*خرید', 1),  # Persian: number and buy
                (r'\b\d+\.?\d*/(\d+\.?\d*)', 1),  # price/second
                (r'=\s*(\d+\.?\d*)', 1),  # = price
                (r'(?:\d+\.\d+)[^\d]+(\d+\.\d+)', 1),  # price followed by another price
            ]

            for pattern, group in patterns:
                match = re.search(pattern, message)
                if match:
                    if isinstance(group, list):
                        return float(match.group(group[0]) or match.group(group[1]))
                    else:
                        return float(match.group(group))

            return None
        except Exception:
            return None

    @staticmethod
    def extract_take_profits(message):
        """Extract take profit levels from message"""
        try:
            tp_numbers = []
            sentences = re.split(r'\n+', message)

            for sentence in sentences:
                # Multiple patterns for TP extraction
                tp_patterns = [
                    r'tp\s*\d*\s*[@:.\-]?\s*(\d+\.\d+|\d+)',
                    r'tp\s*(?:\d*\s*:\s*)?(\d+\.\d+)',
                    r'\btp\b\s*[:\-@.]?\s*(\d+(?:\.\d+)?)',
                    r'tp\s*:\s*(\d+\.?\d*)',
                    r'tp1\s*:\s*(\d+\.?\d*)',
                    r'tp1\s*\s*(\d+\.?\d*)',
                    r'tp\s*[-:]\s*(\d+\.\d+|\d+)',
                    r'tp\s*1\s*[-:]\s*(\d+\.\d+|\d+)',
                    r'checkpoint\s*1\s*:\s*(\d+\.?\d*|OPEN)',
                    r'takeprofit\s*1\s*=\s*(\d+\.\d+|\d+)',
                    r'take\s*profit\s*1\s*:\s*(\d+\.\d+|\d+)',
                    r'تی پی\s*(\d+)',  # Persian
                ]

                for pattern in tp_patterns:
                    matches = re.findall(pattern, sentence, re.IGNORECASE)
                    if matches:
                        tp_numbers.extend([float(tp) for tp in matches if tp != '0'])

                # Additional TP patterns
                tp_match_takeprofit = re.findall(
                    r'take\s*profit\s*\d+\s*[-:]\s*(\d+\.\d+|\d+)', sentence, re.IGNORECASE)
                if tp_match_takeprofit:
                    tp_numbers.extend([float(tp) for tp in tp_match_takeprofit])

                # TP2, TP3, TP4 patterns
                tp_match_2 = re.findall(
                    r'tp(\d+)\s*[:\-]?\s*(\d+\.\d+|\d+)', sentence, re.IGNORECASE)
                if tp_match_2:
                    for tp in tp_match_2:
                        tp_numbers.append(float(tp[1]))

                # Persian comma-separated TP values
                persian_tp_match = re.findall(r'تی پی\s*([\d\s,،]+)', sentence)
                if persian_tp_match:
                    persian_tp_numbers = []
                    for match in persian_tp_match:
                        numbers = [float(tp.strip()) for tp in re.split(r'[,\s،]+', match)
                                 if tp.strip().isdigit() and '/' not in tp]
                        persian_tp_numbers.extend(numbers)
                    return set(persian_tp_numbers)

            # Filter out invalid values
            if not tp_numbers or tp_numbers == [1.0]:
                return None

            # Remove duplicates and invalid values
            tp_numbers = set(tp_numbers)
            return {tp for tp in tp_numbers if tp != 1.0}

        except Exception:
            return None

    @staticmethod
    def extract_stop_loss(message):
        """Extract stop loss level from message"""
        try:
            message = message.lower()
            sl_numbers = []
            sentences = re.split(r'\n+', message)

            for sentence in sentences:
                # Multiple SL patterns
                sl_patterns = [
                    r'sl\s*:\s*(\d+\.\d+)',
                    r'sl\s*:\s*(\d+\.?\d*)',
                    r'(?i)stop\s*(\d+\.?\d*)',
                    r'حد\s*(\d+\.\d+|\d+)',  # Persian
                    r'STOP LOSS\s*:\s*(\d+\.?\d*)',
                    r'sl\s*[-:]\s*(\d+\.\d+|\d+)',
                    r'sl\s*[:\-]\s*(\d+\.?\d*)',
                    r'stop\s*loss\s*[:\-]\s*(\d+\.?\d*)',
                    r'sl\s*(\d+\.?\d*)',
                    r'stop\s*loss\s*[@:]\s*(\d+\.?\d*)',
                    r'Stoploss\s*=\s*(\d+\.\d+|\d+)',
                    r'SL\s*@\s*(\d+\.\d+|\d+)',
                    r'(?i)stop\s*loss\s*(\d+)',
                    r'استاپ\s*(\d+\.?\d*)',  # Persian
                    r'sl[\s.:]*([\d]+\.?\d*)',
                    r'stop\s*loss\s*(?:point)?\s*[:\-]?\s*(\d+\.\d+|\d+)',
                ]

                for pattern in sl_patterns:
                    match = re.search(pattern, sentence, re.IGNORECASE)
                    if match:
                        sl_numbers.append(float(match.group(1)))
                        break  # Found one, move to next sentence

                # Special case: number followed by 'sl'
                if not sl_numbers:
                    words = re.findall(r'\b\d+\b', sentence.lower())
                    if 'sl' in sentence.lower():
                        for word in words:
                            if sentence.lower().find(word) < sentence.lower().find('sl'):
                                try:
                                    sl_numbers.append(float(word))
                                    break
                                except ValueError:
                                    continue

            return sl_numbers[0] if sl_numbers else None

        except Exception:
            return None

    @staticmethod
    def extract_simple_price(message):
        """Extract a simple price with @ symbol"""
        match = re.search(r'@[\s]*([0-9]+(?:\.[0-9]+)?)', message)
        if match:
            return float(match.group(1))
        return None