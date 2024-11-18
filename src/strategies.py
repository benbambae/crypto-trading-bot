import pandas as pd
import numpy as np

def moving_average(data, short_window=50, long_window=200):
    """Implements the Moving Average strategy with additional validation."""
    data['short_ma'] = data['close'].rolling(window=short_window).mean()
    data['long_ma'] = data['close'].rolling(window=long_window).mean()
    
    # Add volume weighted moving average for confirmation
    data['vwma'] = (data['close'] * data['volume']).rolling(window=short_window).sum() / data['volume'].rolling(window=short_window).sum()
    
    buy_signals = []
    sell_signals = []
    
    for i in range(len(data)):
        # Buy when short MA crosses above long MA and price is above VWMA
        if (data['short_ma'].iloc[i] > data['long_ma'].iloc[i] and 
            data['close'].iloc[i] > data['vwma'].iloc[i]):
            buy_signals.append(data['close'].iloc[i])
            sell_signals.append(None)
        # Sell when short MA crosses below long MA or price drops below VWMA    
        elif (data['short_ma'].iloc[i] < data['long_ma'].iloc[i] or
              data['close'].iloc[i] < data['vwma'].iloc[i]):
            buy_signals.append(None)
            sell_signals.append(data['close'].iloc[i])
        else:
            buy_signals.append(None)
            sell_signals.append(None)
    
    return buy_signals, sell_signals

def rsi(data, window=14, buy_threshold=30, sell_threshold=70):
    """Implements the RSI strategy with trend confirmation."""
    # Calculate RSI
    delta = data['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))
    
    # Add trend indicator (20-period EMA)
    data['trend'] = data['close'].ewm(span=20, adjust=False).mean()
    
    buy_signals = []
    sell_signals = []
    
    for i in range(len(data)):
        # Buy when RSI is oversold and price is above trend
        if (data['rsi'].iloc[i] < buy_threshold and 
            data['close'].iloc[i] > data['trend'].iloc[i]):
            buy_signals.append(data['close'].iloc[i])
            sell_signals.append(None)
        # Sell when RSI is overbought or price drops below trend    
        elif (data['rsi'].iloc[i] > sell_threshold or
              data['close'].iloc[i] < data['trend'].iloc[i]):
            buy_signals.append(None)
            sell_signals.append(data['close'].iloc[i])
        else:
            buy_signals.append(None)
            sell_signals.append(None)
    
    return buy_signals, sell_signals

def macd(data, short_window=12, long_window=26, signal_window=9):
    """Implements the MACD strategy with histogram and volume confirmation."""
    # Calculate MACD
    data['macd'] = data['close'].ewm(span=short_window, adjust=False).mean() - data['close'].ewm(span=long_window, adjust=False).mean()
    data['signal'] = data['macd'].ewm(span=signal_window, adjust=False).mean()
    data['histogram'] = data['macd'] - data['signal']
    
    # Add volume confirmation
    data['vol_ma'] = data['volume'].rolling(window=20).mean()
    
    buy_signals = []
    sell_signals = []
    
    for i in range(len(data)):
        # Buy when MACD crosses above signal with increasing histogram and above average volume
        if (data['macd'].iloc[i] > data['signal'].iloc[i] and
            data['histogram'].iloc[i] > data['histogram'].iloc[i-1] and
            data['volume'].iloc[i] > data['vol_ma'].iloc[i]):
            buy_signals.append(data['close'].iloc[i])
            sell_signals.append(None)
        # Sell when MACD crosses below signal or histogram starts decreasing    
        elif (data['macd'].iloc[i] < data['signal'].iloc[i] or
              data['histogram'].iloc[i] < data['histogram'].iloc[i-1]):
            buy_signals.append(None)
            sell_signals.append(data['close'].iloc[i])
        else:
            buy_signals.append(None)
            sell_signals.append(None)
    
    return buy_signals, sell_signals

def bollinger_bands(data, window=20, num_std=2):
    """Implements Bollinger Bands strategy."""
    # Calculate Bollinger Bands
    data['bb_middle'] = data['close'].rolling(window=window).mean()
    data['bb_std'] = data['close'].rolling(window=window).std()
    data['bb_upper'] = data['bb_middle'] + (data['bb_std'] * num_std)
    data['bb_lower'] = data['bb_middle'] - (data['bb_std'] * num_std)
    
    buy_signals = []
    sell_signals = []
    
    for i in range(len(data)):
        # Buy when price touches lower band and starts moving up
        if (data['close'].iloc[i] <= data['bb_lower'].iloc[i] and
            data['close'].iloc[i] > data['close'].iloc[i-1]):
            buy_signals.append(data['close'].iloc[i])
            sell_signals.append(None)
        # Sell when price touches upper band and starts moving down    
        elif (data['close'].iloc[i] >= data['bb_upper'].iloc[i] and
              data['close'].iloc[i] < data['close'].iloc[i-1]):
            buy_signals.append(None)
            sell_signals.append(data['close'].iloc[i])
        else:
            buy_signals.append(None)
            sell_signals.append(None)
            
    return buy_signals, sell_signals
