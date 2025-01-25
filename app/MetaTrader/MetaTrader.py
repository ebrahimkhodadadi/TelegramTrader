from app import Database
from app.Database import Migrations
from loguru import logger
import MetaTrader5 as mt5
import Configure
import time
import asyncio
from datetime import datetime, timedelta


class MetaTrader:
    def __init__(self, path, server, user, password):
        self.path = path
        self.server = server
        self.user = user
        self.password = password

    def Login(self):
        try:
            logger.info(f"try to login to {self.server} with {self.user}")
            # establish connection to the MetaTrader 5 terminal
            if not mt5.initialize(path=self.path, login=self.user, server=self.server, password=self.password):
                logger.error("MetaTrader Login failed, error code =",
                             mt5.last_error())
                return False
            return True
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False

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
        return tick.bid if tick else None

    def get_open_positions(self):
        """Get open positions from MetaTrader"""
        positions = mt5.positions_get()
        return positions if positions else []
    
    def get_pending_orders(self):
        """Get pending orders from MetaTrader"""
        orders = mt5.orders_get()
        return orders if orders else []

    def close_half_position(self, ticket, lots):
        """Close half of the position volume"""
        new_lot_size = lots / 2
        if new_lot_size >= 0.01:
            print(f"Closing half of position {
                  ticket}, new lot: {new_lot_size}")
            mt5.order_send({
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "volume": new_lot_size,
                "type": mt5.ORDER_TYPE_SELL
            })
        else:
            self.close_position(ticket)

    def update_stop_loss(self, ticket, new_stop_loss):
        """Updating stop loss"""
        mt5.order_send({
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl": new_stop_loss
        })

    def close_position(self, ticket):
        """Close position"""
        mt5.order_send({
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "type": mt5.ORDER_TYPE_SELL
        })

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
                "type_filling": mt5.ORDER_FILLING_IOC,
                # comment.replace("https://t.me/", ""),
                "comment": "TelegramTrader",
                "deviation": deviation,
                "magic": 2024,
                "type_time": mt5.ORDER_TIME_GTC,
            }

            if tp != None and tp != 0:
                request["tp"] = takeProfit

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
            self.TakeProfit = account_dict.get('TakeProfit')
            self.server = account_dict.get('server')
            self.username = account_dict.get('username')
            self.password = account_dict.get('password')
            self.lot = account_dict.get('lot')
            self.path = account_dict.get('path')
            self.HighRisk = account_dict.get('HighRisk')
            self.EnableTp = account_dict.get('EnableTp')
            self.expirePendinOrderInMinutes = account_dict.get(
                'expirePendinOrderInMinutes')

# ==============================
# POSITION
# ==============================
    def Trade(actionType, symbol, openPrice, secondPrice, tp, sl, comment, signal_id):
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

            openPrice = mt.validate(openPrice, symbol)
            openPriceAvg = mt.validate(openPrice, symbol)
            sl = mt.validate(sl, symbol)
            secondPrice = mt.validate(secondPrice, symbol)
            # Note: test
            if mtAccount.EnableTp is True:
                tp = None

            if secondPrice is not None and mtAccount.HighRisk == False:
                openPriceAvg = (mt.validate(openPrice, symbol) +
                                mt.validate(secondPrice, symbol)) / 2

            # tp first price
            tpStatic = mt.calculate_new_price(
                symbol, openPriceAvg, mtAccount.TakeProfit, tp, actionType)
            # lot
            lot = mt.calculate_lot_size_with_prices(
                symbol, mtAccount.lot, openPrice, sl)

            # validate
            openPriceAvg = mt.validate(openPriceAvg, symbol)
            tpStatic = mt.validate(tpStatic, symbol)

            if mt.AnyPositionByData(symbol, openPriceAvg, sl, tpStatic) == True:
                logger.info(f"position already exist: symbol={
                            symbol}, openPrice={openPriceAvg}, sl={sl}, tp={tpStatic}")
            else:
                mt.OpenPosition(actionType, lot, symbol.upper(
                ), sl, tpStatic, openPriceAvg, mtAccount.expirePendinOrderInMinutes, comment, signal_id)

            if secondPrice is not None and mtAccount.HighRisk == True:
                # tp first price
                tpStatic = mt.calculate_new_price(
                    symbol, openPriceAvg, mtAccount.TakeProfit, tp, actionType)
                # lot
                lot = mt.calculate_lot_size_with_prices(
                    symbol, mtAccount.lot, secondPrice, sl)
                # validate
                secondPrice = mt.validate(secondPrice, symbol)
                tpStatic = mt.validate(tpStatic, symbol)
                sl = mt.validate(sl, symbol)

                if mt.AnyPositionByData(symbol, secondPrice, sl, tpStatic) == True:
                    logger.info(f"position already exist: symbol={symbol}, secondPrice={
                                secondPrice}, sl={sl}, tp={tpStatic}")
                    continue

                mt.OpenPosition(actionType, lot, symbol.upper(
                ), sl, tpStatic, secondPrice, mtAccount.expirePendinOrderInMinutes, comment, signal_id)
    # Note: test
    def CloseLastSignalPositions():
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
            
            positions = Database.Migrations.get_last_signal_positions()
            for position in positions:
                mt.ClosePosition(position)

# ==============================
# MONITORING
# ==============================
    # Note: test
    def on_tick(self, symbol):
        last_tick = None  # Store the last tick to detect changes
        while True:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error("Failed to get tick data")
                continue

            # Check if tick is updated
            if last_tick is None or last_tick.time != tick.time:
                last_tick = tick  # Update last tick

                self.trailing()
                self.manage_positions()

            # time.sleep(1)  # Adjust the interval as needed

    # Note: test
    async def Monitor(symbol="XAUUSD"):
        cfg = Configure.GetSettings()
        meta_trader_accounts = [MetaTrader.MetaTraderAccount(
            acc) for acc in cfg["MetaTrader"]]

        tasks = []
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

            tasks.append(mt.on_tick(symbol))

        await asyncio.gather(*tasks)

    # Note: test
    def trailing(self):
        positions = self.get_open_positions()

        for position in positions:
            ticket = position.ticket
            lots = position.volume
            stop_loss = position.sl
            entry_price = position.price_open
            trade_type = position.type
            trade_type = position.type
            symbol = position.symbol

            current_price = self.get_current_price(symbol)
            if not current_price:
                continue

            tp_levels = Database.Migrations.get_tp_levels(ticket.id)
            if not tp_levels:
                continue

            # بررسی رسیدن به سطح سود
            for i, tp in enumerate(tp_levels):
                if trade_type == "buy":
                    if current_price >= tp and stop_loss < tp_levels[max(i - 1, 0)]:
                        self.close_half_position(ticket, lots)
                        self.update_stop_loss(
                            ticket, tp_levels[max(i - 1, 0)] if i > 0 else entry_price)

                elif trade_type == "sell":
                    if current_price <= tp and stop_loss > tp_levels[max(i - 1, 0)]:
                        self.close_half_position(ticket, lots)
                        self.update_stop_loss(
                            ticket, tp_levels[max(i - 1, 0)] if i > 0 else entry_price)

    # Note: test
    def manage_positions(self):
        open_positions = self.GetOpenPositions()

        pending_orders = self.get_pending_orders()

        for pos in open_positions:
            position_id = pos['ticket']
            position_type = pos['type']  # Buy = 0, Sell = 1
            symbol = pos['symbol']

            tp_levels = Database.Migrations.get_tp_levels(position_id)
            tp_levels = sorted(map(float, tp_levels.split(',')))
            
            current_price = self.GetCurrentPrice(symbol)

            if (position_type == 0 and current_price >= tp_levels[0]) or (position_type == 1 and current_price <= tp_levels[0]):
                for order in pending_orders:
                    if order['ticket'] == position_id:
                        self.ClosePosition(order['ticket'])
                        break
