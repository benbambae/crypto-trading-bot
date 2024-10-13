import pandas as pd

def moving_average(data, short_window=50, long_window=200):
    """Implements the Moving Average strategy."""
    data['short_ma'] = data['close'].rolling(window=short_window).mean()
    data['long_ma'] = data['close'].rolling(window=long_window).mean()
    
    buy_signals = []
    sell_signals = []
    
    for i in range(len(data)):
        if data['short_ma'].iloc[i] > data['long_ma'].iloc[i]:
            buy_signals.append(data['close'].iloc[i])
            sell_signals.append(None)
        elif data['short_ma'].iloc[i] < data['long_ma'].iloc[i]:
            buy_signals.append(None)
            sell_signals.append(data['close'].iloc[i])
        else:
            buy_signals.append(None)
            sell_signals.append(None)
    
    return buy_signals, sell_signals

def rsi(data, window=14, buy_threshold=30, sell_threshold=70):
    """Implements the RSI strategy."""
    delta = data['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))
    
    buy_signals = []
    sell_signals = []
    
    for i in range(len(data)):
        if data['rsi'].iloc[i] < buy_threshold:
            buy_signals.append(data['close'].iloc[i])
            sell_signals.append(None)
        elif data['rsi'].iloc[i] > sell_threshold:
            buy_signals.append(None)
            sell_signals.append(data['close'].iloc[i])
        else:
            buy_signals.append(None)
            sell_signals.append(None)
    
    return buy_signals, sell_signals

def macd(data, short_window=12, long_window=26, signal_window=9):
    """Implements the MACD strategy."""
    data['macd'] = data['close'].ewm(span=short_window, adjust=False).mean() - data['close'].ewm(span=long_window, adjust=False).mean()
    data['signal'] = data['macd'].ewm(span=signal_window, adjust=False).mean()
    
    buy_signals = []
    sell_signals = []
    
    for i in range(len(data)):
        if data['macd'].iloc[i] > data['signal'].iloc[i]:
            buy_signals.append(data['close'].iloc[i])
            sell_signals.append(None)
        elif data['macd'].iloc[i] < data['signal'].iloc[i]:
            buy_signals.append(None)
            sell_signals.append(data['close'].iloc[i])
        else:
            buy_signals.append(None)
            sell_signals.append(None)
    
    return buy_signals, sell_signals
