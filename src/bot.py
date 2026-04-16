import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import database 

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTHORIZED_CHAT_ID = int(os.getenv("AUTHORIZED_CHAT_ID")) 

async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != AUTHORIZED_CHAT_ID:
        return

    if not context.args or context.args[0].lower() not in ["waterfall", "proportional"]:
        await update.message.reply_text("⚠️ Usage: /mode waterfall OR /mode proportional")
        return

    new_mode = context.args[0].lower()
    
    # Save to the local DB directly using sqlite3 to bypass the module lock
    import sqlite3
    conn = sqlite3.connect('crypto_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET mode = ?", (new_mode,))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"✅ Rebalance mode locked in: {new_mode.upper()}")

async def get_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != AUTHORIZED_CHAT_ID:
        return
        
    settings = database.get_settings()
    await update.message.reply_text(f"🤖 Slipstream Online.\nActive Mode: {settings['mode'].upper()}")

if __name__ == "__main__":
    print("📡 Telegram listener booting up...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("mode", set_mode))
    app.add_handler(CommandHandler("status", get_status))
    app.run_polling()