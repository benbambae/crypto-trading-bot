from binance.client import Client
import pandas as pd
import yaml
import os
from strategies import moving_average_strategy

# Load config.yaml
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')

with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# Initialize Binance Client (Testnet)
client = Client(config['binance']['test_api_key'], config['binance']['test_secret_key'])
client.API_URL = 'https://testnet.binance.vision/api'

# Fetch historical market data using Binance API
def get_market_data(client, symbol):
    # Fetch the market data with correct parameters
    candles = client.get_klines(
        symbol=symbol, 
        interval=Client.KLINE_INTERVAL_1HOUR, 
        startTime=client._get_earliest_valid_timestamp(symbol, Client.KLINE_INTERVAL_1HOUR),
        endTime=None
    )
    
    # Create a DataFrame for the market data
    df = pd.DataFrame(candles, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 
                                        'close_time', 'quote_asset_volume', 'number_of_trades', 
                                        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['close'] = df['close'].astype(float)
    return df

# Backtest function to simulate the trading strategy on historical data
def backtest(client, symbol):
    data = get_market_data(client, symbol)
    balance = 1000000  # Starting balance in USD
    position = 0  # Number of coins held
    price_per_unit = 0  # Track the price at which a unit was bought

    for index, row in data.iterrows():
        decision = moving_average_strategy(data[:index+1])

        # Debug output to see the decisions being made
        print(f"Decision: {decision}, Price: {row['close']:.2f}")

        if decision == 'buy' and balance >= row['close']:
            amount_to_buy = balance / row['close']  # Buy as much as balance allows
            position += amount_to_buy  # Update position
            balance -= amount_to_buy * row['close']  # Reduce balance
            price_per_unit = row['close']  # Track price at which we bought
            print(f"Bought {amount_to_buy:.4f} units at {row['close']:.2f}. Balance: {balance:.2f}, Position: {position:.4f}")

        elif decision == 'sell' and position > 0:
            amount_to_sell = position  # Sell all units
            balance += amount_to_sell * row['close']  # Add selling value to balance
            profit_or_loss = (row['close'] - price_per_unit) * amount_to_sell  # Calculate profit/loss
            print(f"Sold {amount_to_sell:.4f} units at {row['close']:.2f}. Profit/Loss: {profit_or_loss:.2f}, Balance: {balance:.2f}")
            position = 0  # Reset position to 0

    print(f'Final balance: {balance:.2f} USD, Final position: {position:.4f} coins')

if __name__ == "__main__":
    backtest(client, 'BTCUSDT')
