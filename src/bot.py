import logging
import time
import pandas as pd
from binance.client import Client
from strategies import moving_average, rsi, macd
import yaml
import os
from datetime import datetime

# Load config.yaml
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')

with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# Set up logging
logging.basicConfig(filename=config['logging']['file'], level=logging.INFO, format='%(asctime)s %(message)s')

# Initialize Binance client
client = Client(config['binance']['test_api_key'], config['binance']['test_secret_key'])

class TradingBot:
    def __init__(self):
        self.symbol = config['trading']['symbol']
        self.capital = config['trading']['capital']
        self.position = None
        self.entry_price = None
        self.strategy = config['strategies']['default_strategy']
        self.max_risk = config.get('trading', {}).get('risk', 0.01)  # Optional risk management

    def fetch_data(self, limit=200):
        """Fetch real-time price data from Binance."""
        try:
            klines = client.get_klines(symbol=self.symbol, interval=config['trading']['interval'], limit=limit)
            data = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                                 'close_time', 'quote_asset_volume', 'number_of_trades',
                                                 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
            data['close'] = pd.to_numeric(data['close'])
            data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
            return data
        except Exception as e:
            logging.error(f"Error fetching data: {e}")
            return pd.DataFrame()

    def apply_strategy(self, data):
        """Apply the selected strategy to make trading decisions."""
        if data.empty:
            logging.warning("No data to apply strategy on")
            return [], []

        logging.info(f"Applying {self.strategy} strategy...")
        if self.strategy == 'moving_average':
            return moving_average(data)
        elif self.strategy == 'rsi':
            return rsi(data)
        elif self.strategy == 'macd':
            return macd(data)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    def execute_trade(self, buy_signals, sell_signals):
        """Simulate executing a trade based on buy/sell signals."""
        latest_buy_signal = buy_signals[-1] if buy_signals else None
        latest_sell_signal = sell_signals[-1] if sell_signals else None

        # Buy if we are not in a position
        if latest_buy_signal and self.position is None:
            self.position = 'long'
            self.entry_price = latest_buy_signal
            logging.info(f"BUY at {self.entry_price}")

        # Sell if we are in a position
        elif latest_sell_signal and self.position == 'long':
            profit = (latest_sell_signal - self.entry_price) * (self.capital / self.entry_price)
            self.capital += profit
            self.position = None
            self.entry_price = None
            logging.info(f"SELL at {latest_sell_signal}, Profit: {profit:.2f}")

        # Add risk management (e.g., stop-loss), only if there's a valid sell signal
        if self.position == 'long' and latest_sell_signal is not None and (self.entry_price - latest_sell_signal) / self.entry_price > self.max_risk:
            logging.info(f"Stop-loss triggered at {latest_sell_signal}")
            profit = (latest_sell_signal - self.entry_price) * (self.capital / self.entry_price)
            self.capital += profit
            self.position = None
            self.entry_price = None
            logging.info(f"SELL at {latest_sell_signal}, Profit: {profit:.2f} due to stop-loss")


    def run(self):
        """Main loop to run the bot."""
        while True:
            data = self.fetch_data()
            if not data.empty:
                buy_signals, sell_signals = self.apply_strategy(data)
                self.execute_trade(buy_signals, sell_signals)
                logging.info(f"Current Capital: {self.capital}")
            else:
                logging.warning("No data fetched, skipping this cycle")
            time.sleep(60)  # Run every minute

if __name__ == '__main__':
    bot = TradingBot()
    bot.run()
