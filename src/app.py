from flask import Flask, jsonify, request, render_template
from backtest import Backtest
import os

app = Flask(__name__)

@app.route('/run-backtest', methods=['POST'])
def run_backtest():
    """
    API endpoint to run the backtest and return the results.
    """
    try:
        # Initialize and run backtest
        backtest = Backtest()
        backtest.run()
        
        # Prepare results
        results = {
            "initial_capital": backtest.initial_capital,
            "final_capital": backtest.capital,
            "performance_metrics": backtest.performance_metrics,
            "trades": backtest.trades
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
    app.run(debug=True)
