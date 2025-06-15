
# === Complex Strategies ===
from strategies import rsi_macd_pullback, hybrid_strategy, advanced_hybrid_strategy
# === Simple Strategies ===
def moving_average_strategy(data, short_window=50, long_window=200):
    data['short_ma'] = data['close'].rolling(window=short_window).mean()
    data['long_ma'] = data['close'].rolling(window=long_window).mean()

    buy_signals, sell_signals = [], []
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

def rsi_strategy(data, window=14, buy_threshold=30, sell_threshold=70):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))

    buy_signals, sell_signals = [], []
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

def macd_strategy(data, short=12, long=26, signal=9):
    data['ema_short'] = data['close'].ewm(span=short).mean()
    data['ema_long'] = data['close'].ewm(span=long).mean()
    data['macd'] = data['ema_short'] - data['ema_long']
    data['macd_signal'] = data['macd'].ewm(span=signal).mean()

    buy_signals, sell_signals = [], []
    for i in range(len(data)):
        if data['macd'].iloc[i] > data['macd_signal'].iloc[i]:
            buy_signals.append(data['close'].iloc[i])
            sell_signals.append(None)
        elif data['macd'].iloc[i] < data['macd_signal'].iloc[i]:
            buy_signals.append(None)
            sell_signals.append(data['close'].iloc[i])
        else:
            buy_signals.append(None)
            sell_signals.append(None)
    return buy_signals, sell_signals

# === Mid-Level ===
def bollinger_rsi(data, window=20, std=2):
    data['mid'] = data['close'].rolling(window).mean()
    data['std'] = data['close'].rolling(window).std()
    data['upper'] = data['mid'] + (data['std'] * std)
    data['lower'] = data['mid'] - (data['std'] * std)

    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))

    buy, sell = [], []
    for i in range(len(data)):
        if data['close'].iloc[i] < data['lower'].iloc[i] and data['rsi'].iloc[i] < 35:
            buy.append(data['close'].iloc[i])
            sell.append(None)
        elif data['close'].iloc[i] > data['upper'].iloc[i] or data['rsi'].iloc[i] > 65:
            buy.append(None)
            sell.append(data['close'].iloc[i])
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell


# === Strategy Assignments ===
STRATEGY_PLAN = {
    "ETH": {
        "1h": rsi_macd_pullback,
        "4h": hybrid_strategy,
        "1d": advanced_hybrid_strategy
    },
    "LINK": {
        "1h": moving_average_strategy,
        "4h": macd_strategy,
        "1d": bollinger_rsi
    },
    "MATIC": {
        "1h": macd_strategy,
        "4h": hybrid_strategy,
        "1d": moving_average_strategy
    },
    "DOGE": {
        "1h": rsi_strategy,
        "4h": bollinger_rsi,
        "1d": rsi_macd_pullback
    }
}
