from flask import Flask, jsonify, request, render_template
from backtest import Backtest
import os

app = Flask(__name__)

def choose_strategy() -> str:
    """
    Allow user to choose a trading strategy.
    Returns the chosen strategy name.
    """
    strategies = {
        '1': 'moving_average',
        '2': 'rsi', 
        '3': 'macd',
        '4': 'bollinger_bands',
        '5': 'hybrid_strategy',
        '6': 'advanced_hybrid_strategy'
    }
    
    print("\nAvailable Trading Strategies:")
    for key, strategy in strategies.items():
        print(f"{key}. {strategy}")
        
    while True:
        choice = input("\nChoose a strategy (1-6): ")
        if choice in strategies:
            return strategies[choice]
        print("Invalid choice. Please select a number between 1 and 6.")

@app.route('/run-backtest', methods=['POST'])
def run_backtest():
    """
    API endpoint to run the backtest and return the results.
    """
    try:
        strategy = request.json.get('strategy')
        backtest = Backtest(strategy)
        backtest.run()
        
        # Get the historical data and trades
        historical_data = backtest.fetch_historical_data(backtest.start_date, backtest.end_date)
        
        # For advanced hybrid strategy, also fetch higher timeframe data
        if strategy == 'advanced_hybrid_strategy':
            higher_tf_data = historical_data.resample('4h', on='timestamp').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        
        # Prepare chart data by combining price data with trades
        chart_data = []
        for index, row in historical_data.iterrows():
            data_point = {
                'timestamp': row['timestamp'].isoformat(),
                'close': float(row['close']),
                'capital': None  # Will be filled in based on trades
            }
            
            # Find matching trade for this timestamp
            for trade in backtest.trades:
                if abs(trade['price'] - row['close']) < 0.01:  # Price match within small threshold
                    data_point['capital'] = trade['capital']
                    break
                    
            chart_data.append(data_point)
        
        # Prepare results
        results = {
            "initial_capital": backtest.initial_capital,
            "final_capital": backtest.capital,
            "performance_metrics": backtest.performance_metrics,
            "trades": backtest.trades,
            "chart_data": chart_data
        }
        
        return jsonify({"success": True, "results": results}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/')
def index():
    """
    Serve the frontend HTML.
    """
    return render_template('index.html')  # Use render_template to serve index.html

# Serve static files
@app.route('/static/<path:path>')
def static_files(path):
    """
    Serve static files like JavaScript and CSS.
    """
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    return app.send_from_directory(static_dir, path)

if __name__ == '__main__':
    app.run(debug=True, port=8080)
