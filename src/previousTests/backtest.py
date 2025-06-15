# Standard library imports
import os
import logging
from datetime import datetime
from typing import Tuple, List, Optional
import math

# Third party imports
import pandas as pd
import numpy as np
import yaml
from binance.client import Client

# Local imports
from strategies import moving_average, rsi, macd, bollinger_bands, hybrid_strategy, advanced_hybrid_strategy, rsi_macd_pullback

# Load configuration from config.yaml
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')

with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'backtest_logs')
os.makedirs(log_dir, exist_ok=True)

# Configure logging to file with timestamp in filename
current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = os.path.join(log_dir, f'backtest_{current_time}.log')

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Add file handler to also write to a summary file
summary_handler = logging.FileHandler(os.path.join(log_dir, 'backtest_summary.log'))
summary_handler.setLevel(logging.INFO)
summary_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
logging.getLogger('').addHandler(summary_handler)

# Initialize Binance API client with test credentials
client = Client(config['binance']['test_api_key'], config['binance']['test_secret_key'])

def choose_strategy() -> str:
    """
    Allow user to choose a trading strategy.
    Returns the chosen strategy name.
    """
    strategies = {
        '1': 'moving_average',
        '2': 'rsi', 
        '3': 'macd',
        '4': 'bollinger_bands',
        '5': 'hybrid_strategy',
        '6': 'advanced_hybrid_strategy',
        '7': 'rsi_macd_pullback'
    }
    
    print("\nAvailable Trading Strategies:")
    for key, strategy in strategies.items():
        print(f"{key}. {strategy}")
        
    while True:
        choice = input("\nChoose a strategy (1-7): ")
        if choice in strategies:
            return strategies[choice]
        print("Invalid choice. Please select a number between 1 and 7.")

class Backtest:
    """
    A class for backtesting trading strategies using historical price data.
    
    This class allows testing of different trading strategies on historical data
    to evaluate their performance before live trading.
    
    Attributes:
        symbol: Trading pair symbol (e.g. 'BTCUSDT')
        strategy: Trading strategy to test
        start_date: Beginning of backtest period
        end_date: End of backtest period
        initial_capital: Starting capital amount
        capital: Current capital amount
        position: Current trading position ('long' or None)
        entry_price: Price at which current position was entered
        trades: List of executed trades
        performance_metrics: Dictionary of backtest performance statistics
    """
    
    def __init__(self, strategy: Optional[str] = None):
        """Initialize backtest parameters from config file."""
        self.symbol = config['trading']['symbol']
        self.strategy = strategy if strategy else choose_strategy()
        self.start_date = config['backtest']['start_date']
        self.end_date = config['backtest']['end_date']
        self.initial_capital = config['trading']['capital']
        self.capital = self.initial_capital
        self.position: Optional[str] = None
        self.entry_price: Optional[float] = None
        self.trades: List[dict] = []
        self.daily_returns = []
        self.performance_metrics = {
            'total_trades': 0,
            'profitable_trades': 0,
            'total_profit': 0,
            'win_rate': 0,
            'return_pct': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'avg_profit_per_trade': 0,
            'avg_loss_per_trade': 0,
            'profit_factor': 0,
            'risk_reward_ratio': 0
        }
        
        logging.info("=== BACKTEST INITIALIZATION ===")
        logging.info(f"Symbol: {self.symbol}")
        logging.info(f"Strategy: {self.strategy}")
        logging.info(f"Period: {self.start_date} to {self.end_date}")
        logging.info(f"Initial Capital: ${self.initial_capital:,.2f}")

    def fetch_historical_data(self, start_date: str, end_date: str, limit: int = 1000) -> pd.DataFrame:
        """
        Fetch historical price data from Binance within a date range.
        """
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d %b, %Y')
            end_date = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d %b, %Y')
            logging.info("=== FETCHING HISTORICAL DATA ===")
            logging.info(f"Requesting data from {start_date} to {end_date}")

            klines = client.get_historical_klines(
                self.symbol, 
                config['trading']['interval'],
                start_date,
                end_date
            )
            
            if not klines:
                logging.error("❌ No data received from Binance API")
                return pd.DataFrame()

            data = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric)
            data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
            
            logging.info(f"✓ Successfully fetched {len(data):,} data points")
            return data

        except Exception as e:
            logging.error(f"❌ Error fetching data: {str(e)}")
            return pd.DataFrame()

    def apply_strategy(self, data: pd.DataFrame) -> Tuple[List, List]:
        """
        Apply the selected trading strategy to historical data.
        """
        if data.empty:
            logging.error("❌ Cannot apply strategy - No data available")
            return [], []
        
        logging.info("=== APPLYING STRATEGY ===")
        logging.info(f"Strategy: {self.strategy}")
        
        try:
            if self.strategy == 'moving_average':
                signals = moving_average(data)
            elif self.strategy == 'rsi':
                signals = rsi(data)
            elif self.strategy == 'macd':
                signals = macd(data)
            elif self.strategy == 'bollinger_bands':
                signals = bollinger_bands(data)
            elif self.strategy == 'hybrid_strategy':
                signals = hybrid_strategy(data)
            elif self.strategy == 'rsi_macd_pullback':
                signals = rsi_macd_pullback(data)
            elif self.strategy == 'advanced_hybrid_strategy':
                # For advanced hybrid strategy, we need higher timeframe data
                # Resample current data to 4h for higher timeframe analysis
                higher_tf_data = data.resample('4h', on='timestamp').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min', 
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
                signals = advanced_hybrid_strategy(data, higher_tf_data)
                
                # Update entry price based on advanced strategy signals
                if signals[0] and not self.position:
                    self.entry_price = data['close'].iloc[-1]
                
            else:
                raise ValueError(f"Unknown strategy: {self.strategy}")
                
            logging.info("✓ Strategy signals generated successfully")
            return signals
        except Exception as e:
            logging.error(f"❌ Strategy application failed: {str(e)}")
            return [], []

    def execute_trade(self, buy_signals: List[float], sell_signals: List[float]) -> None:
        """
        Simulate executing trades based on strategy signals.
        """
        logging.info("=== EXECUTING TRADES ===")
        
        for i in range(len(buy_signals)):
            if buy_signals[i] and self.position is None:
                self.position = 'long'
                self.entry_price = buy_signals[i]
                self.trades.append({
                    'type': 'buy',
                    'price': self.entry_price,
                    'capital': self.capital,
                    'timestamp': datetime.now()
                })
                logging.info(f"BUY | Price: ${self.entry_price:,.2f} | Capital: ${self.capital:,.2f}")

            elif sell_signals[i] and self.position == 'long':
                exit_price = sell_signals[i]
                profit = (exit_price - self.entry_price) * (self.capital / self.entry_price)
                self.capital += profit
                
                # Calculate daily return
                days_held = (datetime.now() - self.trades[-1]['timestamp']).days
                if days_held > 0:
                    daily_return = (profit / self.capital) / days_held
                    self.daily_returns.append(daily_return)
                
                self.trades.append({
                    'type': 'sell',
                    'price': exit_price,
                    'profit': profit,
                    'capital': self.capital,
                    'timestamp': datetime.now()
                })
                logging.info(f"SELL | Price: ${exit_price:,.2f} | Profit: ${profit:,.2f} | Capital: ${self.capital:,.2f}")
                self.position = None
                self.entry_price = None
    
    def calculate_performance_metrics(self) -> None:
        """
        Calculate and store key performance metrics from backtest results.
        """
        if not self.trades:
            logging.warning("No trades executed - cannot calculate metrics")
            return
            
        profits = [trade['profit'] for trade in self.trades if trade['type'] == 'sell']
        winning_trades = [p for p in profits if p > 0]
        losing_trades = [p for p in profits if p < 0]
        
        # Calculate Sharpe Ratio
        if self.daily_returns:
            returns_array = np.array(self.daily_returns)
            avg_return = np.mean(returns_array)
            std_return = np.std(returns_array)
            risk_free_rate = 0.02 / 252  # Assuming 2% annual risk-free rate
            sharpe_ratio = (avg_return - risk_free_rate) / std_return * math.sqrt(252) if std_return != 0 else 0
        else:
            sharpe_ratio = 0
            
        # Calculate Maximum Drawdown
        peak = self.initial_capital
        max_drawdown = 0
        for trade in self.trades:
            if trade['capital'] > peak:
                peak = trade['capital']
            drawdown = (peak - trade['capital']) / peak
            max_drawdown = max(max_drawdown, drawdown)
            
        self.performance_metrics = {
            'total_trades': len(self.trades) // 2,
            'profitable_trades': len(winning_trades),
            'total_profit': sum(profits),
            'win_rate': len(winning_trades) / len(profits) if profits else 0,
            'return_pct': ((self.capital - self.initial_capital) / self.initial_capital) * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,
            'avg_profit_per_trade': np.mean(winning_trades) if winning_trades else 0,
            'avg_loss_per_trade': abs(np.mean(losing_trades)) if losing_trades else 0,
            'profit_factor': abs(sum(winning_trades) / sum(losing_trades)) if losing_trades else float('inf'),
            'risk_reward_ratio': (np.mean(winning_trades) / abs(np.mean(losing_trades))) if losing_trades and winning_trades else 0
        }

    def run(self) -> None:
        """
        Run the complete backtest simulation.
        """
        logging.info("\n=== STARTING BACKTEST ===")
        logging.info(f"Symbol: {self.symbol}")
        logging.info(f"Period: {self.start_date} to {self.end_date}")
        
        data = self.fetch_historical_data(self.start_date, self.end_date)
        
        if not data.empty:
            buy_signals, sell_signals = self.apply_strategy(data)
            self.execute_trade(buy_signals, sell_signals)
            
            # Calculate metrics before logging results
            self.calculate_performance_metrics()
            
            logging.info("\n=== BACKTEST RESULTS ===")
            logging.info(f"Initial Capital: ${self.initial_capital:,.2f}")
            logging.info(f"Final Capital: ${self.capital:,.2f}")
            logging.info("\nPerformance Metrics:")
            logging.info(f"Total Trades: {self.performance_metrics['total_trades']}")
            logging.info(f"Profitable Trades: {self.performance_metrics['profitable_trades']}")
            logging.info(f"Win Rate: {self.performance_metrics['win_rate']*100:.1f}%")
            logging.info(f"Total Profit/Loss: ${self.performance_metrics['total_profit']:,.2f}")
            logging.info(f"Return: {self.performance_metrics['return_pct']:.1f}%")
            logging.info(f"Sharpe Ratio: {self.performance_metrics['sharpe_ratio']:.2f}")
            logging.info(f"Maximum Drawdown: {self.performance_metrics['max_drawdown']:.1f}%")
            logging.info(f"Average Profit per Trade: ${self.performance_metrics['avg_profit_per_trade']:,.2f}")
            logging.info(f"Average Loss per Trade: ${self.performance_metrics['avg_loss_per_trade']:,.2f}")
            logging.info(f"Profit Factor: {self.performance_metrics['profit_factor']:.2f}")
            logging.info(f"Risk/Reward Ratio: {self.performance_metrics['risk_reward_ratio']:.2f}")
        else:
            logging.error("❌ Backtest failed - No data available")

if __name__ == '__main__':
    backtest = Backtest()
    backtest.run()
