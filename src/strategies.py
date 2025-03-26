import pandas as pd
import numpy as np

def rsi_macd_pullback(data, rsi_period=14, macd_fast=12, macd_slow=26, macd_signal=9):
    """
    RSI/MACD Pullback + Trend Continuation Strategy optimized for Ethereum
    Modified to be more aggressive with moving average signals while maintaining core strategy
    """
    # === Core Indicators ===
    # RSI Calculation with smoothing
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0).ewm(span=rsi_period, adjust=False).mean()
    loss = -delta.where(delta < 0, 0).ewm(span=rsi_period, adjust=False).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD with optimized parameters for ETH
    data['ema_fast'] = data['close'].ewm(span=macd_fast, adjust=False).mean()
    data['ema_slow'] = data['close'].ewm(span=macd_slow, adjust=False).mean()
    data['macd'] = data['ema_fast'] - data['ema_slow']
    data['macd_signal'] = data['macd'].ewm(span=macd_signal, adjust=False).mean()
    data['macd_hist'] = data['macd'] - data['macd_signal']
    
    # Moving Averages for more aggressive trend following
    data['ma_10'] = data['close'].rolling(window=10).mean()  # Faster MA
    data['ma_30'] = data['close'].rolling(window=30).mean()  # Medium MA
    data['ma_50'] = data['close'].rolling(window=50).mean()  # Slower MA
    
    # Volume Analysis
    data['vol_sma'] = data['volume'].rolling(window=20).mean()
    data['vol_ratio'] = data['volume'] / data['vol_sma']
    
    # ATR for volatility-based exits
    data['tr'] = pd.DataFrame({
        'hl': data['high'] - data['low'],
        'hc': abs(data['high'] - data['close'].shift()),
        'lc': abs(data['low'] - data['close'].shift())
    }).max(axis=1)
    data['atr'] = data['tr'].ewm(span=14).mean()
    
    buy_signals = []
    sell_signals = []
    in_position = False
    entry_price = 0
    trailing_stop = 0
    
    for i in range(len(data)):
        if i < 50:  # Wait for indicators to warm up
            buy_signals.append(None)
            sell_signals.append(None)
            continue
            
        current_price = data['close'].iloc[i]
        
        if in_position:
            # Update trailing stop - tighter now for faster exits
            trailing_stop = max(trailing_stop, current_price - 2 * data['atr'].iloc[i])
            
            # More aggressive sell conditions incorporating MA crossovers
            sell_condition = (
                (current_price < trailing_stop) or  # Trail stop hit
                (data['ma_10'].iloc[i] < data['ma_30'].iloc[i]) or  # Fast MA crosses below medium
                (current_price < data['ma_30'].iloc[i] and  # Price breaks below medium MA
                 data['macd_hist'].iloc[i] < 0) or
                (data['rsi'].iloc[i] > 70)  # RSI overbought
            )
            
            if sell_condition:
                buy_signals.append(None)
                sell_signals.append(current_price)
                in_position = False
                continue
        
        # More aggressive MA-based trend identification
        trend_up = (
            data['ma_10'].iloc[i] > data['ma_30'].iloc[i] > data['ma_50'].iloc[i] and
            current_price > data['ma_10'].iloc[i]
        )
        
        # Buy conditions combining MA crossovers with original strategy
        ma_cross = (
            data['ma_10'].iloc[i] > data['ma_30'].iloc[i] and
            data['ma_10'].iloc[i-1] <= data['ma_30'].iloc[i-1]
        )
        
        rsi_condition = data['rsi'].iloc[i] < 40  # Less strict RSI condition
        macd_cross = (data['macd'].iloc[i] > data['macd_signal'].iloc[i] and 
                     data['macd'].iloc[i-1] <= data['macd_signal'].iloc[i-1])
        volume_surge = data['vol_ratio'].iloc[i] > 1.1  # Slightly relaxed volume requirement
        
        buy_condition = (
            not in_position and
            trend_up and
            (ma_cross or (rsi_condition and macd_cross)) and
            volume_surge and
            data['macd_hist'].iloc[i] > data['macd_hist'].iloc[i-1]  # Increasing momentum
        )
        
        if buy_condition:
            buy_signals.append(current_price)
            sell_signals.append(None)
            in_position = True
            entry_price = current_price
            trailing_stop = current_price - 2 * data['atr'].iloc[i]
        else:
            buy_signals.append(None)
            sell_signals.append(None)
            
    return buy_signals, sell_signals

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

def rsi(data, window=14, buy_threshold=35, sell_threshold=65):
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
    """Implements Bollinger Bands strategy with RSI and trend confirmation."""
    # Calculate Bollinger Bands
    data['bb_middle'] = data['close'].rolling(window=window).mean()
    data['bb_std'] = data['close'].rolling(window=window).std()
    data['bb_upper'] = data['bb_middle'] + (data['bb_std'] * num_std)
    data['bb_lower'] = data['bb_middle'] - (data['bb_std'] * num_std)
    
    # Add RSI for confirmation with more lenient thresholds
    delta = data['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))
    
    # Add trend confirmation
    data['trend_ma'] = data['close'].ewm(span=50, adjust=False).mean()
    
    buy_signals = []
    sell_signals = []
    
    for i in range(len(data)):
        if i == 0:
            buy_signals.append(None)
            sell_signals.append(None)
            continue
            
        # Buy when price is near lower band (within 0.2%) and RSI < 40
        # Also require upward momentum and price above short trend
        if (data['close'].iloc[i] <= data['bb_lower'].iloc[i] * 1.002 and
            data['rsi'].iloc[i] < 40 and
            data['close'].iloc[i] > data['close'].iloc[i-1] and
            data['close'].iloc[i] > data['trend_ma'].iloc[i]):
            buy_signals.append(data['close'].iloc[i])
            sell_signals.append(None)
        # Sell when price is near upper band (within 0.2%) or RSI > 60
        # Or if price drops below trend
        elif ((data['close'].iloc[i] >= data['bb_upper'].iloc[i] * 0.998 and
               data['close'].iloc[i] < data['close'].iloc[i-1]) or
              data['rsi'].iloc[i] > 60 or
              data['close'].iloc[i] < data['trend_ma'].iloc[i]):
            buy_signals.append(None)
            sell_signals.append(data['close'].iloc[i])
        else:
            buy_signals.append(None)
            sell_signals.append(None)
            
    return buy_signals, sell_signals

def hybrid_strategy(data, bb_window=20, bb_std=2, rsi_window=14, fast_ma=12, slow_ma=26):
    """
    Advanced hybrid strategy combining Bollinger Bands, RSI, and Moving Averages
    with optimized parameters based on backtest results.
    """
    # Calculate Bollinger Bands
    data['bb_middle'] = data['close'].rolling(window=bb_window).mean()
    data['bb_std'] = data['close'].rolling(window=bb_window).std()
    data['bb_upper'] = data['bb_middle'] + (data['bb_std'] * bb_std)
    data['bb_lower'] = data['bb_middle'] - (data['bb_std'] * bb_std)
    
    # Calculate RSI
    delta = data['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_window).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))
    
    # Calculate Moving Averages
    data['ema_fast'] = data['close'].ewm(span=fast_ma, adjust=False).mean()
    data['ema_slow'] = data['close'].ewm(span=slow_ma, adjust=False).mean()
    data['macd'] = data['ema_fast'] - data['ema_slow']
    data['signal'] = data['macd'].ewm(span=9, adjust=False).mean()
    
    # Volume trend
    data['volume_ma'] = data['volume'].rolling(window=20).mean()
    
    buy_signals = []
    sell_signals = []
    
    for i in range(len(data)):
        if i < slow_ma:
            buy_signals.append(None)
            sell_signals.append(None)
            continue
            
        # Buy conditions (more conservative based on backtest results)
        buy_condition = (
            # Price near lower BB with cushion
            data['close'].iloc[i] <= data['bb_lower'].iloc[i] * 1.005 and
            # RSI showing oversold but not extreme
            data['rsi'].iloc[i] < 45 and data['rsi'].iloc[i] > 25 and
            # Positive MACD momentum
            data['macd'].iloc[i] > data['macd'].iloc[i-1] and
            # Volume confirmation
            data['volume'].iloc[i] > data['volume_ma'].iloc[i] and
            # Trend confirmation
            data['close'].iloc[i] > data['close'].iloc[i-3]
        )
        
        # Sell conditions (more aggressive profit taking)
        sell_condition = (
            # Price near upper BB
            (data['close'].iloc[i] >= data['bb_upper'].iloc[i] * 0.995) or
            # RSI overbought
            (data['rsi'].iloc[i] > 70) or
            # MACD bearish cross
            (data['macd'].iloc[i] < data['signal'].iloc[i] and 
             data['macd'].iloc[i-1] > data['signal'].iloc[i-1]) or
            # Stop loss - trend reversal
            (data['close'].iloc[i] < data['ema_slow'].iloc[i] and
             data['close'].iloc[i] < data['close'].iloc[i-2])
        )
        
        if buy_condition:
            buy_signals.append(data['close'].iloc[i])
            sell_signals.append(None)
        elif sell_condition:
            buy_signals.append(None)
            sell_signals.append(data['close'].iloc[i])
        else:
            buy_signals.append(None)
            sell_signals.append(None)
            
    return buy_signals, sell_signals


def advanced_hybrid_strategy(data, higher_tf_data):
    """
    Enhanced hybrid strategy with optimized parameters and additional filters:
    - Multi-timeframe analysis (1h and 4h)
    - Price action patterns
    - Enhanced trend detection
    - Dynamic volatility thresholds
    - Risk management rules
    """
    # === CORE INDICATORS ===
    # MACD with optimized parameters
    data['ema_fast'] = data['close'].ewm(span=8).mean()  # Faster response
    data['ema_slow'] = data['close'].ewm(span=21).mean() # More reactive
    data['macd'] = data['ema_fast'] - data['ema_slow']
    data['signal'] = data['macd'].ewm(span=5).mean()  # Quicker signal line
    data['histogram'] = data['macd'] - data['signal']

    # Enhanced RSI calculation
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0).ewm(span=10).mean()  # Using EMA for smoother RSI
    loss = -delta.where(delta < 0, 0).ewm(span=10).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))

    # Dynamic ATR for volatility measurement
    data['tr'] = pd.DataFrame({
        'hl': data['high'] - data['low'],
        'hc': abs(data['high'] - data['close'].shift()),
        'lc': abs(data['low'] - data['close'].shift())
    }).max(axis=1)
    data['atr'] = data['tr'].ewm(span=10).mean()

    # === PRICE ACTION PATTERNS ===
    data['body'] = data['close'] - data['open']
    data['upper_wick'] = data['high'] - data['close'].where(data['close'] > data['open'], data['open'])
    data['lower_wick'] = data['close'].where(data['close'] < data['open'], data['open']) - data['low']
    
    # === TREND STRENGTH ===
    data['supertrend'] = data['close'].ewm(span=30).mean()  # Longer-term trend
    data['short_trend'] = data['close'].ewm(span=10).mean()  # Short-term trend

    # === VOLUME ANALYSIS ===
    data['vol_ema'] = data['volume'].ewm(span=10).mean()
    data['vol_ratio'] = data['volume'] / data['vol_ema']

    # === SIGNAL GENERATION ===
    buy_signals = []
    sell_signals = []
    in_position = False
    entry_price = 0
    max_price = 0

    for i in range(len(data)):
        if i < 30:  # Warm-up period
            buy_signals.append(None)
            sell_signals.append(None)
            continue

        current_price = data['close'].iloc[i]
        
        if in_position:
            max_price = max(max_price, current_price)
            # Dynamic trailing stop based on ATR
            stop_loss = max_price - (data['atr'].iloc[i] * 2)
            
            # Sell conditions when in position
            sell_condition = (
                (current_price < stop_loss) or  # Trailing stop hit
                (data['rsi'].iloc[i] > 80 and data['vol_ratio'].iloc[i] > 1.5) or  # Overbought with volume
                (current_price < data['supertrend'].iloc[i] and data['histogram'].iloc[i] < 0)  # Trend reversal
            )
            
            if sell_condition:
                buy_signals.append(None)
                sell_signals.append(current_price)
                in_position = False
                continue

        # Enhanced buy conditions
        trend_strength = (data['short_trend'].iloc[i] > data['supertrend'].iloc[i])
        momentum_positive = (data['histogram'].iloc[i] > 0 and data['histogram'].iloc[i] > data['histogram'].iloc[i-1])
        volume_confirmation = (data['vol_ratio'].iloc[i] > 1.2)
        price_pattern = (data['body'].iloc[i] > 0 and data['lower_wick'].iloc[i] < abs(data['body'].iloc[i]) * 0.5)
        
        # Higher timeframe confirmation
        if i < len(higher_tf_data):
            higher_tf_trend = higher_tf_data['close'].iloc[i] > higher_tf_data['close'].iloc[i-1]
        else:
            higher_tf_trend = True

        buy_condition = (
            not in_position and
            trend_strength and
            momentum_positive and
            volume_confirmation and
            price_pattern and
            higher_tf_trend and
            data['rsi'].iloc[i] < 60  # Not overbought
        )

        if buy_condition:
            buy_signals.append(current_price)
            sell_signals.append(None)
            in_position = True
            entry_price = current_price
            max_price = current_price
        else:
            buy_signals.append(None)
            sell_signals.append(None)

    return buy_signals, sell_signals
