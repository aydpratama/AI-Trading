"""Test MT5 Connection"""
import sys
import os

# Change to backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("MT5 Connection Test")
print("=" * 50)

try:
    import MetaTrader5 as mt5
    print(f"✅ MT5 module imported successfully")
    print(f"   MT5 version: {mt5.__version__}")
    print(f"   Python: {sys.executable}")
    print()
    
    # Path ke MT5 Terminal
    mt5_path = r"C:\Program Files\Dupoin Futures MT5 Terminal\terminal64.exe"
    print(f"MT5 Path: {mt5_path}")
    print(f"Path exists: {os.path.exists(mt5_path)}")
    print()
    
    # Initialize MT5
    print("Initializing MT5...")
    if not mt5.initialize(path=mt5_path):
        error = mt5.last_error()
        print(f"❌ MT5 initialize FAILED!")
        print(f"   Error code: {error[0]}")
        print(f"   Error message: {error[1]}")
        sys.exit(1)
    
    print("✅ MT5 initialized successfully!")
    print()
    
    # Login credentials
    login = 22622639
    password = "gaIG763268~"
    server = "DupoinFuturesID-Real"
    
    print(f"Attempting login: {login}@{server}")
    authorized = mt5.login(login, password, server)
    
    if not authorized:
        error = mt5.last_error()
        print(f"❌ MT5 login FAILED!")
        print(f"   Error code: {error[0]}")
        print(f"   Error message: {error[1]}")
        mt5.shutdown()
        sys.exit(1)
    
    print("✅ MT5 logged in successfully!")
    print()
    
    # Get account info
    account = mt5.account_info()
    if account:
        print("=" * 50)
        print("Account Information:")
        print("=" * 50)
        print(f"  Login: {account.login}")
        print(f"  Server: {account.server}")
        print(f"  Balance: ${account.balance:.2f}")
        print(f"  Equity: ${account.equity:.2f}")
        print(f"  Margin: ${account.margin:.2f}")
        print(f"  Free Margin: ${account.margin_free:.2f}")
        print(f"  Profit: ${account.profit:.2f}")
        print(f"  Leverage: 1:{account.leverage}")
        print(f"  Currency: {account.currency}")
        print()
    
    # Get terminal info
    terminal = mt5.terminal_info()
    if terminal:
        print("Terminal Info:")
        print(f"  Company: {terminal.company}")
        print(f"  Name: {terminal.name}")
        print(f"  Path: {terminal.path}")
        print(f"  Connected: {terminal.connected}")
        print(f"  Trade Allowed: {terminal.trade_allowed}")
        print()
    
    # Test getting prices
    print("Testing market data...")
    tick = mt5.symbol_info_tick("EURUSD")
    if tick:
        print(f"✅ EURUSD Bid: {tick.bid}, Ask: {tick.ask}")
    else:
        print("⚠️ Could not get EURUSD prices")
    
    # Shutdown
    mt5.shutdown()
    print()
    print("=" * 50)
    print("✅ ALL TESTS PASSED!")
    print("=" * 50)

except ImportError as e:
    print(f"❌ Failed to import MetaTrader5: {e}")
    print("   Make sure you installed: pip install MetaTrader5")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()