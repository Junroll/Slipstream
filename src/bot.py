import os
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import src.database as database

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTHORIZED_CHAT_ID = int(os.getenv("AUTHORIZED_CHAT_ID"))

AWAITING_PANIC = False

# --- SYSTEM FLARE ---
def send_sync_alert(message):
    """A synchronous HTTP sender used strictly for boot-up and shutdown flares."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": AUTHORIZED_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

# --- SECURITY WRAPPER ---
def is_authorized(chat_id):
    return chat_id == AUTHORIZED_CHAT_ID

# --- CORE COMMANDS ---

async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id): return
    menu = (
        "🏎️ **Slipstream Command Center**\n\n"
        "⚠️ *NOTE: The engine boots in a PAUSED state. Configure your /ignore list, then use /resume to start trading.*\n\n"
        "**Core Controls:**\n"
        "/info - What is Slipstream?\n"
        "/status - View current bot settings and HWM\n"
        "/history [n] - View recent transactions\n"
        "/pause - Emergency stop (halts trading)\n"
        "/resume - Reactivate trading loop\n"
        "/mute - Stop push notifications\n"
        "/unmute - Resume push notifications\n\n"
        "**Trading Logic:**\n"
        "/mode - Change allocation logic\n"
        "/floor - Update the lockdown drop percentage\n\n"
        "**Blacklist Management:**\n"
        "/blacklist - View ignored coins\n"
        "/ignore [COIN] - Add to blacklist\n"
        "/allow [COIN] - Remove from blacklist\n\n"
        "**Emergency:**\n"
        "/panic - Liquidate all assets into fiat"
    )
    await update.message.reply_text(menu, parse_mode='Markdown')

async def info_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id): return
    msg = (
        "🏎️ **Slipstream Engine v1.0**\n\n"
        "Slipstream is an algorithmic, stateful portfolio rebalancer.\n"
        "It acts as a mechanical investment strategy, running on a scheduled interval to check your live Coinbase balances against a mathematically perfect target weight.\n\n"
        "It aggressively skims profits from assets that pump past your threshold and reallocates that capital into bleeding assets, automating the \"buy low, sell high\" cycle without emotion. It also utilizes a dynamic High-Water Mark to freeze all trading if the market crashes."
    )
    await update.message.reply_text(msg)

async def get_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id): return
    settings = database.get_settings()
    hwm = database.get_high_water_mark()
    
    state = "🔴 PAUSED" if settings['is_paused'] else "🟢 ACTIVE"
    audio = "🔇 MUTED" if settings['is_muted'] else "🔊 ON"
    
    msg = (
        f"🤖 **Slipstream Status:** {state}\n"
        f"🔔 **Alerts:** {audio}\n"
        f"📈 **High-Water Mark:** ${hwm:,.2f}\n"
        f"⚙️ **Mode:** {settings['mode'].upper()}\n"
        f"📊 **Threshold:** {settings['threshold_pct'] * 100}%\n"
        f"🛡️ **Floor:** {settings['floor_pct'] * 100}%"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def get_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id): return
    
    limit = 10
    if context.args:
        try:
            limit = int(context.args[0])
        except ValueError:
            await update.message.reply_text("⚠️ Please provide a valid number. Defaulting to 10.")
            
    txs = database.get_recent_transactions(limit)
    
    if not txs:
        await update.message.reply_text("📭 No transaction history found.")
        return
        
    msg = f"📜 **Last {len(txs)} Transactions:**\n\n"
    for tx in txs:
        # e.g., 2026-04-16 12:00:00 | BUY | BTC | $50.00
        clean_time = tx['timestamp'].split('.')[0] # Strips milliseconds if present
        msg += f"`{clean_time}` | **{tx['action']}** {tx['coin']} | ${tx['amount_usd']:,.2f}\n"
        
    await update.message.reply_text(msg, parse_mode='Markdown')

# --- TOGGLE SWITCHES ---

async def pause_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id): return
    database.update_setting('is_paused', 1)
    await update.message.reply_text("🛑 **Slipstream is PAUSED.**", parse_mode='Markdown')

async def resume_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id): return
    database.update_setting('is_paused', 0)
    await update.message.reply_text("🟢 **Slipstream is ACTIVE.**", parse_mode='Markdown')

async def mute_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id): return
    database.update_setting('is_muted', 1)
    await update.message.reply_text("🔇 **Notifications Muted.**")

async def unmute_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id): return
    database.update_setting('is_muted', 0)
    await update.message.reply_text("🔊 **Notifications Active.**")

# --- PARAMETER CONTROLS ---

async def update_floor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id): return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /floor [NEGATIVE PERCENTAGE]\nExample: `/floor -20`", parse_mode='Markdown')
        return
        
    try:
        val = float(context.args[0])
        
        # Enforce negative requirement
        if val >= 0:
            await update.message.reply_text("❌ The floor must be a **negative** number (e.g., -20 for a 20% drop).", parse_mode='Markdown')
            return
            
        # If user types "-20", convert to "-0.20" for the math engine
        if val <= -1.0:
            val = val / 100.0
            
        database.update_setting('floor_pct', val)
        await update.message.reply_text(f"🛡️ **Floor Updated:** Lockdown will trigger on a {val * 100}% drop from the High-Water Mark.", parse_mode='Markdown')
        
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number (e.g., -20).")

async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id): return
    keyboard = [
        [InlineKeyboardButton("🌊 Waterfall", callback_data='mode_waterfall'),
         InlineKeyboardButton("⚖️ Proportional", callback_data='mode_proportional')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ **Select Rebalance Logic:**", reply_markup=reply_markup, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_authorized(query.message.chat.id):
        await query.answer("Unauthorized.", show_alert=True)
        return
    await query.answer()
    if query.data.startswith('mode_'):
        new_mode = query.data.split('_')[1]
        database.update_setting('mode', new_mode)
        await query.edit_message_text(f"✅ Rebalance mode locked in: **{new_mode.upper()}**", parse_mode='Markdown')

# --- BLACKLIST CONTROLS ---

async def view_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id): return
    ignored = database.get_blacklist()
    if not ignored:
        await update.message.reply_text("The blacklist is currently empty.")
    else:
        await update.message.reply_text(f"🚫 **Blacklisted Coins:**\n{', '.join(ignored)}", parse_mode='Markdown')

async def ignore_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id): return
    if not context.args: return
    coin = context.args[0].upper()
    success = database.add_to_blacklist(coin)
    msg = f"✅ {coin} added to the blacklist." if success else f"⚠️ {coin} is already on the blacklist."
    await update.message.reply_text(msg)

async def allow_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id): return
    if not context.args: return
    coin = context.args[0].upper()
    deleted = database.remove_from_blacklist(coin)
    msg = f"✅ {coin} removed from the blacklist." if deleted else f"⚠️ {coin} wasn't on the blacklist."
    await update.message.reply_text(msg)

# --- TEXT-BASED PANIC SYSTEM ---

async def panic_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AWAITING_PANIC
    if not is_authorized(update.effective_chat.id): return
    AWAITING_PANIC = True
    await update.message.reply_text(
        "🚨 **WARNING: PANIC MODE** 🚨\n\n"
        "Are you absolutely sure? This will instantly market-sell all non-blacklisted assets into fiat and halt the bot.\n\n"
        "To proceed, reply exactly with: `CONFIRM PANIC`\n"
        "*(Type anything else to cancel)*",
        parse_mode='Markdown'
    )

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AWAITING_PANIC
    if not is_authorized(update.effective_chat.id): return

    if AWAITING_PANIC:
        if update.message.text.strip() == "CONFIRM PANIC":
            AWAITING_PANIC = False
            await update.message.reply_text("🚨 **PANIC MODE ENGAGED** 🚨\nInitiating emergency liquidation...", parse_mode='Markdown')
            database.update_setting('is_paused', 1)
            
            import src.exchange as exchange
            balances = exchange.get_portfolio_balances()
            blacklist = database.get_blacklist()
            sold_count = 0
            for coin, amount_usd in balances.items():
                if coin not in blacklist and amount_usd > 1.00:
                    res = exchange.execute_trade("SELL", coin, amount_usd)
                    if res:
                        database.log_transaction("SELL (PANIC)", coin, amount_usd)
                        sold_count += 1
            await update.message.reply_text(f"🛑 **Liquidation Complete.** Sold {sold_count} assets. Slipstream is PAUSED.", parse_mode='Markdown')
        else:
            AWAITING_PANIC = False
            await update.message.reply_text("✅ **Panic aborted.**", parse_mode='Markdown')

if __name__ == "__main__":
    try:
        print("📡 Telegram listener booting up...")
        send_sync_alert("🟢 Slipstream Mission Control Online.\n🛑 Engine is currently PAUSED for setup. Configure your /ignore list, then text /resume to engage. \n\n Use /help for a list of commands.")
        
        app = Application.builder().token(BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", help_menu))
        app.add_handler(CommandHandler("help", help_menu))
        app.add_handler(CommandHandler("info", info_bot))
        app.add_handler(CommandHandler("status", get_status))
        app.add_handler(CommandHandler("history", get_history))
        app.add_handler(CommandHandler("pause", pause_bot))
        app.add_handler(CommandHandler("resume", resume_bot))
        app.add_handler(CommandHandler("mute", mute_bot))
        app.add_handler(CommandHandler("unmute", unmute_bot))
        app.add_handler(CommandHandler("mode", set_mode))
        app.add_handler(CommandHandler("floor", update_floor))
        app.add_handler(CommandHandler("blacklist", view_blacklist))
        app.add_handler(CommandHandler("ignore", ignore_coin))
        app.add_handler(CommandHandler("allow", allow_coin))
        app.add_handler(CommandHandler("panic", panic_request))
        
        app.add_handler(CallbackQueryHandler(button_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
        
        app.run_polling()
        
    except KeyboardInterrupt:
        print("\nManual shutdown intercepted.")
    finally:
        print("📡 Server shutting down... sending final flare.")
        send_sync_alert("🔴 Slipstream Mission Control Offline (Process Terminated).")