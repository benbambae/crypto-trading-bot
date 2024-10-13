import pandas as pd

# Simple Moving Average Strategy
def moving_average_strategy(data):
    short_window = 5  # Short moving average window
    long_window = 20  # Long moving average window

    # Calculate the short and long moving averages
    short_ma = data['close'].rolling(window=short_window).mean().iloc[-1]
    long_ma = data['close'].rolling(window=long_window).mean().iloc[-1]

    print(f"Short MA: {short_ma}, Long MA: {long_ma}")

    # Buy signal: when short MA crosses above long MA
    if short_ma > long_ma:
        return 'buy'
    # Sell signal: when short MA crosses below long MA
    elif short_ma < long_ma:
        return 'sell'
    else:
        return 'hold'