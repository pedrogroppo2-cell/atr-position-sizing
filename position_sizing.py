"""
position_sizing.py
===================

ATR-based (Average True Range) risk management engine.

WHY ATR INSTEAD OF A FIXED PERCENTAGE
--------------------------------------
The most common mistake in DIY risk management is using a fixed-
distance stop loss (e.g. "always 2% below the entry price"). The
problem: that distance has no relationship to how volatile the asset
actually is at that moment.

- On a calm asset, a 2% stop can be wider than necessary: you risk
  more than the trade actually needs room to breathe.
- On a highly volatile asset, that same 2% can be too tight: price
  hits it on normal market noise, stopping you out of a trade that
  was fundamentally correct.

ATR measures the asset's real recent volatility (the average range it
moves, bar by bar, over a given period). By defining the stop as a
multiple of the ATR, the stop distance adapts automatically: it
widens in volatile markets and tightens in calm ones. This is what
separates a "real" risk management system from an arbitrary rule.

MODULE FLOW
-----------
1. calculate_atr()       -> measures the asset's recent volatility
2. calculate_stop_take() -> sets stop loss and take profit from ATR
3. calculate_position_size() -> calculates how many units to buy so
   that, if the stop is hit, the loss is exactly the account % you
   decided to risk (never more, never a surprise)
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class RiskParameters:
    """Result of the risk calculation for a single trade."""

    entry_price: float
    stop_loss: float
    take_profit: float
    atr_value: float
    position_size: float
    dollar_risk: float
    risk_reward_ratio: float


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculates the ATR (Average True Range) of a price series.

    Parameters
    ----------
    df : DataFrame with columns 'high', 'low', 'close' (one row per
        bar/candle, in chronological order).
    period : number of bars used for the rolling average (14 is the
        most widely used standard, similar to the classic RSI).

    Returns
    -------
    Series with the ATR for each row (the first `period` rows stay
    NaN because there isn't enough history yet).
    """
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    return true_range.rolling(window=period).mean()


def calculate_stop_take(
    entry_price: float,
    atr_value: float,
    direction: str = "long",
    stop_multiplier: float = 2.0,
    reward_ratio: float = 2.0,
) -> tuple[float, float]:
    """
    Sets stop loss and take profit as multiples of the ATR.

    Parameters
    ----------
    entry_price : trade entry price.
    atr_value : ATR value at the time of entry.
    direction : 'long' or 'short'.
    stop_multiplier : how many ATRs away the stop loss sits.
        2.0 is a reasonable starting point: wide enough not to get
        hit by noise, tight enough to limit the loss.
    reward_ratio : desired risk/reward ratio. 2.0 means the take
        profit is twice as far away as the stop loss.

    Returns
    -------
    (stop_loss, take_profit)
    """
    stop_distance = atr_value * stop_multiplier
    reward_distance = stop_distance * reward_ratio

    if direction == "long":
        stop_loss = entry_price - stop_distance
        take_profit = entry_price + reward_distance
    elif direction == "short":
        stop_loss = entry_price + stop_distance
        take_profit = entry_price - reward_distance
    else:
        raise ValueError("direction must be 'long' or 'short'")

    return stop_loss, take_profit


def calculate_position_size(
    account_size: float,
    risk_pct: float,
    entry_price: float,
    stop_loss: float,
) -> float:
    """
    Calculates how many units to buy/sell so that, if the stop is
    hit, the loss is exactly `risk_pct` of the account.

    This is the piece that makes risk *controlled* instead of
    *incidental*: no matter how far away the stop sits (volatile or
    calm asset), the dollar loss if the trade fails is always the
    same proportion of the account.

    Parameters
    ----------
    account_size : total account capital.
    risk_pct : percentage of the account to risk per trade, as a
        decimal (0.01 = 1%). The convention most serious traders use
        falls between 0.005 and 0.02 (0.5%-2%).
    entry_price : entry price.
    stop_loss : stop loss price (already calculated with ATR).

    Returns
    -------
    Number of units (shares, contracts, etc.) to trade.
    """
    dollar_risk = account_size * risk_pct
    risk_per_unit = abs(entry_price - stop_loss)

    if risk_per_unit == 0:
        raise ValueError("Stop loss cannot equal the entry price")

    return dollar_risk / risk_per_unit


def build_trade_plan(
    df: pd.DataFrame,
    account_size: float,
    risk_pct: float = 0.01,
    direction: str = "long",
    atr_period: int = 14,
    stop_multiplier: float = 2.0,
    reward_ratio: float = 2.0,
) -> RiskParameters:
    """
    Builds the complete risk plan for a trade, from a historical
    price series and available capital.

    This is the module's main function: it combines ATR, stop/take
    and position size into a single, ready-to-use result.

    Parameters
    ----------
    df : price history with columns 'high', 'low', 'close'. The
        entry is taken as the last available 'close'.
    account_size : total account capital.
    risk_pct : % of account to risk (default 1%).
    direction : 'long' or 'short'.
    atr_period : period used for the ATR calculation.
    stop_multiplier : ATR multiple for the stop loss.
    reward_ratio : risk/reward ratio for the take profit.

    Returns
    -------
    RiskParameters with all calculated values.
    """
    atr_series = calculate_atr(df, period=atr_period)
    atr_value = atr_series.iloc[-1]

    if pd.isna(atr_value):
        raise ValueError(
            f"Not enough history to calculate a {atr_period}-period "
            "ATR. Add more rows to the DataFrame."
        )

    entry_price = df["close"].iloc[-1]
    stop_loss, take_profit = calculate_stop_take(
        entry_price, atr_value, direction, stop_multiplier, reward_ratio
    )
    position_size = calculate_position_size(
        account_size, risk_pct, entry_price, stop_loss
    )
    dollar_risk = account_size * risk_pct

    return RiskParameters(
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        atr_value=atr_value,
        position_size=position_size,
        dollar_risk=dollar_risk,
        risk_reward_ratio=reward_ratio,
    )


if __name__ == "__main__":
    # Demo with sample data (replace with real data for the asset
    # you want to trade).
    import numpy as np

    np.random.seed(42)
    n_bars = 60
    close_prices = 100 + np.cumsum(np.random.randn(n_bars))
    demo_df = pd.DataFrame(
        {
            "close": close_prices,
            "high": close_prices + np.random.uniform(0.5, 2.0, n_bars),
            "low": close_prices - np.random.uniform(0.5, 2.0, n_bars),
        }
    )

    plan = build_trade_plan(
        df=demo_df,
        account_size=10_000,
        risk_pct=0.01,
        direction="long",
    )

    print("=== Risk plan ===")
    print(f"Entry price:        {plan.entry_price:.2f}")
    print(f"Current ATR:        {plan.atr_value:.2f}")
    print(f"Stop loss:          {plan.stop_loss:.2f}")
    print(f"Take profit:        {plan.take_profit:.2f}")
    print(f"Position size:      {plan.position_size:.2f} units")
    print(f"Dollar risk:        ${plan.dollar_risk:.2f}")
    print(f"Risk/reward ratio:  1:{plan.risk_reward_ratio:.1f}")
