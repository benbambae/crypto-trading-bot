import requests
from datetime import datetime, timedelta
import time
import yaml
import os

# Load config.yaml from parent directory's config folder
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')

with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

API_KEY = config['whaleAlert']['api_key']
BASE_URL = "https://api.whale-alert.io/v1/transactions"

def get_whale_alerts():
    now = int(time.time())
    start_time = now - 500  # last 60 seconds

    params = {
        'api_key': API_KEY,
        'start': start_time,
        'min_value': 10000,  # minimum USD value to filter whales
        'currency': 'usd',
    }

    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if data['count'] > 0:
        print(f"\nWhale Transactions @ {datetime.now()}:")
        for tx in data['transactions']:
            print(f"{tx['amount']} {tx['symbol']} | From: {tx['from']['owner_type']} → To: {tx['to']['owner_type']}")
    else:
        print("No whale transactions in last minute.")

if __name__ == "__main__":
    while True:
        get_whale_alerts()
        time.sleep(60)
