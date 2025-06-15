#!/usr/bin/env python3
"""
Historical Whale Alert API Test Script

This script attempts to fetch as much historical data as possible from the Whale Alert API
by making multiple requests with different start and end times.
"""

import os
import yaml
import requests
import json
from datetime import datetime, timedelta
import time

# Update this path to point to your config.yaml file
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.yaml'))

# Supported coins to filter by
SUPPORTED_COINS = ['ETH', 'LINK', 'DOGE', 'ARB']

def load_config():
    """Load configuration from YAML file."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def get_unix_timestamp(days_ago):
    """Convert days ago to Unix timestamp."""
    date = datetime.now() - timedelta(days=days_ago)
    return int(date.timestamp())

def test_historical_whale_data(api_key, min_value=1000000, days_back=10):
    """Test historical data from the Whale Alert API."""
    print(f"🔍 Attempting to fetch historical whale transactions for the past {days_back} days...")
    print(f"👉 Min Value: ${min_value:,}")
    print(f"👉 Looking for: {', '.join(SUPPORTED_COINS)}")
    
    now = int(datetime.now().timestamp())
    all_transactions = []
    total_api_calls = 0
    
    # Try to get data for each day going back
    for day in range(days_back, 0, -1):
        start_time = get_unix_timestamp(day)
        end_time = get_unix_timestamp(day - 1)
        
        print(f"\n📅 Checking day {days_back - day + 1} of {days_back}: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')}")
        
        try:
            url = (f"https://api.whale-alert.io/v1/transactions"
                   f"?api_key={api_key}"
                   f"&min_value={min_value}"
                   f"&start={start_time}"
                   f"&end={end_time}"
                   f"&limit=100")
            
            total_api_calls += 1
            resp = requests.get(url, timeout=10)
            
            print(f"📡 API Call {total_api_calls}: Status {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                txs = data.get("transactions", [])
                
                # Check credits
                credits_used = data.get('credits_used', 'N/A')
                credits_remaining = data.get('credits_remaining', 'N/A')
                print(f"💳 Credits - Used: {credits_used}, Remaining: {credits_remaining}")
                
                if txs:
                    print(f"🔢 Found {len(txs)} transactions")
                    # Filter to our supported coins
                    coin_txs = [tx for tx in txs if tx.get("symbol", "").upper() in SUPPORTED_COINS]
                    all_transactions.extend(coin_txs)
                    print(f"🎯 {len(coin_txs)} transactions for your tracked coins")
                else:
                    print("ℹ️ No transactions found for this day")
                
                # Be nice to the API - don't make too many requests too quickly
                time.sleep(1)
            else:
                print(f"❌ API Error: {resp.text}")
                break
                
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            break
    
    # Show summary of all found transactions
    print("\n" + "=" * 80)
    print(f"📊 SUMMARY: Found {len(all_transactions)} transactions for your coins in the past {days_back} days")
    print("=" * 80)
    
    if all_transactions:
        # Sort by timestamp
        all_transactions.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # Group by coin
        coin_stats = {}
        for tx in all_transactions:
            symbol = tx.get("symbol", "").upper()
            if symbol not in coin_stats:
                coin_stats[symbol] = {
                    "count": 0,
                    "total_value": 0,
                    "max_value": 0
                }
            
            coin_stats[symbol]["count"] += 1
            value = tx.get("amount_usd", 0)
            coin_stats[symbol]["total_value"] += value
            coin_stats[symbol]["max_value"] = max(coin_stats[symbol]["max_value"], value)
        
        # Print stats by coin
        print("\n📈 Statistics by Coin:")
        for coin, stats in coin_stats.items():
            print(f"  • {coin}: {stats['count']} transactions")
            print(f"    - Total Value: ${stats['total_value']:,.2f}")
            print(f"    - Average Value: ${stats['total_value'] / stats['count']:,.2f}")
            print(f"    - Max Value: ${stats['max_value']:,.2f}")
        
        # Print details of some transactions
        print("\n🧾 Sample Transactions (most recent first):")
        for i, tx in enumerate(all_transactions[:10], 1):
            tx_id = tx.get("id", "N/A")
            symbol = tx.get("symbol", "").upper()
            value = tx.get("amount_usd", 0)
            from_label = tx.get("from", {}).get("owner", "Unknown")
            to_label = tx.get("to", {}).get("owner", "Unknown")
            timestamp = datetime.fromtimestamp(tx.get("timestamp")).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"\n📝 {i}. {symbol} ${value:,.2f} on {timestamp}")
            print(f"   From: {from_label}")
            print(f"   To: {to_label}")
            print(f"   ID: {tx_id}")
    else:
        print("\nℹ️ No transactions found for your tracked coins in the specified time period.")
        print("Try decreasing the minimum value or checking for different coins.")

def main():
    # Print header
    print("\n" + "=" * 80)
    print("🐋 HISTORICAL WHALE ALERT TEST 🐋".center(80))
    print("=" * 80 + "\n")
    
    # Load configuration
    print("📂 Loading configuration...")
    config = load_config()
    
    if not config:
        print("❌ Failed to load configuration. Please check the CONFIG_PATH.")
        return
    
    # Get Whale Alert settings
    api_key = config.get("whaleAlert", {}).get("api_key")
    # Use a lower threshold to find more transactions
    min_value = 750000  # Lower than the default $1,000,000
    
    if not api_key:
        print("❌ API Key not found in config!")
        return
    
    # Run the test
    days_to_check = 10  # Try to get 10 days of data
    test_historical_whale_data(api_key, min_value, days_to_check)

if __name__ == "__main__":
    main()