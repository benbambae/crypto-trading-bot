import pandas as pd

# Fetch market data using CCXT
def get_market_data(exchange, symbol):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h')  # 1-hour candles
    data = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return data
