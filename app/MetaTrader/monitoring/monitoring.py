import asyncio
import MetaTrader5 as mt5
from loguru import logger
import Database


class MonitoringManager:
    """Handles position monitoring, trailing stops, and automated management"""

    def __init__(self, connection_manager, market_data, position_manager, save_profits=None, close_positions_on_trail=True):
        self.connection = connection_manager
        self.market_data = market_data
        self.position_manager = position_manager
        self.save_profits = save_profits
        self.close_positions_on_trail = close_positions_on_trail

    @staticmethod
    async def monitor_all_accounts():
        """Monitor all accounts concurrently"""
        from Configure.settings import Settings
        from ..connection import AccountConfig
        from ..MetaTrader import MetaTrader

        account = AccountConfig({
            'server': Settings.mt_server(),
            'username': Settings.mt_username(),
            'password': Settings.mt_password(),
            'path': Settings.mt_path(),
            'lot': Settings.mt_lot(),
            'HighRisk': Settings.mt_high_risk(),
            'SaveProfits': Settings.mt_save_profits(),
            'AccountSize': Settings.mt_account_size(),
            'CloserPrice': Settings.mt_closer_price(),
            'expirePendinOrderInMinutes': Settings.mt_expire_pending_orders_minutes(),
            'ClosePositionsOnTrail': Settings.mt_close_positions_on_trail(),
            'disableCache': Settings.mt_disable_cache(),
            'SymbolMappings': Settings.mt_symbol_mappings()
        })

        # Create tasks for all accounts
        tasks = []
        mt = MetaTrader(
            path=account.path,
            server=account.server,
            user=account.username,
            password=account.password,
            saveProfits=account.SaveProfits,
            closePositionsOnTrail=account.close_positions_on_trail,
        )
        tasks.append(mt.monitor_account())

        await asyncio.gather(*tasks)

    async def monitor_account(self):
        """Main async monitoring loop for a single account"""
        logger.info(f"Starting position monitoring for account {self.connection.user}")

        while True:  # Keep trying to reconnect
            try:
                # Initial login/reconnect
                # if mt5.terminal_info() is None:
                if not self.connection.login():
                    logger.error(f"Failed to login to {self.connection.server}, retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    continue

                # Main monitoring loop
                while True:
                    # Check connection status periodically
                    # if mt5.terminal_info() is None:
                    #     logger.warning(f"Connection lost to {self.connection.server}, reconnecting...")
                    #     break  # Break inner loop to reconnect

                    # Get and process positions
                    self.trailing()
                    self.manage_positions()

                    # Async sleep to maintain event loop
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Monitoring error on {self.connection.server}: {e}")
                await asyncio.sleep(5)

    def trailing(self):
        """Implement trailing stop logic with optimizations"""
        positions = self.market_data.get_open_positions()

        # Skip if no positions to process
        if not positions:
            return

        for position in positions:
            signal = Database.Migrations.get_signal_by_positionId(
                position.ticket)
            if signal is None:
                continue

            # get entry price
            if signal["second_price"] is not None:
                signal_position = Database.Migrations.get_position_by_signal_id(
                    signal["id"], second=True)
                if signal_position and signal_position is not None:
                    entry_price = signal["second_price"]
            else:
                signal_position = Database.Migrations.get_position_by_signal_id(
                    signal["id"], first=True)
                if signal_position and signal_position is not None:
                    entry_price = signal["open_price"]
            if signal_position is not None:
                pos = self.market_data.get_position_or_order(
                    ticket_id=signal_position["position_id"])
                if pos is not None:
                    entry_price = pos.price_open

            ticket = position.ticket
            lots = position.volume
            stop_loss = position.sl
            trade_type = position.type
            symbol = position.symbol

            tp_levels = Database.Migrations.get_tp_levels(ticket)
            if not tp_levels or len(tp_levels) == 1:
                continue

            current_price = self.market_data.get_current_price(symbol)
            if not current_price:
                continue

            tp_levels_buy = sorted(map(float, tp_levels))
            tp_levels_sell = sorted(map(float, tp_levels), reverse=True)

            # Check if price reached take profit level (minimize logging in monitoring loop)
            if trade_type == 0:  # Buy position
                for i, tp in enumerate(tp_levels_buy):
                    if current_price >= tp and stop_loss < tp:
                        new_stop_loss = tp_levels_buy[i - 1] if i > 0 else entry_price
                        if self.position_manager.update_stop_loss(ticket, new_stop_loss):
                            self.position_manager.save_profit_position(ticket, i, self.save_profits, self.close_positions_on_trail)
                            break  # Only process first reached TP level
            elif trade_type == 1:  # Sell position
                for i, tp in enumerate(tp_levels_sell):
                    if current_price <= tp and stop_loss > tp:
                        new_stop_loss = tp_levels_sell[i - 1] if i > 0 else entry_price
                        if self.position_manager.update_stop_loss(ticket, new_stop_loss):
                            self.position_manager.save_profit_position(ticket, i, self.save_profits, self.close_positions_on_trail)
                            break  # Only process first reached TP level

    def manage_positions(self):
        """Manage pending orders and position execution with optimizations"""
        pending_orders = self.market_data.get_pending_orders()

        # Skip if no pending orders
        if not pending_orders:
            return

        for order in pending_orders:
            position_id = order.ticket
            position_type = order.type  # Buy = 0, Sell = 1
            symbol = order.symbol

            tp_levels = Database.Migrations.get_tp_levels(position_id)
            if tp_levels is None:
                continue

            tp_levels_buy = sorted(map(float, tp_levels))
            tp_levels_sell = sorted(map(float, tp_levels), reverse=True)

            current_price = self.market_data.get_current_price(symbol)

            # Check if pending order should be activated or cancelled
            if ((position_type == mt5.ORDER_TYPE_BUY_STOP or position_type == mt5.ORDER_TYPE_BUY_LIMIT) and current_price >= tp_levels_buy[0]) or \
               ((position_type == mt5.ORDER_TYPE_SELL_LIMIT or position_type == mt5.ORDER_TYPE_SELL_STOP) and current_price <= tp_levels_sell[0]):

                # Check if one of the positions has already been executed
                positions = Database.Migrations.get_signal_positions_by_positionId(position_id)
                signal = Database.Migrations.get_signal_by_positionId(position_id)

                if len(positions) <= 1:
                    continue

                # Cancel pending order if no second entry price or position already executed
                if signal['second_price'] is None or signal['second_price'] == 0:
                    logger.info(f"Cancelling pending order {position_id} - no second entry needed")
                    self.position_manager.close_position(position_id)
                    continue

                # Check if first position exists
                position = self.market_data.get_open_positions(positions[0]['position_id'])
                if position is None and len(positions) == 2:
                    position = self.market_data.get_open_positions(positions[1]['position_id'])

                if position is None:
                    continue

                logger.info(f"Cancelling pending order {position_id} - first position already active")
                self.position_manager.close_position(position_id)