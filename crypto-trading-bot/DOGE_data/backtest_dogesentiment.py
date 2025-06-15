# Improved DOGE Sentiment Backtest Script
import os
import pandas as pd
from textblob import TextBlob
from binance.client import Client
from datetime import datetime
import yaml
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

API_KEY = config['binance']['api_key']
API_SECRET = config['binance']['secret_key']
SYMBOL = 'DOGEUSDT'
START_DATE = '2021-05-25'
END_DATE = '2021-09-14'
MIN_TWEET_COUNT = 100
STARTING_CASH = 10000
POS_THRESHOLD = 0.3
NEG_THRESHOLD = -0.3

# --- INITIALIZE BINANCE CLIENT ---
client = Client(API_KEY, API_SECRET)

# --- SENTIMENT ANALYSIS FUNCTION ---
def get_weighted_sentiment(text, retweet_count):
    try:
        polarity = TextBlob(str(text)).sentiment.polarity
        weight = 1 + (retweet_count / 10)
        return polarity * weight
    except:
        return 0.0

# --- LOAD SENTIMENT DATA ---
sentiment_files = [f for f in os.listdir() if f.startswith("DOGE_") and f.endswith(".xlsx")]
all_data = []

for file in sentiment_files:
    df = pd.read_excel(file)
    if 'created' in df.columns and 'text' in df.columns:
        df['timestamp'] = pd.to_datetime(df['created'])
        df['retweetCount'] = df.get('retweetCount', 0)
        df['sentiment'] = df.apply(lambda x: get_weighted_sentiment(x['text'], x['retweetCount']), axis=1)
        df['tweetcount'] = df['retweetCount'].fillna(1)
        all_data.append(df[['timestamp', 'sentiment', 'tweetcount']])

sentiment_df = pd.concat(all_data).sort_values('timestamp')

# --- FETCH PRICE DATA ---
def get_price_data(symbol, start_str, end_str, interval='1m'):
    klines = client.get_historical_klines(symbol, interval, start_str, end_str)
    df = pd.DataFrame(klines, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    return df[['timestamp', 'close']]

print("Fetching price data from Binance...")
price_df = get_price_data(SYMBOL, START_DATE, END_DATE)
print("Price data fetched:", price_df.shape)

# --- MERGE DATA ---
merged_df = pd.merge_asof(sentiment_df.sort_values('timestamp'),
                          price_df.sort_values('timestamp'),
                          on='timestamp', direction='backward')

# --- BACKTESTING ---
cash = STARTING_CASH
doge = 0
trade_log = []

for _, row in merged_df.iterrows():
    price = row['close']
    sentiment = row['sentiment']
    tweetcount = row['tweetcount']
    timestamp = row['timestamp']

    if sentiment >= POS_THRESHOLD and tweetcount > MIN_TWEET_COUNT and cash > 0:
        doge = cash / price
        trade_log.append((timestamp, "BUY", price, cash, sentiment, tweetcount))
        cash = 0

    elif sentiment <= NEG_THRESHOLD and tweetcount > MIN_TWEET_COUNT and doge > 0:
        cash = doge * price
        trade_log.append((timestamp, "SELL", price, cash, sentiment, tweetcount))
        doge = 0

final_value = cash + doge * merged_df.iloc[-1]['close']
roi = final_value - STARTING_CASH

# --- LOG RESULTS ---
results_df = pd.DataFrame(trade_log, columns=["timestamp", "action", "price", "value", "sentiment", "tweetcount"])
results_df.to_csv("doge_sentiment_backtest_results.csv", index=False)

# --- SUMMARY ---
num_trades = len(trade_log)
num_buys = results_df[results_df['action'] == 'BUY'].shape[0]
num_sells = results_df[results_df['action'] == 'SELL'].shape[0]
avg_sentiment_buy = results_df[results_df['action'] == 'BUY']['sentiment'].mean()
avg_sentiment_sell = results_df[results_df['action'] == 'SELL']['sentiment'].mean()

summary = f"""
--- DOGE Sentiment Backtest Summary ---
Period: {START_DATE} to {END_DATE}
Initial Cash: ${STARTING_CASH}
Final Value: ${final_value:.2f}
Total Return: ${roi:.2f}
Number of Trades: {num_trades}
  - Buys: {num_buys}
  - Sells: {num_sells}
Avg Sentiment at Buy: {avg_sentiment_buy:.4f}
Avg Sentiment at Sell: {avg_sentiment_sell:.4f}
Min Tweet Count Threshold: {MIN_TWEET_COUNT}
Positive Sentiment Threshold: {POS_THRESHOLD}
Negative Sentiment Threshold: {NEG_THRESHOLD}
"""

print(summary)
with open("doge_sentiment_findings.txt", "w") as f:
    f.write(summary)

# --- PLOTTING ---
price_df.set_index('timestamp', inplace=True)
results_df.set_index('timestamp', inplace=True)

plt.figure(figsize=(15, 6))
plt.plot(price_df['close'], label='DOGE Price', alpha=0.6)

buy_signals = results_df[results_df['action'] == 'BUY']
sell_signals = results_df[results_df['action'] == 'SELL']
plt.scatter(buy_signals.index, buy_signals['price'], marker='^', color='green', label='Buy Signal', s=30)
plt.scatter(sell_signals.index, sell_signals['price'], marker='v', color='red', label='Sell Signal', s=30)

plt.title("DOGE Sentiment Backtest Trades")
plt.xlabel("Timestamp")
plt.ylabel("Price (USDT)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("doge_trade_signals_plot.png")
plt.show()
