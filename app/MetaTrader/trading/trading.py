from datetime import datetime
from loguru import logger
from Database import Migrations


class TradingOperations:
    """High-level trading operations and signal processing"""

    @staticmethod
    def trade(message_username, message_id, message_chatid, actionType, symbol, openPrice, secondPrice, tp_list, sl, comment):
        """Execute a complete trading operation"""
        logger.info(f"Processing trade signal: {actionType.name} {symbol} from {message_username}")

        from Configure import GetSettings
        cfg = GetSettings()
        mtAccount = AccountConfig(cfg["MetaTrader"])

        # Convert action type
        if actionType.value == 1:  # buy
            actionType = 0  # mt5.ORDER_TYPE_BUY
        elif actionType.value == 2:  # sell
            actionType = 1  # mt5.ORDER_TYPE_SELL

        mt = MetaTrader(
            path=mtAccount.path,
            server=mtAccount.server,
            user=mtAccount.username,
            password=mtAccount.password
        )
        if not mt.Login():
            logger.error("Failed to login to MetaTrader")
            return
        if not mt.CheckSymbol(symbol):
            logger.error(f"Symbol {symbol} not available")
            return

        # Validate prices
        openPrice = mt.validate(actionType, openPrice, symbol)
        sl = mt.validate(actionType, sl, symbol, openPrice, isSl=True)
        if secondPrice is not None and secondPrice != 0:
            secondPrice = mt.validate(actionType, secondPrice, symbol, isSecondPrice=True)
            if (actionType == 0 and openPrice > secondPrice) or (actionType == 1 and openPrice < secondPrice):
                openPrice, secondPrice = secondPrice, openPrice

        if tp_list is None:
            logger.warning("No take profit levels specified")
            return

        validated_tp_levels = mt.validate_tp_list(
            actionType, tp_list, symbol, openPrice, secondPrice, mtAccount.CloserPrice)

        # Save to database
        signal_data = {
            "telegram_channel_title": message_username,
            "telegram_message_id": message_id,
            "telegram_message_chatid": message_chatid,
            "open_price": openPrice,
            "second_price": secondPrice,
            "stop_loss": sl,
            "tp_list": ','.join(map(str, validated_tp_levels)),
            "symbol": symbol,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        signal_id = Migrations.signal_repo.insert(signal_data)
        logger.info(f"Signal saved to database with ID {signal_id}")

        # Open first position
        tp_levels = sorted(validated_tp_levels)
        if actionType == 0:  # BUY
            tp = max(tp_levels)
        else:  # SELL
            tp = min(tp_levels)

        lot = mt.calculate_lot_size_with_prices(
            symbol, mtAccount.lot, openPrice, sl, mtAccount.account_size)

        logger.info(f"Opening first position: {symbol} {lot} lots @ {openPrice}, SL: {sl}, TP: {tp}")
        mt.OpenPosition(actionType, lot, symbol, sl, tp, openPrice, mtAccount.expirePendinOrderInMinutes,
                        comment, signal_id, mtAccount.CloserPrice, isFirst=True)

        # Open second position if high risk mode enabled
        if secondPrice is not None and secondPrice != 0 and mtAccount.HighRisk == True:
            lot = mt.calculate_lot_size_with_prices(
                symbol, mtAccount.lot, secondPrice, sl, mtAccount.account_size)
            secondPrice = mt.validate(actionType, secondPrice, symbol)

            logger.info(f"Opening second position: {symbol} {lot} lots @ {secondPrice}, SL: {sl}, TP: {tp}")
            mt.OpenPosition(actionType, lot, symbol, sl, tp, secondPrice, mtAccount.expirePendinOrderInMinutes,
                            comment, signal_id, mtAccount.CloserPrice, isSecond=True)

    @staticmethod
    def risk_free_positions(chat_id, message_id):
        """Move stop loss to entry price for risk-free positions"""
        logger.info(f"Applying risk-free strategy for chat {chat_id}, message {message_id}")

        from Configure import GetSettings
        cfg = GetSettings()
        mtAccount = AccountConfig(cfg["MetaTrader"])
        mt = MetaTrader(
            path=mtAccount.path,
            server=mtAccount.server,
            user=mtAccount.username,
            password=mtAccount.password
        )

        if not mt.Login():
            logger.error("Failed to login for risk-free operation")
            return

        positions = Migrations.get_last_signal_positions_by_chatid_and_messageid(chat_id, message_id)

        orders = mt.get_open_positions()
        for order in (o for o in orders if o.ticket in positions):
            signal = Database.Migrations.get_signal_by_positionId(order.ticket)
            if signal is None:
                logger.error(f"Signal not found for position {order.ticket}")
                continue

            entry_price = signal["open_price"]
            signal_position = Database.Migrations.get_position_by_signal_id(signal["id"], first=True)
            if signal_position is not None:
                pos = mt.get_position_or_order(ticket_id=signal_position["position_id"])
                if pos is not None:
                    entry_price = pos.price_open

            logger.info(f"Moving SL to entry price {entry_price} for position {order.ticket}")
            result = mt.update_stop_loss(order.ticket, entry_price)
            if result:
                logger.info(f"Closing half position {order.ticket} for profit protection")
                mt.close_half_position(order.ticket)

    @staticmethod
    def update_last_signal(chat_id, stop_loss):
        """Update stop loss for last signal"""
        logger.info(f"Updating stop loss to {stop_loss} for last signal in chat {chat_id}")

        from Configure import GetSettings
        cfg = GetSettings()
        account = AccountConfig(cfg["MetaTrader"])
        mt = MetaTrader(
            path=account.path,
            server=account.server,
            user=account.username,
            password=account.password,
            saveProfits=account.SaveProfits,
        )

        stop_loss = float(stop_loss)
        positions = Database.Migrations.get_last_signal_positions_by_chatid(chat_id)

        signal = Migrations.get_signal_by_positionId(positions[0])
        if signal is None or len(str(signal['stop_loss'])) != len(str(stop_loss)):
            logger.warning("Signal not found or stop loss format mismatch")
            return

        result = False
        for position in positions:
            result = mt.update_stop_loss(position, stop_loss)

        if result:
            Migrations.update_stoploss(signal['id'], stop_loss)
            logger.success(f"Stop loss updated to {stop_loss} for signal {signal['id']}")

    @staticmethod
    def update_signal(signal_id, takeProfits, stopLoss):
        """Update signal take profits and stop loss"""
        logger.info(f"Updating signal {signal_id} - SL: {stopLoss}, TP: {takeProfits}")

        from Configure import GetSettings
        cfg = GetSettings()
        account = AccountConfig(cfg["MetaTrader"])
        mt = MetaTrader(
            path=account.path,
            server=account.server,
            user=account.username,
            password=account.password,
            saveProfits=account.SaveProfits,
        )

        stopLoss = float(stopLoss)
        positions = Migrations.get_positions_by_signalid(signal_id)

        signal = Migrations.get_signal_by_id(signal_id)
        if signal is None or len(str(signal['stop_loss'])) != len(str(stopLoss)):
            logger.warning(f"Signal {signal_id} not found or stop loss format mismatch")
            return

        result = False
        for position in positions:
            result = mt.update_stop_loss(position["position_id"], stopLoss)

        if result:
            Migrations.update_stoploss(signal_id, stopLoss)
            logger.success(f"Stop loss updated for signal {signal_id}")

        Migrations.update_takeProfits(signal_id, takeProfits)
        logger.success(f"Take profits updated for signal {signal_id}")

    @staticmethod
    def delete_signal(signal_id):
        """Delete signal and close all related positions"""
        logger.info(f"Deleting signal {signal_id} and closing all positions")

        from Configure import GetSettings
        cfg = GetSettings()
        account = AccountConfig(cfg["MetaTrader"])
        mt = MetaTrader(
                path=account.path,
                server=account.server,
                user=account.username,
                password=account.password,
                saveProfits=account.SaveProfits,
            )

        positions = Migrations.get_positions_by_signalid(signal_id)
        for position in positions:
            logger.info(f"Closing position {position['position_id']} for signal {signal_id}")
            mt.close_position(position["position_id"])

        logger.success(f"Signal {signal_id} deleted and all positions closed")

    @staticmethod
    def close_half_signal(signal_id):
        """Close half of positions for a signal"""
        logger.info(f"Closing half positions for signal {signal_id}")

        from Configure import GetSettings
        cfg = GetSettings()
        account = AccountConfig(cfg["MetaTrader"])
        mt = MetaTrader(
                path=account.path,
                server=account.server,
                user=account.username,
                password=account.password,
                saveProfits=account.SaveProfits,
            )

        positions = Migrations.get_positions_by_signalid(signal_id)
        for position in positions:
            position_obj = mt.get_position_or_order(position["position_id"])
            if position_obj is not None:
                logger.info(f"Closing half of position {position['position_id']}")
                mt.close_half_position(position["position_id"])
                logger.info(f"Moving SL to entry price for position {position['position_id']}")
                mt.update_stop_loss(position["position_id"], position_obj.price_open)


# Import here to avoid circular imports
from MetaTrader import MetaTrader
from MetaTrader.connection import AccountConfig