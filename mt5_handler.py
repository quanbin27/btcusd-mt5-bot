# ============================================================
# MT5 Handler – Connection & Order Management
# ============================================================
import MetaTrader5 as mt5
from datetime import datetime
import config


class MT5Handler:
    """Handles all interactions with the MetaTrader 5 terminal."""

    def __init__(self):
        self.connected = False
        self.symbol = config.SYMBOL
        self.magic = config.MAGIC_NUMBER
        self._login = None
        self._password = None
        self._server = None
        self._path = None

    # ── Connection ──────────────────────────────────────────
    def connect(self, login: int, password: str, server: str,
                path: str = "", symbol: str = "") -> tuple[bool, str]:
        """
        Initialize MT5 and login.
        Returns (success, message).
        """
        if symbol:
            self.symbol = symbol

        kwargs = {}
        if path:
            kwargs["path"] = path

        if not mt5.initialize(**kwargs):
            err = mt5.last_error()
            return False, f"MT5 initialize failed: {err}"

        auth = mt5.login(login=login, password=password, server=server)
        if not auth:
            err = mt5.last_error()
            mt5.shutdown()
            return False, f"MT5 login failed: {err}"

        # Make sure symbol is visible
        info = mt5.symbol_info(self.symbol)
        if info is None:
            mt5.shutdown()
            return False, f"Symbol '{self.symbol}' not found"
        if not info.visible:
            if not mt5.symbol_select(self.symbol, True):
                mt5.shutdown()
                return False, f"Failed to select symbol '{self.symbol}'"

        self.connected = True
        self._login = login
        self._password = password
        self._server = server
        self._path = path or ""
        return True, f"Connected – Account #{login} | {server} | {self.symbol}"

    def disconnect(self):
        """Shutdown MT5 connection."""
        if self.connected:
            mt5.shutdown()
            self.connected = False

    def reconnect(self) -> bool:
        """Try to reconnect using stored credentials."""
        if not self._login:
            return False
        try:
            mt5.shutdown()
            kwargs = {}
            if self._path:
                kwargs["path"] = self._path
            if not mt5.initialize(**kwargs):
                return False
            if not mt5.login(login=self._login, password=self._password,
                             server=self._server):
                return False
            mt5.symbol_select(self.symbol, True)
            self.connected = True
            return True
        except Exception:
            return False

    # ── Market Data ─────────────────────────────────────────
    def get_current_price(self) -> float | None:
        """Return current bid price for the symbol."""
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None:
            return None
        return tick.bid

    def get_candles(self, count: int = 100):
        """
        Return last `count` M15 candles as list of dicts.
        Each dict: {time, open, high, low, close, volume}
        """
        tf = mt5.TIMEFRAME_M15
        rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, count)
        if rates is None or len(rates) == 0:
            return []

        candles = []
        for r in rates:
            candles.append({
                "time": datetime.fromtimestamp(r["time"]),
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": float(r["tick_volume"]),
            })
        return candles

    def get_symbol_digits(self) -> int:
        """Return number of decimal digits for the symbol."""
        info = mt5.symbol_info(self.symbol)
        return info.digits if info else 2

    def get_filling_type(self):
        """Return filling type cho Sell Limit.
        Dùng RETURN: nếu partial fill → phần còn lại tiếp tục chờ.
        """
        return mt5.ORDER_FILLING_RETURN

    # ── Order Management ────────────────────────────────────
    def place_sell_limit(self, volume: float, price: float,
                         sl: float, tp: float) -> tuple[bool, str]:
        """
        Place a SELL LIMIT pending order.
        Returns (success, message).
        """
        digits = self.get_symbol_digits()
        price = round(price, digits)
        sl = round(sl, digits)
        tp = round(tp, digits)

        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": self.symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_SELL_LIMIT,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": config.DEVIATION,
            "magic": self.magic,
            "comment": "BTC_Sell_Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": self.get_filling_type(),
        }

        result = mt5.order_send(request)
        if result is None:
            return False, f"order_send returned None – {mt5.last_error()}"
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return False, (f"Order failed retcode={result.retcode} "
                           f"comment={result.comment}")
        return True, f"Sell Limit placed @ {price} | ticket={result.order}"

    def cancel_all_pending(self) -> list[str]:
        """Cancel all pending orders for this symbol + magic number."""
        orders = mt5.orders_get(symbol=self.symbol)
        messages = []
        if orders is None:
            return messages

        for order in orders:
            if order.magic != self.magic:
                continue
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": order.ticket,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": self.get_filling_type(),
            }
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                messages.append(f"Cancelled order #{order.ticket}")
            else:
                rc = result.retcode if result else "None"
                messages.append(f"Failed cancel #{order.ticket} rc={rc}")
        return messages

    def cancel_order(self, ticket: int) -> tuple[bool, str]:
        """Cancel a single pending order by ticket."""
        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": ticket,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": self.get_filling_type(),
        }
        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            return True, f"Cancelled #{ticket}"
        rc = result.retcode if result else "None"
        return False, f"Failed cancel #{ticket} rc={rc}"

    def get_pending_orders(self) -> list:
        """Return list of pending orders for this symbol + magic."""
        orders = mt5.orders_get(symbol=self.symbol)
        if orders is None:
            return []
        return [o for o in orders if o.magic == self.magic]

    def get_open_positions(self) -> list:
        """Return list of open positions for this symbol + magic."""
        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None:
            return []
        return [p for p in positions if p.magic == self.magic]

    def has_tp_hit(self) -> bool:
        """
        Check if any position with our magic was closed by TP recently.
        We detect this by comparing pending orders vs positions.
        If we had pending orders + positions before and now positions are gone
        but pending orders remain, TP was hit.
        
        Simpler approach: if there are pending orders but no open positions,
        it means TP was hit (positions were closed).
        This is checked only AFTER orders have been placed.
        """
        positions = self.get_open_positions()
        return len(positions) == 0

    def check_filled_positions_tp(self) -> bool:
        """
        Check if we have any filled positions (from our sell limits).
        If some sell limits got filled but later closed (TP hit), 
        we return True to signal cleanup.
        """
        pending = self.get_pending_orders()
        positions = self.get_open_positions()

        # If we have pending orders but no positions, and we know 
        # some orders were filled before, then TP has been hit.
        # This logic will be driven by the bot engine state.
        return len(pending) > 0 and len(positions) == 0
