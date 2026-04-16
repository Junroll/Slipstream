import src.rebalance as rebalance
import test.test_exchange as test_exchange

def run_simulation():
    print("🏎️ Starting Slipstream Simulator...")
    
    # We bypass the database and hardcode settings for the test
    settings = {
        'mode': 'waterfall', 
        'threshold': 0.05, 
        'floor': -0.20
    }

    # Loop through the tape
    total_ticks = len(test_exchange.MOCK_MARKET_TAPE)
    baseline_value = None # We track the high-water mark here
    
    for i in range(total_ticks):
        print(f"\n--- ⏱️ TICK {i} ---")
        
        # 1. Get Fake Balances and Current Total Value
        balances = test_exchange.get_portfolio_balances()
        total_current_value = sum(balances.values())
        
        # Set the baseline strictly on the very first tick (Tick 0)
        if baseline_value is None:
            baseline_value = total_current_value
            
        print("💰 Current Wallet Value:")
        for coin, val in balances.items():
            print(f"   - {coin}: ${val:,.2f}")
            
        # 2. Run the Real Math (Now protected by the Circuit Breaker!)
        sells, buys = rebalance.calculate_rebalance(
            portfolio_balances=balances, 
            threshold_pct=settings['threshold'], 
            mode=settings['mode'],
            floor_pct=settings['floor'],
            baseline_value=baseline_value
        )
        
        # 3. Execute Fake Sells
        for trade in sells:
            if trade['amount_usd'] > 1.00:
                print(f"📉 SCRIPT CALL: Sell ${trade['amount_usd']:,.2f} of {trade['coin']}")
                test_exchange.execute_trade("SELL", trade['coin'], trade['amount_usd'])
                
        # 4. Execute Fake Buys
        for trade in buys:
            if trade['amount_usd'] > 1.00:
                print(f"📈 SCRIPT CALL: Buy ${trade['amount_usd']:,.2f} of {trade['coin']}")
                test_exchange.execute_trade("BUY", trade['coin'], trade['amount_usd'])

        # 5. Move time forward
        test_exchange.advance_simulation()

if __name__ == "__main__":
    run_simulation()