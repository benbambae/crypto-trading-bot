from binance.client import Client
import yaml
import os
import pandas as pd
from strategies import moving_average_strategy

# Load config.yaml
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')

with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# Initialize Binance Client (Testnet)
client = Client(config['binance']['test_api_key'], config['binance']['test_secret_key'])
client.API_URL = 'https://testnet.binance.vision/api'

# Fetch real market data using Binance API
def get_market_data(client, symbol):
    candles = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1HOUR)
    # Create a DataFrame for the market data
    df = pd.DataFrame(candles, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['close'] = df['close'].astype(float)
    return df

# Simulation bot: No actual trading on Binance
def run_simulation_bot():
    symbol = config['trading']['default_symbol']
    virtual_balance = 1000000  # Start with a $1000 virtual balance
    position = 0  # Number of units (BTC, ETH, etc.)
    price_per_unit = 0  # Track the price at which a unit was bought

    print("Simulation started with virtual balance of $1000.")

    while True:
        # Fetch real market data using Binance API (for simulation)
        market_data = get_market_data(client, symbol)  # Fetch real-time data

        # Execute strategy to decide whether to buy, sell, or hold
        decision = moving_average_strategy(market_data)

        # Simulate buy or sell order based on the decision
        current_price = market_data['close'].iloc[-1]  # Get the latest closing price

        if decision == 'buy':
            amount_to_buy = virtual_balance / current_price  # Buy as much as balance allows
            if amount_to_buy > 0:
                position += amount_to_buy  # Buy fractional units
                price_per_unit = current_price  # Record the price bought at
                virtual_balance -= amount_to_buy * current_price  # Reduce virtual balance
                print(f"Bought {amount_to_buy:.4f} units at {current_price}. Virtual balance: {virtual_balance}, Position: {position:.4f}")

        elif decision == 'sell' and position > 0:
            amount_to_sell = position  # Sell all holdings
            position = 0  # Clear position
            virtual_balance += amount_to_sell * current_price  # Add sale price to balance
            profit_or_loss = (current_price - price_per_unit) * amount_to_sell  # Calculate P/L
            print(f"Sold {amount_to_sell:.4f} units at {current_price}. Profit/Loss: {profit_or_loss}, Virtual balance: {virtual_balance}")

        else:
            print(f"Holding... Current Price: {current_price}, Virtual balance: {virtual_balance}, Position: {position:.4f}")
        
        # Add a short delay (e.g., use time.sleep()) to simulate real-time trading if necessary

if __name__ == "__main__":
    run_simulation_bot()
