import praw
import pandas as pd
from textblob import TextBlob
import datetime
import logging
from collections import defaultdict
import yaml
import os
from binance.client import Client
from datetime import timedelta

class RedditSentimentAnalyzer:
    def __init__(self):
        # Load credentials from config file
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        self.reddit = praw.Reddit(
            client_id=config['reddit']['client_id'],
            client_secret=config['reddit']['client_secret'],
            user_agent=config['reddit']['user_agent']
        )
        
        # Initialize Binance client
        self.binance_client = Client(
            config['binance']['api_key'],
            config['binance']['secret_key']
        )
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'reddit_sentiment.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)

    def get_historical_ethereum_posts(self, start_date, end_date, 
                                    subreddits=['ethereum', 'ethtrader', 'ethfinance']):
        """
        Fetch historical Ethereum-related posts from specified subreddits within date range
        """
        posts = []
        for subreddit in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit)
                # Use pushshift.io API to get historical posts
                for post in subreddit.search(
                    'timestamp:{}..{}'.format(
                        int(start_date.timestamp()),
                        int(end_date.timestamp())
                    ),
                    sort='new',
                    syntax='cloudsearch'
                ):
                    post_data = {
                        'title': post.title,
                        'body': post.selftext,
                        'score': post.score,
                        'created_utc': datetime.datetime.fromtimestamp(post.created_utc),
                        'num_comments': post.num_comments,
                        'subreddit': subreddit.display_name,
                        'upvote_ratio': post.upvote_ratio,
                        'is_original_content': post.is_original_content
                    }
                    posts.append(post_data)
                    
            except Exception as e:
                self.logger.error(f"Error fetching historical posts from r/{subreddit}: {str(e)}")
        
        return pd.DataFrame(posts)

    def get_historical_ethereum_price(self, start_date, end_date, interval='1h'):
        """Get historical Ethereum price data from Binance"""
        try:
            klines = self.binance_client.get_historical_klines(
                "ETHUSDT", 
                interval,
                start_date.strftime("%d %b %Y %H:%M:%S"),
                end_date.strftime("%d %b %Y %H:%M:%S")
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignored'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching historical price data: {str(e)}")
            return pd.DataFrame()

    def analyze_sentiment(self, text):
        """Analyze sentiment of text using TextBlob"""
        try:
            analysis = TextBlob(text)
            sentiment = {
                'polarity': analysis.sentiment.polarity,
                'subjectivity': analysis.sentiment.subjectivity
            }
            return sentiment
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {str(e)}")
            return {'polarity': 0, 'subjectivity': 0}

    def backtest_sentiment_strategy(self, start_date, end_date, initial_capital=10000):
        """
        Backtest trading strategy using historical Reddit sentiment and price data
        """
        # Get historical data
        posts_df = self.get_historical_ethereum_posts(start_date, end_date)
        price_df = self.get_historical_ethereum_price(start_date, end_date)
        
        if posts_df.empty or price_df.empty:
            self.logger.error("Unable to get historical data for backtesting")
            return None
            
        # Initialize backtest variables
        capital = initial_capital
        eth_held = 0
        trades = []
        
        # Group posts by day and calculate daily sentiment
        posts_df['date'] = posts_df['created_utc'].dt.date
        daily_sentiments = []
        
        for date, day_posts in posts_df.groupby('date'):
            sentiments = []
            for _, post in day_posts.iterrows():
                title_sentiment = self.analyze_sentiment(post['title'])
                body_sentiment = self.analyze_sentiment(post['body'])
                
                engagement_score = (post['score'] * post['upvote_ratio'] + post['num_comments']) / 2
                if post['is_original_content']:
                    engagement_score *= 1.2
                
                weighted_sentiment = {
                    'polarity': engagement_score * (title_sentiment['polarity'] * 0.7 + 
                                                  body_sentiment['polarity'] * 0.3),
                    'subjectivity': engagement_score * (title_sentiment['subjectivity'] * 0.7 + 
                                                      body_sentiment['subjectivity'] * 0.3),
                    'weight': engagement_score
                }
                sentiments.append(weighted_sentiment)
            
            if sentiments:
                total_weight = sum(s['weight'] for s in sentiments)
                avg_sentiment = {
                    'date': date,
                    'polarity': sum(s['polarity'] for s in sentiments) / total_weight,
                    'subjectivity': sum(s['subjectivity'] for s in sentiments) / total_weight,
                    'total_engagement': total_weight
                }
                daily_sentiments.append(avg_sentiment)
        
        # Execute trades based on daily sentiment
        for sentiment in daily_sentiments:
            date = sentiment['date']
            day_prices = price_df[price_df['timestamp'].dt.date == date]
            
            if not day_prices.empty:
                price = float(day_prices.iloc[0]['close'])
                
                # Trading logic based on sentiment
                if sentiment['polarity'] > 0.2 and sentiment['subjectivity'] < 0.5 and eth_held == 0:
                    # Buy signal
                    eth_amount = capital / price
                    eth_held = eth_amount
                    capital = 0
                    trades.append({
                        'date': date,
                        'action': 'BUY',
                        'price': price,
                        'eth_amount': eth_amount,
                        'capital': capital
                    })
                    
                elif sentiment['polarity'] < -0.2 and sentiment['subjectivity'] < 0.5 and eth_held > 0:
                    # Sell signal
                    capital = eth_held * price
                    trades.append({
                        'date': date,
                        'action': 'SELL',
                        'price': price,
                        'eth_amount': eth_held,
                        'capital': capital
                    })
                    eth_held = 0
        
        # Calculate final portfolio value
        final_price = float(price_df.iloc[-1]['close'])
        portfolio_value = capital + (eth_held * final_price)
        roi = (portfolio_value - initial_capital) / initial_capital * 100
        
        results = {
            'initial_capital': initial_capital,
            'final_portfolio_value': portfolio_value,
            'roi_percent': roi,
            'trades': trades
        }
        
        self.logger.info(f"Backtest completed - ROI: {roi:.2f}% | Final Value: ${portfolio_value:.2f}")
        return results
