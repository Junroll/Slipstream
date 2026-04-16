import os
from dotenv import load_dotenv
from coinbase.rest import RESTClient
import uuid

load_dotenv()

API_KEY = os.getenv("COINBASE_API_KEY")
API_SECRET = os.getenv("COINBASE_API_SECRET").replace('\\n', '\n')

client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)

def get_portfolio_balances():
    accounts = client.get_accounts()
    balances = {}

    # Add any coins here that you DO NOT want the bot to rebalance
    IGNORE_LIST = ['USD', 'USDC']

    for acc in accounts['accounts']:
        value = float(acc['available_balance']['value'])
        if value > 0:
            balances[acc['currency']] = value
    return balances

def execute_trade(action, coin, amount_usd):
    order_id = str(uuid.uuid4()) 
    product = f"{coin}-USD"
    
    try:
        if action == "SELL":
            order = client.market_order_sell(
                client_order_id=order_id, 
                product_id=product, 
                quote_size=str(amount_usd)
            )
        elif action == "BUY":
            order = client.market_order_buy(
                client_order_id=order_id, 
                product_id=product, 
                quote_size=str(amount_usd)
            )
        return order
    except Exception as e:
        print(f"❌ API Error during {action} for {coin}: {e}")
        return None