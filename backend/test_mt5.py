import metaTrader5 as mt5

print("MT5 version:", mt5.__version__)
result = mt5.initialize()
print("Initialize result:", result)
print("Connected:", mt5.connected())

if result:
    account_info = mt5.account_info()
    print("Account:", account_info)
    mt5.shutdown()
else:
    print("Failed to initialize MT5")
