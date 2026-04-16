def calculate_rebalance(portfolio_balances, threshold_pct, mode="waterfall", floor_pct=-0.20, baseline_value=None):
    if not portfolio_balances:
        return [], []

    total_portfolio_value = sum(portfolio_balances.values())
    
    # 🚨 THE CIRCUIT BREAKER (Lockdown Check)
    if baseline_value and baseline_value > 0:
        drop_pct = (total_portfolio_value - baseline_value) / baseline_value
        if drop_pct <= floor_pct:
            print(f"   🛑 LOCKDOWN TRIGGERED: Portfolio dropped by {drop_pct*100:.2f}%!")
            print("   🛑 HALTING ALL TRADES TO PREVENT CATCHING A FALLING KNIFE.")
            return [], [] # Return empty lists to cancel all trading

    target_weight = total_portfolio_value / len(portfolio_balances)
    
    sell_orders = []
    buy_orders = []
    cash_pool = 0.0
    
    # 1. THE SELL PHASE
    for coin, value in portfolio_balances.items():
        trigger_line = target_weight * (1 + threshold_pct)
        if value >= trigger_line:
            excess = value - target_weight
            sell_orders.append({"coin": coin, "amount_usd": excess})
            cash_pool += excess 
            
    # 2. THE BUY PHASE
    losers = {c: v for c, v in portfolio_balances.items() if v < target_weight}
    
    if mode == "waterfall":
        sorted_losers = sorted(losers.items(), key=lambda item: item[1])
        for coin, value in sorted_losers:
            if cash_pool <= 0:
                break 
            deficit = target_weight - value
            buy_amount = min(deficit, cash_pool) 
            buy_orders.append({"coin": coin, "amount_usd": buy_amount})
            cash_pool -= buy_amount

    elif mode == "proportional":
        total_deficit = sum((target_weight - v) for v in losers.values())
        for coin, value in losers.items():
            if cash_pool <= 0 or total_deficit <= 0:
                break
            deficit = target_weight - value
            weight = deficit / total_deficit 
            raw_allocation = cash_pool * weight
            buy_amount = min(raw_allocation, deficit)
            buy_orders.append({"coin": coin, "amount_usd": buy_amount})

    return sell_orders, buy_orders