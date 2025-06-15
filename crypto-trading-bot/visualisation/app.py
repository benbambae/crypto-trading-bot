from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import json
from datetime import datetime

app = Flask(__name__)

# Directory where CSV files are stored
DATA_DIR = 'data'

@app.route('/')
def index():
    """Render the main dashboard page"""
    # Get list of available CSV files
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
    
    # Group files by coin
    coins = {}
    for file in csv_files:
        coin = file.split('_')[0]  # Extract coin name from filename
        if coin not in coins:
            coins[coin] = []
        coins[coin].append(file)
    
    return render_template('index.html', coins=coins)

@app.route('/api/available_files')
def available_files():
    """Return a list of available CSV files"""
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
    
    # Group files by coin
    coins = {}
    for file in csv_files:
        coin = file.split('_')[0]  # Extract coin name from filename
        if coin not in coins:
            coins[coin] = []
        coins[coin].append(file)
    
    return jsonify(coins)

@app.route('/api/file_metadata/<filename>')
def file_metadata(filename):
    """Return metadata about a CSV file"""
    filepath = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # Read just the first few rows to get column information
        df = pd.read_csv(filepath, nrows=5)
        
        # Get basic file info
        file_size = os.path.getsize(filepath) / 1024  # size in KB
        
        # Get timeframe and date range from filename
        parts = filename.split('_')
        coin = parts[0]
        timeframe = parts[1] if len(parts) > 1 else 'unknown'
        
        # Try to identify date range
        date_range = 'N/A'
        if len(parts) > 3:
            try:
                start_date = parts[2]
                end_date = parts[4].split('.')[0]
                date_range = f"{start_date} to {end_date}"
            except:
                date_range = 'Unknown'
        
        metadata = {
            'filename': filename,
            'coin': coin,
            'timeframe': timeframe,
            'date_range': date_range,
            'columns': list(df.columns),
            'num_rows': len(pd.read_csv(filepath)),
            'file_size_kb': round(file_size, 2)
        }
        
        return jsonify(metadata)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/<filename>')
def get_data(filename):
    """Return the data from a CSV file"""
    filepath = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        df = pd.read_csv(filepath)
        
        # Convert date column to datetime if it exists
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['date'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert dataframe to JSON
        data = df.to_dict(orient='records')
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/comparison')
def compare_coins():
    """Compare metrics across coins"""
    # Get query parameters
    files = request.args.getlist('files')
    metric = request.args.get('metric', 'close')
    
    if not files:
        return jsonify({'error': 'No files selected for comparison'}), 400
    
    try:
        # Initialize results
        comparison_data = []
        
        for filename in files:
            filepath = os.path.join(DATA_DIR, filename)
            if not os.path.exists(filepath):
                continue
            
            df = pd.read_csv(filepath)
            
            # Skip if the metric doesn't exist in this file
            if metric not in df.columns:
                continue
            
            # Calculate basic statistics
            stats = {
                'filename': filename,
                'coin': filename.split('_')[0],
                'min': df[metric].min(),
                'max': df[metric].max(),
                'mean': df[metric].mean(),
                'median': df[metric].median(),
                'std': df[metric].std(),
                'percent_change': ((df[metric].iloc[-1] - df[metric].iloc[0]) / df[metric].iloc[0]) * 100 if len(df) > 1 else 0
            }
            
            comparison_data.append(stats)
        
        return jsonify(comparison_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tariff_impact')
def tariff_impact():
    """Analyze pre and post tariff data"""
    coins = ['ETH', 'LINK', 'DOGE', 'ARB']
    results = []
    
    for coin in coins:
        pre_file = f"{coin}_1h_2025-03-08_to_2025-04-08_pre_tariff.csv"
        post_file = f"{coin}_1h_2025-04-09_to_2025-04-13_post_tariff.csv"
        
        pre_path = os.path.join(DATA_DIR, pre_file)
        post_path = os.path.join(DATA_DIR, post_file)
        
        if not (os.path.exists(pre_path) and os.path.exists(post_path)):
            continue
        
        try:
            pre_df = pd.read_csv(pre_path)
            post_df = pd.read_csv(post_path)
            
            # Calculate average price before and after
            pre_avg_price = pre_df['close'].mean()
            post_avg_price = post_df['close'].mean()
            
            # Calculate average volume before and after
            pre_avg_volume = pre_df['volume'].mean()
            post_avg_volume = post_df['volume'].mean()
            
            # Calculate price change
            price_change_pct = ((post_avg_price - pre_avg_price) / pre_avg_price) * 100
            
            # Calculate volume change
            volume_change_pct = ((post_avg_volume - pre_avg_volume) / pre_avg_volume) * 100
            
            results.append({
                'coin': coin,
                'pre_avg_price': pre_avg_price,
                'post_avg_price': post_avg_price,
                'price_change_pct': price_change_pct,
                'pre_avg_volume': pre_avg_volume,
                'post_avg_volume': post_avg_volume,
                'volume_change_pct': volume_change_pct
            })
        
        except Exception as e:
            print(f"Error processing {coin}: {str(e)}")
    
    return jsonify(results)

@app.route('/api/calculate_metrics/<filename>')
def calculate_metrics(filename):
    """Calculate trading metrics for a file"""
    filepath = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        df = pd.read_csv(filepath)
        
        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                return jsonify({'error': f'Missing required column: {col}'}), 400
        
        # Calculate various metrics
        metrics = {
            'filename': filename,
            'coin': filename.split('_')[0],
            'num_periods': len(df),
            'avg_price': df['close'].mean(),
            'price_volatility': df['close'].std() / df['close'].mean() * 100,  # Coefficient of variation
            'avg_volume': df['volume'].mean(),
            'volume_volatility': df['volume'].std() / df['volume'].mean() * 100,
            'max_drawdown': calculate_max_drawdown(df['close']),
            'sharpe_ratio': calculate_simple_sharpe(df['close']),
            'avg_daily_return': calculate_avg_return(df['close']),
        }
        
        return jsonify(metrics)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_max_drawdown(prices):
    """Calculate maximum drawdown from a series of prices"""
    if len(prices) < 2:
        return 0
    
    # Calculate the running maximum and drawdowns
    running_max = prices.cummax()
    drawdowns = (prices / running_max - 1) * 100
    
    # Get the minimum drawdown
    max_drawdown = drawdowns.min()
    return max_drawdown

def calculate_simple_sharpe(prices, risk_free_rate=0.03):
    """Calculate a simplified Sharpe ratio"""
    if len(prices) < 2:
        return 0
    
    # Calculate daily returns
    returns = prices.pct_change().dropna()
    
    # Annualize (approximately)
    annual_return = returns.mean() * 252
    annual_volatility = returns.std() * (252 ** 0.5)
    
    # Calculate Sharpe
    if annual_volatility == 0:
        return 0
    
    sharpe = (annual_return - risk_free_rate) / annual_volatility
    return sharpe

def calculate_avg_return(prices):
    """Calculate average daily return"""
    if len(prices) < 2:
        return 0
    
    returns = prices.pct_change().dropna()
    return returns.mean() * 100  # As percentage

if __name__ == '__main__':
    app.run(debug=True)