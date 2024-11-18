document.addEventListener('DOMContentLoaded', function() {
    const runButton = document.getElementById('runBacktest');
    const resultsDiv = document.getElementById('results');

    runButton.addEventListener('click', () => {
        // Show loading state with spinner animation
        resultsDiv.innerHTML = `
            <div class="loading">
                <p>Running backtest...</p>
            </div>
        `;

        // Send POST request to backend
        fetch('/run-backtest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const results = data.results;
                // Format results with consistent spacing and styling
                resultsDiv.innerHTML = `
                    <div class="results-container">
                        <h3 class="results-title">Backtest Results</h3>
                        
                        <div class="metric">
                            <p><strong>Initial Capital:</strong> 
                                <span class="value">$${results.initial_capital.toFixed(2)}</span>
                            </p>
                        </div>

                        <div class="metric">
                            <p><strong>Final Capital:</strong> 
                                <span class="value">$${results.final_capital.toFixed(2)}</span>
                            </p>
                        </div>

                        <div class="metric">
                            <p><strong>Total Trades:</strong>
                                <span class="value">${results.performance_metrics.total_trades}</span>
                            </p>
                        </div>

                        <div class="metric">
                            <p><strong>Profitable Trades:</strong>
                                <span class="value">${results.performance_metrics.profitable_trades}</span>
                            </p>
                        </div>

                        <div class="metric">
                            <p><strong>Win Rate:</strong>
                                <span class="value">${(results.performance_metrics.win_rate * 100).toFixed(2)}%</span>
                            </p>
                        </div>

                        <div class="metric">
                            <p><strong>Total Profit:</strong>
                                <span class="value">$${results.performance_metrics.total_profit.toFixed(2)}</span>
                            </p>
                        </div>

                        <div class="metric">
                            <p><strong>Return:</strong>
                                <span class="value">${results.performance_metrics.return_pct.toFixed(2)}%</span>
                            </p>
                        </div>
                    </div>
                `;
            } else {
                resultsDiv.innerHTML = `
                    <div class="error-message">
                        <p>Error: ${data.error}</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            resultsDiv.innerHTML = `
                <div class="error-message">
                    <p>Error: ${error.message}</p>
                </div>
            `;
        });
    });
});