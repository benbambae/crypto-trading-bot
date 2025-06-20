# live_trading_manager.py

import threading
import os
import sys
import time
from datetime import datetime
from eth_bot import run_eth_bot
from link_bot import run_link_bot
from matic_bot import run_matic_bot
from doge_bot import run_doge_bot
from arb_bot import run_arb_bot
from bot_base import get_logger, load_config

# Add parent directory to path to import logging utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging_utils import (
    setup_logging,
    get_system_logger
)

# Initialize logging
setup_logging()
manager_logger = get_system_logger()

CONFIG_RELOAD_INTERVAL = 120

global_config = load_config()

# Thread and stop signal containers
bot_threads = {}
stop_events = {}

def config_watcher():
    global global_config
    while True:
        try:
            global_config = load_config()
            manager_logger.info("Config reloaded successfully")
            print(f"[{datetime.now()}] 🔁 Config reloaded.")
        except Exception as e:
            manager_logger.error(f"Config watcher error: {e}")
            print(f"[Config Watcher] ❌ Error: {e}")
        time.sleep(CONFIG_RELOAD_INTERVAL)

def start_bot(name):
    if name in bot_threads and bot_threads[name].is_alive():
        return f"{name.upper()} bot already running."

    stop_event = threading.Event()
    stop_events[name] = stop_event

    def wrapper():
        logger = get_logger(name.upper())
        try:
            {
                'eth': run_eth_bot,
                'link': run_link_bot,
                'matic': run_matic_bot,
                'doge': run_doge_bot,
                'arb': run_arb_bot
            }[name](logger, stop_event)
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            manager_logger.error(f"{name.upper()} bot crashed: {e}")

    t = threading.Thread(target=wrapper)
    t.daemon = True
    t.start()
    bot_threads[name] = t
    manager_logger.info(f"Started {name.upper()} bot thread")

    def monitor_thread():
        while True:
            if not t.is_alive():
                manager_logger.warning(f"{name.upper()} bot thread died, restarting...")
                print(f"[{name.upper()} Watchdog] ⚠️ Bot crashed. Restarting...")
                start_bot(name)
                break
            time.sleep(30)

    threading.Thread(target=monitor_thread, daemon=True).start()
    return f"{name.upper()} bot started."

def stop_bot(name):
    if name in stop_events:
        stop_events[name].set()
        return f"{name.upper()} bot stopping..."
    return f"{name.upper()} bot not running."

if __name__ == '__main__':
    threads = []

    for bot_name in ['eth', 'link', 'matic', 'doge', 'arb']:
        start_bot(bot_name)

    threads.append(threading.Thread(target=config_watcher, daemon=True))
    threads[-1].start()

    # Main thread will idle
    while True:
        time.sleep(60)
