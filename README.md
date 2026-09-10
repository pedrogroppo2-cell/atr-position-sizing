# atr-position-sizing

A small, dependency-light Python module for volatility-based position sizing -
stop loss, take profit, and position size calculated from an asset's real recent
volatility (ATR), instead of an arbitrary fixed percentage.

## The problem this solves

Most DIY risk management uses a fixed-distance stop: "always 2% below entry."
That distance has no relationship to how volatile the asset actually is right now.

- On a calm asset, a 2% stop is often wider than necessary - you risk more capital
  than the trade needs room to breathe.
- On a volatile asset, that same 2% can be too tight - price hits it on normal
  noise, stopping out a trade that was fundamentally correct.

ATR (Average True Range) measures an asset's real recent volatility. Sizing your
stop as a multiple of ATR makes the stop distance adapt automatically: wider in
volatile conditions, tighter in calm ones.

## Install

No dependencies beyond pandas. Just drop position_sizing.py into your project,
or:

pip install pandas

## Usage

See example.py for a runnable end-to-end example.

## What's in this repo

- calculate_atr() - rolling ATR from OHLC data
- calculate_stop_take() - stop loss / take profit as ATR multiples
- calculate_position_size() - position size so a stop-out costs exactly your
  target % of account
- build_trade_plan() - combines all three into one call

## What this does not do

This module handles risk sizing only. It doesn't generate entry signals, doesn't
model slippage/commissions, and doesn't validate a strategy's edge - pair it with
your own signal logic and your own backtesting process.

## Going further

This module is the risk-sizing core of a larger kit I built for myself, which also
includes an out-of-sample backtesting engine, a PRO tier with market-regime
detection and Monte Carlo validation, a runnable Jupyter notebook, and a PDF
walking through the reasoning behind every design choice.

If that's useful to you: Risk Management + Backtesting Kit -
https://groppo.gumroad.com/l/risk-management-kit

## License

MIT - see LICENSE. Use it, fork it, adapt it.
