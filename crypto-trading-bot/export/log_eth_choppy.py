import pandas as pd
import numpy as np
import logging

# Setup logging
logging.basicConfig(
    filename='eth_choppy_analysis.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

# Load data
df = pd.read_csv('eth_choppy_durability_data.csv', parse_dates=['timestamp'])

# Sort by timestamp
df.sort_values(by='timestamp', inplace=True)

# Calculate additional metrics
df['return'] = df['close'].pct_change()
df['volatility'] = df['return'].rolling(window=14).std()
df['price_range'] = df['high'] - df['low']
df['volume_avg'] = df['volume'].rolling(window=14).mean()
df['volume_spike'] = df['volume'] > 1.5 * df['volume_avg']

# Logging metrics
logging.info(f"Data Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
logging.info(f"Total rows: {len(df)}")
logging.info(f"Mean Close: {df['close'].mean():.2f}")
logging.info(f"Volatility (last): {df['volatility'].iloc[-1]:.4f}")
logging.info(f"Max Drawdown Period (high-low): {df['price_range'].max():.2f}")
logging.info(f"Volume Spike Count: {df['volume_spike'].sum()}")

# Print example rows with volatility + volume spike
spikes = df[df['volume_spike'] & df['volatility'].notnull()].tail(10)
for i, row in spikes.iterrows():
    logging.info(f"{row['timestamp']} | Close: {row['close']:.2f} | Volatility: {row['volatility']:.4f} | Volume: {row['volume']:.2f}")

print("Done. Log file generated: eth_choppy_analysis.log")
