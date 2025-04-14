import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import time
import os
import yaml

# Load config file
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Create a directory to store CSV files if it doesn't exist
data_dir = "crypto_data"  # Set default data directory
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

def get_historical_klines(symbol, interval, start_date, end_date=None):
    """
    Get historical klines (candlestick data) for a specific symbol and time interval.
    
    Parameters:
    - symbol (str): Trading pair symbol (e.g., 'ETHUSDT')
    - interval (str): Kline interval (e.g., '1h', '4h', '1d')
    - start_date (str): Start date in 'YYYY-MM-DD' format
    - end_date (str): End date in 'YYYY-MM-DD' format (optional)
    
    Returns:
    - pandas.DataFrame: OHLCV data
    """
    # Convert date strings to timestamps
    start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
    
    if end_date:
        end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
    else:
        end_ts = int(datetime.now().timestamp() * 1000)
    
    url = 'https://api.binance.com/api/v3/klines'
    
    # Initialize an empty list to store all klines
    all_klines = []
    
    # Binance API limit is 1000 candles per request
    # We need to make multiple requests for long time ranges
    while start_ts < end_ts:
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_ts,
            'endTime': end_ts,
            'limit': 1000
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise exception for bad status codes
            data = response.json()
            
            if not data:
                break
            
            all_klines.extend(data)
            
            # Update start_ts for the next request
            start_ts = data[-1][0] + 1
            
            # To avoid hitting rate limits
            time.sleep(1)  # Increased delay to avoid rate limiting
            
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            time.sleep(5)  # Wait longer on error before retrying
            continue
    
    if not all_klines:
        raise ValueError(f"No data retrieved for {symbol}")
        
    # Convert to DataFrame
    columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 
               'close_time', 'quote_asset_volume', 'number_of_trades',
               'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
    
    df = pd.DataFrame(all_klines, columns=columns)
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Convert numeric columns to appropriate types
    numeric_cols = ['open', 'high', 'low', 'close', 'volume', 
                    'quote_asset_volume', 'taker_buy_base_asset_volume', 
                    'taker_buy_quote_asset_volume']
    
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)
    
    # Select only OHLCV columns
    ohlcv_df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    ohlcv_df = ohlcv_df.rename(columns={'timestamp': 'date'})
    
    return ohlcv_df

def fetch_and_save(coin, timeframe, start_date, end_date, description=""):
    """
    Fetch data for a coin and save it to a CSV file with a logical name.
    
    Parameters:
    - coin (str): Coin symbol (e.g., 'ETH')
    - timeframe (str): Timeframe for the data (e.g., '1h', '4h', '1d')
    - start_date (str): Start date in 'YYYY-MM-DD' format
    - end_date (str): End date in 'YYYY-MM-DD' format
    - description (str): Additional description for the file name
    """
    symbol = f"{coin}USDT"
    
    try:
        df = get_historical_klines(symbol, timeframe, start_date, end_date)
        
        # Ensure the crypto_data directory exists
        os.makedirs("crypto_data", exist_ok=True)
        
        # Create a logical file name
        if description:
            file_name = f"crypto_data/{coin}_{timeframe}_{start_date}_to_{end_date}_{description}.csv"
        else:
            file_name = f"crypto_data/{coin}_{timeframe}_{start_date}_to_{end_date}.csv"
        
        # Save to CSV
        df.to_csv(file_name, index=False)
        print(f"Successfully saved {file_name}")
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        # Add a delay before retrying the next coin
        time.sleep(5)

# Define coins
coins = ["ETH", "LINK", "DOGE", "ARB"]

# Create a function to handle the data fetching with retries
def fetch_with_retry(coin, timeframe, start_date, end_date, description="", max_retries=3):
    for attempt in range(max_retries):
        try:
            fetch_and_save(coin, timeframe, start_date, end_date, description)
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {coin}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(10)  # Wait before retrying
            else:
                print(f"Failed to fetch data for {coin} after {max_retries} attempts")
                return False

# 1. All coins from 09 April to 13 April 2025 (After Donald Trump tariff) with 1h timeframe
for coin in coins:
    fetch_with_retry(coin, "1h", "2025-04-09", "2025-04-13", "post_tariff")

# 2. All coins from 08 March to 08 April 2025 (Before Donald Trump tariff) with 1h timeframe
for coin in coins:
    fetch_with_retry(coin, "1h", "2025-03-08", "2025-04-08", "pre_tariff")

# 3. Individual coin-specific timeframes
# ETH
fetch_with_retry("ETH", "1h", "2023-10-01", "2024-03-01")
fetch_with_retry("ETH", "4h", "2022-05-01", "2022-12-01")
fetch_with_retry("ETH", "1d", "2021-07-01", "2021-11-01")

# LINK
fetch_with_retry("LINK", "1h", "2023-06-01", "2023-12-01")
fetch_with_retry("LINK", "4h", "2022-03-01", "2022-09-01")
fetch_with_retry("LINK", "1d", "2021-01-01", "2021-05-01")

# ARB
fetch_with_retry("ARB", "1h", "2023-03-01", "2023-06-01")
fetch_with_retry("ARB", "4h", "2023-06-01", "2024-01-30")
fetch_with_retry("ARB", "1h", "2024-02-01", "2024-06-01")

# DOGE
fetch_with_retry("DOGE", "1h", "2023-10-01", "2023-12-01")
fetch_with_retry("DOGE", "4h", "2021-04-01", "2021-06-01")
fetch_with_retry("DOGE", "1d", "2022-11-01", "2023-02-01")

print("All data has been successfully retrieved and saved to CSV files in the 'crypto_data' directory.")