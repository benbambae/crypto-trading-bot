# Cryptocurrency Trading Bot

A comprehensive Python-based cryptocurrency trading bot that supports multiple trading strategies, backtesting, live trading, and sentiment analysis for various cryptocurrencies including ETH, LINK, MATIC, ARB, and DOGE.

## Features

- **Multi-Cryptocurrency Support**: Trade ETH, LINK, MATIC, ARB, and DOGE
- **Advanced Trading Strategies**: Multiple trading strategies tailored for different market conditions
- **Backtesting Engine**: Test strategies against historical data
- **Live Trading**: Real-time trading with Binance integration
- **Sentiment Analysis**: Twitter and Reddit sentiment analysis for trading signals
- **Telegram Notifications**: Real-time trade alerts and notifications
- **Whale Alert Integration**: Monitor large transactions
- **Risk Management**: Built-in stop-loss and take-profit mechanisms
- **Data Visualization**: Web-based dashboard for performance analysis

## Project Structure

```
bencryptobot/
├── crypto-trading-bot/          # Main trading bot application
│   ├── src/                     # Source code
│   ├── config/                  # Configuration files
│   ├── logs/                    # Log files
│   ├── visualisation/           # Web dashboard
│   └── requirements.txt         # Python dependencies
├── cloud/                       # Cloud deployment version
├── liveBackup/                  # Trading data backups
└── README.md                    # This file
```

## Quick Start

### Prerequisites

- Python 3.8+
- Binance account (for live trading)
- API keys for various services (see Configuration section)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd bencryptobot
   ```

2. **Set up virtual environment**
   ```bash
   cd crypto-trading-bot
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the bot**
   ```bash
   cp config/config.example.yaml config/config.yaml
   # Edit config/config.yaml with your API keys and settings
   ```

### Configuration

Create a `config.yaml` file based on `config.example.yaml` and fill in your API credentials:

#### Required API Keys

1. **Binance API** (for trading)
   - Get from: https://www.binance.com/en/my/settings/api-management
   - Required: `api_key`, `secret_key`
   - Optional: `test_api_key`, `test_secret_key` (for testnet)

2. **Telegram Bot** (for notifications)
   - Create bot: Message @BotFather on Telegram
   - Required: `token`, `chat_id`

3. **Twitter API** (for sentiment analysis)
   - Get from: https://developer.twitter.com/
   - Required: `api_key`, `api_secret_key`, `access_token`, `access_token_secret`, `bearer_token`

4. **Reddit API** (for sentiment analysis)
   - Get from: https://www.reddit.com/prefs/apps
   - Required: `client_id`, `client_secret`

5. **WhaleAlert API** (optional)
   - Get from: https://whale-alert.io/
   - Required: `api_key`

#### Configuration Example

```yaml
binance:
  api_key: "YOUR_BINANCE_API_KEY_HERE"
  secret_key: "YOUR_BINANCE_SECRET_KEY_HERE"
  test_api_key: "YOUR_BINANCE_TESTNET_API_KEY_HERE"
  test_secret_key: "YOUR_BINANCE_TESTNET_SECRET_KEY_HERE"

alerts:
  telegram:
    enabled: true
    token: "YOUR_TELEGRAM_BOT_TOKEN_HERE"
    chat_id: "YOUR_TELEGRAM_CHAT_ID_HERE"

# ... other configurations
```

## Usage

### Backtesting

Run backtests to evaluate strategy performance:

```bash
python src/fourCoinsBacktest2.py
```

### Live Trading

Start the live trading manager:

```bash
python src/live/live_trading_manager.py
```

### Visualization Dashboard

Launch the web dashboard:

```bash
cd visualisation
python app.py
```

Then open http://localhost:5000 in your browser.

## Trading Strategies

The bot includes multiple strategies for different cryptocurrencies:

### ETH Strategies
- `eth_hybrid_trend_sentiment`: Combines trend analysis with sentiment
- `eth_choppy_durability`: Handles choppy market conditions
- `eth_strong_bull_momentum`: Captures strong bull runs

### LINK Strategies
- `link_mean_reversion`: Mean reversion strategy
- `link_macd_downtrend_filter`: MACD-based trend filtering
- `link_cycle_momentum`: Momentum-based cycle trading

### MATIC Strategies
- `matic_breakout_clean`: Breakout detection
- `matic_bull_trend`: Bull trend following
- `matic_consolidation_then_break`: Consolidation breakout

### ARB Strategies
- `arb_breakout_clean`: Clean breakout signals
- `arb_bull_trend`: Trend following
- `arb_oversold_bounce`: Oversold bounce plays

### DOGE Strategies
- `doge_tweet_spike_strategy`: Twitter sentiment-based
- `doge_meme_momentum_strategy`: Meme momentum trading
- `doge_sentiment_consolidation_strategy`: Sentiment consolidation

## Risk Management

- **Stop Loss**: Configurable stop-loss percentages per bot
- **Take Profit**: Configurable take-profit targets
- **Position Sizing**: Risk-based position sizing
- **Rate Limiting**: Respects exchange rate limits
- **Maximum Trades**: Limits concurrent positions

## Security

- **API Keys**: Never commit real API keys to version control
- **Configuration**: Use `config.example.yaml` as template
- **Permissions**: Use read-only keys where possible
- **Testing**: Test with small amounts first

## Docker Deployment

Build and run with Docker:

```bash
cd cloud
docker build -t crypto-trading-bot .
docker run -d --name trading-bot crypto-trading-bot
```

## Monitoring and Logging

- **Telegram Alerts**: Real-time trade notifications
- **Log Files**: Detailed logging in `logs/` directory
- **Performance Metrics**: Track P&L, win rates, and drawdowns
- **Web Dashboard**: Visual performance monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Disclaimer

⚠️ **Important**: This trading bot is for educational purposes only. Cryptocurrency trading involves substantial risk and may result in significant financial losses. Always:

- Test with small amounts first
- Use testnet/paper trading initially
- Understand the risks involved
- Never invest more than you can afford to lose
- Consider consulting with financial advisors

The authors are not responsible for any financial losses incurred while using this software.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Review the documentation
- Check the logs for error messages

## Changelog

### v1.0.0
- Initial release
- Multi-cryptocurrency support
- Backtesting engine
- Live trading capabilities
- Sentiment analysis integration
- Web dashboard

---

**Happy Trading! 📈**