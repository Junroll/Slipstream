import os
import requests
from dotenv import load_dotenv
from coinbase.rest import RESTClient
import uuid
import src.database as database

load_dotenv()

API_KEY = os.getenv("COINBASE_API_KEY")
API_SECRET = os.getenv("COINBASE_API_SECRET").replace('\\n', '\n')

client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)

def get_live_price(ticker):
    """Fetches the real-time USD price of a coin from the public API."""
    try:
        url = f"https://api.coinbase.com/api/v3/brokerage/market/products/{ticker}-USD/ticker"
        response = requests.get(url).json()
        return float(response['trades'][0]['price'])
    except Exception as e:
        print(f"⚠️ Error fetching price for {ticker}: {e}")
        return 0.0

def get_portfolio_balances():
    accounts = client.get_accounts()
    balances = {}

    # Dynamically fetch the blacklist from your database
    ignore_list = database.get_blacklist()

    for acc in accounts['accounts']:
        coin_amount = float(acc['available_balance']['value'])
        ticker = acc['currency']
        
        # Verify the coin is not on the blacklist!
        if coin_amount > 0 and ticker not in ignore_list:
            # Multiply the amount of coins by the live USD price
            live_price = get_live_price(ticker)
            usd_value = coin_amount * live_price
            
            # Only track it if it's actually worth something (ignores micro-dust)
            if usd_value > 10.00: 
                balances[ticker] = usd_value
                
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