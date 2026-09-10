"""
example.py

Runnable example â generates synthetic price data and shows the full
position-sizing flow end to end. No external data needed.

Run: python example.py
"""

import numpy as np
import pandas as pd

from position_sizing import build_trade_plan

np.random.seed(7)
n_bars = 60
close_prices = 100 + np.cumsum(np.random.randn(n_bars))

df = pd.DataFrame({
    "close": close_prices,
    "high": close_prices + np.random.uniform(0.5, 2.0, n_bars),
    "low": close_prices - np.random.uniform(0.5, 2.0, n_bars),
})

# Compare sizing on the same setup at two different risk levels
for risk_pct in (0.005, 0.01, 0.02):
    plan = build_trade_plan(
        df=df,
        account_size=10_000,
        risk_pct=risk_pct,
        direction="long",
    )
    print(f"--- risk_pct={risk_pct:.1%} ---")
    print(f"  Stop loss:     {plan.stop_loss:.2f}")
    print(f"  Take profit:   {plan.take_profit:.2f}")
    print(f"  Position size: {plan.position_size:.2f} units")
    print(f"  Dollar risk:   ${plan.dollar_risk:.2f}")
    print()
