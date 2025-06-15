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

start_date = '2025-04-02'
end_date = '2025-04-08'
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
    ETH: Extremely conservative Bollinger Band reversion strategy with multiple
    confirmation signals, volume validation, and strict risk management during
    tariff uncertainty period.
    """
    # Calculate Bollinger Bands with much wider standard deviation for highly conservative entries
    data['bb_mid'] = data['close'].rolling(window=40).mean()  # Extended window for maximum stability
    data['bb_std'] = data['close'].rolling(window=40).std()
    data['bb_upper'] = data['bb_mid'] + 3.0 * data['bb_std']  # Much wider bands for extreme moves only
    data['bb_lower'] = data['bb_mid'] - 3.0 * data['bb_std']
    
    # Enhanced volume filter with trend confirmation
    data['vol_avg'] = data['volume'].rolling(window=30).mean()
    data['vol_ratio'] = data['volume'] / data['vol_avg']
    
    # RSI with longer lookback for more reliable signals
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=21).mean()  # Extended RSI window
    avg_loss = loss.rolling(window=21).mean()
    rs = avg_gain / avg_loss
    data['rsi'] = 100 - (100 / (1 + rs))
    
    # Add MACD for trend confirmation
    data['ema12'] = data['close'].ewm(span=12).mean()
    data['ema26'] = data['close'].ewm(span=26).mean()
    data['macd'] = data['ema12'] - data['ema26']
    data['macd_signal'] = data['macd'].ewm(span=9).mean()
    data['macd_hist'] = data['macd'] - data['macd_signal']

    buy, sell = [], []
    in_position = False
    consecutive_signals = 0
    exit_signals = 0

    for i in range(len(data)):
        price = data['close'].iloc[i]
        if i < 40:  # Need enough data for all indicators
            buy.append(None)
            sell.append(None)
            continue

        # Buy logic with multiple strict confirmations
        if not in_position:
            # Extreme oversold condition with multiple confirmations
            if (price < data['bb_lower'].iloc[i] * 0.98 and  # Well below lower band
                data['rsi'].iloc[i] < 30 and                 # Deeply oversold
                data['vol_ratio'].iloc[i] > 1.5 and          # Strong volume confirmation
                data['macd_hist'].iloc[i] > data['macd_hist'].iloc[i-1]):  # MACD histogram rising
                consecutive_signals += 1
            else:
                consecutive_signals = 0
                
            # Only buy after 3 consecutive signals (extremely conservative)
            if consecutive_signals >= 3:
                buy.append(price)
                sell.append(None)
                in_position = True
                consecutive_signals = 0
            else:
                buy.append(None)
                sell.append(None)
        # Sell logic - very conservative exit strategy
        elif in_position:
            # Exit conditions - any of these can trigger an exit signal
            if (price >= data['bb_mid'].iloc[i] * 0.95 or    # Approaching middle band
                data['rsi'].iloc[i] > 60 or                  # Moderately overbought (more conservative)
                price <= data['bb_lower'].iloc[i] * 0.92 or  # Stricter stop loss
                data['vol_ratio'].iloc[i] > 2.0):            # Abnormal volume spike
                exit_signals += 1
            else:
                exit_signals = 0
                
            # Require 2 consecutive exit signals for more certainty
            if exit_signals >= 2:
                sell.append(price)
                buy.append(None)
                in_position = False
                exit_signals = 0
            else:
                buy.append(None)
                sell.append(None)
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell


def link_tariff_ema_trend(data):
    """
    LINK: Conservative multi-timeframe EMA strategy with volatility filter
    and market regime detection during tariff uncertainty.
    """
    # Multiple EMAs for confirmation
    data['ema_fast'] = data['close'].ewm(span=12).mean()
    data['ema_mid'] = data['close'].ewm(span=26).mean()
    data['ema_slow'] = data['close'].ewm(span=50).mean()
    
    # Add volatility filter
    data['atr'] = data['high'] - data['low']
    data['atr_ma'] = data['atr'].rolling(window=14).mean()
    data['volatility'] = data['atr_ma'] / data['close']
    
    # Market regime detection
    data['regime'] = 'neutral'
    data.loc[(data['ema_fast'] > data['ema_mid']) & (data['ema_mid'] > data['ema_slow']), 'regime'] = 'bullish'
    data.loc[(data['ema_fast'] < data['ema_mid']) & (data['ema_mid'] < data['ema_slow']), 'regime'] = 'bearish'
    
    # MACD for additional confirmation
    data['macd'] = data['ema_fast'] - data['ema_mid']
    data['macd_signal'] = data['macd'].ewm(span=9).mean()
    data['macd_hist'] = data['macd'] - data['macd_signal']

    buy, sell = [], []
    in_position = False
    signal_counter = 0

    for i in range(len(data)):
        if i < 50:  # Need enough data for all indicators
            buy.append(None)
            sell.append(None)
            continue

        # Only trade in low volatility environments
        low_volatility = data['volatility'].iloc[i] < 0.03
        
        # Buy only in confirmed bullish regimes with multiple signals
        if not in_position:
            bullish_regime = data['regime'].iloc[i] == 'bullish'
            macd_cross = (data['macd'].iloc[i] > data['macd_signal'].iloc[i] and 
                          data['macd'].iloc[i-1] <= data['macd_signal'].iloc[i-1])
            
            if bullish_regime and macd_cross and low_volatility:
                signal_counter += 1
            else:
                signal_counter = 0
                
            # Require 2 consecutive signals for entry
            if signal_counter >= 2:
                buy.append(data['close'].iloc[i])
                sell.append(None)
                in_position = True
                signal_counter = 0
            else:
                buy.append(None)
                sell.append(None)
        # More conservative exit strategy
        elif in_position:
            # Exit on regime change or MACD bearish cross
            bearish_signal = (data['macd'].iloc[i] < data['macd_signal'].iloc[i] and 
                             data['macd'].iloc[i-1] >= data['macd_signal'].iloc[i-1])
            regime_change = data['regime'].iloc[i] != 'bullish'
            
            # Add trailing stop logic
            entry_idx = max([j for j in range(i) if buy[j] is not None])
            entry_price = buy[entry_idx]
            trailing_stop = price_below_threshold = data['close'].iloc[i] < entry_price * 0.97
            
            if bearish_signal or regime_change or trailing_stop:
                sell.append(data['close'].iloc[i])
                buy.append(None)
                in_position = False
            else:
                buy.append(None)
                sell.append(None)
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell


def arb_pullback_trend_strategy(data):
    """
    ARB Strategy: Conservative multi-factor approach with trend confirmation,
    volatility filters, and risk management during tariff uncertainty.
    """
    # Multiple moving averages for trend confirmation
    data['sma50'] = data['close'].rolling(window=50).mean()
    data['sma100'] = data['close'].rolling(window=100).mean()
    data['ema20'] = data['close'].ewm(span=20).mean()
    data['ema50'] = data['close'].ewm(span=50).mean()
    
    # Enhanced volatility metrics
    data['volatility'] = data['close'].pct_change().rolling(10).std()
    data['atr'] = data['high'] - data['low']
    data['atr14'] = data['atr'].rolling(window=14).mean()
    
    # Momentum indicators
    data['rsi'] = 100 - (100 / (1 + (data['close'].diff(1).clip(lower=0).rolling(14).mean() / 
                                    data['close'].diff(1).clip(upper=0).abs().rolling(14).mean())))
    
    # Volume analysis
    data['volume_ma'] = data['volume'].rolling(window=20).mean()
    data['volume_ratio'] = data['volume'] / data['volume_ma']

    buy, sell = [], []
    in_position = False
    entry_price = 0
    confirmation_count = 0

    for i in range(len(data)):
        if i < 100:  # Need enough data for all indicators
            buy.append(None)
            sell.append(None)
            continue

        # Complex entry conditions with multiple confirmations
        strong_trend = (data['sma50'].iloc[i] > data['sma100'].iloc[i] and 
                        data['ema20'].iloc[i] > data['ema50'].iloc[i])
        healthy_pullback = (data['close'].iloc[i] < data['ema20'].iloc[i] and 
                           data['close'].iloc[i] > data['ema50'].iloc[i])
        low_volatility = data['volatility'].iloc[i] < 0.025  # Stricter volatility requirement
        healthy_rsi = 30 < data['rsi'].iloc[i] < 45  # Looking for oversold but not extreme
        volume_confirmation = data['volume_ratio'].iloc[i] > 0.8  # Decent volume

        if not in_position:
            if strong_trend and healthy_pullback and low_volatility and healthy_rsi and volume_confirmation:
                confirmation_count += 1
            else:
                confirmation_count = 0
                
            # Require multiple confirmations before entry
            if confirmation_count >= 2:
                entry_price = data['close'].iloc[i]
                buy.append(entry_price)
                sell.append(None)
                in_position = True
                confirmation_count = 0
            else:
                buy.append(None)
                sell.append(None)
        elif in_position:
            price = data['close'].iloc[i]
            
            # More conservative profit target and tighter stop loss
            take_profit = price >= entry_price * 1.03
            stop_loss = price <= entry_price * 0.98
            
            # Additional exit conditions
            trend_reversal = False
            if i >= 3:
                trend_reversal = (data['ema20'].iloc[i] < data['ema20'].iloc[i-1] and
                                 data['ema20'].iloc[i-1] < data['ema20'].iloc[i-2] and
                                 data['ema20'].iloc[i-2] < data['ema20'].iloc[i-3])
            
            volatility_spike = data['volatility'].iloc[i] > 0.04
            
            if take_profit or stop_loss or trend_reversal or volatility_spike:
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


def doge_sentiment_defense(data):
    """
    DOGE: Conservative sentiment-based strategy with multiple technical filters
    and reduced exposure during tariff uncertainty.
    """
    # Multiple indicators for confirmation
    data['sma20'] = data['close'].rolling(window=20).mean()
    data['sma50'] = data['close'].rolling(window=50).mean()
    data['momentum'] = data['close'].pct_change(3)  # 3-period momentum
    
    # Volatility measures
    data['volatility'] = data['close'].pct_change().rolling(10).std()
    
    # Volume analysis
    data['volume_ma'] = data['volume'].rolling(window=20).mean()
    data['volume_ratio'] = data['volume'] / data['volume_ma']
    
    # RSI for overbought/oversold
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    data['rsi'] = 100 - (100 / (1 + rs))

    buy, sell = [], []
    in_position = False
    confirmation_signals = 0
    entry_price = 0

    for i in range(len(data)):
        if i < 50:  # Need enough data for indicators
            buy.append(None)
            sell.append(None)
            continue
            
        # Complex entry conditions
        positive_momentum = data['momentum'].iloc[i] > 0
        above_sma = data['close'].iloc[i] > data['sma20'].iloc[i]
        low_volatility = data['volatility'].iloc[i] < 0.03
        healthy_volume = data['volume_ratio'].iloc[i] > 1.0
        not_overbought = data['rsi'].iloc[i] < 65
        
        if not in_position:
            # Count consecutive confirmation signals
            if positive_momentum and above_sma and low_volatility and healthy_volume and not_overbought:
                confirmation_signals += 1
            else:
                confirmation_signals = 0
                
            # Only enter after multiple confirmations
            if confirmation_signals >= 3:
                entry_price = data['close'].iloc[i]
                buy.append(entry_price)
                sell.append(None)
                in_position = True
                confirmation_signals = 0
            else:
                buy.append(None)
                sell.append(None)
        elif in_position:
            price = data['close'].iloc[i]
            
            # Conservative exit conditions
            momentum_reversal = data['momentum'].iloc[i] < 0
            price_below_sma = data['close'].iloc[i] < data['sma20'].iloc[i]
            overbought = data['rsi'].iloc[i] > 70
            
            # Trailing stop and take profit
            stop_loss = price <= entry_price * 0.97
            take_profit = price >= entry_price * 1.05
            
            if momentum_reversal or price_below_sma or overbought or stop_loss or take_profit:
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
    trades_df.to_csv(os.path.join(output_dir, f"{coin}_after_tariff_inbetween_trades.csv"), index=False)

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
    summary.to_csv(os.path.join(output_dir, f"{coin}_after_tariff_inbetween_metrics.csv"), index=False)
    print(f"✅ Finished {coin}: Profit ${total_profit:.2f}, Win Rate {win_rate*100:.1f}%")

# === Run All ===
run_backtest("ETH", eth_tariff_bollinger_reversion)
run_backtest("LINK", link_tariff_ema_trend)
run_backtest("ARB", arb_pullback_trend_strategy)
run_backtest("DOGE", doge_sentiment_defense)
