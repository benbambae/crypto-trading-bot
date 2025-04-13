import os
import logging
from datetime import datetime
import yaml
import pandas as pd
from binance.client import Client
from strategiesIndividual import STRATEGY_MAP

# Load config.yaml
config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml'))
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Setup logs
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'full_backtest_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

# Binance client
client = Client(config['binance']['test_api_key'], config['binance']['test_secret_key'])

class Backtester:
    def __init__(self, coin, timeframe, strategy_fn, start_date, end_date):
        self.symbol = coin + 'USDT'
        self.interval = timeframe
        self.strategy_fn = strategy_fn
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = 10000
        self.capital = 10000
        self.trades = []

    def fetch_data(self):
        start_fmt = datetime.strptime(self.start_date, '%Y-%m-%d').strftime('%d %b, %Y')
        end_fmt = datetime.strptime(self.end_date, '%Y-%m-%d').strftime('%d %b, %Y')
        klines = client.get_historical_klines(self.symbol, self.interval, start_fmt, end_fmt)
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                           'close_time', 'qav', 'num_trades', 'tbbav', 'tbqav', 'ignore'])
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

    def run_strategy(self, df):
        result = self.strategy_fn(df)
        
        # Support both formats: (buy, sell) OR (df, metrics)
        if isinstance(result, tuple) and isinstance(result[0], pd.DataFrame):
            df = result[0]
            actions = df['action'].tolist()
            buy = [price if action == 'BUY' else None for price, action in zip(df['close'], actions)]
            sell = [price if action == 'SELL' else None for price, action in zip(df['close'], actions)]
        else:
            buy, sell = result
            
        # Add assertion to catch broken strategies
        assert len(buy) == len(df) and len(sell) == len(df), "Buy/sell length mismatch!"
        
        in_position = False
        entry_price = 0
        trade_data = []

        for i in range(len(df)):
            if buy[i] and not in_position:
                entry_price = buy[i]
                trade_data.append({
                    'timestamp': df['timestamp'][i],
                    'type': 'buy',
                    'price': entry_price,
                    'profit': 0
                })
                in_position = True
            elif sell[i] and in_position:
                exit_price = sell[i]
                profit = (exit_price - entry_price) * (self.capital / entry_price)
                self.capital += profit
                trade_data.append({
                    'timestamp': df['timestamp'][i],
                    'type': 'sell', 
                    'price': exit_price,
                    'profit': profit
                })
                in_position = False

        self.trades = pd.DataFrame(trade_data)
        
        # Save trades to CSV
        filename = f"{self.symbol}_{self.strategy_fn.__name__}_trades.csv"
        filepath = os.path.join("trades_indiv_logs", filename)
        self.trades.to_csv(filepath, index=False)

    def compute_metrics(self):
        if len(self.trades) == 0:
            return {
                'final_capital': self.capital,
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': float('inf'),
                'sharpe_ratio': 0,
                'drawdown': 0,
                'total_profit': 0
            }

        sell_trades = self.trades[self.trades['type'] == 'sell']
        wins = sell_trades[sell_trades['profit'] > 0]
        losses = sell_trades[sell_trades['profit'] <= 0]
        
        win_rate = len(wins) / len(sell_trades) if len(sell_trades) > 0 else 0
        profit_factor = wins['profit'].sum() / abs(losses['profit'].sum()) if len(losses) > 0 else float('inf')
        
        sharpe = 0
        if len(sell_trades) > 0:
            returns = sell_trades['profit'] / self.capital
            sharpe = (returns.mean() / returns.std()) * (252 ** 0.5) if returns.std() != 0 else 0

        # Calculate max drawdown
        capital_curve = self.initial_capital + self.trades['profit'].cumsum()
        peak = capital_curve.expanding().max()
        drawdown = (peak - capital_curve) / peak
        max_drawdown = drawdown.max()

        return {
            'final_capital': round(self.capital, 2),
            'total_trades': len(sell_trades),
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'sharpe_ratio': round(sharpe, 2),
            'drawdown': round(max_drawdown * 100, 2),
            'total_profit': round(self.capital - self.initial_capital, 2)
        }

def main():
    all_scenarios = config['backtest']['backtest_periods']
    for coin, entries in all_scenarios.items():
        for scenario in entries:
            strategy_name = scenario['strategy']
            timeframe = scenario['timeframe']
            start = scenario['start_date']
            end = scenario['end_date']
            strategy_fn = STRATEGY_MAP[coin][strategy_name]

            bt = Backtester(coin, timeframe, strategy_fn, start, end)
            try:
                df = bt.fetch_data()
                bt.run_strategy(df)
                metrics = bt.compute_metrics()
                logging.info(f"\n=== {coin.upper()} | {strategy_name} ===")
                for k, v in metrics.items():
                    logging.info(f"{k}: {v}")
            except Exception as e:
                logging.error(f"❌ Error in {coin}-{strategy_name}: {str(e)}")

if __name__ == '__main__':
    main()