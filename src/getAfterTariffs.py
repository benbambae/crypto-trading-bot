from binance.client import Client
import pandas as pd
import os
import yaml

# Load API keys from config file
with open('../config/config.yaml', 'r') as file:
    config = yaml.safe_load(file)
    api_key = config['binance']['test_api_key']
    api_secret = config['binance']['test_secret_key']

client = Client(api_key, api_secret)

# Create output folder if not exists
output_dir = os.path.join("data", "after_tariffs")
os.makedirs(output_dir, exist_ok=True)

def get_ohlcv(symbol, interval="1h", start="09 Apr, 2025", end="13 Apr, 2025"):
    klines = client.get_historical_klines(symbol, interval, start, end)
    
    df = pd.DataFrame(klines, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base_vol", "taker_buy_quote_vol", "ignore"
    ])
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    
    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

# Coin list
coins = ["ETHUSDT", "LINKUSDT", "ARBUSDT", "DOGEUSDT"]

# Fetch and save all
for coin in coins:
    symbol = coin
    df = get_ohlcv(symbol)
    coin_name = coin.replace("USDT", "")
    csv_path = os.path.join(output_dir, f"{coin_name}_OHLCV_0803_0904.csv")
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved {coin_name} data to {csv_path}")
