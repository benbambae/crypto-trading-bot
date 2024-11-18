document.addEventListener('DOMContentLoaded', function () {
  const runButton = document.getElementById('runBacktest');
  const resultsDiv = document.getElementById('results');

  runButton.addEventListener('click', () => {
      // Show loading state
      resultsDiv.innerHTML = "<p>Running backtest...</p>";

      // Send a POST request to the backend
      fetch('/run-backtest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
      })
      .then(response => response.json())
      .then(data => {
          if (data.success) {
              const results = data.results;
              resultsDiv.innerHTML = `
                  <h3>Backtest Results</h3>
                  <p><strong>Initial Capital:</strong> $${results.initial_capital.toFixed(2)}</p>
                  <p><strong>Final Capital:</strong> $${results.final_capital.toFixed(2)}</p>
                  <p><strong>Total Trades:</strong> ${results.performance_metrics.total_trades}</p>
                  <p><strong>Profitable Trades:</strong> ${results.performance_metrics.profitable_trades}</p>
                  <p><strong>Win Rate:</strong> ${(results.performance_metrics.win_rate * 100).toFixed(2)}%</p>
                  <p><strong>Total Profit:</strong> $${results.performance_metrics.total_profit.toFixed(2)}</p>
                  <p><strong>Return:</strong> ${results.performance_metrics.return_pct.toFixed(2)}%</p>
              `;
          } else {
              resultsDiv.innerHTML = `<p>Error: ${data.error}</p>`;
          }
      })
      .catch(error => {
          resultsDiv.innerHTML = `<p>Error: ${error.message}</p>`;
      });
  });
});
