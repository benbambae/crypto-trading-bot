import ccxt
import pandas as pd
import time
import yaml
import os

# Get the directory path of the project root
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')

# Load the config.yaml file
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# API setup using config data
binance = ccxt.binance({
    'apiKey': config['binance']['api_key'],
    'secret': config['binance']['secret_key'],
    'enableRateLimit': config['binance']['enable_rate_limit'],
})

# Function to fetch historical data (1-hour candles)
def fetch_ohlcv(symbol, timeframe='1h', limit=200):
    data = binance.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

# Simple Moving Average calculation
def moving_average(data, window):
    return data.rolling(window=window).mean()

# Basic trading strategy (MA Crossover)
def moving_average_crossover_strategy(symbol, short_window=10, long_window=30):
    df = fetch_ohlcv(symbol)
    df['SMA10'] = moving_average(df['close'], short_window)
    df['SMA30'] = moving_average(df['close'], long_window)

    # Simple Buy/Sell signal generation
    df['Signal'] = 0
    df.loc[short_window:, 'Signal'] = [1 if df['SMA10'].iloc[i] > df['SMA30'].iloc[i] else -1 for i in range(short_window, len(df))]
    df['Position'] = df['Signal'].diff()  # Track changes in signal
    # buy_signal=1, sell_signal=-1. When prices are rising, buy when trend upward. Prices falling, sell when trend is downward.

    # Print out recent buy/sell signals
    print(f"Latest data for {symbol}:")
    print(df[['timestamp', 'close', 'SMA10', 'SMA30', 'Signal', 'Position']].tail())

    # Simple decision-making based on last signal
    if df['Position'].iloc[-1] == 1:
        print(f"Buy signal for {symbol}")
    elif df['Position'].iloc[-1] == -1:
        print(f"Sell signal for {symbol}")
    else:
        print(f"No new signals for {symbol}")

def testcase_moving_average_crossover_strategy(symbol, short_window=10, long_window=30):
    df = fetch_ohlcv(symbol)
    df['SMA10'] = df['close'] + 1000  # Artificially increase SMA10 for a buy signal
    df['SMA30'] = df['close']

    df['Signal'] = 0
    df.loc[short_window:, 'Signal'] = [1 if df['SMA10'].iloc[i] > df['SMA30'].iloc[i] else -1 for i in range(short_window, len(df))]
    df['Position'] = df['Signal'].diff()

    # Print out recent buy/sell signals
    print(f"Latest data for {symbol}:")
    print(df[['timestamp', 'close', 'SMA10', 'SMA30', 'Signal', 'Position']].tail())

    # Force buy or sell signal for testing
    print(f"Buy signal for {symbol}") if df['Position'].iloc[-1] == 1 else print(f"Sell signal for {symbol}")

# Example usage
if __name__ == "__main__":
    symbol = 'BTC/USDT'
    moving_average_crossover_strategy(symbol)
