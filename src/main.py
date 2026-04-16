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
    
    # 1. Fetch live data
    settings = database.get_settings()
    balances = exchange.get_portfolio_balances()
    
    # 2. Calculate needed trades
    sells, buys = rebalance.calculate_rebalance(
        balances, 
        settings['threshold'], 
        settings['mode']
    )
    
    trades_executed = 0
    
    # 3. Execute Sells (Skimming)
    for trade in sells:
        coin = trade['coin']
        amount = round(trade['amount_usd'], 2)
        if amount > 1.00: # Ignore micro-dust
            print(f"📉 SELLING ${amount} of {coin}")
            res = exchange.execute_trade("SELL", coin, amount)
            if res:
                database.log_transaction("SELL", coin, amount)
                trades_executed += 1
                
    # 4. Execute Buys (Reallocating)
    for trade in buys:
        coin = trade['coin']
        amount = round(trade['amount_usd'], 2)
        if amount > 1.00:
            print(f"📈 BUYING ${amount} of {coin}")
            res = exchange.execute_trade("BUY", coin, amount)
            if res:
                database.log_transaction("BUY", coin, amount)
                trades_executed += 1

    # 5. Notify User if anything happened
    if trades_executed > 0:
        send_alert(f"🏎️ Slipstream executed {trades_executed} overtakes (trades). Portfolio rebalanced. Check your account telemetry!")

if __name__ == "__main__":
    run()