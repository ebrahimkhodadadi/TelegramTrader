import math
import MetaTrader5 as mt5
from loguru import logger


class PositionManager:
    """Handles position operations like closing, modifying, and profit taking"""

    def __init__(self, market_data, magic_number=2025):
        self.market_data = market_data
        self.magic = magic_number

    def close_position(self, ticket):
        """Close a position or cancel a pending order"""
        logger.info(f"Attempting to close ticket {ticket}")

        position = self.market_data.get_open_positions(ticket)
        action = mt5.TRADE_ACTION_DEAL

        # If no open position found, check for pending orders
        if position is None:
            position = self.market_data.get_pending_orders(ticket)
            action = mt5.TRADE_ACTION_REMOVE

        if position is None:
            logger.warning(f"Position/order {ticket} not found")
            return False

        symbol = position.symbol
        volume = position.volume if hasattr(position, "volume") else position.volume_current

        # Initialize request
        request = {
            "action": action,
            "magic": self.magic,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        if action == mt5.TRADE_ACTION_DEAL:
            # Handle closing an open position
            if position.type not in [mt5.POSITION_TYPE_BUY, mt5.POSITION_TYPE_SELL]:
                logger.error(f"Invalid position type for ticket {ticket}")
                return False

            # Determine closing direction and price
            if position.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL  # Sell to close buy
                price = mt5.symbol_info_tick(symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY   # Buy to close sell
                price = mt5.symbol_info_tick(symbol).ask

            # Validate tick data
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error(f"Failed to get tick data for {symbol}")
                return False
            price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask

            # Build request for closing position
            request.update({
                "symbol": symbol,
                "volume": volume,
                "price": price,
                "deviation": 10,
                "type": order_type,
                "position": ticket
            })

            logger.info(f"Closing position {ticket}: {symbol} {volume} lots at {price}")
        else:
            # Handle removing a pending order
            request.update({"order": ticket})
            logger.info(f"Cancelling pending order {ticket}: {symbol}")

        # Send the request
        result = mt5.order_send(request)

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Failed to close/cancel {ticket}: {result.comment}")
            return False

        logger.success(f"Successfully closed/cancelled ticket {ticket}")
        return True

    def close_half_position(self, ticket):
        """Close half of the position volume"""
        position = self.market_data.get_open_positions(ticket)
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
                # "comment": "Closing half position",
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
        # else:
        #     self.close_position(ticket)

    def save_profit_position(self, ticket, index, save_profits=None):
        """Save profit of the position volume"""
        position = self.market_data.get_open_positions(ticket)
        if (position is None):
            return

        new_lot_size = None
        if save_profits is not None and len(save_profits) != 0 and save_profits[index]:
            new_lot_size = round(
                position.volume * (save_profits[index] / 100), 2)

        if new_lot_size == None or new_lot_size == 0:
            logger.critical("There is no strategy to save profit of volume.")
            return

        logger.warning(
            f"new lot size to save {save_profits[index]}% profit of {ticket} is {new_lot_size}")

                #close whole position

        if save_profits[index] == 100:
            self.close_position(ticket)
            return

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
                # "comment": "Closing half position",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(request)
            logger.info(f"{result}")
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Failed to save profit position for {
                              position.symbol}: {result.comment}")
                return False
            else:
                logger.success(f"Successfully saved profit position for {
                                position.symbol}, ticket {ticket}")
        else:
            self.close_position(ticket)

    def update_stop_loss(self, ticket, new_stop_loss):
        """
        Updates stop loss for either an open position or a pending order.
        Automatically detects the type and applies the correct request.
        """
        # Try to find active position first
        position = mt5.positions_get(ticket=ticket)
        if position and len(position) > 0:
            position = position[0]
            symbol_info = mt5.symbol_info(position.symbol)
            if not symbol_info:
                logger.error(f"Symbol info not found for {position.symbol}")
                return False

            digits = symbol_info.digits
            new_stop_loss = round(new_stop_loss, digits)

            if position.sl == new_stop_loss:
                return False  # Already at target SL

            logger.info(f"Updating stop loss for position {ticket} to {new_stop_loss}")

            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "symbol": position.symbol,
                "sl": float(new_stop_loss),
                "tp": position.tp,
                "magic": position.magic,
                "deviation": 10
            }

        else:
            # If not a position, check for pending order
            order = mt5.orders_get(ticket=ticket)
            if not order or len(order) == 0:
                logger.warning(f"Ticket {ticket} not found as position or order")
                return False

            order = order[0]
            symbol_info = mt5.symbol_info(order.symbol)
            if not symbol_info:
                logger.error(f"Symbol info not found for {order.symbol}")
                return False

            digits = symbol_info.digits
            new_stop_loss = round(new_stop_loss, digits)

            if order.sl == new_stop_loss:
                return False  # Already at target SL

            logger.info(f"Updating stop loss for pending order {ticket} to {new_stop_loss}")

            request = {
                "action": mt5.TRADE_ACTION_MODIFY,
                "order": ticket,
                "symbol": order.symbol,
                "price": order.price_open,
                "sl": float(new_stop_loss),
                "tp": order.tp,
                "type_time": order.type_time,
                "type_filling": order.type_filling
            }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Failed to update stop loss for ticket {ticket}: {result.comment}")
            return False
        else:
            logger.success(f"Stop loss updated successfully for ticket {ticket} to {new_stop_loss}")
            return True