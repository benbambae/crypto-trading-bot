import os
import logging
from datetime import datetime
from typing import List, Tuple
import math
import pandas as pd
import numpy as np
import yaml
from binance.client import Client
from strategiesRefactored import (
    moving_average_strategy, rsi_strategy, macd_strategy, bollinger_rsi,
    rsi_macd_pullback, hybrid_strategy, advanced_hybrid_strategy,
    STRATEGY_PLAN
)

yaml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')

with open(yaml_path, 'r') as f:
    config = yaml.safe_load(f)

# Initialize client
client = Client(config['binance']['test_api_key'], config['binance']['test_secret_key'])

# Set up logs
time_tag = datetime.now().strftime('%Y%m%d_%H%M%S')
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'multi_backtest')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'the4coins_log_{time_tag}.log')
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

# Use the strategy plan from strategiesRefactored
STRATEGY_MAP = {
    coin: {'timeframes': list(timeframes.keys()), 'strategies': timeframes}
    for coin, timeframes in STRATEGY_PLAN.items()
}

class MultiBacktester:
    def __init__(self, symbol: str, interval: str, strategy_func):
        self.symbol = symbol + 'USDT'
        self.interval = interval
        self.strategy_func = strategy_func
        self.initial_capital = 10000
        self.capital = self.initial_capital
        self.trades = []
        self.daily_returns = []

    def fetch_data(self, start: str, end: str) -> pd.DataFrame:
        start_fmt = datetime.strptime(start, '%Y-%m-%d').strftime('%d %b, %Y')
        end_fmt = datetime.strptime(end, '%Y-%m-%d').strftime('%d %b, %Y')

        klines = client.get_historical_klines(self.symbol, self.interval, start_fmt, end_fmt)
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                           'close_time', 'quote_asset_volume', 'num_trades',
                                           'taker_buy_base', 'taker_buy_quote', 'ignore'])

        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

    def run(self, data: pd.DataFrame):
        buy_signals, sell_signals = self.strategy_func(data)
        position = None
        entry_price = 0
        for i in range(len(data)):
            if buy_signals[i] and position is None:
                position = 'long'
                entry_price = buy_signals[i]
                self.trades.append({'type': 'buy', 'price': entry_price, 'timestamp': data['timestamp'].iloc[i]})
            elif sell_signals[i] and position == 'long':
                sell_price = sell_signals[i]
                profit = (sell_price - entry_price) * (self.capital / entry_price)
                self.capital += profit
                days_held = 1
                self.daily_returns.append((profit / self.capital) / days_held)
                self.trades.append({'type': 'sell', 'price': sell_price, 'profit': profit, 'timestamp': data['timestamp'].iloc[i]})
                position = None

    def metrics(self):
        profits = [t['profit'] for t in self.trades if t['type'] == 'sell']
        win = [p for p in profits if p > 0]
        loss = [p for p in profits if p < 0]

        sharpe = 0
        if self.daily_returns:
            returns = np.array(self.daily_returns)
            avg_ret = np.mean(returns)
            std_ret = np.std(returns)
            sharpe = (avg_ret - 0.02 / 252) / std_ret * np.sqrt(252) if std_ret != 0 else 0

        drawdown = 0
        peak = self.initial_capital
        for t in self.trades:
            if 'profit' in t:
                capital = self.capital
                peak = max(peak, capital)
                drawdown = max(drawdown, (peak - capital) / peak)

        return {
            'final_capital': round(self.capital, 2),
            'total_trades': len(profits),
            'win_rate': round(len(win)/len(profits), 2) if profits else 0,
            'profit_factor': round(sum(win)/abs(sum(loss)), 2) if loss else float('inf'),
            'sharpe_ratio': round(sharpe, 2),
            'drawdown': round(drawdown * 100, 2),
            'total_profit': round(sum(profits), 2)
        }

def main():
    start = config['backtest']['start_date']
    end = config['backtest']['end_date']

    for coin, details in STRATEGY_MAP.items():
        for tf in details['timeframes']:
            strategy = details['strategies'][tf]
            bt = MultiBacktester(coin, tf, strategy)
            try:
                df = bt.fetch_data(start, end)
                bt.run(df)
                metrics = bt.metrics()
                logging.info(f"\n==== {coin} | {tf} ====")
                for k, v in metrics.items():
                    logging.info(f"{k}: {v}")
            except Exception as e:
                logging.error(f"Error on {coin}-{tf}: {str(e)}")

if __name__ == '__main__':
    main()