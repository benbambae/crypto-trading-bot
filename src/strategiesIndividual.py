# strategies.py

import pandas as pd
import numpy as np

# ===ARB Strategies ===


def arb_breakout_strategy(data):
    """
    Classic breakout strategy: Price breaking above recent resistance + volume spike.
    """
    data['high_20'] = data['high'].rolling(window=20).max()
    data['volume_ma'] = data['volume'].rolling(window=20).mean()

    buy, sell = [], []
    in_position = False

    for i in range(len(data)):
        if i < 20:
            buy.append(None)
            sell.append(None)
            continue

        price = data['close'].iloc[i]
        resistance = data['high_20'].iloc[i - 1]
        volume = data['volume'].iloc[i]

        if not in_position and price > resistance and volume > data['volume_ma'].iloc[i]:
            buy.append(price)
            sell.append(None)
            in_position = True
        elif in_position and price < resistance:
            buy.append(None)
            sell.append(price)
            in_position = False
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell
def arb_adx_trend_strategy(data):
    """Improved trend-following strategy using EMA cross and price momentum."""
    data['ema_fast'] = data['close'].ewm(span=10).mean()
    data['ema_slow'] = data['close'].ewm(span=30).mean()
    data['momentum'] = data['close'] - data['close'].shift(3)

    buy, sell, in_position = [], [], False
    for i in range(len(data)):
        if (
            data['ema_fast'][i] > data['ema_slow'][i] and
            data['momentum'][i] > 0 and not in_position
        ):
            buy.append(data['close'][i])
            sell.append(None)
            in_position = True
        elif in_position and (
            data['momentum'][i] < 0 or
            data['close'][i] < data['ema_fast'][i]
        ):
            sell.append(data['close'][i])
            buy.append(None)
            in_position = False
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell

def arb_consolidation_break_strategy(data):
    """
    Identifies consolidation (low volatility) then breakout via price + volume.
    """
    data['range'] = data['high'].rolling(window=10).max() - data['low'].rolling(window=10).min()
    data['range_avg'] = data['range'].rolling(window=10).mean()
    data['volume_ma'] = data['volume'].rolling(window=20).mean()

    buy, sell = [], []
    in_position = False

    for i in range(len(data)):
        if i < 20:
            buy.append(None)
            sell.append(None)
            continue

        low_volatility = data['range'].iloc[i] < data['range_avg'].iloc[i]
        volume_spike = data['volume'].iloc[i] > 1.2 * data['volume_ma'].iloc[i]
        price_break = data['close'].iloc[i] > data['close'].iloc[i - 1] * 1.02

        if not in_position and low_volatility and volume_spike and price_break:
            buy.append(data['close'].iloc[i])
            sell.append(None)
            in_position = True
        elif in_position and data['close'].iloc[i] < data['close'].iloc[i - 1]:
            buy.append(None)
            sell.append(data['close'].iloc[i])
            in_position = False
        else:
            buy.append(None)
            sell.append(None)

def arb_bull_trend_refined(df, trailing_sl_pct=0.03):
    df['ema_fast'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=26, adjust=False).mean()
    df['volume_avg'] = df['volume'].rolling(window=20).mean()

    buy, sell = [], []
    position = False
    entry_price = 0
    trailing_stop = 0

    for i in range(1, len(df)):
        if (df['ema_fast'].iloc[i] > df['ema_slow'].iloc[i] and 
            df['volume'].iloc[i] > df['volume_avg'].iloc[i] and 
            not position):
            position = True
            entry_price = df['close'].iloc[i]
            trailing_stop = entry_price * (1 - trailing_sl_pct)
            buy.append(entry_price)
            sell.append(None)
        elif position:
            trailing_stop = max(trailing_stop, df['close'].iloc[i] * (1 - trailing_sl_pct))
            if (df['close'].iloc[i] < trailing_stop or 
                df['ema_fast'].iloc[i] < df['ema_slow'].iloc[i]):
                position = False
                buy.append(None)
                sell.append(df['close'].iloc[i])
            else:
                buy.append(None)
                sell.append(None)
        else:
            buy.append(None)
            sell.append(None)

    # Add first entry
    buy.insert(0, None)
    sell.insert(0, None)

    return buy, sell


def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rs = rs.replace([np.inf, -np.inf], np.nan).fillna(0)  # prevent inf/nan errors
    rsi = 100 - (100 / (1 + rs))

    return rsi


def arb_oversold_bounce(df):
    try:
        print(">> calculating RSI")
        df['rsi'] = calculate_rsi(df['close'], period=14)
        print(">> setting signal")
        df['signal'] = 0
        df.loc[(df['rsi'] < 30) & (df['close'] > df['close'].shift(1)), 'signal'] = 1
        df.loc[(df['rsi'] > 50), 'signal'] = -1

        print(">> processing signals")
        actions = []
        in_position = False
        capital = 10000
        balance = capital
        position_size = 0
        entry_price = 0
        trades = []

        for i in range(len(df)):
            if df.loc[i, 'signal'] == 1 and not in_position:
                in_position = True
                entry_price = df.loc[i, 'close']
                position_size = balance / entry_price
                actions.append("BUY")
            elif df.loc[i, 'signal'] == -1 and in_position:
                in_position = False
                exit_price = df.loc[i, 'close']
                pnl = (exit_price - entry_price) * position_size
                balance += pnl
                trades.append(pnl)
                actions.append("SELL")
            elif in_position:
                actions.append("HOLD")
            else:
                actions.append("WAIT")

        print(">> finalizing metrics")
        df['action'] = actions

        final_capital = balance
        total_profit = final_capital - capital
        total_trades = len(trades)
        win_rate = round(sum(1 for t in trades if t > 0) / total_trades, 2) if total_trades else 0
        gross_profit = sum(t for t in trades if t > 0)
        gross_loss = abs(sum(t for t in trades if t < 0))
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss != 0 else float('inf')
        sharpe_ratio = round((np.mean(trades) / np.std(trades)) * np.sqrt(len(trades)), 2) if len(trades) > 1 and np.std(trades) > 0 else 0
        drawdown = 0

        metrics = {
            'final_capital': round(final_capital, 2),
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'drawdown': drawdown,
            'total_profit': round(total_profit, 2)
        }

        print(">> success")
        return df, metrics

    except Exception as e:
        import traceback
        print("❌ Exception:", str(e))
        traceback.print_exc()
        raise e

# === ETH Strategies ===
def eth_bull_trend(data):
    """Updated hybrid: RSI + MA crossover + volume filter."""
    data['rsi'] = data['close'].rolling(14).apply(
        lambda x: 100 - (100 / (1 + x.pct_change().mean()))
    )
    data['ma50'] = data['close'].rolling(50).mean()
    data['ma200'] = data['close'].rolling(200).mean()
    data['vol_ma'] = data['volume'].rolling(20).mean()

    buy, sell, in_position = [], [], False
    for i in range(len(data)):
        if (
            data['ma50'][i] > data['ma200'][i] and
            data['rsi'][i] < 50 and
            data['close'][i] > data['ma50'][i] and
            data['volume'][i] > data['vol_ma'][i] and not in_position
        ):
            buy.append(data['close'][i])
            sell.append(None)
            in_position = True
        elif in_position and (
            data['rsi'][i] > 65 or
            data['close'][i] < data['ma50'][i]
        ):
            sell.append(data['close'][i])
            buy.append(None)
            in_position = False
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell


def eth_choppy_durability(data):
    """
    Scalping breakout strategy for choppy ETH range.
    Detects small ranges, enters on tiny breakout.
    """
    data['range'] = data['high'].rolling(10).max() - data['low'].rolling(10).min()
    data['range_avg'] = data['range'].rolling(20).mean()
    data['volatility'] = data['close'].pct_change().rolling(5).std()
    data['volatility_ma'] = data['volatility'].rolling(10).mean()

    buy, sell = [], []
    in_position = False
    entry_price = 0

    for i in range(len(data)):
        if i < 20:
            buy.append(None)
            sell.append(None)
            continue

        tight_range = data['range'].iloc[i] < data['range_avg'].iloc[i] * 0.85
        low_vol = data['volatility'].iloc[i] < data['volatility_ma'].iloc[i]
        breakout = data['close'].iloc[i] > data['close'].iloc[i - 1] * 1.005
        breakdown = data['close'].iloc[i] < data['close'].iloc[i - 1] * 0.995

        if not in_position and tight_range and low_vol and breakout:
            entry_price = data['close'].iloc[i]
            buy.append(entry_price)
            sell.append(None)
            in_position = True
        elif in_position:
            price_now = data['close'].iloc[i]
            tp = entry_price * 1.01
            sl = entry_price * 0.985
            if price_now >= tp or price_now <= sl:
                sell.append(price_now)
                buy.append(None)
                in_position = False
            else:
                buy.append(None)
                sell.append(None)
        else:
            buy.append(None)
            sell.append(None)

    return buy, sell









def eth_bull_momentum(data):
    """Trend strategy using EMA crossover + momentum confirmation"""
    data['ema12'] = data['close'].ewm(span=12).mean()
    data['ema26'] = data['close'].ewm(span=26).mean()
    data['momentum'] = data['close'].diff(4)
    buy, sell, in_position = [], [], False
    for i in range(len(data)):
        if data['ema12'][i] > data['ema26'][i] and data['momentum'][i] > 0 and not in_position:
            buy.append(data['close'][i])
            sell.append(None)
            in_position = True
        elif in_position and (data['momentum'][i] < 0):
            sell.append(data['close'][i])
            buy.append(None)
            in_position = False
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell

# Note: Remaining 9 strategies (for LINK, MATIC, DOGE) will be in the next part.
def link_reversion_strategy(data):
    """
    Mean reversion strategy using Bollinger Bands and RSI to capture cycles.
    """
    data['bb_middle'] = data['close'].rolling(window=20).mean()
    data['bb_std'] = data['close'].rolling(window=20).std()
    data['bb_upper'] = data['bb_middle'] + (2 * data['bb_std'])
    data['bb_lower'] = data['bb_middle'] - (2 * data['bb_std'])

    delta = data['close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))

    buy, sell = [], []
    for i in range(len(data)):
        if (data['close'].iloc[i] <= data['bb_lower'].iloc[i] and data['rsi'].iloc[i] < 35):
            buy.append(data['close'].iloc[i])
            sell.append(None)
        elif (data['close'].iloc[i] >= data['bb_upper'].iloc[i] and data['rsi'].iloc[i] > 65):
            buy.append(None)
            sell.append(data['close'].iloc[i])
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell

def link_macd_filter_strategy(data):
    """Tweaked MACD strategy with relaxed histogram threshold and wider exits."""
    data['ema12'] = data['close'].ewm(span=12, adjust=False).mean()
    data['ema26'] = data['close'].ewm(span=26, adjust=False).mean()
    data['macd'] = data['ema12'] - data['ema26']
    data['signal'] = data['macd'].ewm(span=9, adjust=False).mean()
    data['macd_hist'] = data['macd'] - data['signal']

    buy, sell = [], []
    in_position = False

    for i in range(len(data)):
        if i < 2:
            buy.append(None)
            sell.append(None)
            continue

        entry_cond = (
            data['macd_hist'].iloc[i] > 0.01 and  # Lowered from 0.05
            data['macd_hist'].iloc[i - 1] <= 0 and
            not in_position
        )

        exit_cond = (
            data['macd_hist'].iloc[i] < -0.01 or  # Less strict
            data['close'].iloc[i] < data['ema26'].iloc[i]
        )

        if entry_cond:
            buy.append(data['close'].iloc[i])
            sell.append(None)
            in_position = True
        elif in_position and exit_cond:
            buy.append(None)
            sell.append(data['close'].iloc[i])
            in_position = False
        else:
            buy.append(None)
            sell.append(None)

    return buy, sell



def link_ema_volume_strategy(data):
    """
    Revised: Fast EMA cross + momentum confirmation + early exit.
    """
    data['ema_fast'] = data['close'].ewm(span=5).mean()
    data['ema_slow'] = data['close'].ewm(span=13).mean()
    data['momentum'] = data['close'].diff(3)
    data['high_rolling'] = data['close'].rolling(window=10).max()

    buy, sell = [], []
    in_position = False
    entry_price = 0

    for i in range(len(data)):
        if not in_position and data['ema_fast'].iloc[i] > data['ema_slow'].iloc[i] and data['momentum'].iloc[i] > 0:
            buy.append(data['close'].iloc[i])
            sell.append(None)
            entry_price = data['close'].iloc[i]
            in_position = True
        elif in_position:
            price = data['close'].iloc[i]
            gain_pct = (price - entry_price) / entry_price
            if gain_pct > 0.06 or gain_pct < -0.03 or price < data['ema_slow'].iloc[i]:
                sell.append(price)
                buy.append(None)
                in_position = False
            else:
                buy.append(None)
                sell.append(None)
        else:
            buy.append(None)
            sell.append(None)

    return buy, sell

def matic_breakout_strategy(data):
    """
    Classic breakout strategy: Price breaking above recent resistance + volume spike.
    """
    data['high_20'] = data['high'].rolling(window=20).max()
    data['volume_ma'] = data['volume'].rolling(window=20).mean()

    buy, sell = [], []
    in_position = False

    for i in range(len(data)):
        if i < 20:
            buy.append(None)
            sell.append(None)
            continue

        price = data['close'].iloc[i]
        resistance = data['high_20'].iloc[i - 1]
        volume = data['volume'].iloc[i]

        if not in_position and price > resistance and volume > data['volume_ma'].iloc[i]:
            buy.append(price)
            sell.append(None)
            in_position = True
        elif in_position and price < resistance:
            buy.append(None)
            sell.append(price)
            in_position = False
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell
def matic_adx_trend_strategy(data):
    """Improved trend-following strategy using EMA cross and price momentum."""
    data['ema_fast'] = data['close'].ewm(span=10).mean()
    data['ema_slow'] = data['close'].ewm(span=30).mean()
    data['momentum'] = data['close'] - data['close'].shift(3)

    buy, sell, in_position = [], [], False
    for i in range(len(data)):
        if (
            data['ema_fast'][i] > data['ema_slow'][i] and
            data['momentum'][i] > 0 and not in_position
        ):
            buy.append(data['close'][i])
            sell.append(None)
            in_position = True
        elif in_position and (
            data['momentum'][i] < 0 or
            data['close'][i] < data['ema_fast'][i]
        ):
            sell.append(data['close'][i])
            buy.append(None)
            in_position = False
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell

def matic_consolidation_break_strategy(data):
    """
    Identifies consolidation (low volatility) then breakout via price + volume.
    """
    data['range'] = data['high'].rolling(window=10).max() - data['low'].rolling(window=10).min()
    data['range_avg'] = data['range'].rolling(window=10).mean()
    data['volume_ma'] = data['volume'].rolling(window=20).mean()

    buy, sell = [], []
    in_position = False

    for i in range(len(data)):
        if i < 20:
            buy.append(None)
            sell.append(None)
            continue

        low_volatility = data['range'].iloc[i] < data['range_avg'].iloc[i]
        volume_spike = data['volume'].iloc[i] > 1.2 * data['volume_ma'].iloc[i]
        price_break = data['close'].iloc[i] > data['close'].iloc[i - 1] * 1.02

        if not in_position and low_volatility and volume_spike and price_break:
            buy.append(data['close'].iloc[i])
            sell.append(None)
            in_position = True
        elif in_position and data['close'].iloc[i] < data['close'].iloc[i - 1]:
            buy.append(None)
            sell.append(data['close'].iloc[i])
            in_position = False
        else:
            buy.append(None)
            sell.append(None)

    return buy, sell
def doge_tweet_spike_strategy(data):
    """Loosened spike trigger and RSI limit to allow more entries."""
    data['price_change'] = data['close'].pct_change()
    data['volume_ma'] = data['volume'].rolling(window=10).mean()

    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))

    buy, sell = [], []
    in_position = False

    for i in range(len(data)):
        if i < 15:
            buy.append(None)
            sell.append(None)
            continue

        spike = data['price_change'].iloc[i] > 0.015  # Lowered to 1.5%
        volume_surge = data['volume'].iloc[i] > 0.75 * data['volume_ma'].iloc[i]
        not_overbought = data['rsi'].iloc[i] < 80  # Was 75

        if not in_position and spike and volume_surge and not_overbought:
            buy.append(data['close'].iloc[i])
            sell.append(None)
            in_position = True
        elif in_position and data['rsi'].iloc[i] > 85:
            buy.append(None)
            sell.append(data['close'].iloc[i])
            in_position = False
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell


def doge_meme_momentum_strategy(data):
    """
    Meme-fueled rally phase strategy. Trend-following using price, MA, and hype spike pattern.
    """
    data['ma_20'] = data['close'].rolling(window=20).mean()
    data['ma_50'] = data['close'].rolling(window=50).mean()

    buy, sell = [], []
    in_position = False

    for i in range(len(data)):
        if i < 50:
            buy.append(None)
            sell.append(None)
            continue

        price = data['close'].iloc[i]
        trend_up = data['ma_20'].iloc[i] > data['ma_50'].iloc[i]
        big_candle = price > data['close'].iloc[i - 1] * 1.03  # >3% jump

        if not in_position and trend_up and big_candle:
            buy.append(price)
            sell.append(None)
            in_position = True
        elif in_position and price < data['ma_20'].iloc[i]:
            buy.append(None)
            sell.append(price)
            in_position = False
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell
def doge_sentiment_consolidation_strategy(data):
    """Loosen volatility and volume filters to trigger more"""
    data['range'] = data['high'].rolling(window=10).max() - data['low'].rolling(window=10).min()
    data['range_avg'] = data['range'].rolling(window=10).mean()
    data['vol_ma'] = data['volume'].rolling(window=10).mean()

    buy, sell = [], []
    in_position = False

    for i in range(len(data)):
        if i < 10:
            buy.append(None)
            sell.append(None)
            continue

        volatility_low = data['range'].iloc[i] < 1.2 * data['range_avg'].iloc[i]
        price_break = data['close'].iloc[i] > data['close'].iloc[i - 1] * 1.015
        volume_pop = data['volume'].iloc[i] > data['vol_ma'].iloc[i] * 1.2

        if not in_position and volatility_low and price_break and volume_pop:
            buy.append(data['close'].iloc[i])
            sell.append(None)
            in_position = True
        elif in_position and data['close'].iloc[i] < data['close'].iloc[i - 1]:
            buy.append(None)
            sell.append(data['close'].iloc[i])
            in_position = False
        else:
            buy.append(None)
            sell.append(None)

    return buy, sell


STRATEGY_MAP = {
    "ETH": {
        "eth_hybrid_trend_sentiment": eth_bull_trend,
        "eth_choppy_durability": eth_choppy_durability,
        "eth_strong_bull_momentum": eth_bull_momentum
    },
    "LINK": {
        "link_mean_reversion": link_reversion_strategy,
        "link_macd_downtrend_filter": link_macd_filter_strategy,
        "link_cycle_momentum": link_ema_volume_strategy
    },
    "MATIC": {
        "matic_breakout_clean": matic_breakout_strategy,
        "matic_bull_trend": matic_adx_trend_strategy,
        "matic_consolidation_then_break": matic_consolidation_break_strategy
    },    
    "ARB": {
        "arb_breakout_clean": arb_breakout_strategy,
        "arb_bull_trend": arb_bull_trend_refined,
        "arb_oversold_bounce": arb_oversold_bounce
    },
    "DOGE": {
        "doge_tweet_spike_strategy": doge_tweet_spike_strategy,
        "doge_meme_momentum_strategy": doge_meme_momentum_strategy,
        "doge_sentiment_consolidation_strategy": doge_sentiment_consolidation_strategy
    }
}

