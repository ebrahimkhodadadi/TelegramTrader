import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from loguru import logger
import Database
from Database import Migrations
from ..connection import AccountConfig


class TradingOperations:
    """High-level trading operations and signal processing"""

    @staticmethod
    def trade(message_username, message_id, message_chatid, actionType, symbol, openPrice, secondPrice, tp_list, sl, comment):
        """Execute a complete trading operation"""
        from MessageHandler import PerformanceMonitor
        PerformanceMonitor.start_operation("trade_execution")

        # logger.debug(f"Processing trade signal: {actionType.name} {symbol}")

        from Configure import GetSettings
        from ..MetaTrader import MetaTrader

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
            secondPrice = mt.validate(
                actionType, secondPrice, symbol, isSecondPrice=True)
            if (actionType == 0 and openPrice > secondPrice) or (actionType == 1 and openPrice < secondPrice):
                openPrice, secondPrice = secondPrice, openPrice

        if tp_list is None:
            logger.warning("No take profit levels specified")
            return

        validated_tp_levels = mt.validate_tp_list(
            actionType, tp_list, symbol, openPrice, secondPrice, mtAccount.CloserPrice)

        # Save to database with transaction for atomicity
        import sqlite3
        signal_id = None
        try:
            # Use transaction for atomic signal + position inserts
            conn = Migrations.signal_repo._connect()
            conn.execute("BEGIN TRANSACTION")

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

            # Pre-insert position data for batch processing
            position_data_list = []
            for params in position_params:
                position_data = {
                    "signal_id": signal_id,
                    "position_id": 0,  # Will be updated after MT5 order
                    "user_id": mt.user,
                    "is_first": params['isFirst'],
                    "is_second": params['isSecond']
                }
                position_data_list.append(position_data)

            conn.commit()
            logger.debug(f"Signal {signal_id} saved to database atomically")

        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()

        # Prepare position opening parameters
        tp_levels = sorted(validated_tp_levels)
        if actionType == 0:  # BUY
            tp = max(tp_levels)
        else:  # SELL
            tp = min(tp_levels)

        # First position parameters
        first_lot = mt.calculate_lot_size_with_prices(
            symbol, mtAccount.lot, openPrice, sl, mtAccount.account_size)

        position_params = []

        # Add first position parameters
        first_params = {
            'actionType': actionType,
            'lot': first_lot,
            'symbol': symbol,
            'sl': sl,
            'tp': tp,
            'price': openPrice,
            'expirePendinOrderInMinutes': mtAccount.expirePendinOrderInMinutes,
            'comment': comment,
            'signal_id': signal_id,
            'closerPrice': mtAccount.CloserPrice,
            'isFirst': True,
            'isSecond': False,
            'position_name': 'first'
        }
        position_params.append(first_params)

        # Add second position parameters if high risk mode enabled
        if secondPrice is not None and secondPrice != 0 and mtAccount.HighRisk == True:
            second_lot = mt.calculate_lot_size_with_prices(
                symbol, mtAccount.lot, secondPrice, sl, mtAccount.account_size)
            secondPrice = mt.validate(actionType, secondPrice, symbol)

            second_params = {
                'actionType': actionType,
                'lot': second_lot,
                'symbol': symbol,
                'sl': sl,
                'tp': tp,
                'price': secondPrice,
                'expirePendinOrderInMinutes': mtAccount.expirePendinOrderInMinutes,
                'comment': comment,
                'signal_id': signal_id,
                'closerPrice': mtAccount.CloserPrice,
                'isFirst': False,
                'isSecond': True,
                'position_name': 'second'
            }
            position_params.append(second_params)

        # Execute position openings concurrently using shared executor
        if position_params:
            # logger.debug(f"Opening {len(position_params)} position(s) concurrently for signal {signal_id}")

            def open_single_position(params):
                """Open a single position with given parameters"""
                return mt.OpenPosition(
                    params['actionType'], params['lot'], params['symbol'], params['sl'], params['tp'], params['price'],
                    params['expirePendinOrderInMinutes'], params['comment'], params['signal_id'],
                    params['closerPrice'], params['isFirst'], params['isSecond']
                )

            # Use shared trade executor for better performance
            from MessageHandler import ConcurrentOperationProcessor
            futures = [ConcurrentOperationProcessor._trade_executor.submit(open_single_position, params) for params in position_params]
            results = [future.result() for future in futures]

            # logger.debug(f"All {len(position_params)} positions processed for signal {signal_id}")

        PerformanceMonitor.end_operation("trade_execution")

    @staticmethod
    def risk_free_positions(chat_id, message_id):
        """Move stop loss to entry price for risk-free positions"""
        logger.info(
            f"Applying risk-free strategy for chat {chat_id}, message {message_id}")

        from Configure import GetSettings
        from ..MetaTrader import MetaTrader

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

        positions = Migrations.get_last_signal_positions_by_chatid_and_messageid(
            chat_id, message_id)

        orders = mt.get_open_positions()
        for order in (o for o in orders if o.ticket in positions):
            signal = Database.Migrations.get_signal_by_positionId(order.ticket)
            if signal is None:
                logger.error(f"Signal not found for position {order.ticket}")
                continue

            entry_price = signal["open_price"]
            signal_position = Database.Migrations.get_position_by_signal_id(
                signal["id"], first=True)
            if signal_position is not None:
                pos = mt.get_position_or_order(
                    ticket_id=signal_position["position_id"])
                if pos is not None:
                    entry_price = pos.price_open

            logger.info(
                f"Moving SL to entry price {entry_price} for position {order.ticket}")
            result = mt.update_stop_loss(order.ticket, entry_price)
            if result:
                logger.info(
                    f"Closing half position {order.ticket} for profit protection")
                mt.close_half_position(order.ticket)

    @staticmethod
    def update_last_signal(chat_id, stop_loss):
        """Update stop loss for last signal"""
        logger.info(
            f"Updating stop loss to {stop_loss} for last signal in chat {chat_id}")

        from Configure import GetSettings
        from ..MetaTrader import MetaTrader

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
        positions = Database.Migrations.get_last_signal_positions_by_chatid(
            chat_id)

        signal = Migrations.get_signal_by_positionId(positions[0])
        if signal is None or len(str(signal['stop_loss'])) != len(str(stop_loss)):
            logger.warning("Signal not found or stop loss format mismatch")
            return

        result = False
        for position in positions:
            result = mt.update_stop_loss(position, stop_loss)

        if result:
            Migrations.update_stoploss(signal['id'], stop_loss)
            logger.success(
                f"Stop loss updated to {stop_loss} for signal {signal['id']}")

    @staticmethod
    def update_signal(signal_id, takeProfits, stopLoss):
        """Update signal take profits and stop loss"""
        logger.info(
            f"Updating signal {signal_id} - SL: {stopLoss}, TP: {takeProfits}")

        from Configure import GetSettings
        from ..MetaTrader import MetaTrader

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
            logger.warning(
                f"Signal {signal_id} not found or stop loss format mismatch")
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
        from ..MetaTrader import MetaTrader

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
        if not positions:
            logger.warning(f"No positions found for signal {signal_id}")
            return

        # Process position closures concurrently
        def close_single_position(position):
            """Close a single position"""
            logger.info(f"Closing position {position['position_id']} for signal {signal_id}")
            return mt.close_position(position["position_id"])

        logger.info(f"Closing {len(positions)} positions concurrently for signal {signal_id}")

        # Use ThreadPoolExecutor for concurrent processing
        with ThreadPoolExecutor(max_workers=min(len(positions), 3)) as executor:
            futures = [executor.submit(close_single_position, position) for position in positions]
            results = [future.result() for future in futures]

        successful_closures = sum(1 for result in results if result)
        logger.success(f"Signal {signal_id} deleted - {successful_closures}/{len(positions)} positions closed successfully")

    @staticmethod
    def close_half_signal(signal_id):
        """Close half of positions for a signal"""
        logger.info(f"Closing half positions for signal {signal_id}")

        from Configure import GetSettings
        from ..MetaTrader import MetaTrader

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
        if not positions:
            logger.warning(f"No positions found for signal {signal_id}")
            return

        # Process positions concurrently
        def process_single_position(position):
            """Process a single position for half-close operation"""
            position_obj = mt.get_position_or_order(position["position_id"])
            if position_obj is not None:
                logger.info(f"Closing half of position {position['position_id']}")
                mt.close_half_position(position["position_id"])
                logger.info(f"Moving SL to entry price for position {position['position_id']}")
                mt.update_stop_loss(position["position_id"], position_obj.price_open)
                return True
            return False

        logger.info(f"Processing {len(positions)} positions concurrently for half-close operation")

        # Use ThreadPoolExecutor for concurrent processing
        with ThreadPoolExecutor(max_workers=min(len(positions), 3)) as executor:
            futures = [executor.submit(process_single_position, position) for position in positions]
            results = [future.result() for future in futures]

        successful_operations = sum(1 for result in results if result)
        logger.success(f"Half-close operation completed for {successful_operations}/{len(positions)} positions in signal {signal_id}")
