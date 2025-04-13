# strategies.py

def eth_strategy(df):
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma50'] = df['close'].rolling(window=50).mean()
    df['volume_ma'] = df['volume'].rolling(window=20).mean()
    df['momentum'] = df['close'].diff(3)
    
    last = df.iloc[-1]
    return (
        last['ma20'] > last['ma50'],  # ma_cross
        last['volume'] > df['volume_ma'].iloc[-1] * 1.2,  # vol_spike
        last['momentum'] > 0,  # momentum_up
        last['close']
    )

def link_strategy(df):
    df['ema_fast'] = df['close'].ewm(span=5).mean()
    df['ema_slow'] = df['close'].ewm(span=13).mean()
    df['momentum'] = df['close'].diff(3)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    return (
        last['ema_fast'] > last['ema_slow'] and last['momentum'] > 0 and prev['ema_fast'] <= prev['ema_slow'],
        last['close'] < last['ema_slow'] or last['momentum'] < 0,
        last['close']
    )

def matic_strategy(df):
    df['ema_fast'] = df['close'].ewm(span=10).mean()
    df['ema_slow'] = df['close'].ewm(span=30).mean()
    df['momentum'] = df['close'] - df['close'].shift(3)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    return (
        last['ema_fast'] > last['ema_slow'] and last['momentum'] > 0 and prev['ema_fast'] <= prev['ema_slow'],
        last['momentum'] < 0 or last['close'] < last['ema_fast'],
        last['close']
    )

def doge_strategy(df):
    df['ma_20'] = df['close'].rolling(window=20).mean()
    df['ma_50'] = df['close'].rolling(window=50).mean()
    df['prev_close'] = df['close'].shift(1)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    return (
        last['ma_20'] > last['ma_50'] and last['close'] > prev['close'] * 1.03,
        last['close'] < last['ma_20'],
        last['close']
    )
