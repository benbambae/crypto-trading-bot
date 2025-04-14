import pandas as pd
import os
import glob

# Get all CSV files in the current directory
metrics_files = glob.glob('*_tariff_metrics.csv')
trades_files = glob.glob('*_tariff_trades.csv')

# Initialize empty lists to store dataframes
metrics_dfs = []
trades_dfs = []

# Process metrics files
for file in metrics_files:
    df = pd.read_csv(file)
    # Extract coin name from filename
    coin_name = file.replace('_tariff_metrics.csv', '')
    df['coin'] = coin_name
    metrics_dfs.append(df)

# Process trades files  
for file in trades_files:
    df = pd.read_csv(file)
    # Extract coin name from filename
    coin_name = file.replace('_tariff_trades.csv', '')
    df['coin'] = coin_name
    trades_dfs.append(df)

# Combine metrics dataframes
if metrics_dfs:
    combined_metrics = pd.concat(metrics_dfs, ignore_index=True)
    # Reorder columns to put coin first
    cols = ['coin'] + [col for col in combined_metrics.columns if col != 'coin']
    combined_metrics = combined_metrics[cols]
    # Save metrics
    combined_metrics.to_csv('BeforeTariff_metrics.csv', index=False)
    print("Metrics successfully collated into BeforeTariff_metrics.csv")
else:
    print("No metrics files found to collate")

# Combine trades dataframes
if trades_dfs:
    combined_trades = pd.concat(trades_dfs, ignore_index=True)
    # Reorder columns to put coin first
    cols = ['coin'] + [col for col in combined_trades.columns if col != 'coin']
    combined_trades = combined_trades[cols]
    # Save trades
    combined_trades.to_csv('BeforeTariff_trades.csv', index=False)
    print("Trades successfully collated into BeforeTariff_trades.csv")
else:
    print("No trades files found to collate")
