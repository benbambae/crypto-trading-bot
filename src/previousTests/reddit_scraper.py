import praw
import pandas as pd
from datetime import datetime
import time
import yaml
import os

# Load credentials from config file
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Initialize Reddit API client
reddit = praw.Reddit(
    client_id=config['reddit']['client_id'],
    client_secret=config['reddit']['client_secret'],
    user_agent=config['reddit']['user_agent']
)

# List of cryptocurrencies to track
CRYPTOCURRENCIES = [
    "Bitcoin", "BTC", 
    "Ethereum", "ETH",
    "Binance", "BNB",
    "XRP", "Ripple",
    "Cardano", "ADA",
    "Solana", "SOL", 
    "Polkadot", "DOT",
    "Avalanche", "AVAX",
    "Chainlink", "LINK",
    "Polygon", "MATIC",
    "Dogecoin", "DOGE",
    "PEPE", "SHIBA", "SHIB", "FLOKI", "TRUMP"
]


def fetch_reddit_posts():
    """
    Fetch latest posts from Reddit for specified cryptocurrencies
    """
    posts_data = []
    
    # Fetch from relevant subreddits
    subreddits = ["cryptocurrency", "CryptoMarkets", "CryptoCurrencies"]
    
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        
        # Get new posts
        for post in subreddit.new(limit=1000):
            # Check if post contains any of our target cryptocurrencies
            if any(crypto.lower() in post.title.lower() or crypto.lower() in post.selftext.lower() 
                   for crypto in CRYPTOCURRENCIES):
                
                posts_data.append({
                    'timestamp': datetime.fromtimestamp(post.created_utc),
                    'title': post.title,
                    'text': post.selftext,
                    'score': post.score,
                    'num_comments': post.num_comments,
                    'subreddit': subreddit_name,
                    'post_id': post.id
                })
    
    # Convert to DataFrame
    df = pd.DataFrame(posts_data)
    
    # Save to CSV with timestamp
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    df.to_csv(f'reddit_data_{current_time}.csv', index=False)
    
    return df

# Run daily data collection
while True:
    try:
        print(f"Fetching Reddit data at {datetime.now()}")
        fetch_reddit_posts()
        # Sleep for 24 hours
        time.sleep(24 * 60 * 60)
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        # Wait 5 minutes before retrying
        time.sleep(300)
