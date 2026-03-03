# 📈 Nifty Options Pro Bot

A 5-strategy adaptive Nifty options trading bot with a live Streamlit dashboard.

## Strategies
| # | Strategy | Regime |
|---|---|---|
| 1 | Bull Put Spread | Trending Up |
| 2 | Bear Call Spread | Trending Down |
| 3 | Iron Condor | Range Bound |
| 4 | Short Straddle | High IV Spike |
| 5 | 0DTE Theta Burn | Expiry Day |

## Features
- ✅ Breakeven trail at 50% target
- ✅ Trailing stop at 75% target
- ✅ Daily profit lock + loss limit
- ✅ Dynamic lot sizing by drawdown
- ✅ RSI + Bollinger Band + EMA + VWAP filters
- ✅ Re-entry up to 3x/day

## Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud
1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo → set `app.py` as main file
4. Deploy

## ⚠️ Disclaimer
Paper trade first. Options trading involves substantial risk of loss.
