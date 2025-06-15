import os
import logging
import pandas as pd
from datetime import datetime
import yaml
from binance.client import Client
# === Configuration ===
# Load config from yaml
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

start_date = '2025-04-09'
end_date = '2025-05-15'
interval = '1h'
output_dir = 'liveBackup'
os.makedirs(output_dir, exist_ok=True)

client = Client(
    config['binance']['test_api_key'],
    config['binance']['test_secret_key']
)

# === Define Strategies ===
def eth_tariff_bollinger_reversion(data):
    """
    ETH: Bollinger Band reversion strategy — enters when price dips below lower band
    and exits when it reverts to mean.
    """
    data['bb_mid'] = data['close'].rolling(window=20).mean()
    data['bb_std'] = data['close'].rolling(window=20).std()
    data['bb_upper'] = data['bb_mid'] + 2 * data['bb_std']
    data['bb_lower'] = data['bb_mid'] - 2 * data['bb_std']

    buy, sell = [], []
    in_position = False

    for i in range(len(data)):
        price = data['close'].iloc[i]
        if i < 20:
            buy.append(None)
            sell.append(None)
            continue

        if not in_position and price < data['bb_lower'].iloc[i]:
            buy.append(price)
            sell.append(None)
            in_position = True
        elif in_position and price >= data['bb_mid'].iloc[i]:
            sell.append(price)
            buy.append(None)
            in_position = False
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell


def link_tariff_ema_trend(data):
    """
    LINK: Trend-following strategy using EMA crossovers.
    Buys when fast EMA crosses above slow EMA, exits on reverse.
    """
    data['ema_fast'] = data['close'].ewm(span=8).mean()
    data['ema_slow'] = data['close'].ewm(span=21).mean()

    buy, sell = [], []
    in_position = False

    for i in range(len(data)):
        if i < 21:
            buy.append(None)
            sell.append(None)
            continue

        fast = data['ema_fast'].iloc[i]
        slow = data['ema_slow'].iloc[i]

        if not in_position and fast > slow and data['ema_fast'].iloc[i - 1] <= data['ema_slow'].iloc[i - 1]:
            buy.append(data['close'].iloc[i])
            sell.append(None)
            in_position = True
        elif in_position and fast < slow:
            sell.append(data['close'].iloc[i])
            buy.append(None)
            in_position = False
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell


def arb_pullback_trend_strategy(data):
    """
    ARB Strategy v2: Trend pullback with volatility filter
    """
    data['ema20'] = data['close'].ewm(span=20).mean()
    data['ema50'] = data['close'].ewm(span=50).mean()
    data['volatility'] = data['close'].pct_change().rolling(5).std()

    buy, sell = [], []
    in_position = False
    entry_price = 0

    for i in range(len(data)):
        if i < 50:
            buy.append(None)
            sell.append(None)
            continue

        in_trend = data['close'].iloc[i] > data['ema50'].iloc[i]
        pullback = data['close'].iloc[i] < data['ema20'].iloc[i]
        stable_vol = data['volatility'].iloc[i] < 0.03  # below 3% std dev

        if not in_position and in_trend and pullback and stable_vol:
            entry_price = data['close'].iloc[i]
            buy.append(entry_price)
            sell.append(None)
            in_position = True
        elif in_position:
            price = data['close'].iloc[i]
            if price >= entry_price * 1.04 or price <= entry_price * 0.975:
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


def doge_sentiment_defense(df):
    df['momentum'] = df['close'].diff()
    buy, sell, in_position = [], [], False
    for i in range(len(df)):
        if not in_position and df['momentum'][i] > 0:
            buy.append(df['close'][i])
            sell.append(None)
            in_position = True
        elif in_position and df['momentum'][i] < 0:
            sell.append(df['close'][i])
            buy.append(None)
            in_position = False
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell



def doge_breakout_strategy(data, lookback=5, take_profit_pct=0.05, stop_loss_pct=0.03, max_hold_periods=48):
    """
    DOGE trading strategy based on breakout patterns with volume confirmation
    
    Args:
        data (pandas.DataFrame): DataFrame with OHLCV data
        lookback (int): Periods to look back for resistance levels
        take_profit_pct (float): Take profit percentage target
        stop_loss_pct (float): Stop loss percentage
        max_hold_periods (int): Maximum number of periods to hold a position
        
    Returns:
        tuple: (buy_signals, sell_signals) lists for backtest runner
    """
    # Initialize signals lists
    buy_signals = [None] * len(data)
    sell_signals = [None] * len(data)
    
    position = 0  # 0 = no position, 1 = long
    entry_price = 0
    entry_index = 0
    
    # Strategy Implementation
    for i in range(lookback, len(data)):
        # If not in position, look for breakout opportunities
        if position == 0:
            # Find recent resistance level (highest high in lookback period)
            resistance = data.iloc[i-lookback:i]['high'].max()
            
            # Check if we have a clear breakout
            current_close = data.iloc[i]['close']
            previous_close = data.iloc[i-1]['close']
            
            # Calculate average volume for confirmation
            avg_volume = data.iloc[i-lookback:i]['volume'].mean()
            volume_increase = data.iloc[i]['volume'] > avg_volume * 1.5
            
            # Breakout conditions:
            # 1. Close above resistance
            # 2. Previous close below resistance
            # 3. Volume spike
            if current_close > resistance and previous_close <= resistance and volume_increase:
                position = 1
                entry_price = current_close
                entry_index = i
                buy_signals[i] = current_close
        
        # If in position, look for exit conditions
        elif position == 1:
            current_price = data.iloc[i]['close']
            periods_held = i - entry_index
            
            # Exit conditions:
            # 1. Take profit hit
            # 2. Stop loss hit
            # 3. Price falls back below the breakout level (original resistance)
            # 4. Maximum holding period reached
            
            # Find the resistance level that triggered our entry
            resistance = data.iloc[entry_index-lookback:entry_index]['high'].max()
            
            take_profit = entry_price * (1 + take_profit_pct)
            stop_loss = entry_price * (1 - stop_loss_pct)
            
            if (current_price >= take_profit or 
                current_price <= stop_loss or 
                current_price < resistance or 
                periods_held >= max_hold_periods):
                
                position = 0
                sell_signals[i] = current_price
    
    # Close any open position at the end
    if position == 1:
        sell_signals[-1] = data.iloc[-1]['close']
    
    return buy_signals, sell_signals

# === Backtest Runner ===
def fetch_data(symbol, interval, start, end):
    start_fmt = datetime.strptime(start, '%Y-%m-%d').strftime('%d %b, %Y')
    end_fmt = datetime.strptime(end, '%Y-%m-%d').strftime('%d %b, %Y')
    klines = client.get_historical_klines(symbol, interval, start_fmt, end_fmt)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'qav', 'num_trades', 'tbbav', 'tbqav', 'ignore'
    ])
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

def run_backtest(coin, strategy_fn):
    symbol = f"{coin}USDT"
    df = fetch_data(symbol, interval, start_date, end_date)
    buy, sell = strategy_fn(df)

    capital = 10000
    trades = []
    in_position = False
    entry_price = 0

    for i in range(len(df)):
        if buy[i] and not in_position:
            entry_price = buy[i]
            trades.append({'timestamp': df['timestamp'][i], 'type': 'buy', 'price': entry_price, 'profit': 0})
            in_position = True
        elif sell[i] and in_position:
            exit_price = sell[i]
            profit = (exit_price - entry_price) * (capital / entry_price)
            capital += profit
            trades.append({'timestamp': df['timestamp'][i], 'type': 'sell', 'price': exit_price, 'profit': profit})
            in_position = False

    trades_df = pd.DataFrame(trades)
    trades_df.to_csv(os.path.join(output_dir, f"{coin}_after_tariff_trades.csv"), index=False)

    if trades_df.empty:
        print(f"⚠️  No trades executed for {coin}. Skipping metrics.")
        return

    sell_trades = trades_df[trades_df['type'] == 'sell']
    win_rate = len(sell_trades[sell_trades['profit'] > 0]) / len(sell_trades) if len(sell_trades) else 0
    total_profit = capital - 10000

    summary = pd.DataFrame([{
        "coin": coin,
        "final_capital": round(capital, 2),
        "total_trades": len(sell_trades),
        "win_rate": round(win_rate, 2),
        "total_profit": round(total_profit, 2)
    }])
    summary.to_csv(os.path.join(output_dir, f"{coin}_after_tariff_metrics.csv"), index=False)
    print(f"✅ Finished {coin}: Profit ${total_profit:.2f}, Win Rate {win_rate*100:.1f}%")

# === Run All ===
run_backtest("ETH", eth_tariff_bollinger_reversion)
run_backtest("LINK", link_tariff_ema_trend)
run_backtest("ARB", arb_pullback_trend_strategy)
run_backtest("DOGE", doge_breakout_strategy)
