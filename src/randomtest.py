from binance.client import Client
import yaml
import os

# Load config.yaml
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')

with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# Initialize Binance Client with Testnet keys
client = Client(config['binance']['test_api_key'], config['binance']['test_secret_key'])

# Set the Testnet API URL
client.API_URL = 'https://testnet.binance.vision/api'

# Test fetching account balance
def test_fetch_balance():
    try:
        # Fetch account information (including balance)
        account_info = client.get_account()
        print("Account information fetched successfully:")
        print(account_info)
    except Exception as e:
        print(f"Error fetching account information: {e}")

if __name__ == "__main__":
    test_fetch_balance()
