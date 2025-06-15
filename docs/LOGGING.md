# Logging System Documentation

## Overview

The cryptocurrency trading bot now uses a comprehensive, organized logging system that automatically categorizes logs by type and provides easy management tools.

## Directory Structure

```
logs/
├── live_trading/           # Live trading operation logs
│   ├── system/            # System-wide trading logs
│   ├── ETH/               # Ethereum-specific logs
│   ├── LINK/              # Chainlink-specific logs
│   ├── MATIC/             # Polygon-specific logs
│   ├── ARB/               # Arbitrum-specific logs
│   └── DOGE/              # Dogecoin-specific logs
├── backtesting/           # Backtesting operation logs
│   ├── full_runs/         # Complete backtest runs
│   ├── individual_strategies/  # Single strategy tests
│   └── multi_coin/        # Multi-cryptocurrency tests
├── sentiment_analysis/    # Social media sentiment logs
├── system/               # System and error logs
└── archived/             # Archived logs by year
    ├── 2024/
    └── 2025/
```

## Log Types

### 1. Live Trading Logs
- **Location**: `logs/live_trading/`
- **Purpose**: Track real-time trading activities
- **Rotation**: 5MB per file, 3 backups
- **Format**: `TIMESTAMP - [LEVEL] - COIN - STRATEGY - MESSAGE`

### 2. Backtesting Logs
- **Location**: `logs/backtesting/`
- **Purpose**: Record strategy testing results
- **Rotation**: 10MB per file, 5 backups
- **Format**: Detailed with function names and line numbers

### 3. Sentiment Analysis Logs
- **Location**: `logs/sentiment_analysis/`
- **Purpose**: Track social media sentiment analysis
- **Rotation**: 5MB per file, 3 backups
- **Format**: Standard with timestamp and level

### 4. System Logs
- **Location**: `logs/system/`
- **Purpose**: General system operations and errors
- **Rotation**: 10MB per file, 10 backups for errors
- **Format**: Detailed with module and function information

## Using the Logging System

### Quick Start

```python
from utils.logging_utils import setup_logging, get_trading_logger, log_trade

# Initialize logging system
setup_logging()

# Get a logger for ETH trading
logger = get_trading_logger("ETH", "bull_momentum_strategy")

# Log trading activities
logger.info("Starting ETH bull momentum strategy")

# Log a trade with helper function
log_trade("ETH", "bull_momentum", "BUY", 3450.50, 0.1, stop_loss=3300.00)
```

### Getting Different Logger Types

```python
from utils.logging_utils import (
    get_trading_logger,
    get_backtest_logger, 
    get_sentiment_logger,
    get_system_logger
)

# Trading logger for specific coin/strategy
eth_logger = get_trading_logger("ETH", "trend_following")

# Backtesting logger
backtest_logger = get_backtest_logger("multi_coin_strategy")

# Sentiment analysis logger
sentiment_logger = get_sentiment_logger()

# System operations logger
system_logger = get_system_logger()
```

### Helper Functions

#### Log Trades
```python
from utils.logging_utils import log_trade

log_trade(
    coin="ETH",
    strategy="bull_momentum", 
    action="BUY",
    price=3450.50,
    quantity=0.1,
    stop_loss=3300.00,
    take_profit=3600.00,
    confidence=0.85
)
```

#### Log Backtest Results
```python
from utils.logging_utils import log_backtest_result

log_backtest_result(
    strategy="eth_bull_momentum",
    coin="ETH", 
    total_return=15.3,
    win_rate=68.5,
    max_drawdown=8.2,
    sharpe_ratio=1.45
)
```

#### Log Sentiment Analysis
```python
from utils.logging_utils import log_sentiment_analysis

log_sentiment_analysis(
    coin="DOGE",
    source="twitter",
    sentiment_score=0.72,
    tweet_count=1542,
    trending_rank=3
)
```

## Log Management

### Automatic Management

The logging system includes automatic features:
- **Log Rotation**: Prevents files from growing too large
- **Organized Structure**: Automatically sorts logs by type and coin
- **Timestamped Entries**: All logs include precise timestamps

### Manual Management

Use the log management script for maintenance:

```bash
# Show log directory summary
python scripts/log_manager.py --summary

# Clean up empty log files
python scripts/log_manager.py --cleanup

# Rotate large log files (>10MB)
python scripts/log_manager.py --rotate 10

# Archive old logs (>30 days)
python scripts/log_manager.py --archive 30

# Organize logs by date
python scripts/log_manager.py --organize

# Run all maintenance operations
python scripts/log_manager.py --all
```

### Log Retention Policy

- **Active Logs**: Keep for 30 days
- **Archived Logs**: Compressed and stored by year
- **Error Logs**: Keep for 90 days (10 backup files)
- **Large Files**: Auto-rotate when exceeding size limits

## Configuration

### Logging Configuration File
Location: `config/logging_config.yaml`

Key settings:
- Log levels (DEBUG, INFO, WARNING, ERROR)
- File rotation sizes and backup counts
- Output formats for different log types
- Handler assignments for each logger

### Customizing Logging

To modify logging behavior:

1. Edit `config/logging_config.yaml`
2. Adjust log levels, file sizes, or formats
3. Restart your trading applications

Example configuration changes:

```yaml
# Change ETH log level to DEBUG
loggers:
  trading.live.eth:
    level: DEBUG
    handlers: [eth_trading_file, live_trading_file]

# Increase backup count for system logs
handlers:
  system_file:
    backupCount: 10  # Keep 10 backup files
```

## Log File Locations

### Current Active Logs
- **ETH Trading**: `logs/live_trading/ETH/eth_trading.log`
- **LINK Trading**: `logs/live_trading/LINK/link_trading.log`
- **MATIC Trading**: `logs/live_trading/MATIC/matic_trading.log`
- **ARB Trading**: `logs/live_trading/ARB/arb_trading.log`
- **DOGE Trading**: `logs/live_trading/DOGE/doge_trading.log`
- **Backtesting**: `logs/backtesting/backtest.log`
- **Sentiment**: `logs/sentiment_analysis/sentiment.log`
- **System**: `logs/system/system.log`
- **Errors**: `logs/system/errors.log`

### Historical Logs
- **Live Trading System**: `logs/live_trading/system/`
- **Backtest Runs**: `logs/backtesting/full_runs/`
- **Individual Strategies**: `logs/backtesting/individual_strategies/`
- **Multi-Coin Tests**: `logs/backtesting/multi_coin/`
- **Archived**: `logs/archived/2024/`, `logs/archived/2025/`

## Best Practices

### 1. Use Appropriate Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error conditions that don't stop execution
- **CRITICAL**: Serious errors that may stop execution

### 2. Include Context in Log Messages
```python
# Good: Includes relevant context
logger.info(f"Buy order executed: {quantity} {coin} @ ${price:.2f}")

# Better: Use helper functions for consistency
log_trade(coin, strategy, "BUY", price, quantity)
```

### 3. Log Important Events
- Trade executions (buy/sell orders)
- Strategy signals and decisions
- Error conditions and recoveries
- System state changes
- Performance metrics

### 4. Regular Maintenance
- Run log cleanup weekly: `python scripts/log_manager.py --cleanup`
- Archive old logs monthly: `python scripts/log_manager.py --archive 30`
- Monitor log sizes: `python scripts/log_manager.py --summary`

## Troubleshooting

### Common Issues

#### Logs Not Appearing
1. Check if log directories exist
2. Verify logging configuration file exists
3. Ensure proper permissions on log directories

#### Large Log Files
1. Run log rotation: `python scripts/log_manager.py --rotate 5`
2. Archive old logs: `python scripts/log_manager.py --archive 7`
3. Adjust rotation settings in `logging_config.yaml`

#### Missing Log Context
1. Use `TradingLoggerAdapter` for coin/strategy context
2. Use helper functions (`log_trade`, `log_backtest_result`)
3. Include relevant data in log messages

### Getting Help

If you encounter logging issues:
1. Check the `logs/system/errors.log` file
2. Run `python examples/logging_example.py` to test the system
3. Verify your logging configuration with `--summary`

## Example Usage

See `examples/logging_example.py` for a complete demonstration of the logging system features.