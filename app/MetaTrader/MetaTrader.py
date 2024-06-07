from loguru import logger
import MetaTrader5 as mt5
import Configure
import time
from datetime import datetime, timedelta


class MetaTrader:
    def __init__(self, server, user, password):
        self.server = server
        self.user = user
        self.password = password

    @logger.catch
    def Login(server, user, password):
        # establish connection to the MetaTrader 5 terminal
        if not mt5.initialize(login=user, server=server, password=password):
            logger.error("MetaTrader Login failed, error code =",
                         mt5.last_error())
            return False
        return True

    @logger.catch
    def CheckSymbol(symbol):
        logger.info("Check symbol " + symbol)
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.critical(symbol, "not found, can not call order_check()")
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
    def OpenPosition(type, lot, symbol, sl, tp, price, expirePendinOrderInMinutes, comment):
        try:
            # Get filling mode
            # filling_mode = mt5.symbol_info(symbol).filling_mode - 1

            # Take ask price
            ask_price = mt5.symbol_info_tick(symbol).ask
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

            # Open the trade
            request = {
                "action": action,
                "symbol": symbol,
                "volume": lot,
                "type": type,
                "price": float(price),
                "sl": float(sl),
                "tp": float(tp),
                "type_filling": mt5.ORDER_FILLING_IOC,
                "comment": comment,
                "deviation": deviation,
                "magic": 2024,
                "type_time": mt5.ORDER_TIME_GTC,
            }
            logger.warning("-> Open Trade: \n" + request)

            # expiration
            if type != mt5.ORDER_TYPE_BUY and type != mt5.ORDER_TYPE_SELL:
                symbol_info = mt5.symbol_info(symbol)
                timestamp = symbol_info.time
                # Calculate expiration time
                expiration_time = datetime.fromtimestamp(
                    timestamp) + timedelta(minutes=expirePendinOrderInMinutes)
                expiration_timestamp = int(expiration_time.timestamp())
                request["expiration"] = expiration_timestamp
                request["type_time"] = mt5.ORDER_TIME_SPECIFIED

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
            logger.info("result of open position: \n"+result)
            return result
        except Exception as ex:
            logger.error(f"Unexpected error in open trade position: {ex}")

    def Trade(actionType, symbol, openPrice, tp, sl, comment):
        cfg = Configure.GetSettings()
        if MetaTrader.Login(cfg.MetaTrader.server, cfg.MetaTrader.username, cfg.MetaTrader.password) == False:
            return
        if MetaTrader.CheckSymbol(symbol) == False:
            return

        if actionType == 1:  # buy
            actionType = mt5.ORDER_TYPE_BUY
        elif actionType == 2:  # sell
            actionType = mt5.ORDER_TYPE_BUY

        MetaTrader.OpenPosition(actionType, cfg.MetaTrader.lot, symbol, sl, tp, openPrice, cfg.MetaTrader.expirePendinOrderInMinutes, comment)
