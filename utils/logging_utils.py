"""
Logging utilities for the cryptocurrency trading bot
Provides centralized logging configuration and helper functions
"""

import logging
import logging.config
import yaml
import os
from pathlib import Path
from typing import Optional

class TradingLoggerAdapter(logging.LoggerAdapter):
    """
    Custom logger adapter that adds trading-specific context to log records
    """
    def __init__(self, logger, coin=None, strategy=None):
        super().__init__(logger, {})
        self.coin = coin or "SYSTEM"
        self.strategy = strategy or "GENERAL"
    
    def process(self, msg, kwargs):
        return f"[{self.coin}:{self.strategy}] {msg}", kwargs

class LoggingManager:
    """
    Centralized logging management for the trading bot
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.setup_logging()
    
    def _get_default_config_path(self) -> str:
        """Get the default logging configuration path"""
        current_dir = Path(__file__).parent
        return str(current_dir.parent / "config" / "logging_config.yaml")
    
    def setup_logging(self):
        """Setup logging configuration from YAML file"""
        try:
            # Ensure log directories exist
            self._create_log_directories()
            
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                logging.config.dictConfig(config)
                print(f"Logging configured from: {self.config_path}")
            else:
                # Fallback to basic configuration
                self._setup_basic_logging()
                print(f"Config file not found: {self.config_path}. Using basic logging.")
                
        except Exception as e:
            print(f"Error setting up logging: {e}")
            self._setup_basic_logging()
    
    def _create_log_directories(self):
        """Create necessary log directories"""
        base_log_dir = Path(__file__).parent.parent / "logs"
        
        directories = [
            "live_trading/system",
            "live_trading/ETH",
            "live_trading/LINK", 
            "live_trading/MATIC",
            "live_trading/ARB",
            "live_trading/DOGE",
            "backtesting/full_runs",
            "backtesting/individual_strategies",
            "backtesting/multi_coin",
            "sentiment_analysis",
            "system",
            "archived"
        ]
        
        for directory in directories:
            (base_log_dir / directory).mkdir(parents=True, exist_ok=True)
    
    def _setup_basic_logging(self):
        """Setup basic logging configuration as fallback"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def get_logger(self, name: str, coin: Optional[str] = None, strategy: Optional[str] = None) -> logging.Logger:
        """
        Get a logger with optional trading context
        
        Args:
            name: Logger name
            coin: Cryptocurrency symbol (ETH, BTC, etc.)
            strategy: Trading strategy name
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        
        if coin or strategy:
            return TradingLoggerAdapter(logger, coin=coin, strategy=strategy)
        
        return logger
    
    def get_trading_logger(self, coin: str, strategy: str = None) -> logging.Logger:
        """
        Get a logger specifically for trading operations
        
        Args:
            coin: Cryptocurrency symbol
            strategy: Trading strategy name
            
        Returns:
            Trading logger instance
        """
        logger_name = f"trading.live.{coin.lower()}"
        logger = logging.getLogger(logger_name)
        return TradingLoggerAdapter(logger, coin=coin, strategy=strategy)
    
    def get_backtest_logger(self, strategy: str = None) -> logging.Logger:
        """
        Get a logger for backtesting operations
        
        Args:
            strategy: Strategy being backtested
            
        Returns:
            Backtest logger instance
        """
        logger = logging.getLogger("trading.backtest")
        if strategy:
            return TradingLoggerAdapter(logger, coin="BACKTEST", strategy=strategy)
        return logger
    
    def get_sentiment_logger(self) -> logging.Logger:
        """Get a logger for sentiment analysis operations"""
        return logging.getLogger("trading.sentiment")
    
    def get_system_logger(self) -> logging.Logger:
        """Get a logger for system operations"""
        return logging.getLogger("trading.system")

# Global logging manager instance
_logging_manager = None

def get_logging_manager() -> LoggingManager:
    """Get the global logging manager instance"""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager()
    return _logging_manager

def setup_logging(config_path: Optional[str] = None):
    """Setup logging for the entire application"""
    global _logging_manager
    _logging_manager = LoggingManager(config_path)

def get_logger(name: str, coin: Optional[str] = None, strategy: Optional[str] = None) -> logging.Logger:
    """Convenience function to get a logger"""
    return get_logging_manager().get_logger(name, coin, strategy)

def get_trading_logger(coin: str, strategy: str = None) -> logging.Logger:
    """Convenience function to get a trading logger"""
    return get_logging_manager().get_trading_logger(coin, strategy)

def get_backtest_logger(strategy: str = None) -> logging.Logger:
    """Convenience function to get a backtest logger"""
    return get_logging_manager().get_backtest_logger(strategy)

def get_sentiment_logger() -> logging.Logger:
    """Convenience function to get a sentiment logger"""
    return get_logging_manager().get_sentiment_logger()

def get_system_logger() -> logging.Logger:
    """Convenience function to get a system logger"""
    return get_logging_manager().get_system_logger()

# Example usage functions
def log_trade(coin: str, strategy: str, action: str, price: float, quantity: float, **kwargs):
    """
    Log a trade action with consistent formatting
    
    Args:
        coin: Cryptocurrency symbol
        strategy: Trading strategy
        action: BUY, SELL, etc.
        price: Trade price
        quantity: Trade quantity
        **kwargs: Additional trade details
    """
    logger = get_trading_logger(coin, strategy)
    
    trade_info = f"{action} {quantity} {coin} @ ${price:.2f}"
    if kwargs:
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        trade_info += f" | {extra_info}"
    
    logger.info(trade_info)

def log_backtest_result(strategy: str, coin: str, total_return: float, win_rate: float, **kwargs):
    """
    Log backtest results with consistent formatting
    
    Args:
        strategy: Strategy name
        coin: Cryptocurrency tested
        total_return: Total return percentage
        win_rate: Win rate percentage
        **kwargs: Additional metrics
    """
    logger = get_backtest_logger(strategy)
    
    result_info = f"BACKTEST COMPLETE - {coin} | Return: {total_return:.2f}% | Win Rate: {win_rate:.1f}%"
    if kwargs:
        extra_metrics = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        result_info += f" | {extra_metrics}"
    
    logger.info(result_info)

def log_sentiment_analysis(coin: str, source: str, sentiment_score: float, **kwargs):
    """
    Log sentiment analysis results
    
    Args:
        coin: Cryptocurrency symbol
        source: Data source (twitter, reddit, etc.)
        sentiment_score: Sentiment score
        **kwargs: Additional sentiment data
    """
    logger = get_sentiment_logger()
    
    sentiment_info = f"SENTIMENT - {coin} | Source: {source} | Score: {sentiment_score:.3f}"
    if kwargs:
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        sentiment_info += f" | {extra_info}"
    
    logger.info(sentiment_info)