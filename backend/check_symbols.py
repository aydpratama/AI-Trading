"""Check available symbols in MT5"""
import sys
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import MetaTrader5 as mt5

print("=" * 60)
print("CHECKING AVAILABLE SYMBOLS IN MT5")
print("=" * 60)

# Connect to MT5
mt5_path = r"C:\Program Files\Dupoin Futures MT5 Terminal\terminal64.exe"
if not mt5.initialize(path=mt5_path):
    print(f"Failed to initialize MT5: {mt5.last_error()}")
    sys.exit(1)

# Login
if not mt5.login(22622639, "gaIG763268~", "DupoinFuturesID-Real"):
    print(f"Failed to login: {mt5.last_error()}")
    mt5.shutdown()
    sys.exit(1)

print("Connected to MT5!\n")

# Get all symbols
symbols = mt5.symbols_get()
print(f"Total symbols: {len(symbols)}")
print()

# Filter for common forex pairs
forex_keywords = ['EUR', 'USD', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF', 'XAU', 'XAG', 'GOLD', 'SILVER']

print("=" * 60)
print("FOREX & METALS SYMBOLS:")
print("=" * 60)

count = 0
for s in symbols:
    name_upper = s.name.upper()
    # Check if it contains any forex keyword
    for keyword in forex_keywords:
        if keyword in name_upper:
            print(f"  {s.name:20} | {s.description[:40]:40} | Digits: {s.digits}")
            count += 1
            break

print(f"\nTotal forex/metals symbols found: {count}")

# Try to find EURUSD specifically
print("\n" + "=" * 60)
print("SEARCHING FOR EURUSD VARIANTS:")
print("=" * 60)

for s in symbols:
    if 'EUR' in s.name.upper() and 'USD' in s.name.upper():
        print(f"  {s.name:20} | {s.description[:40]:40}")

# Try to get tick for common symbols
print("\n" + "=" * 60)
print("TESTING TICK DATA FOR COMMON SYMBOLS:")
print("=" * 60)

test_symbols = ['EURUSD', 'EURUSD.f', 'EURUSDc', 'EURUSD.ecn', 'GBPUSD', 'GBPUSD.f', 
                'XAUUSD', 'XAUUSD.f', 'GOLD', 'BTCUSD', 'BTC']

for sym in test_symbols:
    tick = mt5.symbol_info_tick(sym)
    if tick:
        print(f"  ✅ {sym:15} | Bid: {tick.bid} | Ask: {tick.ask}")
    else:
        # Try to find similar
        for s in symbols:
            if sym.replace('.', '').replace(' ', '').lower() in s.name.replace('.', '').replace(' ', '').lower():
                tick = mt5.symbol_info_tick(s.name)
                if tick:
                    print(f"  ✅ {s.name:15} (similar to {sym}) | Bid: {tick.bid}")
                break

mt5.shutdown()
print("\nDone!")