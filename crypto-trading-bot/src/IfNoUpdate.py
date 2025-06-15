import os
import logging
import pandas as pd
from datetime import datetime
import yaml
from binance.client import Client
import numpy as np

# === Configuration ===
# Load config from yaml
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)


start_date = '2025-02-28'
end_date = '2025-05-15'
interval = '1h'
output_dir = 'liveBackup'
os.makedirs(output_dir, exist_ok=True)

client = Client(
    config['binance']['test_api_key'],
    config['binance']['test_secret_key']
)

def eth_volatility_breakout_strategy(data_path, initial_capital=10000):
    """
    Implement a volatility breakout strategy for Ethereum using Bollinger Bands, RSI, and volume indicators.
    
    Parameters:
    -----------
    data_path : str
        Path to the OHLCV CSV file
    initial_capital : float
        Initial trading capital
        
    Returns:
    --------
    dict
        Dictionary containing backtest results and performance metrics
    """
    # Load and prepare the OHLCV data
    df = pd.read_csv(data_path)
    
    # Ensure datetime format
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sort by timestamp if not already sorted
    df = df.sort_values('timestamp')
    
    # Set the index to timestamp
    df = df.set_index('timestamp')
    
    # Initialize trading variables
    capital = initial_capital
    holdings = 0
    trades = []
    stop_loss = 0
    take_profit = 0
    
    # Calculate Bollinger Bands (20-day, 2 standard deviations)
    df['sma20'] = df['close'].rolling(window=20).mean()
    df['std20'] = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['sma20'] + (2 * df['std20'])
    df['bb_lower'] = df['sma20'] - (2 * df['std20'])
    
    # Calculate Average True Range (ATR) for volatility measurement
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    df['tr'] = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
    df['atr'] = df['tr'].rolling(window=14).mean()
    
    # Calculate volume indicators
    df['vol_sma5'] = df['volume'].rolling(window=5).mean()
    
    # Calculate RSI (14-day)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    
    with np.errstate(divide='ignore', invalid='ignore'):
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
    
    # Volume trend confirmation
    df['obv'] = 0
    obv = 0
    for i, row in df.iterrows():
        if i == df.index[0]:
            continue
            
        prev_close = df.loc[df.index[df.index.get_loc(i) - 1], 'close']
        if row['close'] > prev_close:
            obv += row['volume']
        elif row['close'] < prev_close:
            obv -= row['volume']
        
        df.at[i, 'obv'] = obv
        
    df['obv_ema10'] = df['obv'].ewm(span=10, adjust=False).mean()
    
    # Filter out NaN values after indicator calculation
    df = df.dropna()
    
    # Initialize signal column
    df['signal'] = 0
    
    # Generate signals
    for i in range(1, len(df)):
        today = df.iloc[i]
        yesterday = df.iloc[i-1]
        
        # BUY CONDITIONS:
        # 1. Price is near or below the lower Bollinger Band
        # 2. Volume is above 5-day average (high interest)
        # 3. RSI is below 30 (oversold condition)
        # 4. OBV shows accumulation (increasing)
        if (holdings == 0 and
            today['close'] <= today['bb_lower'] * 1.01 and
            today['volume'] > today['vol_sma5'] and
            today['rsi'] < 30 and
            today['obv'] > yesterday['obv']):
            
            df.iloc[i, df.columns.get_loc('signal')] = 1
            
            # Execute buy
            price = today['close']
            holdings = capital / price
            capital = 0
            
            # Set stop loss at 2x ATR below entry
            stop_loss = price - (2 * today['atr'])
            
            # Set take profit at middle band
            take_profit = today['sma20']
            
            # Record trade
            trades.append({
                'date': df.index[i],
                'action': 'BUY',
                'price': price,
                'quantity': holdings,
                'value': holdings * price
            })
        
        # SELL CONDITIONS:
        # 1. Price reaches the middle Bollinger Band (take profit)
        # 2. Price hits stop loss
        # 3. RSI above 70 (overbought)
        elif (holdings > 0 and
              (today['close'] >= take_profit or
               today['close'] <= stop_loss or
               today['rsi'] > 70)):
            
            df.iloc[i, df.columns.get_loc('signal')] = -1
            
            # Execute sell
            price = today['close']
            capital = holdings * price
            holdings = 0
            
            # Record trade
            trades.append({
                'date': df.index[i],
                'action': 'SELL',
                'price': price,
                'value': capital,
                'reason': 'Take Profit' if today['close'] >= take_profit else 'Stop Loss' if today['close'] <= stop_loss else 'RSI Overbought'
            })
    
    # Calculate final portfolio value
    if holdings > 0:
        final_value = holdings * df['close'].iloc[-1]
    else:
        final_value = capital
        
    # Calculate returns
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    # Prepare trade summary
    trades_df = pd.DataFrame(trades)
    
    return {
        'initial_capital': initial_capital,
        'final_value': final_value,
        'total_return': total_return,
        'num_trades': len(trades),
        'trades': trades_df,
        'data': df
    }

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


def calculate_average_volume(data, current_index, lookback_period):
    """
    Calculate average volume over a lookback period
    
    Args:
        data (pandas.DataFrame): DataFrame with OHLCV data
        current_index (int): Current index position
        lookback_period (int): Number of periods to look back
        
    Returns:
        float: Average volume
    """
    sum_volume = 0
    start_index = max(0, current_index - lookback_period)
    
    for i in range(start_index, current_index):
        sum_volume += data.iloc[i]['volume']
    
    return sum_volume / (current_index - start_index)


# Enhanced version with trailing stop logic
def doge_advanced_breakout_strategy(data, lookback=5, take_profit_pct=0.05, initial_stop_loss_pct=0.03, max_hold_periods=48):
    """
    Advanced DOGE trading strategy with breakout detection and trailing stops
    
    Args:
        data (pandas.DataFrame): DataFrame with OHLCV data
        lookback (int): Periods to look back for resistance levels
        take_profit_pct (float): Take profit percentage target
        initial_stop_loss_pct (float): Initial stop loss percentage
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
    stop_loss_price = 0
    
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
            # 2. Previous close below or at resistance
            # 3. Volume spike
            if current_close > resistance and previous_close <= resistance and volume_increase:
                position = 1
                entry_price = current_close
                entry_index = i
                stop_loss_price = entry_price * (1 - initial_stop_loss_pct)
                buy_signals[i] = current_close
        
        # If in position, look for exit conditions
        elif position == 1:
            current_price = data.iloc[i]['close']
            periods_held = i - entry_index
            
            # Exit conditions:
            # 1. Take profit hit
            # 2. Stop loss hit
            # 3. Maximum holding period reached
            
            take_profit = entry_price * (1 + take_profit_pct)
            
            if (current_price >= take_profit or 
                current_price <= stop_loss_price or 
                periods_held >= max_hold_periods):
                
                position = 0
                sell_signals[i] = current_price
            
            # Update trailing stop if price moves in our favor
            elif current_price > entry_price * 1.02:  # Once price is 2% up
                # Tighten stop loss to lock in some gains
                new_stop = current_price * 0.985  # 1.5% below current price
                if new_stop > stop_loss_price:
                    stop_loss_price = new_stop
    
    # Close any open position at the end
    if position == 1:
        sell_signals[-1] = data.iloc[-1]['close']
    
    return buy_signals, sell_signals


# Hybrid strategy combining breakout and mean reversion elements
def doge_hybrid_strategy(data, lookback=5, rsi_period=14, rsi_buy_threshold=30, take_profit_pct=0.05, stop_loss_pct=0.03):
    """
    Hybrid DOGE strategy combining breakout detection with RSI-based entries
    
    Args:
        data (pandas.DataFrame): DataFrame with OHLCV data
        lookback (int): Periods to look back for patterns
        rsi_period (int): Period for RSI calculation
        rsi_buy_threshold (int): RSI threshold for buy signals
        take_profit_pct (float): Take profit percentage
        stop_loss_pct (float): Stop loss percentage
        
    Returns:
        tuple: (buy_signals, sell_signals) lists for backtest runner
    """
    # Calculate RSI
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=rsi_period).mean()
    avg_loss = loss.rolling(window=rsi_period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    # Initialize signals lists
    buy_signals = [None] * len(data)
    sell_signals = [None] * len(data)
    
    position = 0  # 0 = no position, 1 = long
    entry_price = 0
    stop_loss_price = 0
    
    # Strategy Implementation
    for i in range(max(lookback, rsi_period), len(data)):
        current_price = data.iloc[i]['close']
        current_rsi = rsi.iloc[i]
        
        # If not in position, look for entry opportunities
        if position == 0:
            # Find recent resistance level
            resistance = data.iloc[i-lookback:i]['high'].max()
            
            # Calculate average volume for confirmation
            avg_volume = data.iloc[i-lookback:i]['volume'].mean()
            volume_increase = data.iloc[i]['volume'] > avg_volume * 1.2
            
            # Entry conditions:
            # 1. RSI is below buy threshold (oversold)
            # 2. Close is within 2% of recent resistance 
            # 3. Volume is above average
            price_near_resistance = current_price > resistance * 0.98
            
            if current_rsi < rsi_buy_threshold and price_near_resistance and volume_increase:
                position = 1
                entry_price = current_price
                stop_loss_price = entry_price * (1 - stop_loss_pct)
                buy_signals[i] = current_price
        
        # If in position, look for exit conditions
        elif position == 1:
            # Exit conditions:
            # 1. Take profit hit
            # 2. Stop loss hit
            # 3. RSI becomes overbought (>70)
            
            take_profit = entry_price * (1 + take_profit_pct)
            
            if (current_price >= take_profit or 
                current_price <= stop_loss_price or 
                current_rsi > 70):
                
                position = 0
                sell_signals[i] = current_price
            
            # Update trailing stop if price moves in our favor
            elif current_price > entry_price * 1.03:  # Once price is 3% up
                # Move stop loss to break even + small profit
                new_stop = entry_price * 1.01  # 1% above entry
                if new_stop > stop_loss_price:
                    stop_loss_price = new_stop
    
    # Close any open position at the end
    if position == 1:
        sell_signals[-1] = data.iloc[-1]['close']
    
    return buy_signals, sell_signals




def link_vwma_strategy(data, short_period=20, long_period=50, stop_loss=0.05):
    """
    LINK trading strategy based on Volume-Weighted Moving Average crossovers with stop loss
    
    Args:
        data (pandas.DataFrame): DataFrame with OHLCV data
        short_period (int): Period for short VWMA
        long_period (int): Period for long VWMA
        stop_loss (float): Initial stop loss percentage
        
    Returns:
        tuple: (buy_signals, sell_signals) lists for backtest runner
    """
    # Calculate Volume-Weighted Moving Averages
    vwma_short = calculate_vwma(data, short_period)
    vwma_long = calculate_vwma(data, long_period)
    
    position = 0  # 0 = no position, 1 = long
    entry_price = 0
    
    # Initialize signals lists
    buy_signals = [None] * len(data)
    sell_signals = [None] * len(data)
    
    # Strategy Implementation
    for i in range(long_period, len(data)):
        current_price = data.iloc[i]['close']
        
        # Buy signal: Short VWMA crosses above Long VWMA with volume confirmation
        if (vwma_short[i-1] <= vwma_long[i-1] and 
            vwma_short[i] > vwma_long[i] and 
            position == 0 and
            data.iloc[i]['volume'] > calculate_average_volume(data, i, 5)):
            
            position = 1
            entry_price = current_price
            buy_signals[i] = current_price
            
        # Sell signal: Short VWMA crosses below Long VWMA or stop loss
        elif ((vwma_short[i-1] >= vwma_long[i-1] and vwma_short[i] < vwma_long[i] and position == 1) or
              # Stop loss condition
              (position == 1 and current_price <= entry_price * (1 - stop_loss))):
            
            sell_signals[i] = current_price
            position = 0
        
        # Add trailing stop once in profit
        elif position == 1 and current_price >= entry_price * 1.1:
            # Update stop loss to breakeven + small profit once we're 10% up
            stop_loss = (entry_price * 1.02) / current_price
    
    # Close any open position at the end
    if position == 1:
        sell_signals[-1] = data.iloc[-1]['close']
    
    return buy_signals, sell_signals


def doge_rsi_strategy(data, rsi_period=14, buy_threshold=30, sell_threshold=70, stop_loss=0.05):
    """
    DOGE trading strategy based on RSI with volume filter and stop loss
    
    Args:
        data (pandas.DataFrame): DataFrame with OHLCV data
        rsi_period (int): Period for RSI calculation
        buy_threshold (float): RSI level to trigger buy signals
        sell_threshold (float): RSI level to trigger sell signals
        stop_loss (float): Initial stop loss percentage
        
    Returns:
        tuple: (buy_signals, sell_signals) lists for backtest runner
    """
    # Calculate RSI
    rsi = calculate_rsi(data, rsi_period)
    
    position = 0  # 0 = no position, 1 = long
    entry_price = 0
    
    # Initialize signals lists
    buy_signals = [None] * len(data)
    sell_signals = [None] * len(data)
    
    # Strategy Implementation
    for i in range(rsi_period + 1, len(data)):
        current_price = data.iloc[i]['close']
        
        # Buy signal: RSI crosses above oversold threshold with volume confirmation
        if (rsi[i-1] <= buy_threshold and 
            rsi[i] > buy_threshold and 
            position == 0 and
            data.iloc[i]['volume'] > calculate_average_volume(data, i, 5)):
            
            position = 1
            entry_price = current_price
            buy_signals[i] = current_price
            
        # Sell signal: RSI crosses above overbought threshold or stop loss
        elif ((rsi[i-1] <= sell_threshold and rsi[i] > sell_threshold and position == 1) or
              # Stop loss condition
              (position == 1 and current_price <= entry_price * (1 - stop_loss))):
            
            sell_signals[i] = current_price
            position = 0
        
        # Add trailing stop once in profit
        elif position == 1 and current_price >= entry_price * 1.15:
            # Update stop loss to breakeven + small profit once we're 15% up
            stop_loss = (entry_price * 1.05) / current_price
    
    # Close any open position at the end
    if position == 1:
        sell_signals[-1] = data.iloc[-1]['close']
    
    return buy_signals, sell_signals


# Helper Functions
def calculate_vwma(data, period):
    """
    Calculate Volume-Weighted Moving Average
    
    Args:
        data (pandas.DataFrame): DataFrame with OHLCV data
        period (int): Period for VWMA calculation
        
    Returns:
        list: List of VWMA values with None for the first period-1 entries
    """
    vwma = []
    
    for i in range(len(data)):
        if i < period - 1:
            vwma.append(None)
        else:
            sum_price_volume = 0
            sum_volume = 0
            
            for j in range(period):
                price = data.iloc[i-j]['close']
                volume = data.iloc[i-j]['volume']
                
                sum_price_volume += price * volume
                sum_volume += volume
            
            vwma.append(sum_price_volume / sum_volume)
    
    return vwma


def calculate_rsi(data, period=14):
    """
    Calculate Relative Strength Index
    
    Args:
        data (pandas.DataFrame): DataFrame with OHLCV data
        period (int): Period for RSI calculation
        
    Returns:
        list: List of RSI values with None for the first period entries
    """
    rsi = []
    changes = []
    
    # Calculate price changes
    for i in range(1, len(data)):
        changes.append(data.iloc[i]['close'] - data.iloc[i-1]['close'])
    
    # Calculate RSI
    for i in range(len(data)):
        if i < period:
            rsi.append(None)
        else:
            gains = 0
            losses = 0
            
            for j in range(period):
                change = changes[i - period + j]
                if change > 0:
                    gains += change
                else:
                    losses -= change
            
            avg_gain = gains / period
            avg_loss = losses / period
            
            if avg_loss == 0:
                rsi.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi.append(100 - (100 / (1 + rs)))
    
    return rsi


def calculate_average_volume(data, current_index, lookback_period):
    """
    Calculate average volume over a lookback period
    
    Args:
        data (pandas.DataFrame): DataFrame with OHLCV data
        current_index (int): Current index position
        lookback_period (int): Number of periods to look back
        
    Returns:
        float: Average volume
    """
    sum_volume = 0
    start_index = max(0, current_index - lookback_period)
    
    for i in range(start_index, current_index):
        sum_volume += data.iloc[i]['volume']
    
    return sum_volume / (current_index - start_index)


# Example usage:
# import pandas as pd
# 
# # Load data
# link_data = pd.read_csv('LINK_OHLCV_0803_0904.csv')
# doge_data = pd.read_csv('DOGE_OHLCV_0803_0904.csv')
# 
# # Convert timestamp if needed
# link_data['timestamp'] = pd.to_datetime(link_data['timestamp'])
# doge_data['timestamp'] = pd.to_datetime(doge_data['timestamp'])
# 
# # Run strategies
# link_trades = link_vwma_strategy(link_data)
# doge_trades = doge_rsi_strategy(doge_data)
# 
# # Calculate overall performance
# link_pnl = sum(trade['pnl'] for trade in link_trades if 'pnl' in trade)
# doge_pnl = sum(trade['pnl'] for trade in doge_trades if 'pnl' in trade)
# 
# print(f"LINK Strategy PnL: {link_pnl:.2%}")
# print(f"DOGE Strategy PnL: {doge_pnl:.2%}")

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


def optimize_link_strategy(data):
    data = data.copy()
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    data['rsi'] = 100 - (100 / (1 + rs))
    data['ma_trend'] = data['close'].rolling(window=20).mean()
    data['volume_ma'] = data['volume'].rolling(window=10).mean()

    buy_signals = []
    sell_signals = []
    in_position = False
    entry_price = 0

    for i in range(len(data)):
        if i < 20:
            buy_signals.append(None)
            sell_signals.append(None)
            continue

        entry_condition = (
            data['rsi'].iloc[i] < 40 and
            data['close'].iloc[i] > data['ma_trend'].iloc[i] and
            data['volume'].iloc[i] > 0.8 * data['volume_ma'].iloc[i]
        )

        if not in_position and entry_condition:
            entry_price = data['close'].iloc[i]
            buy_signals.append(entry_price)
            sell_signals.append(None)
            in_position = True
        elif in_position:
            price = data['close'].iloc[i]
            if price >= entry_price * 1.05 or price <= entry_price * 0.95:
                sell_signals.append(price)
                buy_signals.append(None)
                in_position = False
            else:
                buy_signals.append(None)
                sell_signals.append(None)
        else:
            buy_signals.append(None)
            sell_signals.append(None)

    return buy_signals, sell_signals




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


def optimize_doge_strategy(data):
    data = data.copy()
    data['ma_fast'] = data['close'].rolling(window=6).mean()
    data['ma_slow'] = data['close'].rolling(window=18).mean()
    data['vol_ma'] = data['volume'].rolling(window=12).mean()
    data['momentum'] = data['close'] - data['close'].shift(4)

    buy_signals = []
    sell_signals = []
    in_position = False
    entry_price = 0

    for i in range(len(data)):
        if i < 18:
            buy_signals.append(None)
            sell_signals.append(None)
            continue

        entry_condition = (
            data['ma_fast'].iloc[i] > data['ma_slow'].iloc[i] and
            data['momentum'].iloc[i] > 0 and
            data['volume'].iloc[i] > 1.2 * data['vol_ma'].iloc[i]
        )

        if not in_position and entry_condition:
            entry_price = data['close'].iloc[i]
            buy_signals.append(entry_price)
            sell_signals.append(None)
            in_position = True
        elif in_position:
            price = data['close'].iloc[i]
            if price >= entry_price * 1.03 or price <= entry_price * 0.97:
                sell_signals.append(price)
                buy_signals.append(None)
                in_position = False
            else:
                buy_signals.append(None)
                sell_signals.append(None)
        else:
            buy_signals.append(None)
            sell_signals.append(None)

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
    trades_df.to_csv(os.path.join(output_dir, f"{coin}_noupdate_tariff_trades.csv"), index=False)

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
    summary.to_csv(os.path.join(output_dir, f"{coin}_noupdate_tariff_metrics.csv"), index=False)
    print(f"✅ Finished {coin}: Profit ${total_profit:.2f}, Win Rate {win_rate*100:.1f}%")

# === Run All ===
run_backtest("ETH", eth_queue_bounce_scalper)
run_backtest("LINK", link_vwma_strategy)
run_backtest("ARB", arb_queue_bounce_scalper)
run_backtest("DOGE", doge_breakout_strategy)
