import math
import os
import Configure
import Database
from Database import Migrations
from loguru import logger
import MetaTrader5 as mt5
import time
import asyncio
from datetime import datetime, timedelta

# https://www.mql5.com/en/docs/constants/errorswarnings/enum_trade_return_codes


class MetaTrader:
    def __init__(self, path, server, user, password):
        self.path = path
        self.server = server
        self.user = user
        self.password = password
        self.magic = 2025
        self.connected = False

    def Login(self) -> bool:
        try:
            logger.info(f"try to login to {self.server} with {self.user}")
            # establish connection to the MetaTrader 5 terminal
            if not mt5.initialize(path=self.path, login=self.user, server=self.server, password=self.password):
                logger.error("MetaTrader Login failed, error code =",
                             mt5.last_error())
                self.connected = False
                return self.connected
            logger.success(f"login was successful for {self.user}")
            self.connected = True
            return self.connected
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.connected = False
            return self.connected

    def CheckSymbol(self, symbol):
        logger.info("Check symbol " + symbol)
        symbol_info = mt5.symbol_info(symbol.upper())
        if symbol_info is None:
            logger.critical(f"not found {symbol}, can not call order_check()")
            mt5.shutdown()
            return False
        # if the symbol is unavailable in MarketWatch, add it
        if not symbol_info.visible:
            logger.debug(symbol, "is not visible, trying to switch on")
            if not mt5.symbol_select(symbol, True):
                logger.critical("symbol_select({}}) failed, exit", symbol)
                mt5.shutdown()
                return False
        return True

    def get_current_price(self, symbol: str):
        """Get the current price of the symbol"""
        tick = mt5.symbol_info_tick(symbol)
        # logger.info(f"{symbol} current price is: {tick.bid}")
        return tick.bid if tick else None

    def get_open_positions(self, ticket_id=None):
        """Get open positions from MetaTrader"""
        if ticket_id != None:
            positions = mt5.positions_get(ticket=ticket_id)
            if (len(positions) == 0):
                # logger.error(f"Can't find position {ticket_id}")
                return None
            return positions[0]
        else:
            positions = mt5.positions_get()

        return list(positions) if positions else []

    def get_pending_orders(self, ticket_id=None):
        """Get pending orders from MetaTrader"""
        if ticket_id != None:
            orders = mt5.orders_get(ticket=ticket_id)
            if (len(orders) == 0):
                logger.error(f"Can't find order {ticket_id}")
                return None
            return orders[0]
        else:
            orders = mt5.orders_get()

        return list(orders) if orders else []

    def close_half_position(self, ticket):
        """Close half of the position volume"""
        position = self.get_open_positions(ticket)
        if (position is None):
            return

        new_lot_size = math.floor((position.volume / 2) * 100) / 100
        logger.warning(f"new lot size to close half of {
                       ticket} is {new_lot_size}")

        if new_lot_size >= 0.01:
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": float(new_lot_size),
                "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "position": position.ticket,
                "price": mt5.symbol_info_tick(position.symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(position.symbol).ask,
                "deviation": 10,
                "magic": self.magic,
                "comment": "Closing half position",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(request)
            logger.info(f"{result}")
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Failed to close half position for {
                             position.symbol}: {result.comment}")
                return False
            else:
                logger.success(f"Successfully closed half position for {
                               position.symbol}, ticket {ticket}")
        else:
            self.close_position(ticket)

    def update_stop_loss(self, ticket, new_stop_loss):
        """Updating stop loss"""
        position = self.get_open_positions(ticket)
        if (position.sl == new_stop_loss):
            return False

        symbol_info = mt5.symbol_info(position.symbol)
        if symbol_info:
            digits = symbol_info.digits
            new_stop_loss = round(new_stop_loss, digits)
            logger.info(f"try changing {ticket} stop loss {
                        position.sl} to {new_stop_loss}")

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "price_open": position.price_open,
            "sl": float(new_stop_loss),
            "tp": position.tp,
            "magic": self.magic,
            "deviation": 10,
            "comment": "Updating stop loss",
        }

        # Send the modification request
        result = mt5.order_send(request)
        logger.info(f"result: {result}")
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Failed to update stop loss for position {
                         ticket}: {result.comment}")
            return False
        else:
            logger.success(f"Successfully updated stop loss for position {
                           ticket} to {new_stop_loss}")
        return True

    def close_position(self, ticket):
        logger.info(f"Trying to close ticket: {ticket}")
        position = self.get_open_positions(ticket)
        action = mt5.TRADE_ACTION_DEAL

        # If no open position is found, check for pending orders
        if position is None:
            position = self.get_pending_orders(ticket)
            action = mt5.TRADE_ACTION_REMOVE

        # If no position or pending order exists, log and exit
        if position is None:
            logger.error(f"Can't find position or order with ticket {
                         ticket} to close.")
            return False

        # Determine symbol, volume, and price based on the position type
        symbol = position.symbol
        volume = position.volume if hasattr(
            position, "volume") else position.volume_current
        price = (
            mt5.symbol_info_tick(
                symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).ask
        )

        # Build the close request
        request = {
            "action": action,
            "symbol": symbol,
            "volume": volume,
            "price": price,
            "deviation": 10,
            "magic": self.magic,
            "comment": "Closing position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        if action == mt5.TRADE_ACTION_REMOVE:
            request["order"] = ticket
        else:
            request["position"] = ticket

        # Send the close order request
        result = mt5.order_send(request)

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Failed to close position {
                         ticket}: {result.comment}")
            return False

        logger.success(f"Successfully closed position {ticket}.")
        return True

    def determine_order_type_and_price(self, current_price, open_order_price, order_type_signal):
        if order_type_signal == mt5.ORDER_TYPE_BUY:
            if (open_order_price > current_price):
                return mt5.ORDER_TYPE_BUY_STOP
            elif (open_order_price < current_price):
                return mt5.ORDER_TYPE_BUY_LIMIT
        elif order_type_signal == mt5.ORDER_TYPE_SELL:
            if (open_order_price > current_price):
                return mt5.ORDER_TYPE_SELL_LIMIT
            elif (open_order_price < current_price):
                return mt5.ORDER_TYPE_SELL_STOP

        return order_type_signal

    def validate(self, price, symbol):
        currentPrice = mt5.symbol_info_tick(symbol).bid

        currentPrice = str(int(currentPrice))
        priceStr = str(int(price))
        if len(priceStr) != len(currentPrice):
            return float(currentPrice[0:-len(priceStr)] + priceStr)
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

    def calculate_lot_size_with_prices(self, symbol, risk_percentage, open_price, stop_loss_price):
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

    def OpenPosition(self, type, lot, symbol, sl, tp, price, expirePendinOrderInMinutes, comment, signal_id):
        try:
            # Get filling mode
            # filling_mode = mt5.symbol_info(symbol).filling_mode - 1

            # Take ask price
            # ask_price = mt5.symbol_info_tick(symbol).ask
            # Take bid price
            bid_price = mt5.symbol_info_tick(symbol).bid
            # Take the point of the asset
            point = mt5.symbol_info(symbol).point
            deviation = 20  # mt5.getSlippage(symbol)

            type = self.determine_order_type_and_price(
                bid_price, price, type)

            action = mt5.TRADE_ACTION_PENDING
            if type == mt5.ORDER_TYPE_BUY or type == mt5.ORDER_TYPE_SELL:
                action = mt5.TRADE_ACTION_DEAL

            lot = float(lot)
            openPrice = float(price)
            stopLoss = float(sl)
            takeProfit = float(tp)
            # Open the trade
            request = {
                "action": action,
                "symbol": symbol,
                "volume": lot,
                "type": type,
                "price": openPrice,
                "sl": stopLoss,
                "tp": takeProfit,
                "type_filling": mt5.ORDER_FILLING_IOC,
                # comment.replace("https://t.me/", ""),
                "comment": "TelegramTrader",
                "deviation": deviation,
                "magic": self.magic,
                "type_time": mt5.ORDER_TIME_GTC,
            }

            # expiration
            if type != mt5.ORDER_TYPE_BUY and type != mt5.ORDER_TYPE_SELL:
                if expirePendinOrderInMinutes != None and expirePendinOrderInMinutes != 0:
                    symbol_info = mt5.symbol_info(symbol)
                    timestamp = symbol_info.time
                    # Calculate expiration time
                    expiration_time = datetime.fromtimestamp(
                        timestamp) + timedelta(minutes=expirePendinOrderInMinutes)
                    expiration_timestamp = int(expiration_time.timestamp())
                    request["expiration"] = expiration_timestamp
                    request["type_time"] = mt5.ORDER_TIME_SPECIFIED

            logger.warning(f"-> Open Trade: \n{request}")

            # create a open request
            # send a trading request
            result = mt5.order_send(request)
            # check the execution result
            if result is not None:
                # check the execution result
                # logger.info("1. order_send(): by {} {} lots at {} with deviation={} points".format(symbol, lot, price, deviation))
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    logger.error(
                        "2. order_send failed, retcode={}".format(result.retcode))
                if result.retcode == 10027:
                    logger.critical("Enable Algo Trading in MetaTrader.")
                # if result.retcode == 10016:
                #     request["sl"] = stopLoss - 10
                #     resultMinusStop = mt5.order_send(request)

                    # Print the error message
                    error_message = mt5.last_error()
                    logger.error(f"   Error message: {error_message}")

                    # request the result as a dictionary and display it element by element
                    result_dict = result._asdict()
                    for field in result_dict.keys():
                        logger.error("   {}={}".format(
                            field, result_dict[field]))

                        # if this is a trading request structure, display it element by element as well
                        if field == "request":
                            traderequest_dict = result_dict[field]._asdict()
                            for tradereq_filed in traderequest_dict:
                                logger.error("       traderequest: {}={}".format(
                                    tradereq_filed, traderequest_dict[tradereq_filed]))

                    # print("shutdown() and quit")
                    mt5.shutdown()
                    # quit()
            else:
                logger.error("1. order_send failed. Exiting. ")
                mt5.shutdown()
                # quit()
            # logger.info(f"result: {result}")
            logger.info(f"open position id: {result.order} for {comment}")
            logger.info("result of open position: "+result.comment)

            # save in database
            if signal_id != None:
                position_data = {
                    "signal_id": signal_id,
                    "user_id": self.user,
                    "position_id": result.order
                }
                Migrations.position_repo.insert(position_data)

            return result
        except Exception as ex:
            logger.error(f"Unexpected error in open trade position: {ex}")

    def AnyPositionByData(self, symbol, openPrice, sl, tp):
        """
        Purpose: check if any position or order already exist by this data
        """
        positions = mt5.positions_get(symbol=symbol)
        if positions != None and len(positions) > 0:
            for position in positions:
                if (float(openPrice) == position.price_open and float(sl) == position.sl and float(tp) == position.tp):
                    return True

        orders = mt5.orders_get(symbol=symbol)
        if orders != None and len(orders) > 0:
            for order in orders:
                if (float(openPrice) == order.price_open and float(sl) == order.sl and float(tp) == order.tp):
                    return True

        return False

    class MetaTraderAccount:
        def __init__(self, account_dict):
            self.path = account_dict.get('path')
            if not self.path:  # Check if None or empty
                current_path = os.getcwd()
                self.path = os.path.join(current_path, "terminal64.exe")
            # Check if the file exists
            if not os.path.exists(self.path):
                raise FileNotFoundError(f"Error: The file does not exist at path: {self.path}")
    
            self.TakeProfit = account_dict.get('TakeProfit')
            self.server = account_dict.get('server')
            self.username = account_dict.get('username')
            self.password = account_dict.get('password')
            self.lot = account_dict.get('lot')
            self.HighRisk = account_dict.get('HighRisk')
            self.expirePendinOrderInMinutes = account_dict.get('expirePendinOrderInMinutes')

# ==============================
# POSITION
# ==============================
    def Trade(message_username, message_id, actionType, symbol, openPrice, secondPrice, tp_list, sl, comment):
        cfg = Configure.GetSettings()
        meta_trader_accounts = [MetaTrader.MetaTraderAccount(
            acc) for acc in cfg["MetaTrader"]]

        # action
        if actionType.value == 1:  # buy
            actionType = mt5.ORDER_TYPE_BUY
        elif actionType.value == 2:  # sell
            actionType = mt5.ORDER_TYPE_SELL

        for mtAccount in meta_trader_accounts:
            mt = MetaTrader(
                path=mtAccount.path,
                server=mtAccount.server,
                user=mtAccount.username,
                password=mtAccount.password
            )

            if mt.Login() == False:
                continue
            if mt.CheckSymbol(symbol) == False:
                continue

            # validate
            openPrice = mt.validate(openPrice, symbol)
            sl = mt.validate(sl, symbol)
            if secondPrice != None and secondPrice != 0:
                secondPrice = mt.validate(secondPrice, symbol)
                if (actionType == mt5.ORDER_TYPE_BUY and openPrice < secondPrice) or (actionType == mt5.ORDER_TYPE_SELL and openPrice > secondPrice):
                    openPrice, secondPrice = secondPrice, openPrice

            validated_tp_levels = []
            for tp_number in tp_list:
                validated_tp_levels.append(mt.validate(tp_number, symbol))

            # save to db
            # Check if a similar record already exists in the database
            last_signal = Migrations.get_last_record(
                open_price=openPrice,
                second_price=secondPrice,
                stop_loss=sl,
                symbol=symbol
            )

            if last_signal is None:
                signal_data = {
                    "telegram_channel_title": message_username,
                    "telegram_message_id": message_id,
                    "open_price": openPrice,
                    "second_price": secondPrice,
                    "stop_loss": sl,
                    "tp_list": ','.join(map(str, validated_tp_levels)),
                    "symbol": symbol,
                    "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                signal_id = Migrations.signal_repo.insert(signal_data)
            else:
                signal_id = last_signal["id"]
                # return

            # Open Position
            tp_levels = sorted(validated_tp_levels)
            if actionType == mt5.ORDER_TYPE_BUY:
                tp = max(tp_levels)
            else:
                tp = min(tp_levels)

            # lot
            lot = mt.calculate_lot_size_with_prices(
                symbol, mtAccount.lot, openPrice, sl)

            if mt.AnyPositionByData(symbol, openPrice, sl, tp) == True:
                logger.info(f"position already exist: symbol={
                            symbol}, openPrice={openPrice}, sl={sl}, tp={tp}")
            else:
                mt.OpenPosition(actionType, lot, symbol.upper(
                ), sl, tp, openPrice, mtAccount.expirePendinOrderInMinutes, comment, signal_id)

            if secondPrice is not None and secondPrice != 0 and mtAccount.HighRisk == True:
                # lot
                lot = mt.calculate_lot_size_with_prices(
                    symbol, mtAccount.lot, secondPrice, sl)
                # validate
                secondPrice = mt.validate(secondPrice, symbol)

                if mt.AnyPositionByData(symbol, secondPrice, sl, tp) == True:
                    logger.info(f"position already exist: symbol={
                                symbol}, secondPrice={secondPrice}, sl={sl}, tp={tp}")
                    continue

                mt.OpenPosition(actionType, lot, symbol.upper(
                ), sl, tp, secondPrice, mtAccount.expirePendinOrderInMinutes, comment, signal_id)

    def CloseLastSignalPositions(message_username):
        cfg = Configure.GetSettings()
        meta_trader_accounts = [MetaTrader.MetaTraderAccount(
            acc) for acc in cfg["MetaTrader"]]

        for mtAccount in meta_trader_accounts:
            mt = MetaTrader(
                path=mtAccount.path,
                server=mtAccount.server,
                user=mtAccount.username,
                password=mtAccount.password
            )

            if mt.Login() == False:
                continue

            positions = Database.Migrations.get_last_signal_positions_by_username(
                message_username)
            orders = mt.get_open_positions()
            for order in (o for o in orders if o.ticket in positions):
                mt.close_position(order.ticket)

# ==============================
# MONITORING
# ==============================
    async def monitor_all_accounts():
        """Monitor all accounts concurrently"""
        cfg = Configure.GetSettings()
        accounts = [MetaTrader.MetaTraderAccount(
            acc) for acc in cfg["MetaTrader"]]

        # Create tasks for all accounts
        tasks = []
        for account in accounts:
            mt = MetaTrader(
                path=account.path,
                server=account.server,
                user=account.username,
                password=account.password
            )
            tasks.append(mt.monitor_account())

        await asyncio.gather(*tasks)

    async def monitor_account(self):
        """Main async monitoring loop for a single account"""
        while True:  # Keep trying to reconnect
            try:
                # Initial login/reconnect
                if not self.connected:
                    if not self.Login():
                        logger.error(f"Failed to login to {
                                     self.server}, retrying in 5 seconds...")
                        await asyncio.sleep(5)
                        continue

                    logger.success(f"Connected to {
                                   self.server}, starting monitoring...")

                # Main monitoring loop
                while True:
                    # Check connection status periodically
                    if not mt5.terminal_info().connected:
                        logger.warning(f"Connection lost to {
                                       self.server}, reconnecting...")
                        self.connected = False
                        break  # Break inner loop to reconnect

                    # Get and process positions
                    self.trailing()
                    self.manage_positions()

                    # Async sleep to maintain event loop
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Monitoring error on {self.server}: {e}")
                self.connected = False
                await asyncio.sleep(5)

    def trailing(self):
        positions = self.get_open_positions()

        for position in positions:
            signal = Database.Migrations.get_signal_by_positionId(
                position.ticket)
            if signal is None:
                continue

            # entry_price = position.price_open
            entry_price = signal["open_price"]
            ticket = position.ticket
            lots = position.volume
            stop_loss = position.sl
            trade_type = position.type
            symbol = position.symbol

            current_price = self.get_current_price(symbol)
            if not current_price:
                continue

            tp_levels = Database.Migrations.get_tp_levels(ticket)
            if not tp_levels:
                continue
            tp_levels_buy = sorted(map(float, tp_levels))
            tp_levels_sell = sorted(map(float, tp_levels), reverse=True)

            # بررسی رسیدن به سطح سود
            if trade_type == 0:  # Buy
                for i, tp in enumerate(tp_levels_buy):
                    # اگر قیمت به سطح TP رسید و حجم نصف نشده است
                    if current_price >= tp and stop_loss < tp:
                        if (lots <= 0.01):
                            self.close_position(ticket)

                        # انتقال Stop Loss به سطح قبلی یا نقطه ورود
                        new_stop_loss = tp_levels_buy[i -
                                                      1] if i > 0 else entry_price
                        if (self.update_stop_loss(ticket, new_stop_loss) == False):
                            continue

                        # نصف کردن حجم معامله
                        self.close_half_position(ticket)
            elif trade_type == 1:  # Sell
                for i, tp in enumerate(tp_levels_sell):
                    # اگر قیمت به سطح TP رسید و حجم نصف نشده است
                    if current_price <= tp and stop_loss > tp:
                        if (lots <= 0.01):
                            self.close_position(ticket)

                        # انتقال Stop Loss به سطح قبلی یا نقطه ورود
                        new_stop_loss = tp_levels_sell[i -
                                                       1] if i > 0 else entry_price
                        # new_stop_loss = tp_levels[i + 1] if i < len(tp_levels) - 1 else entry_price
                        if (self.update_stop_loss(ticket, new_stop_loss) == False):
                            continue

                        # نصف کردن حجم معامله
                        self.close_half_position(ticket)

    def manage_positions(self):
        pending_orders = self.get_pending_orders()

        for order in pending_orders:
            position_id = order.ticket
            position_type = order.type  # Buy = 0, Sell = 1
            symbol = order.symbol

            tp_levels = Database.Migrations.get_tp_levels(position_id)
            
            tp_levels_buy = sorted(map(float, tp_levels))
            tp_levels_sell = sorted(map(float, tp_levels), reverse=True)

            current_price = self.get_current_price(symbol)

            if ((position_type == mt5.ORDER_TYPE_BUY_STOP or position_type == mt5.ORDER_TYPE_BUY_LIMIT) and current_price >= tp_levels_buy[0]) or ((position_type == mt5.ORDER_TYPE_SELL_LIMIT or position_type == mt5.ORDER_TYPE_SELL_STOP) and current_price <= tp_levels_sell[0]):
                # at first check if one of the poistions executed
                positions = Database.Migrations.get_signal_positions_by_positionId(position_id)
                signal = Database.Migrations.get_signal_by_positionId(position_id)
                
                if (len(positions) == 0):
                    continue
                
                if(signal['second_price'] is None or signal['second_price'] == 0):
                    self.close_position(position_id)
                    
                position = self.get_open_positions(positions[0]['position_id'])
                if (position is None and len(positions) == 2):
                    position = self.get_open_positions(positions[1]['position_id'])
                else:
                    continue
                if (position is None):
                    continue
                
                self.close_position(position_id)
