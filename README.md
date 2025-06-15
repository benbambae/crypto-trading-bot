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
- **Professional Logging**: Organized logging system with automatic categorization
- **Docker Support**: Easy deployment with containerization

## Project Structure

```
bencryptobot/
├── crypto-trading-bot/          # Main trading bot application
│   ├── src/                     # Source code
│   ├── config/                  # Configuration files
│   ├── visualisation/           # Web dashboard
│   └── requirements.txt         # Python dependencies
├── cloud/                       # Cloud deployment version
├── logs/                        # Organized logging system
├── utils/                       # Shared utilities and logging
├── docs/                        # Documentation
├── scripts/                     # Management tools
└── examples/                    # Usage examples
```

## Quick Start

### Prerequisites

- Python 3.8+
- Binance account (for live trading)
- API keys for various services (see Configuration section)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/benbambae/crypto-trading-bot.git
   cd crypto-trading-bot
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
   cp config.example.yaml config.yaml
   # Edit config.yaml with your API keys and settings
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

## Usage

### Backtesting

Run backtests to evaluate strategy performance:

```bash
python crypto-trading-bot/src/fourCoinsBacktest2.py
```

### Live Trading

Start the live trading manager:

```bash
python cloud/live_trading_manager.py
```

### Visualization Dashboard

Launch the web dashboard:

```bash
cd crypto-trading-bot/visualisation
python app.py
```

Then open http://localhost:5000 in your browser.

## AWS EC2 Deployment

### Step 1: Launch EC2 Instance

1. **Choose Instance Type**:
   - Minimum: `t3.small` (2 vCPU, 2 GB RAM)
   - Recommended: `t3.medium` (2 vCPU, 4 GB RAM) for better performance

2. **Configure Instance**:
   - AMI: Ubuntu Server 22.04 LTS
   - Storage: 20 GB gp3 (General Purpose SSD)
   - Security Group: Allow SSH (port 22) from your IP

### Step 2: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Git
sudo apt install git -y
```

### Step 3: Deploy with Docker

```bash
# Clone and configure
git clone https://github.com/benbambae/crypto-trading-bot.git
cd crypto-trading-bot/cloud

# Configure your API keys
cp ../config.example.yaml config.yaml
nano config.yaml

# Build and run
docker build -t crypto-bot .
docker run -d --name crypto-bot --restart=unless-stopped crypto-bot
```

## Trading Strategies

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

## Professional Logging System

The bot includes an organized logging system:

```
logs/
├── live_trading/          # Live trading logs by coin
├── backtesting/          # Backtesting results
├── sentiment_analysis/   # Social media analysis
└── system/              # System operations
```

### Log Management

```bash
# View log summary
python scripts/log_manager.py --summary

# Clean up old logs
python scripts/log_manager.py --cleanup

# Archive logs older than 30 days
python scripts/log_manager.py --archive 30
```

## Telegram Bot Commands

- `/start` - Initialize bot
- `/menu` - Show main menu
- `/start_all` - Start all enabled trading bots
- `/stop_all` - Stop all trading bots
- `/metrics` - View trading metrics
- `/logs` - View recent logs
- `/whale_alerts` - Toggle whale alerts
- `/sentiment` - Check market sentiment

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

## Documentation

- `docs/LOGGING.md` - Complete logging system guide
- `docs/LOGGING_MIGRATION.md` - Migration details
- `examples/logging_example.py` - Usage examples

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

## Support

For support and questions:
- Create an issue on GitHub
- Review the documentation
- Check the logs for error messages

---

**Happy Trading! 📈**
