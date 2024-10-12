import praw
import yaml
import os

# Get the directory path of the project root
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')

# Load the config.yaml file
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# Reddit API setup
reddit = praw.Reddit(
    client_id=config['reddit']['client_id'],
    client_secret=config['reddit']['client_secret'],
    user_agent=config['reddit']['user_agent']
)

# Fetch the top 5 posts from a subreddit
subreddit = reddit.subreddit('cryptocurrency')
for post in subreddit.top(limit=5):
    print(f"Title: {post.title}")
    print(f"Score: {post.score}")
    print(f"URL: {post.url}\n")
