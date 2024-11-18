import logging
import time
import pandas as pd
from binance.client import Client
from strategies import moving_average, rsi, macd  # Import strategy modules
import yaml
import os
from datetime import datetime
from typing import Tuple, List, Optional, Dict, Any

# Load config.yaml from parent directory's config folder
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')

with open(config_path, 'r') as file:
    config = yaml.safe_load(file)  # Load YAML config into dict

# Configure logging with file output and timestamp format
logging.basicConfig(
    filename=config['logging']['file'],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize Binance client with test API keys and testnet URL
client = Client(config['binance']['test_api_key'], config['binance']['test_secret_key'])
client.API_URL = 'https://testnet.binance.vision/api'  # Use testnet for paper trading

class TradingBot:
    """Trading bot that executes trades based on technical analysis strategies."""
    
    def __init__(self):
        """Initialize trading bot with configuration parameters."""
        self.symbol: str = config['trading']['symbol']  # Trading pair (e.g. ETHUSDT)
        self.capital: float = config['trading']['capital']  # Starting capital
        self.initial_capital: float = self.capital  # Store initial capital for performance tracking
        self.position: Optional[str] = None  # Current position (long/None)
        self.entry_price: Optional[float] = None  # Entry price of current position
        self.strategy: str = config['strategies']['default_strategy']  # Selected strategy
        self.max_risk: float = config.get('trading', {}).get('risk', 0.01)  # Max risk per trade (1% default)
        self.trades_history: List[Dict[str, Any]] = []  # List to track all trades

    def fetch_data(self, limit: int = 200) -> pd.DataFrame:
        """
        Fetch real-time price data from Binance.
        
        Args:
            limit: Number of candlesticks to fetch
            
        Returns:
            DataFrame containing price data
        """
        try:
            # Get candlestick data from Binance API
            klines = client.get_klines(
                symbol=self.symbol,
                interval=config['trading']['interval'],
                limit=limit
            )
            
            # Convert to DataFrame with named columns
            data = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert numeric columns and timestamp
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric)
            data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
            
            return data
            
        except Exception as e:
            logging.error(f"Error fetching data: {str(e)}")
            return pd.DataFrame()  # Return empty DataFrame on error

    def apply_strategy(self, data: pd.DataFrame) -> Tuple[List[float], List[float]]:
        """
        Apply the selected trading strategy to make trading decisions.
        
        Args:
            data: DataFrame containing price data
            
        Returns:
            Tuple containing buy and sell signals
        """
        if data.empty:
            logging.warning("No data to apply strategy on")
            return [], []

        logging.info(f"Applying {self.strategy} strategy...")
        try:
            # Call appropriate strategy function based on config
            if self.strategy == 'moving_average':
                return moving_average(data)
            elif self.strategy == 'rsi':
                return rsi(data)
            elif self.strategy == 'macd':
                return macd(data)
            else:
                raise ValueError(f"Unknown strategy: {self.strategy}")
        except Exception as e:
            logging.error(f"Error applying strategy: {str(e)}")
            return [], []

    def execute_trade(self, buy_signals: List[float], sell_signals: List[float]) -> None:
        """
        Execute trades based on strategy signals with risk management.
        
        Args:
            buy_signals: List of buy signal prices
            sell_signals: List of sell signal prices
        """
        # Get latest signals
        latest_buy_signal = buy_signals[-1] if buy_signals else None
        latest_sell_signal = sell_signals[-1] if sell_signals else None
        current_time = datetime.now()

        # Execute buy order if we have a buy signal and no position
        if latest_buy_signal and self.position is None:
            self.position = 'long'
            self.entry_price = latest_buy_signal
            self.trades_history.append({
                'type': 'buy',
                'price': self.entry_price,
                'time': current_time,
                'capital': self.capital
            })
            logging.info(f"BUY signal executed at {self.entry_price}")

        # Execute sell order if we have a sell signal and long position
        elif latest_sell_signal and self.position == 'long':
            profit = (latest_sell_signal - self.entry_price) * (self.capital / self.entry_price)
            self.capital += profit
            self.position = None
            self.trades_history.append({
                'type': 'sell',
                'price': latest_sell_signal,
                'time': current_time,
                'profit': profit,
                'capital': self.capital
            })
            logging.info(f"SELL signal executed at {latest_sell_signal}, Profit: {profit:.2f}")
            self.entry_price = None

        # Check stop-loss - exit if loss exceeds max risk
        if (self.position == 'long' and latest_sell_signal is not None and 
            (self.entry_price - latest_sell_signal) / self.entry_price > self.max_risk):
            
            profit = (latest_sell_signal - self.entry_price) * (self.capital / self.entry_price)
            self.capital += profit
            self.position = None
            self.trades_history.append({
                'type': 'stop_loss',
                'price': latest_sell_signal,
                'time': current_time,
                'profit': profit,
                'capital': self.capital
            })
            logging.warning(f"Stop-loss triggered at {latest_sell_signal}, Loss: {profit:.2f}")
            self.entry_price = None

    def run(self) -> None:
        """Main trading loop with performance tracking."""
        logging.info(f"Starting trading bot with {self.capital} initial capital")
        try:
            while True:
                data = self.fetch_data()
                if not data.empty:
                    buy_signals, sell_signals = self.apply_strategy(data)
                    self.execute_trade(buy_signals, sell_signals)
                    
                    # Calculate and log performance metrics
                    total_return = ((self.capital - self.initial_capital) / self.initial_capital) * 100
                    logging.info(f"Current Capital: {self.capital:.2f} | Return: {total_return:.2f}%")
                else:
                    logging.warning("No data fetched, skipping this cycle")
                    
                time.sleep(60)  # Wait 1 minute before next iteration
                
        except KeyboardInterrupt:
            logging.info("Trading bot stopped by user")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
        finally:
            self._log_final_performance()  # Log final stats on exit
    
    def _log_final_performance(self) -> None:
        """Log final trading performance metrics."""
        # Calculate performance statistics
        total_trades = len(self.trades_history)
        profitable_trades = len([t for t in self.trades_history if t.get('profit', 0) > 0])
        total_profit = sum(t.get('profit', 0) for t in self.trades_history)
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Log summary statistics
        logging.info("=== Trading Session Summary ===")
        logging.info(f"Total Trades: {total_trades}")
        logging.info(f"Profitable Trades: {profitable_trades}")
        logging.info(f"Win Rate: {win_rate:.2f}%")
        logging.info(f"Total Profit: {total_profit:.2f}")
        logging.info(f"Final Capital: {self.capital:.2f}")

if __name__ == '__main__':
    bot = TradingBot()  # Create bot instance
    bot.run()  # Start trading loop
