import os
import requests
from dotenv import load_dotenv
import src.database as database
import src.exchange as exchange
import src.rebalance as rebalance

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("AUTHORIZED_CHAT_ID")

def send_alert(message):
    """Sends a quick push notification via Telegram using standard HTTP."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, json=payload)

def run():
    print("🏎️ Traveling in the slipstream... DRS enabled.")
    
    # 1. Fetch live settings and check the Kill Switch
    settings = database.get_settings()
    
    if settings.get('is_paused', 0) == 1:
        print("🛑 Bot is currently PAUSED via Telegram. Aborting run.")
        return
        
    # 2. Fetch live data
    balances = exchange.get_portfolio_balances()
    
    total_current_value = sum(balances.values())
    if total_current_value == 0:
        print("Wallet is empty or API failed. Aborting run.")
        return

    # 3. High-Water Mark Logic (The Trailing Stop-Loss)
    saved_hwm = database.get_high_water_mark()
    
    if total_current_value > saved_hwm:
        print(f"🌟 NEW ALL-TIME HIGH! Updating High-Water Mark from ${saved_hwm:,.2f} to ${total_current_value:,.2f}")
        database.update_high_water_mark(total_current_value)
        active_hwm = total_current_value
    else:
        print(f"📊 Current Value: ${total_current_value:,.2f} (High-Water Mark: ${saved_hwm:,.2f})")
        active_hwm = saved_hwm

    # 4. Calculate needed trades (Now driven 100% by DB settings)
    sells, buys = rebalance.calculate_rebalance(
        portfolio_balances=balances, 
        threshold_pct=settings['threshold_pct'], 
        mode=settings['mode'],
        floor_pct=settings['floor_pct'],
        baseline_value=active_hwm
    )
    
    trades_executed = 0
    
    # 5. Execute Sells (Skimming)
    for trade in sells:
        coin = trade['coin']
        amount = round(trade['amount_usd'], 2)
        if amount > 1.00: 
            print(f"📉 SELLING ${amount} of {coin}")
            res = exchange.execute_trade("SELL", coin, amount)
            if res:
                database.log_transaction("SELL", coin, amount)
                trades_executed += 1
                
    # 6. Execute Buys (Reallocating)
    for trade in buys:
        coin = trade['coin']
        amount = round(trade['amount_usd'], 2)
        if amount > 1.00:
            print(f"📈 BUYING ${amount} of {coin}")
            res = exchange.execute_trade("BUY", coin, amount)
            if res:
                database.log_transaction("BUY", coin, amount)
                trades_executed += 1

    # 7. Notify User if anything happened (and if not muted)
    if trades_executed > 0 and settings.get('is_muted', 0) == 0:
        send_alert(f"🏎️ Slipstream executed {trades_executed} overtakes (trades). Portfolio rebalanced. Check your account telemetry!")

if __name__ == "__main__":
    run()