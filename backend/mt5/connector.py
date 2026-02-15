"""MT5 Connection Manager"""
import MetaTrader5 as mt5
import logging
from typing import Optional, Dict, Any, List
from config import settings
from models.broker import update_connected_broker, clear_brokers

logger = logging.getLogger(__name__)


class MT5Connector:
    """Manages MT5 connection and authentication"""

    def __init__(self):
        self.connected = False
        # Symbol suffix for Dupoin Futures broker
        self.symbol_suffix = "u"
        self._current_broker_id = "primary"

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol name for broker (add suffix if needed)"""
        if not symbol:
            return symbol
        
        # Already has suffix
        if symbol.endswith(self.symbol_suffix):
            return symbol
        
        # Try with suffix first
        symbol_with_suffix = symbol + self.symbol_suffix
        if mt5.symbol_info(symbol_with_suffix) is not None:
            return symbol_with_suffix
        
        # Return original if suffix version not found
        return symbol

    def connect(self) -> bool:
        """Connect to MT5 terminal"""
        try:
            # Initialize MT5
            if not mt5.initialize(path=settings.MT5_PATH):
                logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                return False

            # Login
            authorized = mt5.login(
                settings.MT5_LOGIN,
                settings.MT5_PASSWORD,
                settings.MT5_SERVER
            )
            if not authorized:
                logger.error(f"MT5 login failed: {mt5.last_error()}")
                mt5.shutdown()
                return False

            self.connected = True
            
            # Register the connected broker
            clear_brokers()  # Clear any previous brokers
            update_connected_broker(
                broker_id=self._current_broker_id,
                name=settings.MT5_SERVER.split('-')[0],  # Extract broker name from server
                server=settings.MT5_SERVER
            )
            
            logger.info(f"✅ Connected to MT5: {settings.MT5_LOGIN}@{settings.MT5_SERVER}")
            return True

        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from MT5"""
        try:
            mt5.shutdown()
        except Exception:
            pass
        self.connected = False
        clear_brokers()
        logger.info("Disconnected from MT5")

    def switch_broker(self, login: int, password: str, server: str) -> bool:
        """Switch to a different broker account"""
        try:
            # Disconnect current session
            if self.connected:
                mt5.shutdown()
                self.connected = False
            
            # Initialize MT5
            if not mt5.initialize(path=settings.MT5_PATH):
                logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                return False

            # Login to new broker
            authorized = mt5.login(login, password, server)
            if not authorized:
                logger.error(f"MT5 login failed: {mt5.last_error()}")
                mt5.shutdown()
                return False

            self.connected = True
            self._current_broker_id = f"broker_{login}"
            
            # Register the new broker
            clear_brokers()
            update_connected_broker(
                broker_id=self._current_broker_id,
                name=server.split('-')[0],
                server=server
            )
            
            logger.info(f"✅ Switched to broker: {login}@{server}")
            return True

        except Exception as e:
            logger.error(f"Switch broker error: {e}")
            return False

    def is_connected(self) -> bool:
        """Check connection status - also verify MT5 is still alive"""
        if not self.connected:
            return False

        # Double check MT5 is actually responsive
        try:
            info = mt5.terminal_info()
            if info is None:
                logger.warning(f"MT5 terminal_info is None. Last error: {mt5.last_error()}")
                self.connected = False
                return False
        except Exception as e:
            logger.error(f"MT5 terminal_info exception: {e}")
            self.connected = False
            return False

        return True

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information"""
        if not self.connected:
            return None

        account = mt5.account_info()
        if account is None:
            return None

        return {
            "login": account.login,
            "balance": account.balance,
            "equity": account.equity,
            "margin": account.margin,
            "free_margin": account.margin_free,
            "profit": account.profit,
            "leverage": account.leverage,
            "server": account.server,
            "currency": account.currency
        }

    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information"""
        if not self.connected:
            return None

        # Normalize symbol for broker
        symbol = self._normalize_symbol(symbol)

        # Ensure symbol is visible in Market Watch
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            # Try to add symbol
            if not mt5.symbol_select(symbol, True):
                return None
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return None

        return self._symbol_info_to_dict(symbol_info)

    def _symbol_info_to_dict(self, symbol_info) -> Dict[str, Any]:
        """Convert MT5 symbol info to dictionary"""
        return {
            "name": symbol_info.name,
            "description": symbol_info.description,
            "digits": symbol_info.digits,
            "point": symbol_info.point,
            "trade_tick_size": symbol_info.trade_tick_size,
            "trade_tick_value": symbol_info.trade_tick_value,
            "trade_contract_size": symbol_info.trade_contract_size,
            "volume_min": symbol_info.volume_min,
            "volume_max": symbol_info.volume_max,
            "volume_step": symbol_info.volume_step,
            "spread": symbol_info.spread,
            "currency_base": symbol_info.currency_base,
            "currency_profit": symbol_info.currency_profit,
            "currency_margin": symbol_info.currency_margin,
            "price_precision": symbol_info.digits
        }

    def get_tick_price(self, symbol: str, side: str = "ask") -> Optional[float]:
        """Get current bid or ask price"""
        if not self.connected:
            return None

        # Normalize symbol for broker
        symbol = self._normalize_symbol(symbol)

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None

        if side == "bid":
            return tick.bid
        else:
            return tick.ask

    def get_candles(self, symbol: str, timeframe: str, count: int = 100) -> List[Dict[str, Any]]:
        """Get historical candles"""
        if not self.connected:
            return []

        # Normalize symbol for broker
        symbol = self._normalize_symbol(symbol)

        # Convert timeframe to MT5 format
        timeframe_map = {
            "1M": mt5.TIMEFRAME_M1,
            "5M": mt5.TIMEFRAME_M5,
            "15M": mt5.TIMEFRAME_M15,
            "30M": mt5.TIMEFRAME_M30,
            "1H": mt5.TIMEFRAME_H1,
            "4H": mt5.TIMEFRAME_H4,
            "1D": mt5.TIMEFRAME_D1
        }

        mt5_timeframe = timeframe_map.get(timeframe, mt5.TIMEFRAME_H1)

        # Ensure symbol is visible
        if not mt5.symbol_select(symbol, True):
            logger.warning(f"Failed to select symbol {symbol}")

        # Get candles
        rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)

        if rates is None or len(rates) == 0:
            logger.warning(f"No candles returned for {symbol} {timeframe}")
            return []

        # Convert to list of dictionaries
        # rates is a numpy structured array with named fields
        candles = []
        for rate in rates:
            candles.append({
                "time": int(rate[0]),     # time
                "open": float(rate[1]),   # open
                "high": float(rate[2]),   # high
                "low": float(rate[3]),    # low
                "close": float(rate[4]),  # close
                "volume": int(rate[5]),   # tick_volume -> volume
                "tick_volume": int(rate[5]),
                "real_volume": int(rate[7])
            })

        return candles

    def get_current_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get current bid and ask prices"""
        if not self.connected:
            return None

        # Normalize symbol for broker
        symbol = self._normalize_symbol(symbol)

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None

        return {
            "bid": tick.bid,
            "ask": tick.ask,
            "spread": tick.ask - tick.bid
        }

    def is_symbol_available(self, symbol: str) -> bool:
        """Check if symbol is available in MT5"""
        if not self.connected:
            return False

        # Normalize symbol for broker
        symbol = self._normalize_symbol(symbol)

        return mt5.symbol_info(symbol) is not None

    def get_all_symbols(self) -> List[Dict[str, Any]]:
        """Get all available symbols from MT5"""
        if not self.connected:
            return []

        # Get all symbols
        symbols = mt5.symbols_get()
        if symbols is None:
            logger.warning("Failed to get symbols from MT5")
            return []

        # Filter and categorize symbols
        result = []
        for sym in symbols:
            if not sym.visible:
                continue
            
            # Determine category based on symbol name
            name = sym.name
            category = self._categorize_symbol(name)
            
            symbol_data = {
                "name": name,
                "description": sym.description,
                "category": category,
                "digits": sym.digits,
                "point": sym.point,
                "spread": sym.spread,
                "currency_base": sym.currency_base,
                "currency_profit": sym.currency_profit,
                "currency_margin": sym.currency_margin,
                "volume_min": sym.volume_min,
                "volume_max": sym.volume_max,
                "volume_step": sym.volume_step,
                "trade_contract_size": sym.trade_contract_size,
                "visible": sym.visible,
                "select": sym.select
            }
            result.append(symbol_data)

        # Sort by category then name
        result.sort(key=lambda x: (x["category"], x["name"]))
        return result

    def _categorize_symbol(self, symbol: str) -> str:
        """Categorize symbol based on name"""
        symbol_upper = symbol.upper()
        
        # Forex pairs (6 characters like EURUSD, GBPUSD)
        if len(symbol_upper.replace("U", "").replace("T", "")) == 6 and any(c in symbol_upper for c in ["USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF"]):
            return "forex"
        
        # Gold/Silver
        if "XAU" in symbol_upper or "GOLD" in symbol_upper:
            return "metals"
        if "XAG" in symbol_upper or "SILVER" in symbol_upper:
            return "metals"
        
        # Indices
        if any(idx in symbol_upper for idx in ["US30", "US500", "US100", "DJ", "SPX", "NAS", "DE30", "DE40", "UK100", "JP225", "AU200", "EU50", "ES35", "FR40", "IT40"]):
            return "indices"
        
        # Crypto
        if any(crypto in symbol_upper for crypto in ["BTC", "ETH", "XRP", "LTC", "ADA", "DOGE", "BNB", "SOL"]):
            return "crypto"
        
        # Energy
        if any(energy in symbol_upper for energy in ["OIL", "WTI", "BRENT", "CRUDE", "XBR", "XTI", "GAS", "NG"]):
            return "energy"
        
        # Stocks
        if any(stock in symbol_upper for stock in ["AAPL", "GOOG", "MSFT", "AMZN", "TSLA", "META", "NVDA"]):
            return "stocks"
        
        return "other"

    def get_symbols_by_category(self, category: str = None) -> List[Dict[str, Any]]:
        """Get symbols filtered by category"""
        all_symbols = self.get_all_symbols()
        
        if category:
            return [s for s in all_symbols if s["category"] == category]
        
        return all_symbols

    def get_forex_pairs(self) -> List[str]:
        """Get list of available forex pairs (without suffix)"""
        all_symbols = self.get_all_symbols()
        forex_pairs = []
        
        for sym in all_symbols:
            if sym["category"] == "forex":
                # Remove suffix to get base pair name
                name = sym["name"]
                if name.endswith(self.symbol_suffix):
                    name = name[:-1]
                forex_pairs.append(name)
        
        return sorted(set(forex_pairs))


# Singleton instance
connector = MT5Connector()
