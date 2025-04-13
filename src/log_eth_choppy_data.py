# log_eth_choppy_data.py

import pandas as pd
from binance.client import Client
import datetime
import os
import yaml

# Load API keys
with open("config/config.yaml", "r") as file:
    config = yaml.safe_load(file)

binance_api_key = config["binance"]["api_key"]
binance_api_secret = config["binance"]["secret_key"]

# Init client
client = Client(api_key=binance_api_key, api_secret=binance_api_secret)

# Settings
symbol = "ETHUSDT"
interval = Client.KLINE_INTERVAL_1HOUR

# Get ETH choppy durability strategy config
eth_periods = config["backtest"]["backtest_periods"]["ETH"]
eth_choppy_config = next(period for period in eth_periods if period["strategy"] == "eth_choppy_durability")
start_str = eth_choppy_config["start_date"] 
end_str = eth_choppy_config["end_date"]

# Fetch historical kline data
klines = client.get_historical_klines(symbol, interval, start_str, end_str)

# Parse to DataFrame
df = pd.DataFrame(klines, columns=[
    "timestamp", "open", "high", "low", "close", "volume",
    "close_time", "quote_asset_volume", "num_trades", 
    "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
])

# Convert types
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)

# Trim to only needed columns
df = df[["timestamp", "open", "high", "low", "close", "volume"]]

# Save to CSV
os.makedirs("export", exist_ok=True)
csv_path = "export/eth_choppy_durability_data.csv"
df.to_csv(csv_path, index=False)

print(f"Saved ETH choppy data to {csv_path}")
