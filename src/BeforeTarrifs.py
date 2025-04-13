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

start_date = '2025-03-08'
end_date = '2025-04-08'
interval = '1h'
output_dir = 'before_tarrifs'
os.makedirs(output_dir, exist_ok=True)

client = Client(
    config['binance']['test_api_key'],
    config['binance']['test_secret_key']
)

# === Define Strategies ===
def eth_queue_bounce_scalper(df):
    df = df.copy()
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['vol_ma'] = df['volume'].rolling(10).mean()

    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    buy, sell, in_position = [], [], False

    for i in range(len(df)):
        vol_ok = df['volume'][i] > df['vol_ma'][i]
        downtrend = df['close'][i] < df['ema50'][i]
        rsi_trigger = df['rsi'][i] > 35 and df['rsi'][i-1] <= 35 if i > 0 else False

        if not in_position and downtrend and rsi_trigger and vol_ok:
            buy.append(df['close'][i])
            sell.append(None)
            in_position = True
        elif in_position and (df['rsi'][i] > 55 or df['close'][i] < df['ema20'][i]):
            sell.append(df['close'][i])
            buy.append(None)
            in_position = False
        else:
            buy.append(None)
            sell.append(None)

    return buy, sell


def link_queue_bounce_scalper(df):
    df = df.copy()
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['vol_ma'] = df['volume'].rolling(10).mean()

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    buy, sell, in_position = [], [], False

    for i in range(len(df)):
        vol_ok = df['volume'][i] > df['vol_ma'][i]
        downtrend = df['close'][i] < df['ema50'][i]
        rsi_trigger = df['rsi'][i] > 35 and df['rsi'][i-1] <= 35 if i > 0 else False

        if not in_position and downtrend and rsi_trigger and vol_ok:
            buy.append(df['close'][i])
            sell.append(None)
            in_position = True
        elif in_position and (df['rsi'][i] > 55 or df['close'][i] < df['ema20'][i]):
            sell.append(df['close'][i])
            buy.append(None)
            in_position = False
        else:
            buy.append(None)
            sell.append(None)

    return buy, sell


def arb_queue_bounce_scalper(df):
    df = df.copy()
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['vol_ma'] = df['volume'].rolling(10).mean()

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    buy, sell, in_position = [], [], False

    for i in range(len(df)):
        vol_ok = df['volume'][i] > df['vol_ma'][i]
        downtrend = df['close'][i] < df['ema50'][i]
        rsi_trigger = df['rsi'][i] > 35 and df['rsi'][i-1] <= 35 if i > 0 else False

        if not in_position and downtrend and rsi_trigger and vol_ok:
            buy.append(df['close'][i])
            sell.append(None)
            in_position = True
        elif in_position and (df['rsi'][i] > 55 or df['close'][i] < df['ema20'][i]):
            sell.append(df['close'][i])
            buy.append(None)
            in_position = False
        else:
            buy.append(None)
            sell.append(None)

    return buy, sell


def doge_flat_breakout(df):
    df['ema20'] = df['close'].ewm(span=20).mean()
    df['price_change'] = df['close'].pct_change()
    df['vol_ma'] = df['volume'].rolling(10).mean()

    buy, sell, in_position = [], [], False
    for i in range(len(df)):
        flat = abs(df['close'][i] - df['ema20'][i]) < df['close'][i] * 0.002
        mini_break = df['price_change'][i] > 0.01
        vol_ok = df['volume'][i] > df['vol_ma'][i]

        if not in_position and flat and mini_break and vol_ok:
            buy.append(df['close'][i])
            sell.append(None)
            in_position = True
        elif in_position and df['price_change'][i] < -0.005:
            sell.append(df['close'][i])
            buy.append(None)
            in_position = False
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell

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
    trades_df.to_csv(os.path.join(output_dir, f"{coin}_tariff_trades.csv"), index=False)

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
    summary.to_csv(os.path.join(output_dir, f"{coin}_tariff_metrics.csv"), index=False)
    print(f"✅ Finished {coin}: Profit ${total_profit:.2f}, Win Rate {win_rate*100:.1f}%")

# === Run All ===
run_backtest("ETH", eth_queue_bounce_scalper)
run_backtest("LINK", link_queue_bounce_scalper)
run_backtest("ARB", arb_queue_bounce_scalper)
run_backtest("DOGE", doge_flat_breakout)
