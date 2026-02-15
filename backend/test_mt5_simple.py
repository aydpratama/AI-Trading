import sys
import os

print("Python executable:", sys.executable)
print("Working directory:", os.getcwd())

try:
    import metaTrader5 as mt5
    print("MT5 module imported successfully")
    print("MT5 version:", mt5.__version__)
    
    # Try to initialize MT5 without specifying path
    result = mt5.initialize()
    print("MT5 initialize result:", result)
    print("MT5 connected:", mt5.connected())
    
    if result:
        account_info = mt5.account_info()
        print("Account info:", account_info)
        mt5.shutdown()
    else:
        print("Failed to initialize MT5")
        print("Error code:", mt5.last_error())
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
