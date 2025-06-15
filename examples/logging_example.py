#!/usr/bin/env python3
"""
Example of how to use the new logging system in the trading bot
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging_utils import (
    setup_logging,
    get_trading_logger,
    get_backtest_logger,
    get_sentiment_logger,
    get_system_logger,
    log_trade,
    log_backtest_result,
    log_sentiment_analysis
)

def demonstrate_logging():
    """Demonstrate the new logging system"""
    
    # Setup logging system
    print("Setting up logging system...")
    setup_logging()
    
    # Get different types of loggers
    eth_logger = get_trading_logger("ETH", "eth_bull_momentum")
    backtest_logger = get_backtest_logger("multi_coin_strategy")
    sentiment_logger = get_sentiment_logger()
    system_logger = get_system_logger()
    
    # Example trading logs
    print("\n1. Trading Logs:")
    eth_logger.info("Starting ETH bull momentum strategy")
    eth_logger.info("Market conditions: bullish trend detected")
    
    # Example trade logging
    log_trade(
        coin="ETH",
        strategy="eth_bull_momentum", 
        action="BUY",
        price=3450.50,
        quantity=0.1,
        stop_loss=3300.00,
        take_profit=3600.00,
        confidence=0.85
    )
    
    log_trade(
        coin="ETH",
        strategy="eth_bull_momentum",
        action="SELL", 
        price=3580.75,
        quantity=0.1,
        profit_pct=3.77,
        reason="take_profit_hit"
    )
    
    # Example backtest logs
    print("\n2. Backtest Logs:")
    backtest_logger.info("Starting multi-coin backtest for Q1 2024")
    
    log_backtest_result(
        strategy="multi_coin_strategy",
        coin="ETH",
        total_return=15.3,
        win_rate=68.5,
        max_drawdown=8.2,
        sharpe_ratio=1.45,
        total_trades=127
    )
    
    log_backtest_result(
        strategy="multi_coin_strategy", 
        coin="LINK",
        total_return=22.7,
        win_rate=71.2,
        max_drawdown=12.1,
        sharpe_ratio=1.62,
        total_trades=89
    )
    
    # Example sentiment logs
    print("\n3. Sentiment Analysis Logs:")
    log_sentiment_analysis(
        coin="DOGE",
        source="twitter",
        sentiment_score=0.72,
        tweet_count=1542,
        trending_rank=3,
        elon_mentions=5
    )
    
    log_sentiment_analysis(
        coin="ETH", 
        source="reddit",
        sentiment_score=0.61,
        post_count=234,
        upvote_ratio=0.89,
        top_subreddits=["ethereum", "ethtrader", "defi"]
    )
    
    # Example system logs
    print("\n4. System Logs:")
    system_logger.info("Trading bot initialization complete")
    system_logger.debug("Loading configuration from config.yaml")
    system_logger.warning("Rate limit approaching for Binance API")
    system_logger.error("Failed to connect to Reddit API", exc_info=True)
    
    # Different coin loggers
    print("\n5. Multiple Coin Logs:")
    link_logger = get_trading_logger("LINK", "link_mean_reversion")
    doge_logger = get_trading_logger("DOGE", "doge_sentiment_strategy")
    
    link_logger.info("Detecting oversold conditions")
    doge_logger.info("High social media sentiment detected")
    
    log_trade("LINK", "link_mean_reversion", "BUY", 14.25, 50, rsi=28.5)
    log_trade("DOGE", "doge_sentiment_strategy", "BUY", 0.0825, 1000, sentiment_score=0.78)
    
    print("\nLogging demonstration complete!")
    print("Check the logs/ directory for organized log files:")
    print("- logs/live_trading/ETH/eth_trading.log")
    print("- logs/live_trading/LINK/link_trading.log") 
    print("- logs/live_trading/DOGE/doge_trading.log")
    print("- logs/backtesting/backtest.log")
    print("- logs/sentiment_analysis/sentiment.log")
    print("- logs/system/system.log")

if __name__ == "__main__":
    demonstrate_logging()