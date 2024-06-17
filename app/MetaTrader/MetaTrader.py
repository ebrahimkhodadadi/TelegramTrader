from loguru import logger
import MetaTrader5 as mt5
import Configure
import time
from datetime import datetime, timedelta


class MetaTrader:
    def Login(path, server, user, password):
        try:
            logger.info(f"try to login to {server} with {user}")
            # establish connection to the MetaTrader 5 terminal
            if not mt5.initialize(path=path, login=user, server=server, password=password):
                logger.error("MetaTrader Login failed, error code =",
                             mt5.last_error())
                return False
            return True
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False

    @logger.catch
    def CheckSymbol(symbol):
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

    @logger.catch
    def determine_order_type_and_price(current_price, open_order_price, order_type_signal):
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

    @logger.catch
    def validate(price, symbol):
        currentPrice = mt5.symbol_info_tick(symbol).bid

        currentPrice = str(int(currentPrice))
        priceStr = str(int(price))
        if len(priceStr) != len(currentPrice):
            return float(currentPrice[0:-len(priceStr)] + priceStr)
        return float(price)

    @logger.catch
    def calculate_lot_size_with_prices(account_size, risk_percentage, open_price, stop_loss_price, tick_size, tick_value):
        """
        Calculate the lot size per account size, risk percentage, open position price, and stop loss price.

        Parameters:
        account_size (float): The total capital in the trading account.
        risk_percentage (float): The percentage of the account size to risk on a single trade.
        open_price (float): The open position price.
        stop_loss_price (float): The stop loss price.
        tick_size (float): The smallest price increment of the instrument.
        tick_value (float): The value of a single tick.

        Returns:
        float: The calculated lot size rounded to two decimal places.
        """
        # Calculate the number of ticks between the open price and stop loss price
        risk_ticks = abs(open_price - stop_loss_price) / tick_size

        # Convert the number of ticks to pip value
        risk_pips = risk_ticks  # Assuming risk_ticks are in pip units already

        # Calculate the monetary risk
        risk_amount = account_size * (risk_percentage / 100)

        # Calculate lot size
        lot_size = risk_amount / (risk_pips * tick_value)
        lot_size = round(lot_size, 2)

        if lot_size == 0 or lot_size == 0.00 or lot_size == 0.0:
            logger.warning(f"risk amount is {risk_amount} more than {
                           risk_percentage}% the lot size cant be lower than 0.01 this is on your own risk")
            return 0.01

        return lot_size

    @logger.catch
    def OpenPosition(type, lot, symbol, sl, tp, price, expirePendinOrderInMinutes, comment):
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

            type = MetaTrader.determine_order_type_and_price(
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
                "tp": takeProfit,
                "type_filling": mt5.ORDER_FILLING_IOC,
                # comment.replace("https://t.me/", ""),
                "comment": "TelegramTrader",
                "deviation": deviation,
                "magic": 2024,
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
            logger.info("result of open position: "+result.comment)
            return result
        except Exception as ex:
            logger.error(f"Unexpected error in open trade position: {ex}")

    @logger.catch
    def AnyPositionByData(symbol, openPrice, sl, tp):
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
            self.expirePendinOrderInMinutes = account_dict.get(
                'expirePendinOrderInMinutes')

    def Trade(actionType, symbol, openPrice, secondPrice, tp, sl, comment):
        cfg = Configure.GetSettings()
        meta_trader_accounts = [MetaTrader.MetaTraderAccount(
            acc) for acc in cfg["MetaTrader"]]

        # action
        if actionType.value == 1:  # buy
            actionType = mt5.ORDER_TYPE_BUY
        elif actionType.value == 2:  # sell
            actionType = mt5.ORDER_TYPE_SELL

        for mtAccount in meta_trader_accounts:
            if MetaTrader.Login(mtAccount.path, mtAccount.server, mtAccount.username, mtAccount.password) == False:
                return
            if MetaTrader.CheckSymbol(symbol) == False:
                return

            if secondPrice is not None and mtAccount.HighRisk == False:
                openPrice = (openPrice + secondPrice) / 2

            # tp first price
            if mtAccount.TakeProfit is not None and mtAccount.TakeProfit != 0 and symbol.upper() == 'XAUUSD':
                if actionType == mt5.ORDER_TYPE_BUY:
                    tp = openPrice + (mtAccount.TakeProfit / 10)
                elif actionType == mt5.ORDER_TYPE_SELL:
                    tp = openPrice - (mtAccount.TakeProfit / 10)
            # lot
            lot = None
            balance = mt5.account_info().balance
            riskPercentage = float(mtAccount.lot.replace("%", ""))
            tickValue = mt5.symbol_info(symbol).trade_tick_value
            tickSize = mt5.symbol_info(symbol).trade_tick_size
            lot = MetaTrader.calculate_lot_size_with_prices(
                balance, riskPercentage, openPrice, sl, tickSize, tickValue)

            # validate
            openPrice = MetaTrader.validate(openPrice, symbol)
            tp = MetaTrader.validate(tp, symbol)
            sl = MetaTrader.validate(sl, symbol)

            if MetaTrader.AnyPositionByData(symbol, openPrice, sl, tp) == True:
                logger.info(f"position already exist: symbol={
                            symbol}, openPrice={openPrice}, sl={sl}, tp={tp}")
            else:
                MetaTrader.OpenPosition(actionType, lot, symbol.upper(
                ), sl, tp, openPrice, mtAccount.expirePendinOrderInMinutes, comment)

            if secondPrice is not None and mtAccount.HighRisk == True:
                # tp first price
                if mtAccount.TakeProfit is not None and mtAccount.TakeProfit != 0 and symbol.upper() == 'XAUUSD':
                    if actionType == mt5.ORDER_TYPE_BUY:
                        tp = secondPrice + (mtAccount.TakeProfit / 10)
                    elif actionType == mt5.ORDER_TYPE_SELL:
                        tp = secondPrice - (mtAccount.TakeProfit / 10)
                # lot
                lot = None
                balance = mt5.account_info().balance
                riskPercentage = float(mtAccount.lot.replace("%", ""))
                tickValue = mt5.symbol_info(symbol).trade_tick_value
                tickSize = mt5.symbol_info(symbol).trade_tick_size
                lot = MetaTrader.calculate_lot_size_with_prices(
                    balance, riskPercentage, secondPrice, sl, tickSize, tickValue)

                # validate
                secondPrice = MetaTrader.validate(secondPrice, symbol)
                tp = MetaTrader.validate(tp, symbol)
                sl = MetaTrader.validate(sl, symbol)

                if MetaTrader.AnyPositionByData(symbol, secondPrice, sl, tp) == True:
                    logger.info(f"position already exist: symbol={symbol}, secondPrice={secondPrice}, sl={sl}, tp={tp}")
                    continue

                MetaTrader.OpenPosition(actionType, lot, symbol.upper(
                ), sl, tp, secondPrice, mtAccount.expirePendinOrderInMinutes, comment)
