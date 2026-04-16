import uuid
import requests

# --- SIMULATION SETTINGS ---
# Set to True to use your custom tape. Set to False to use LIVE Coinbase data!
# --- SIMULATION SETTINGS ---
SIMULATION_MODE = True  
CURRENT_TICK = 0

# The expanded tape: 3 coins, testing pumps, bleed, and a total market crash
MOCK_MARKET_TAPE = [
    {'BTC': 60000, 'ETH': 3000, 'SOL': 100}, # Tick 0: Baseline (Perfectly balanced at $900 each)
    {'BTC': 60000, 'ETH': 3000, 'SOL': 150}, # Tick 1: SOL pumps 50% (Should sell SOL, buy BTC/ETH)
    {'BTC': 58000, 'ETH': 2800, 'SOL': 140}, # Tick 2: Minor market bleed (Should hold, under 5% threshold)
    {'BTC': 30000, 'ETH': 1500, 'SOL': 50},  # Tick 3: 50% MARKET CRASH (Should trigger the -20% Floor Lockdown!)
]

# The fake 3-coin portfolio
paper_wallet = {
    'BTC': 0.015,  # $900 value at Tick 0
    'ETH': 0.30,   # $900 value at Tick 0
    'SOL': 9.00    # $900 value at Tick 0
}

def get_live_price(ticker):
    """Fetches the price from the simulation tape OR the live public internet."""
    global CURRENT_TICK
    
    if SIMULATION_MODE:
        # Option A: Read from the simulated tape
        tick_index = min(CURRENT_TICK, len(MOCK_MARKET_TAPE) - 1)
        return float(MOCK_MARKET_TAPE[tick_index][ticker])
    else:
        # Option B: Read from the real, unauthenticated Coinbase market
        url = f"https://api.coinbase.com/api/v3/brokerage/market/products/{ticker}-USD/ticker"
        response = requests.get(url).json()
        return float(response['trades'][0]['price'])

def get_portfolio_balances():
    """Calculates fake USD balances based on the tape or live market."""
    balances = {}
    for coin, amount in paper_wallet.items():
        live_price = get_live_price(coin)
        usd_value = amount * live_price
        balances[coin] = usd_value
    return balances

def execute_trade(action, coin, amount_usd):
    """Fakes the trade by updating our local paper_wallet."""
    live_price = get_live_price(coin)
    coin_amount = amount_usd / live_price
    
    if action == "SELL":
        paper_wallet[coin] -= coin_amount
        print(f"   📝 PAPER TRADE: Sold {coin_amount:.5f} {coin} at ${live_price:,.2f}")
    elif action == "BUY":
        paper_wallet[coin] += coin_amount
        print(f"   📝 PAPER TRADE: Bought {coin_amount:.5f} {coin} at ${live_price:,.2f}")
        
    return {"order_id": str(uuid.uuid4()), "status": "FILLED"}

def advance_simulation():
    """Moves the tape forward by one tick."""
    global CURRENT_TICK
    CURRENT_TICK += 1