# bot_base.py
import requests
import yaml
import os
import logging
import time
from datetime import datetime

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml'))
TRADE_LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'logs', 'trade_logs.txt'))

# Load or reload config
def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

# Setup logger for each bot
def get_logger(name):
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(os.path.join(log_dir, f'{name}_live.log'))
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    handler.setFormatter(formatter)
    if not logger.hasHandlers():
        logger.addHandler(handler)
    return logger

# Log trade with timestamp
def log_trade(symbol, action, price, pnl=None):
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'logs'))
    os.makedirs(log_dir, exist_ok=True)
    with open(TRADE_LOG_PATH, 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        pnl_str = f" | PnL: {round(pnl, 4)}" if pnl is not None else ""
        f.write(f"{timestamp} | {symbol} | {action.upper()} | Price: {price}{pnl_str}\n")


def telegram_alert(message):
    try:
        config = load_config()
        alert_cfg = config.get("alerts", {}).get("telegram", {})
        if not alert_cfg.get("enabled", False):
            return

        token = alert_cfg["token"]
        chat_id = alert_cfg["chat_id"]

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload)
    except Exception as e:
        print(f"[TELEGRAM ALERT ERROR] {e}")

def retry_binance_call(fn, retries=3, delay=2):
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e
