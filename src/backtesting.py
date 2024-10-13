import os
import pandas as pd
from binance.client import Client
from strategies import moving_average, rsi, macd
import yaml
from datetime import datetime

# Load config.yaml
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')

with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# Initialize Binance client
client = Client(config['binance']['test_api_key'], config['binance']['test_secret_key'])

class Backtest:
    def __init__(self):
        self.symbol = config['trading']['symbol']
        self.strategy = config['strategies']['default_strategy']
        self.start_date = config['backtest']['start_date']
        self.end_date = config['backtest']['end_date']
        self.capital = config['trading']['capital']
        self.position = None
        self.entry_price = None

    def fetch_historical_data(self, start_date, end_date, limit=1000):
        """Fetch historical data from Binance within a date range."""
        # Convert start and end dates to required format
        start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d %b, %Y')
        end_date = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d %b, %Y')
        print(f"Fetching historical data from {start_date} to {end_date}...")

        klines = client.get_historical_klines(self.symbol, config['trading']['interval'], start_date, end_date)
        
        if not klines:
            print("No data fetched. Check the date range or API limits.")
            return pd.DataFrame()

        # Create DataFrame from klines data
        data = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                             'close_time', 'quote_asset_volume', 'number_of_trades',
                                             'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        data['close'] = pd.to_numeric(data['close'])
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')

        # Log number of rows fetched
        print(f"Fetched {len(data)} rows of data")
        return data

    def apply_strategy(self, data):
        """Apply the selected strategy to make trading decisions."""
        if data.empty:
            print("No data available to apply strategy.")
            return [], []
        
        print(f"Applying {self.strategy} strategy...")
        
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
        for i in range(len(buy_signals)):
            if buy_signals[i] and self.position is None:
                self.position = 'long'
                self.entry_price = buy_signals[i]
                print(f"BUY at {self.entry_price}")

            elif sell_signals[i] and self.position == 'long':
                profit = (sell_signals[i] - self.entry_price) * (self.capital / self.entry_price)
                self.capital += profit
                self.position = None
                self.entry_price = None
                print(f"SELL at {sell_signals[i]}, Profit: {profit:.2f}")
    
    def run(self):
        """Run the backtest over the given time frame."""
        print(f"Starting backtest from {self.start_date} to {self.end_date}...")
        data = self.fetch_historical_data(self.start_date, self.end_date)
        
        if not data.empty:
            buy_signals, sell_signals = self.apply_strategy(data)
            self.execute_trade(buy_signals, sell_signals)
        else:
            print("No data returned for the backtest.")
        
        print(f"Final Capital: {self.capital}")

if __name__ == '__main__':
    backtest = Backtest()
    backtest.run()
