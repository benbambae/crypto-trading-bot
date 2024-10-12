import tweepy
import yaml
import os


# Get the directory path of the project root
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')

# Load the config.yaml file
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# Twitter API setup using OAuth 2.0 (Bearer Token)
client = tweepy.Client(
    bearer_token=config['twitter']['bearer_token']
)

# Replace with the Twitter username
username = "elonmusk"

# Get user information (this works with the free tier)
user = client.get_user(username=username)

# Print user information
print(f"Username: {user.data.username}")
print(f"ID: {user.data.id}")
print(f"Name: {user.data.name}")

