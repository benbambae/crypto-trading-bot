# data.py

import pandas as pd
from binance.client import Client
import dateparser
import pytz

def get_historical_data(symbol, start_date, end_date, interval):
    """
    Fetches historical candlestick data from Binance.

    Parameters:
    - symbol: Trading pair symbol, e.g., 'ETHUSDT'.
    - start_date: Start date in a string format, e.g., '6 months ago UTC'.
    - end_date: End date in a string format, e.g., 'now UTC'.
    - interval: Data interval, e.g., '1m', '1h', '1d'.

    Returns:
    - data: pandas DataFrame containing historical data.
    """
    client = Client()
    # Convert dates to milliseconds
    start_ts = int(dateparser.parse(start_date).timestamp() * 1000)
    end_ts = int(dateparser.parse(end_date).timestamp() * 1000)

    klines = client.get_historical_klines(symbol, interval, start_ts, end_ts)

    data = pd.DataFrame(klines, columns=[
        'Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume',
        'Close_Time', 'Quote_Asset_Volume', 'Number_of_Trades',
        'Taker_Buy_Base_Asset_Volume', 'Taker_Buy_Quote_Asset_Volume', 'Ignore'
    ])

    # Convert columns to appropriate data types
    data['Open_Time'] = pd.to_datetime(data['Open_Time'], unit='ms')
    data['Close_Time'] = pd.to_datetime(data['Close_Time'], unit='ms')
    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume',
                    'Quote_Asset_Volume', 'Number_of_Trades',
                    'Taker_Buy_Base_Asset_Volume', 'Taker_Buy_Quote_Asset_Volume']
    data[numeric_cols] = data[numeric_cols].apply(pd.to_numeric, axis=1)

    data.set_index('Close_Time', inplace=True)

    return data
