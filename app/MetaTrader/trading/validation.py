import math
import MetaTrader5 as mt5
from loguru import logger


class PriceValidator:
    """Handles price validation and adjustments for different symbols"""

    def __init__(self, connection_manager):
        self.connection = connection_manager

    def validate(self, action, price, symbol, currentPrice=None, isSl=False, isSecondPrice=False):
        """Validate and adjust price for broker requirements"""
        # bug: need to fix because current price returns wrong rounded number
        if symbol != self.connection.validate_symbol('XAUUSD') and symbol != self.connection.validate_symbol('DJIUSD'):
            return float(price)

        if currentPrice is None:
            currentPrice = self.get_current_price(symbol, action)

        priceStr = str(int(price))
        currentPrice = int(currentPrice)  # تبدیل قیمت به عدد صحیح
        if len(priceStr) < len(str(currentPrice)):
            fractional_part, price = math.modf(price)  # splite int and decimal

            # قسمت ابتدایی قیمت فعلی
            base = int(str(currentPrice)[:-len(priceStr)])
            newPrice = float(f"{base}{price}")

            if isSl:
                if action == mt5.ORDER_TYPE_BUY:
                    while newPrice >= currentPrice:  # کاهش برای BUY
                        base -= 1
                        newPrice = float(f"{base}{price}")
                elif action == mt5.ORDER_TYPE_SELL:
                    while newPrice <= currentPrice:  # افزایش برای SELL
                        base += 1
                        newPrice = float(f"{base}{price}")

            if isSecondPrice:
                if action == mt5.ORDER_TYPE_BUY:
                    while newPrice >= currentPrice:  # اطمینان از کمتر بودن secondPrice در خرید
                        base -= 1
                        newPrice = float(f"{base}{price}")
                elif action == mt5.ORDER_TYPE_SELL:
                    while newPrice <= currentPrice:  # اطمینان از بیشتر بودن secondPrice در فروش
                        base += 1
                        newPrice = float(f"{base}{price}")

            return newPrice + fractional_part

        return float(price)  # اگر TP از ابتدا معتبر بود، همان را برگردان

    def validate_tp_list(self, action, tp_list, symbol, firstPrice, secondPrice=None, closerPrice=None):
        """Validate take profit levels"""
        if symbol != self.connection.validate_symbol('XAUUSD'):
            return tp_list

        validated_tp_levels = []

        if firstPrice is None:
            firstPrice = self.get_current_price(symbol, action)

        last_price = None  # ذخیره آخرین مقدار TP معتبر برای استفاده در مقدار جدید

        for price in tp_list:
            if len(str(int(price))) == len(str(int(firstPrice))):
                validated_tp_levels.append(price)
                continue

            firstPrice = int(firstPrice)  # تبدیل قیمت به عدد صحیح
            price = int(price)  # تبدیل مقدار ورودی به عدد صحیح
            priceStr = str(price)

            # استفاده از مقدار قبلی در صورتی که price کوتاه‌تر باشد
            if last_price is not None and len(priceStr) < len(str(last_price)):
                # گرفتن بخش ابتدایی از مقدار قبلی
                base = int(str(last_price)[:-len(priceStr)])
            else:
                # گرفتن بخش ابتدایی از قیمت فعلی
                base = int(str(firstPrice)[:-len(priceStr)])

            newPrice = float(f"{base}{price}")

            # تنظیم TP بر اساس نوع سفارش
            if action == mt5.ORDER_TYPE_BUY:
                while newPrice <= firstPrice or newPrice <= secondPrice:  # افزایش برای BUY
                    base += 1
                    newPrice = float(f"{base}{price}")
            elif action == mt5.ORDER_TYPE_SELL:
                while newPrice >= firstPrice or newPrice >= secondPrice:  # کاهش برای SELL
                    base -= 1
                    newPrice = float(f"{base}{price}")

            if newPrice is not None and newPrice != 0:
            #     newPrice = self.convert_closer_price(
            #         symbol, action, newPrice, closerPrice, isTp=True)
                validated_tp_levels.append(newPrice)
                last_price = int(newPrice)  # ذخیره آخرین مقدار معتبر

        return validated_tp_levels

    def calculate_lot_size_with_prices(self, symbol, risk_percentage, open_price, stop_loss_price, account_size):
        """
        Calculate the lot size per account size, risk percentage, open position price, and stop loss price.

        Parameters:
        account_size (float): The total capital in the trading account.
        risk_percentage (float): The percentage of the account size to risk on a single trade.
        open_price (float): The open position price.
        stop_loss_price (float): The stop loss price.

        Returns:
        float: The calculated lot size rounded to two decimal places.
        """
        if '%' not in risk_percentage:
            return float(risk_percentage)

        risk_percentage = float(risk_percentage.replace("%", ""))

        if account_size is None or account_size == 0:
            account_size = mt5.account_info().balance
        tick_value = mt5.symbol_info(symbol).trade_tick_value
        tick_size = mt5.symbol_info(symbol).trade_tick_size

        # Calculate the number of ticks between the open price and stop loss price
        risk_ticks = abs(open_price - stop_loss_price) / tick_size

        # Calculate the monetary risk
        risk_amount = account_size * (risk_percentage / 100)

        # Calculate initial lot size
        lot_size = risk_amount / (risk_ticks * tick_value)
        lot_size = round(lot_size, 2)

        # Calculate the actual risk amount with the initial lot size
        actual_risk_amount = lot_size * risk_ticks * tick_value

        # If actual risk amount is higher than the desired risk amount, reduce the lot size
        while actual_risk_amount > risk_amount and lot_size > 0.01:
            lot_size -= 0.01
            lot_size = round(lot_size, 2)
            actual_risk_amount = lot_size * risk_ticks * tick_value

        # Ensure the lot size does not drop below 0.01
        if lot_size < 0.01:
            # lot_size = 0.01
            logger.warning(f"Risk amount of {risk_amount} exceeds {
                            risk_percentage}%. The lot size cannot be lower than 0.01, this is at your own risk.")

        return lot_size

    def convert_closer_price(self, symbol, actionType, price, closerPrice, isCurrentPrice=None, isTp=None):
        """Convert price with closer adjustment"""
        if closerPrice is None or closerPrice == 0:
            return float(price)
        if self.connection.validate_symbol('XAUUSD') != symbol:
            return float(price)

        if isTp:
            if actionType in [mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_BUY_STOP, mt5.ORDER_TYPE_BUY_LIMIT]:
                return float(price - closerPrice)
            elif actionType in [mt5.ORDER_TYPE_SELL, mt5.ORDER_TYPE_SELL_LIMIT, mt5.ORDER_TYPE_SELL_STOP]:
                return float(price + closerPrice)
        if isCurrentPrice:
            if actionType == mt5.ORDER_TYPE_BUY_LIMIT or actionType == mt5.ORDER_TYPE_SELL_STOP:
                return float(price + closerPrice)
            elif actionType == mt5.ORDER_TYPE_BUY_STOP or actionType == mt5.ORDER_TYPE_SELL_LIMIT:
                return float(price - closerPrice)

        return float(price)

    def calculate_new_price(self, symbol, price, num_points, tp, actionType):
        """
        Calculate a new price by adding/subtracting a number of points to/from the given price.

        Args:
        symbol (str): The financial instrument symbol (e.g., 'EURUSD').
        price (float): The current price of the symbol.
        num_points (int): The number of points (ticks) to add/subtract.
        actionType (buy or sell): Meta trader type

        Returns:
        float: The new calculated price.
        """
        # validate
        if num_points is None or num_points == 0:
            return float(tp)
        # Get symbol information
        symbol_info = mt5.symbol_info(symbol)
        # Get the tick size
        tick_size = symbol_info.point
        # Calculate the new price
        if actionType == mt5.ORDER_TYPE_BUY or actionType == mt5.ORDER_TYPE_BUY_STOP or actionType == mt5.ORDER_TYPE_BUY_LIMIT:
            return price + ((num_points * 10) * tick_size)
        elif actionType == mt5.ORDER_TYPE_SELL or actionType == mt5.ORDER_TYPE_SELL_LIMIT or actionType == mt5.ORDER_TYPE_SELL_STOP:
            return price - ((num_points * 10) * tick_size)

        return float(price)

    def get_current_price(self, symbol, action=None):
        """Get current price for validation"""
        tick = mt5.symbol_info_tick(symbol)
        if action == mt5.ORDER_TYPE_BUY:
            return tick.ask if tick else None
        elif action == mt5.ORDER_TYPE_SELL:
            return tick.bid if tick else None
        return tick.bid if tick else None