import os
from dotenv import load_dotenv
from coinbase.rest import RESTClient

# Load the keys from your secure .env vault
load_dotenv()

API_KEY = os.getenv("COINBASE_API_KEY")
API_SECRET = os.getenv("COINBASE_API_SECRET").replace('\\n', '\n')

def ping_account():
    print("📡 Pinging Coinbase via Advanced Trade SDK...")
    try:
        # Initialize the official client with your credentials
        client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
        
        # Request account balances (100% Read-Only Action)
        accounts = client.get_accounts()
        
        print("✅ Authentication Successful! Here are your active balances:")
        for acc in accounts['accounts']:
            value = float(acc['available_balance']['value'])
            if value > 0:
                print(f"   - {acc['currency']}: {value}")
                
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    ping_account()