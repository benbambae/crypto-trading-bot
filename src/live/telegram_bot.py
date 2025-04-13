# telegram_bot.py

import os
import yaml
import requests
import asyncio
import logging
import subprocess
from datetime import datetime
from collections import deque, defaultdict
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.helpers import escape_markdown

# Update config path to point to correct location
config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.yaml'))

with open(config_path, 'r') as f:
    CONFIG = yaml.safe_load(f)

BOT_TOKEN = CONFIG.get('alerts', {}).get('telegram', {}).get('token')
ALLOWED_CHAT_ID = str(CONFIG.get('alerts', {}).get('telegram', {}).get('chat_id'))

whale_enabled = CONFIG.get("whaleAlert", {}).get("enabled", True)
WH_API_KEY = CONFIG.get("whaleAlert", {}).get("api_key")
MIN_VALUE = CONFIG.get("whaleAlert", {}).get("min_value_usd", 1000000)

last_tx_ids = deque(maxlen=500)

def auth(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.effective_chat.id) != ALLOWED_CHAT_ID:
            await update.message.reply_text("⛔ Unauthorized.")
            return
        return await func(update, context)
    return wrapper

@auth
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/help - command list\n"
        "/status - check bot status\n"
        "/metrics - win rate / trades\n"
        "/logs [COIN] - tail of log\n"
        "/config - show config\n"
        "/whale on|off - toggle whale alerts\n"
        "/restart [COIN] - restart specific bot\n"
        "/reload - reload config"
    )

@auth
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot system is running.")

@auth
async def config_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config_preview = yaml.dump(CONFIG, default_flow_style=False)
    await update.message.reply_text(escape_markdown(f"🛠️ Current Config:\n{config_preview}", version=2), parse_mode="MarkdownV2")

@auth
async def metrics_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        trade_log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'logs', 'trade_logs.txt'))
        with open(trade_log_path, 'r') as f:
            lines = f.readlines()
        total = len([line for line in lines if "SELL" in line])
        wins = len([line for line in lines if "PnL:" in line and float(line.split("PnL: ")[-1]) > 0])
        msg = f"📊 Win Rate: {wins}/{total} ({round((wins/total)*100, 2)}%)" if total > 0 else "No trades yet."
        await update.message.reply_text(escape_markdown(msg, version=2), parse_mode="MarkdownV2")
    except Exception as e:
        await update.message.reply_text(escape_markdown(f"⚠️ Error fetching metrics: {e}", version=2), parse_mode="MarkdownV2")

@auth
async def logs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        coin = context.args[0].upper() if context.args else None
        if not coin:
            await update.message.reply_text("⚠️ Usage: /logs COIN")
            return
        log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'logs', f'{coin}_live.log'))
        if not os.path.exists(log_path):
            await update.message.reply_text("❌ Log file not found.")
            return
        with open(log_path, 'r') as f:
            lines = f.readlines()[-10:]
        await update.message.reply_text(escape_markdown("🧾 Last 10 log lines:\n" + "".join(lines[-10:]), version=2), parse_mode="MarkdownV2")
    except Exception as e:
        await update.message.reply_text(escape_markdown(f"⚠️ Error reading logs: {e}", version=2), parse_mode="MarkdownV2")

@auth
async def whale_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global whale_enabled
    arg = context.args[0].lower() if context.args else ''
    if arg == 'off':
        whale_enabled = False
        await update.message.reply_text("🐋 Whale alerts turned OFF.")
    elif arg == 'on':
        whale_enabled = True
        await update.message.reply_text("🐋 Whale alerts turned ON.")
    else:
        await update.message.reply_text("Usage: /whale on | /whale off")

@auth
async def restart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin = context.args[0].lower() if context.args else None
    if coin not in ['eth', 'link', 'doge', 'matic']:
        await update.message.reply_text("⚠️ Usage: /restart eth|link|doge|matic")
        return
    try:
        from live_trading_manager import start_bot
        msg = start_bot(coin)
        await update.message.reply_text(escape_markdown(f"♻️ {msg}", version=2), parse_mode="MarkdownV2")
    except Exception as e:
        await update.message.reply_text(escape_markdown(f"⚠️ Restart error: {e}", version=2), parse_mode="MarkdownV2")

@auth
async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin = context.args[0].lower() if context.args else None
    if coin not in ['eth', 'link', 'doge', 'matic']:
        await update.message.reply_text("⚠️ Usage: /stop eth|link|doge|matic")
        return
    try:
        from live_trading_manager import stop_bot
        msg = stop_bot(coin)
        await update.message.reply_text(escape_markdown(f"🛑 {msg}", version=2), parse_mode="MarkdownV2")
    except Exception as e:
        await update.message.reply_text(escape_markdown(f"⚠️ Stop error: {e}", version=2), parse_mode="MarkdownV2")

@auth
async def reload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global CONFIG
        with open(config_path, 'r') as f:
            CONFIG = yaml.safe_load(f)
        await update.message.reply_text("🔁 Config reloaded.")
    except Exception as e:
        await update.message.reply_text(escape_markdown(f"⚠️ Reload failed: {e}", version=2), parse_mode="MarkdownV2")

async def whale_alert_loop(app):
    global whale_enabled, last_tx_ids
    while True:
        try:
            if whale_enabled:
                url = f"https://api.whale-alert.io/v1/transactions?api_key={WH_API_KEY}&min_value={MIN_VALUE}&limit=20"
                resp = requests.get(url)
                data = resp.json()
                txs = data.get("transactions", [])
                for tx in txs:
                    tx_id = tx.get("id")
                    if tx_id in last_tx_ids:
                        continue
                    last_tx_ids.append(tx_id)

                    symbol = tx.get("symbol", "").upper()
                    if symbol not in {"ETH", "LINK", "MATIC", "DOGE"}:
                        continue

                    value = tx.get("amount_usd", 0)
                    from_label = tx.get("from", {}).get("owner", "Unknown")
                    to_label = tx.get("to", {}).get("owner", "Unknown")
                    ts = datetime.fromtimestamp(tx.get("timestamp")).strftime('%Y-%m-%d %H:%M:%S')

                    msg = (
                        f"🐋 Whale Alert\n"
                        f"Token: {symbol}\n"
                        f"Value: ${round(value):,}\n"
                        f"From: {from_label}\n"
                        f"To: {to_label}\n"
                        f"Time: {ts}"
                    )
                    await app.bot.send_message(
                        chat_id=ALLOWED_CHAT_ID,
                        text=escape_markdown(msg, version=2),
                        parse_mode="MarkdownV2"
                    )
        except Exception as e:
            print(f"[WhaleAlert Error] {e}")
        await asyncio.sleep(90)

def generate_daily_summary():
    try:
        trade_log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'logs', 'trade_logs.txt'))
        today = datetime.now().date()
        
        stats = defaultdict(lambda: {"wins": 0, "losses": 0, "total_pnl": 0})
        
        with open(trade_log_path, 'r') as f:
            for line in f:
                try:
                    # Parse date from log line
                    log_date = datetime.strptime(line.split(" - ")[0], "%Y-%m-%d %H:%M:%S").date()
                    
                    if log_date == today and "SELL" in line:
                        # Extract symbol and PnL
                        symbol = line.split(" ")[2]  # Assumes format like "ETHUSDT SELL"
                        pnl = float(line.split("PnL: ")[1].split(" ")[0])
                        
                        stats[symbol]["total_pnl"] += pnl
                        if pnl > 0:
                            stats[symbol]["wins"] += 1
                        else:
                            stats[symbol]["losses"] += 1
                except:
                    continue

        # Generate summary message
        summary = "📊 Daily Trading Summary\n\n"
        total_pnl = 0
        
        for symbol in sorted(stats.keys()):
            stat = stats[symbol]
            total = stat["wins"] + stat["losses"]
            win_rate = (stat["wins"] / total * 100) if total > 0 else 0
            total_pnl += stat["total_pnl"]
            
            summary += (f"{symbol}:\n"
                       f"Trades: {total} (W: {stat['wins']}, L: {stat['losses']})\n"
                       f"Win Rate: {win_rate:.1f}%\n"
                       f"PnL: ${stat['total_pnl']:.2f}\n\n")
            
        summary += f"Total Daily PnL: ${total_pnl:.2f}"
        return summary
        
    except Exception as e:
        return f"⚠️ Error generating daily summary: {e}"

async def daily_summary_loop(app):
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            try:
                summary = generate_daily_summary()
                await app.bot.send_message(
                    chat_id=ALLOWED_CHAT_ID,
                    text=escape_markdown(summary, version=2),
                    parse_mode="MarkdownV2"
                )
            except Exception as e:
                print(f"[Daily Summary Error] {e}")
        await asyncio.sleep(60)

async def post_init(app):
    asyncio.create_task(whale_alert_loop(app))
    asyncio.create_task(daily_summary_loop(app))
    print("🚀 Telegram bot running with WhaleAlert and Daily Summary...")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("metrics", metrics_cmd))
    app.add_handler(CommandHandler("logs", logs_cmd))
    app.add_handler(CommandHandler("config", config_cmd))
    app.add_handler(CommandHandler("whale", whale_cmd))
    app.add_handler(CommandHandler("restart", restart_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("reload", reload_cmd))

    app.run_polling()
