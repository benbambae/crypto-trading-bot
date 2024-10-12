import ccxt
import pandas as pd
import time
import yaml
import os
import csv

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

# Ensure the 'data' folder exists
data_folder = os.path.join(os.path.dirname(__file__), 'data')
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

# Function to get price data
def get_price_data(symbol, interval, limit=100):
    # Fetches OHLCV data (Open, High, Low, Close, Volume)
    timeframe = interval
    data = binance.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    return data

# Save data to CSV inside 'data' folder
def save_to_csv(filename, data):
    filepath = os.path.join(data_folder, filename)
    with open(filepath, mode='a', newline='') as file:
        writer = csv.writer(file)
        for row in data:
            writer.writerow(row)

# Collect data continuously
def collect_price_data(symbol, interval, filename, duration):
    start_time = time.time()
    while time.time() - start_time < duration:
        data = get_price_data(symbol, interval)
        save_to_csv(filename, data)
        print(f"Collected and saved {len(data)} rows")
        time.sleep(60)  # Collect data every minute

# Example usage
collect_price_data('BTC/USDT', '1m', 'price_data.csv', 3600)  # Collect for 1 hour
