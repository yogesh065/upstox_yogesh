# ================================================================
# NIFTY OPTIONS PRO BOT — v3.0 FINAL CLEAN BUILD
#
# ROOT CAUSE OF JS CRASH FIXED:
#   Old code had time.sleep(1) + st.rerun() in a loop at the
#   bottom of the script. This hammers Streamlit's React websocket
#   until it corrupts → Wc@ / Xe@ JS error.
#
# FIX: Zero auto-refresh. Every action is button-triggered only.
#
# PAPER vs LIVE explained clearly:
#   PAPER = pure simulation, works 24/7, no real money, no API
#   LIVE  = real Upstox orders, market hours 9:15–3:30 only
# ================================================================

import streamlit as st
import pandas as pd
import numpy as np
import datetime
import math
import plotly.graph_objects as go

st.set_page_config(
    page_title="Nifty Options Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
html,body,.stApp{background:#0b0f1a !important;color:#dde4f0;}
[data-testid="stSidebar"]{background:#0d1424 !important;}
[data-testid="stSidebar"] *{color:#dde4f0 !important;}
.block-container{padding:1.2rem 2rem !important;}
label{font-family:'Space Mono',monospace !important;font-size:.71rem !important;
      text-transform:uppercase !important;letter-spacing:.6px !important;color:#6b7894 !important;}
.stButton>button{background:#00d4aa !important;color:#000 !important;border:none !important;
  border-radius:6px !important;font-family:'Space Mono',monospace !important;
  font-weight:700 !important;font-size:.76rem !important;}
.stButton>button:disabled{background:#1a2235 !important;color:#2d3f5e !important;}
.stTabs [data-baseweb="tab"]{font-family:'Space Mono',monospace !important;font-size:.72rem !important;}
.stTabs [aria-selected="true"]{color:#00d4aa !important;}
hr{border-color:#1e2d45 !important;}
div[data-testid="stNumberInput"] input,div[data-testid="stTextInput"] input{
  background:#0d1424 !important;border:1px solid #1e2d45 !important;color:#dde4f0 !important;}
div[data-testid="stSelectbox"]>div>div{background:#0d1424 !important;border-color:#1e2d45 !important;}
.card{background:#111827;border:1px solid #1e2d45;border-radius:8px;padding:14px 16px;margin-bottom:4px;}
.row{display:flex;justify-content:space-between;align-items:center;
     padding:5px 0;border-bottom:1px solid #0d1424;font-size:.78rem;}
.lbl{font-family:'Space Mono',monospace;font-size:.65rem;color:#6b7894;}
.val{font-family:'Space Mono',monospace;font-size:.75rem;font-weight:600;}
.logbox{background:#060b14;border:1px solid #1e2d45;border-radius:6px;padding:10px 14px;
        font-family:'Space Mono',monospace;font-size:.7rem;line-height:1.9;
        max-height:300px;overflow-y:auto;}
.banner{border-radius:8px;padding:12px 16px;margin-bottom:12px;font-size:.82rem;}
.banner-yellow{background:#2a1f00;border:1px solid #664d00;color:#f5c842;}
.banner-blue  {background:#001528;border:1px solid #003366;color:#4f9cf9;}
.banner-green {background:#001f18;border:1px solid #006644;color:#00d4aa;}
.banner-red   {background:#200010;border:1px solid #660033;color:#ff4d6a;}
.step{background:#0d1424;border-left:3px solid #00d4aa;border-radius:0 6px 6px 0;
      padding:12px 16px;margin-bottom:8px;}
.step-num{font-family:'Space Mono',monospace;font-size:.75rem;color:#00d4aa;font-weight:700;margin-bottom:3px;}
.step-body{font-size:.78rem;color:#b0bcd4;line-height:1.7;}
</style>
""", unsafe_allow_html=True)

# ================================================================
# STRATEGY / CONSTANTS
# ================================================================
STRAT_CLR = {
    "Bull Put Spread":"#00d4aa","Bear Call Spread":"#ff4d6a",
    "Iron Condor":"#a78bfa","Short Straddle":"#f5c842",
    "0DTE Theta Burn":"#4f9cf9","Scanning...":"#6b7894",
}
MARKET_OPEN  = datetime.time(9, 15)
ENTRY_CUTOFF = datetime.time(13, 30)
SQUARE_OFF   = datetime.time(15, 15)
MARKET_CLOSE = datetime.time(15, 30)

# ================================================================
# SESSION STATE
# ================================================================
_D = dict(
    paper_trade=True, access_token="", start_capital=200_000,
    lot_size=50, max_trades=3, profit_lock=6_000, loss_limit=4_000,
    target_pct=40, sl_mult=1.8, min_vix=13.5, max_vix=30.0,
    spread_min=100, spread_max=400, condor_wing=200,
    spot=24580.0, vix=16.8, iv_rank=52.0, rsi=57.5,
    atr=148.0, bb_w=1.25, vwap=24540.0,
    regime="Trending Up", strategy="Bull Put Spread",
    running=False, session_pnl=0.0, trade_count=0,
    capital=200_000, peak=200_000, trades=[], logs=[],
    pnl_hist=[0.0], time_hist=["Start"],
    open_trade=None, open_pnl=0.0,
    be_active=False, trail_active=False, tick_count=0,
)
for k, v in _D.items():
    if k not in st.session_state:
        st.session_state[k] = v
s = st.session_state

# ================================================================
# HELPERS
# ================================================================
def add_log(msg, level="i"):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    s.logs.insert(0, {"ts": ts, "msg": msg, "lv": level})
    if len(s.logs) > 100:
        s.logs = s.logs[:100]

def dd():
    return (s.peak - s.capital) / s.peak * 100 if s.peak > 0 else 0.0

def lots():
    d = dd()
    if d < 5:  return 3
    if d < 10: return 2
    if d < 15: return 1
    return 0

def is_market_open():
    if datetime.date.today().weekday() >= 5:
        return False
    t = datetime.datetime.now().time()
    return MARKET_OPEN <= t <= MARKET_CLOSE

def entry_window():
    if datetime.date.today().weekday() >= 5:
        return False
    t = datetime.datetime.now().time()
    return MARKET_OPEN <= t <= ENTRY_CUTOFF

# ================================================================
# PAPER SIMULATION FUNCTIONS
# ================================================================
def sim_market():
    s.spot   = max(20000, s.spot + float(np.random.normal(0, 12)))
    s.vix    = max(10, min(35, s.vix + float(np.random.normal(0, .15)) + (16.5 - s.vix) * .04))
    s.iv_rank= max(0, min(100, (s.vix - 11) / 24 * 100))
    s.rsi    = max(20, min(80, s.rsi + float(np.random.normal(0, 1.2)) + (50 - s.rsi) * .02))
    s.atr    = max(80, min(300, s.atr + float(np.random.normal(0, 2))))
    s.bb_w   = max(0.4, min(3.0, s.bb_w + float(np.random.normal(0, .04))))
    s.vwap   = s.vwap * 0.996 + s.spot * 0.004
    if s.vix >= 22 and s.iv_rank >= 60:
        s.regime = "High IV Spike";  s.strategy = "Short Straddle"
    elif s.rsi > 55 and s.spot > s.vwap and s.vix < s.max_vix:
        s.regime = "Trending Up";    s.strategy = "Bull Put Spread"
    elif s.rsi < 45 and s.spot < s.vwap and s.vix < s.max_vix:
        s.regime = "Trending Down";  s.strategy = "Bear Call Spread"
    elif 42 < s.rsi < 58 and s.bb_w < 1.5 and s.vix >= s.min_vix:
        s.regime = "Range Bound";    s.strategy = "Iron Condor"
    else:
        s.regime = "Unknown";        s.strategy = "Scanning..."

def sim_pnl():
    if not s.open_trade:
        return
    credit = s.open_trade["credit"]
    target = credit * s.target_pct / 100
    drift  = credit * 0.007
    noise  = float(np.random.normal(0, credit * 0.035))
    s.open_pnl = min(s.open_pnl + drift + noise, target * 1.01)

# ================================================================
# TRADE LOGIC
# ================================================================
def check_exits():
    if not s.open_trade:
        return False, ""
    credit      = s.open_trade["credit"]
    target      = credit * s.target_pct / 100
    hard_stop   = -credit * s.sl_mult
    trail_floor = credit * 0.60
    pnl         = s.open_pnl

    if not s.be_active and pnl >= target * 0.50:
        s.be_active = True
        add_log(f"BREAKEVEN LOCKED — stop moved to Rs0 (PnL Rs{pnl:+.0f})", "s")

    if not s.trail_active and pnl >= target * 0.75:
        s.trail_active = True
        add_log(f"TRAILING STOP armed — floor Rs{trail_floor:.0f}", "s")

    if pnl >= target:                                    return True, "Target Hit"
    if s.trail_active and pnl < trail_floor:             return True, "Trailing Stop"
    if s.be_active and not s.trail_active and pnl <= 0:  return True, "Breakeven Stop"
    if not s.be_active and pnl <= hard_stop:             return True, "Hard Stop"
    return False, ""

def book_exit(reason, pnl):
    t = s.open_trade
    s.session_pnl += pnl
    s.capital     += pnl
    s.peak         = max(s.peak, s.capital)
    s.trade_count += 1
    s.trades.append({
        "num": s.trade_count, "strategy": t["strategy"],
        "credit": t["credit"], "pnl": round(pnl, 2),
        "reason": reason, "lots": t.get("lots", 1),
        "time": datetime.datetime.now().strftime("%H:%M"),
    })
    s.pnl_hist.append(round(s.session_pnl, 2))
    s.time_hist.append(datetime.datetime.now().strftime("%H:%M:%S"))
    add_log(f"CLOSED #{s.trade_count} | {reason} | Rs{pnl:+,.0f}",
            "s" if pnl >= 0 else "e")
    s.open_trade = None; s.open_pnl = 0.0
    s.be_active  = False; s.trail_active = False

def try_enter():
    if s.open_trade:                        return False
    if s.trade_count >= s.max_trades:       return False
    if s.session_pnl >= s.profit_lock:      return False
    if s.session_pnl <= -s.loss_limit:      return False
    if lots() == 0:                         return False
    if s.strategy == "Scanning...":         return False

    n      = lots()
    credit = round(float(np.random.uniform(2500, 6500))) * n
    s.open_trade   = {"strategy": s.strategy, "credit": credit, "lots": n,
                      "entry_spot": s.spot,
                      "entry_time": datetime.datetime.now().strftime("%H:%M:%S")}
    s.open_pnl     = 0.0
    s.be_active    = False
    s.trail_active = False
    add_log(f"ENTRY: {s.strategy} | Credit Rs{credit:,} | {n} lots", "s")
    add_log(f"  Target Rs{credit*s.target_pct//100:,} | Stop Rs{int(-credit*s.sl_mult):,}", "i")
    return True

# ================================================================
# LIVE UPSTOX (only when paper_trade = False)
# ================================================================
def connect_upstox():
    try:
        from upstox_connector import make_client, get_spot, get_vix
        apis = make_client(s.access_token)
        sp   = get_spot(apis)
        vx   = get_vix(apis)
        s["apis"] = apis
        s.spot = sp; s.vix = vx
        add_log(f"Connected Upstox | Spot Rs{sp:,.0f} | VIX {vx:.1f}", "s")
        return True
    except Exception as e:
        add_log(f"Upstox connect error: {e}", "e")
        return False

def fetch_live():
    apis = s.get("apis")
    if not apis: return
    try:
        from upstox_connector import get_spot, get_vix, get_live_pnl
        s.spot    = get_spot(apis)
        s.vix     = get_vix(apis)
        s.iv_rank = max(0, min(100, (s.vix - 11) / 24 * 100))
        if s.open_trade:
            s.open_pnl = get_live_pnl(apis)
    except Exception as e:
        add_log(f"Live data error: {e}", "e")

def place_live_order():
    apis = s.get("apis")
    if not apis: return False
    try:
        from upstox_connector import (
            get_nearest_expiry, is_expiry_day,
            enter_bull_put_spread, enter_bear_call_spread,
            enter_iron_condor, enter_short_straddle, enter_zero_dte,
        )
        exp   = get_nearest_expiry(apis)
        n     = lots()
        strat = s.strategy
        if is_expiry_day(exp) and datetime.datetime.now().hour >= 14:
            strat = "0DTE Theta Burn"

        trade = None
        if strat == "Bull Put Spread":
            trade = enter_bull_put_spread(apis, n, s.lot_size, exp, s.spread_min, s.spread_max, s.atr)
        elif strat == "Bear Call Spread":
            trade = enter_bear_call_spread(apis, n, s.lot_size, exp, s.spread_min, s.spread_max, s.atr)
        elif strat == "Iron Condor":
            trade = enter_iron_condor(apis, n, s.lot_size, exp, s.condor_wing)
        elif strat == "Short Straddle":
            trade = enter_short_straddle(apis, n, s.lot_size, exp, s.atr)
        elif strat == "0DTE Theta Burn":
            trade = enter_zero_dte(apis, n, s.lot_size, exp)

        if trade:
            s.open_trade   = {**trade, "entry_time": datetime.datetime.now().strftime("%H:%M:%S")}
            s.open_pnl     = 0.0
            s.be_active    = False
            s.trail_active = False
            add_log(f"[LIVE] ENTRY: {trade['strategy']} | Credit Rs{trade['credit']:,}", "s")
            return True
    except Exception as e:
        add_log(f"Order error: {e}", "e")
    return False

def close_live():
    apis = s.get("apis")
    if not apis: return
    try:
        from upstox_connector import close_all_positions
        close_all_positions(apis)
    except Exception as e:
        add_log(f"Close error: {e}", "e")

# ================================================================
# SIDEBAR
# ================================================================
with st.sidebar:
    st.markdown("### ⚙ Config")
    st.markdown("---")
    s.access_token = st.text_input(
        "Upstox Access Token", value=s.access_token, type="password",
        placeholder="From get_token.py — needed for LIVE only",
    )
    s.paper_trade = st.toggle("📄 Paper Trade Mode", value=s.paper_trade)

    if not s.paper_trade:
        if s.access_token:
            st.success("Token entered ✅")
        else:
            st.error("⚠ Add token for live mode")

    st.markdown("---")
    s.start_capital = st.number_input("Start Capital ₹", value=s.start_capital, step=10_000)
    s.profit_lock   = st.number_input("Daily Profit Lock ₹", value=s.profit_lock, step=500)
    s.loss_limit    = st.number_input("Daily Loss Limit ₹", value=s.loss_limit, step=500)
    s.max_trades    = st.slider("Max Trades/Day", 1, 5, s.max_trades)
    s.lot_size      = st.number_input("Lot Size", value=s.lot_size, step=25, min_value=25)
    st.markdown("---")
    s.target_pct = st.slider("Target % of Credit", 20, 70, s.target_pct)
    s.sl_mult    = st.slider("Stop Loss ×", 1.0, 3.0, s.sl_mult, 0.1)
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1: s.min_vix = st.number_input("Min VIX", value=s.min_vix, step=0.5)
    with c2: s.max_vix = st.number_input("Max VIX", value=s.max_vix, step=0.5)
    c1, c2 = st.columns(2)
    with c1: s.spread_min = st.number_input("Spread Min", value=s.spread_min, step=50)
    with c2: s.spread_max = st.number_input("Spread Max", value=s.spread_max, step=50)
    s.condor_wing = st.number_input("Condor Wing", value=s.condor_wing, step=50)

# ================================================================
# STATUS BAR
# ================================================================
now       = datetime.datetime.now()
mkt_open  = is_market_open()
mode_clr  = "#f5c842" if s.paper_trade else "#ff4d6a"
mode_lbl  = "PAPER SIMULATION" if s.paper_trade else "LIVE TRADING"
run_clr   = "#00d4aa" if s.running else "#6b7894"
run_lbl   = "● RUNNING" if s.running else "○ STOPPED"
mkt_clr   = "#00d4aa" if mkt_open else "#6b7894"
mkt_lbl   = "MARKET OPEN" if mkt_open else "MARKET CLOSED"

st.markdown(f"""
<div style="background:#111827;border:1px solid #1e2d45;border-radius:8px;
     padding:14px 20px;margin-bottom:14px;
     display:flex;justify-content:space-between;align-items:center;">
  <div style="font-family:'Space Mono',monospace;font-size:1.1rem;
       font-weight:700;color:#00d4aa;">
    ◈ NIFTY OPTIONS PRO BOT
    <span style="font-size:.68rem;color:#4d5f7a;font-weight:400;">
      &nbsp;5-Strategy Engine
    </span>
  </div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;">
    <span style="background:#1a1a00;border:1px solid {mode_clr}55;color:{mode_clr};
          font-family:'Space Mono',monospace;font-size:.68rem;font-weight:700;
          padding:4px 10px;border-radius:4px;">{mode_lbl}</span>
    <span style="background:#0d1424;border:1px solid {run_clr}55;color:{run_clr};
          font-family:'Space Mono',monospace;font-size:.68rem;font-weight:700;
          padding:4px 10px;border-radius:4px;">{run_lbl}</span>
    <span style="background:#0d1424;border:1px solid {mkt_clr}55;color:{mkt_clr};
          font-family:'Space Mono',monospace;font-size:.68rem;font-weight:700;
          padding:4px 10px;border-radius:4px;">{mkt_lbl}</span>
    <span style="background:#0d1424;border:1px solid #1e2d45;color:#4d5f7a;
          font-family:'Space Mono',monospace;font-size:.68rem;
          padding:4px 10px;border-radius:4px;">{now.strftime('%d %b  %H:%M:%S')}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Context banners ──────────────────────────────────────────
if s.paper_trade:
    st.markdown("""
    <div class="banner banner-blue">
      📄 <strong>PAPER MODE — SIMULATION ONLY</strong><br>
      No real orders. No API needed. Works 24/7 even when market is closed.
      Market data is <em>randomly simulated</em> each time you press a button.
      Use this to learn the strategy and test settings safely.
    </div>""", unsafe_allow_html=True)
elif not mkt_open:
    st.markdown("""
    <div class="banner banner-yellow">
      ⚠ <strong>Market is CLOSED</strong> — Live orders will not be placed.<br>
      NSE F&amp;O hours: Mon–Fri, 9:15 AM – 3:30 PM IST.
      Switch to Paper Mode to simulate trades any time.
    </div>""", unsafe_allow_html=True)
elif not s.access_token:
    st.markdown("""
    <div class="banner banner-red">
      🔑 <strong>No access token</strong> — Add your Upstox token in the sidebar
      before starting live trading.
    </div>""", unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="banner banner-green">
      🟢 <strong>LIVE MODE — Market Open</strong> — Real orders will be placed on Upstox.
      Monitor positions in your Upstox app after each entry.
    </div>""", unsafe_allow_html=True)

# ================================================================
# CONTROL BUTTONS
# ================================================================
c1, c2, c3, c4, c5 = st.columns([1, 1, 1.3, 1.3, 1.3])

with c1:
    can_start = not s.running and (s.paper_trade or bool(s.access_token))
    if st.button("▶  START", disabled=not can_start, use_container_width=True):
        s.running      = True
        s.session_pnl  = 0.0
        s.trade_count  = 0
        s.capital      = s.start_capital
        s.peak         = s.start_capital
        s.trades       = []
        s.pnl_hist     = [0.0]
        s.time_hist    = [now.strftime("%H:%M:%S")]
        s.open_trade   = None
        s.open_pnl     = 0.0
        s.be_active    = False
        s.trail_active = False
        s.tick_count   = 0
        s.logs         = []
        add_log(f"Session started | Rs{s.start_capital:,} | {'PAPER' if s.paper_trade else 'LIVE'}", "s")
        if not s.paper_trade:
            ok = connect_upstox()
            if not ok:
                s.running = False
        st.rerun()

with c2:
    if st.button("■  STOP", disabled=not s.running, use_container_width=True):
        if s.open_trade:
            if not s.paper_trade:
                close_live()
            book_exit("Manual Stop", s.open_pnl)
        s.running = False
        add_log("Bot stopped", "w")
        st.rerun()

with c3:
    btn3_help = (
        "Simulate 1 market scan: randomise spot/VIX/RSI/regime, try to enter trade"
        if s.paper_trade else
        "Fetch live market data and try to enter trade (market hours only)"
    )
    btn3_lbl = "⟳  SCAN + ENTER" if not s.open_trade else "⟳  REFRESH DATA"
    if st.button(btn3_lbl, disabled=not s.running,
                 use_container_width=True, help=btn3_help):
        s.tick_count += 1
        if s.paper_trade:
            sim_market()
        else:
            fetch_live()

        if not s.open_trade:
            entered = (try_enter() if s.paper_trade else
                       (place_live_order() if (entry_window() and mkt_open) else False))
            if not entered:
                reasons = []
                if s.trade_count >= s.max_trades:     reasons.append("max trades reached")
                if s.session_pnl >= s.profit_lock:    reasons.append("profit locked")
                if s.session_pnl <= -s.loss_limit:    reasons.append("loss limit hit")
                if lots() == 0:                        reasons.append("drawdown >15%")
                if s.strategy == "Scanning...":        reasons.append("no clear regime")
                if not entry_window() and not s.paper_trade:
                    reasons.append("outside entry window 9:15–1:30")
                add_log(f"Scan #{s.tick_count} | {s.regime} | "
                        f"Spot Rs{s.spot:,.0f} | VIX {s.vix:.1f} | "
                        f"No entry: {', '.join(reasons) or 'conditions not met'}", "i")
        else:
            should_exit, reason = check_exits()
            if should_exit:
                if not s.paper_trade:
                    close_live()
                book_exit(reason, s.open_pnl)
                add_log("Ready for next entry — press Scan again", "i")
            else:
                credit = s.open_trade["credit"]
                target = credit * s.target_pct / 100
                add_log(f"Scan #{s.tick_count} | PnL Rs{s.open_pnl:+,.0f} / Rs{target:,.0f} | "
                        f"BE:{'on' if s.be_active else 'off'} Trail:{'on' if s.trail_active else 'off'}", "i")
        st.rerun()

with c4:
    if st.button("📊  SIM PNL TICK",
                 disabled=not s.running or not s.open_trade or not s.paper_trade,
                 use_container_width=True,
                 help="Paper only: simulate one PnL movement on open trade"):
        sim_pnl()
        should_exit, reason = check_exits()
        if should_exit:
            book_exit(reason, s.open_pnl)
        else:
            credit = s.open_trade["credit"]
            target = credit * s.target_pct / 100
            add_log(f"PnL Rs{s.open_pnl:+,.0f} / target Rs{target:,.0f} | "
                    f"BE:{'LOCKED' if s.be_active else 'waiting'} "
                    f"Trail:{'ACTIVE' if s.trail_active else 'waiting'}", "i")
        st.rerun()

with c5:
    if st.button("✕  FORCE CLOSE",
                 disabled=not s.open_trade,
                 use_container_width=True,
                 help="Close open trade immediately"):
        if not s.paper_trade:
            close_live()
        book_exit("Manual Close", s.open_pnl)
        st.rerun()

st.markdown("---")

# ================================================================
# KPI ROW
# ================================================================
dd_val   = dd()
pnl_clr  = "#00d4aa" if s.session_pnl >= 0 else "#ff4d6a"
dd_clr   = "#ff4d6a" if dd_val > 10 else "#f5c842" if dd_val > 5 else "#6b7894"
ls       = lots()
ls_clr   = "#00d4aa" if ls == 3 else "#f5c842" if ls >= 1 else "#ff4d6a"
op_clr   = "#00d4aa" if s.open_pnl >= 0 else "#ff4d6a"

if s.open_trade:
    credit = s.open_trade["credit"]
    target = credit * s.target_pct / 100
    op_sub = f"{max(0, min(100, s.open_pnl/target*100)) if target else 0:.0f}% to target"
else:
    op_sub = "No active trade"

k1, k2, k3, k4, k5 = st.columns(5)
for col, lbl, val, sub, clr in [
    (k1, "Session P&L",    f"₹{s.session_pnl:+,.0f}",  f"Lock ₹{s.profit_lock:,} / -₹{s.loss_limit:,}", pnl_clr),
    (k2, "Capital",        f"₹{s.capital:,.0f}",         f"Peak ₹{s.peak:,.0f}",                          "#4f9cf9"),
    (k3, "Drawdown",       f"{dd_val:.2f}%",              f"Lot scale: {ls} lots",                         dd_clr),
    (k4, "Trades",         f"{s.trade_count}/{s.max_trades}", "Open: " + ("YES" if s.open_trade else "NO"), "#a78bfa"),
    (k5, "Live Trade PnL", f"₹{s.open_pnl:+,.0f}" if s.open_trade else "—", op_sub,                     op_clr),
]:
    with col:
        st.markdown(f"""
        <div class="card" style="border-bottom:2px solid {clr}55;">
          <div class="lbl">{lbl}</div>
          <div style="font-family:'Space Mono',monospace;font-size:1.25rem;
               font-weight:700;color:{clr};margin:2px 0;">{val}</div>
          <div style="font-size:.65rem;color:#4d5f7a;">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ================================================================
# TABS
# ================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📡 Live Monitor",
    "📋 Trade Log",
    "📈 P&L Chart",
    "📟 Console",
    "📖 Setup Guide",
])

# ────────────────────────────────────────────────────────────
# TAB 1: LIVE MONITOR
# ────────────────────────────────────────────────────────────
with tab1:
    ca, cb, cc = st.columns([1, 1.4, 1])

    with ca:
        st.markdown("**Market Data**")
        vix_c = "#f5c842" if s.vix > 22 else "#ff4d6a" if s.vix > 27 else "#00d4aa"
        rsi_c = "#00d4aa" if s.rsi > 55 else "#ff4d6a" if s.rsi < 45 else "#6b7894"
        vwap_c= "#00d4aa" if s.spot > s.vwap else "#ff4d6a"
        sc    = STRAT_CLR.get(s.strategy, "#6b7894")
        rows  = [
            ("NIFTY SPOT",  f"₹{s.spot:,.2f}",    "#4f9cf9"),
            ("INDIA VIX",   f"{s.vix:.2f}",         vix_c),
            ("IV RANK",     f"{s.iv_rank:.0f}%",    vix_c),
            ("RSI (14)",    f"{s.rsi:.1f}",          rsi_c),
            ("ATR (14)",    f"{s.atr:.1f} pts",     "#dde4f0"),
            ("BB WIDTH",    f"{s.bb_w:.2f}%",       "#dde4f0"),
            ("VWAP",        f"₹{s.vwap:,.1f}",      vwap_c),
            ("VS VWAP",     "ABOVE ↑" if s.spot>s.vwap else "BELOW ↓", vwap_c),
            ("REGIME",      s.regime,               sc),
            ("STRATEGY",    s.strategy,             sc),
        ]
        html = '<div class="card">'
        for lbl, val, color in rows:
            html += (f'<div class="row">'
                     f'<span class="lbl">{lbl}</span>'
                     f'<span class="val" style="color:{color};">{val}</span>'
                     f'</div>')
        if s.paper_trade:
            html += ('<div style="margin-top:8px;font-size:.65rem;color:#2d3f5e;'
                     'font-family:\'Space Mono\',monospace;border-top:1px solid #1a2235;'
                     'padding-top:6px;">⚠ Simulated data — not real market prices</div>')
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    with cb:
        st.markdown("**Active Trade**")
        if s.open_trade:
            t      = s.open_trade
            credit = t["credit"]
            target = credit * s.target_pct / 100
            sl_val = -credit * s.sl_mult
            pct    = max(0, min(100, s.open_pnl/target*100)) if target else 0
            pc     = "#00d4aa" if s.open_pnl >= 0 else "#ff4d6a"
            sc2    = STRAT_CLR.get(t["strategy"], "#6b7894")
            be_tag = (f'<span style="background:#003d2e;color:#00d4aa;padding:2px 8px;'
                      f'border-radius:4px;font-family:\'Space Mono\',monospace;'
                      f'font-size:.62rem;border:1px solid #006644;margin-left:6px;">'
                      f'BE LOCKED</span>' if s.be_active else "")
            tr_tag = (f'<span style="background:#3d2e00;color:#f5c842;padding:2px 8px;'
                      f'border-radius:4px;font-family:\'Space Mono\',monospace;'
                      f'font-size:.62rem;border:1px solid #664d00;margin-left:6px;">'
                      f'TRAILING</span>' if s.trail_active else "")
            st.markdown(f"""
            <div class="card">
              <div style="margin-bottom:12px;">
                <span style="font-family:'Space Mono',monospace;font-size:.85rem;
                     font-weight:700;color:{sc2};">{t['strategy']}</span>
                {be_tag}{tr_tag}
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:10px;">
                <div style="background:#0d1424;border-radius:6px;padding:10px;text-align:center;">
                  <div class="lbl">CREDIT</div>
                  <div style="font-family:'Space Mono',monospace;color:#4f9cf9;font-weight:700;">₹{credit:,.0f}</div>
                </div>
                <div style="background:#0d1424;border-radius:6px;padding:10px;text-align:center;">
                  <div class="lbl">LIVE P&L</div>
                  <div style="font-family:'Space Mono',monospace;color:{pc};font-weight:700;">₹{s.open_pnl:+,.0f}</div>
                </div>
                <div style="background:#0d1424;border-radius:6px;padding:10px;text-align:center;">
                  <div class="lbl">LOTS</div>
                  <div style="font-family:'Space Mono',monospace;font-weight:700;">{t.get('lots',1)}</div>
                </div>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;">
                <div style="background:#0d1424;border-radius:6px;padding:9px 12px;">
                  <div class="lbl">TARGET ({s.target_pct}%)</div>
                  <div style="font-family:'Space Mono',monospace;color:#00d4aa;font-weight:700;">₹{target:,.0f}</div>
                </div>
                <div style="background:#0d1424;border-radius:6px;padding:9px 12px;">
                  <div class="lbl">HARD STOP</div>
                  <div style="font-family:'Space Mono',monospace;color:#ff4d6a;font-weight:700;">₹{sl_val:,.0f}</div>
                </div>
              </div>
              <div style="font-size:.6rem;color:#4d5f7a;font-family:'Space Mono',monospace;
                   display:flex;justify-content:space-between;margin-bottom:3px;">
                <span>0%</span>
                <span style="color:{'#4f9cf9' if pct>=25 else '#2d3f5e'}">25% Partial</span>
                <span style="color:{'#00d4aa' if s.be_active else '#2d3f5e'}">50% BE</span>
                <span style="color:{'#f5c842' if s.trail_active else '#2d3f5e'}">75% Trail</span>
                <span>100%</span>
              </div>
              <div style="background:#060b14;border-radius:4px;height:10px;overflow:hidden;border:1px solid #1e2d45;">
                <div style="height:100%;width:{pct:.1f}%;background:linear-gradient(90deg,#003d2e,{pc});"></div>
              </div>
              <div style="margin-top:6px;font-family:'Space Mono',monospace;font-size:.68rem;color:{pc};">
                {pct:.1f}% of target &nbsp;|&nbsp; Entered: {t.get('entry_time','')}
              </div>
            </div>""", unsafe_allow_html=True)
        else:
            next_action = ""
            if s.running:
                if s.paper_trade:
                    next_action = "Press ⟳ SCAN + ENTER to simulate market and enter trade"
                elif not mkt_open:
                    next_action = "Waiting for market to open (9:15 AM)"
                elif not entry_window():
                    next_action = "Entry window closed (past 1:30 PM)"
                else:
                    next_action = "Press ⟳ SCAN + ENTER to scan live market"
            else:
                next_action = "Press ▶ START to begin"

            st.markdown(f"""
            <div class="card" style="text-align:center;padding:50px 20px;">
              <div style="font-size:2rem;color:#1e2d45;margin-bottom:10px;">◎</div>
              <div style="font-family:'Space Mono',monospace;font-size:.78rem;
                   color:#4d5f7a;letter-spacing:1px;">NO ACTIVE TRADE</div>
              <div style="font-size:.72rem;color:#2d3f5e;margin-top:8px;line-height:1.6;">
                {next_action}
              </div>
            </div>""", unsafe_allow_html=True)

    with cc:
        st.markdown("**Session Risk**")
        pp = min(100, s.session_pnl/s.profit_lock*100) if s.session_pnl > 0 else 0
        lp = min(100, -s.session_pnl/s.loss_limit*100) if s.session_pnl < 0 else 0
        html2 = '<div class="card">'
        html2 += f"""
        <div style="margin-bottom:12px;">
          <div class="row"><span class="lbl">PROFIT</span>
            <span class="val" style="color:#00d4aa;">₹{max(0,s.session_pnl):,.0f}</span></div>
          <div style="background:#0d1424;border-radius:3px;height:6px;margin-top:4px;">
            <div style="height:100%;width:{pp:.0f}%;background:linear-gradient(90deg,#003d2e,#00d4aa);border-radius:3px;"></div>
          </div>
          <div style="font-size:.58rem;color:#2d3f5e;text-align:right;">target ₹{s.profit_lock:,}</div>
        </div>
        <div style="margin-bottom:12px;">
          <div class="row"><span class="lbl">LOSS</span>
            <span class="val" style="color:#ff4d6a;">₹{min(0,s.session_pnl):,.0f}</span></div>
          <div style="background:#0d1424;border-radius:3px;height:6px;margin-top:4px;">
            <div style="height:100%;width:{lp:.0f}%;background:linear-gradient(90deg,#3d001a,#ff4d6a);border-radius:3px;"></div>
          </div>
          <div style="font-size:.58rem;color:#2d3f5e;text-align:right;">limit -₹{s.loss_limit:,}</div>
        </div>"""
        for lbl, val, clr in [
            ("LOT SCALE",   f"{ls} lots",                   ls_clr),
            ("DRAWDOWN",    f"{dd_val:.2f}%",               dd_clr),
            ("BREAKEVEN",   "LOCKED ✅" if s.be_active else "waiting", "#00d4aa" if s.be_active else "#6b7894"),
            ("TRAILING",    "ACTIVE 🚀" if s.trail_active else "waiting", "#f5c842" if s.trail_active else "#6b7894"),
            ("TICKS",       str(s.tick_count),              "#6b7894"),
            ("DATA SOURCE", "SIMULATED" if s.paper_trade else "LIVE API", "#f5c842" if s.paper_trade else "#00d4aa"),
        ]:
            html2 += (f'<div class="row"><span class="lbl">{lbl}</span>'
                      f'<span class="val" style="color:{clr};">{val}</span></div>')
        html2 += '</div>'
        st.markdown(html2, unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────
# TAB 2: TRADE LOG
# ────────────────────────────────────────────────────────────
with tab2:
    if not s.trades:
        st.info("No trades yet. Start the bot and press SCAN + ENTER.")
    else:
        wins = sum(1 for t in s.trades if t["pnl"] > 0)
        loss = len(s.trades) - wins
        totl = sum(t["pnl"] for t in s.trades)
        wr   = wins / len(s.trades) * 100 if s.trades else 0
        aw   = sum(t["pnl"] for t in s.trades if t["pnl"] > 0) / wins  if wins else 0
        al   = sum(t["pnl"] for t in s.trades if t["pnl"] < 0) / loss  if loss else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Win Rate",  f"{wr:.0f}%",       f"{wins}W / {loss}L")
        m2.metric("Avg Win",   f"₹{aw:,.0f}",       "per trade")
        m3.metric("Avg Loss",  f"₹{al:,.0f}",       "per trade")
        m4.metric("Total P&L", f"₹{totl:+,.0f}",   "this session")
        st.markdown("---")

        df = pd.DataFrame(s.trades)[["num","strategy","credit","pnl","reason","time","lots"]]
        df.columns = ["#","Strategy","Credit ₹","P&L ₹","Exit","Time","Lots"]
        st.dataframe(
            df.sort_values("#", ascending=False).reset_index(drop=True),
            use_container_width=True, hide_index=True,
        )

# ────────────────────────────────────────────────────────────
# TAB 3: P&L CHART
# ────────────────────────────────────────────────────────────
with tab3:
    if len(s.pnl_hist) > 1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=s.time_hist, y=s.pnl_hist, mode="lines+markers",
            line=dict(color="#00d4aa", width=2.5),
            fill="tozeroy", fillcolor="rgba(0,212,170,0.06)",
            marker=dict(size=5, color=["#00d4aa" if v>=0 else "#ff4d6a" for v in s.pnl_hist]),
            hovertemplate="<b>%{x}</b><br>₹%{y:+,.0f}<extra></extra>",
        ))
        fig.add_hline(y=s.profit_lock, line=dict(color="#f5c842",width=1,dash="dot"),
                      annotation_text=f"Lock ₹{s.profit_lock:,}", annotation_font_color="#f5c842", annotation_font_size=10)
        fig.add_hline(y=-s.loss_limit, line=dict(color="#ff4d6a",width=1,dash="dot"),
                      annotation_text=f"Limit -₹{s.loss_limit:,}", annotation_font_color="#ff4d6a", annotation_font_size=10)
        fig.add_hline(y=0, line=dict(color="#1e2d45",width=1))
        fig.update_layout(
            paper_bgcolor="#0b0f1a", plot_bgcolor="#0b0f1a",
            font_family="Space Mono", font_color="#6b7894",
            height=420, margin=dict(l=60,r=40,t=20,b=40),
            xaxis=dict(showgrid=False,zeroline=False,tickfont_size=9),
            yaxis=dict(showgrid=True,gridcolor="#111827",tickprefix="₹",tickfont_size=9),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Chart appears after first trade closes.")

# ────────────────────────────────────────────────────────────
# TAB 4: CONSOLE
# ────────────────────────────────────────────────────────────
with tab4:
    ca, cb = st.columns([3, 2])
    with ca:
        st.markdown("**Bot Console**")
        clr_map = {"i":"#4f9cf9","s":"#00d4aa","w":"#f5c842","e":"#ff4d6a"}
        if s.logs:
            rows_html = "".join(
                f'<div><span style="color:#2d3f5e">[{e["ts"]}]</span> '
                f'<span style="color:{clr_map.get(e["lv"],"#4f9cf9")}">{e["msg"]}</span></div>'
                for e in s.logs[:60]
            )
            st.markdown(f'<div class="logbox">{rows_html}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="logbox"><span style="color:#2d3f5e">No logs. Press START.</span></div>',
                        unsafe_allow_html=True)
        if st.button("🗑 Clear"):
            s.logs = []; st.rerun()

    with cb:
        st.markdown("**Strategy Guide**")
        for name, desc in [
            ("Bull Put Spread",  "Sell OTM put + buy lower put. Win if Nifty stays above short strike. Uptrend."),
            ("Bear Call Spread", "Sell OTM call + buy higher call. Win below strike. Downtrend."),
            ("Iron Condor",      "4 legs both sides. Win in range. Best when BB tight + VIX>14."),
            ("Short Straddle",   "Sell ATM call+put (hedged). Win when IV collapses. VIX≥22."),
            ("0DTE Theta Burn",  "Iron fly on expiry day. Options decay to zero in hours."),
        ]:
            c = STRAT_CLR.get(name,"#6b7894")
            active = name == s.strategy
            st.markdown(
                f'<div style="border-left:3px solid {c};padding:7px 12px;margin-bottom:7px;'
                f'background:{"rgba(0,0,0,0.3)" if active else "transparent"};border-radius:0 6px 6px 0;">'
                f'<div style="font-family:\'Space Mono\',monospace;font-size:.7rem;font-weight:700;'
                f'color:{c};margin-bottom:3px;">{"▶ " if active else ""}{name}</div>'
                f'<div style="font-size:.7rem;color:#4d5f7a;line-height:1.5;">{desc}</div></div>',
                unsafe_allow_html=True
            )

# ────────────────────────────────────────────────────────────
# TAB 5: SETUP GUIDE
# ────────────────────────────────────────────────────────────
with tab5:
    ca, cb = st.columns(2)

    with ca:
        st.markdown("### 📄 Paper Mode — Simulation")
        st.markdown("""
        <div class="banner banner-blue">
        Paper mode is 100% simulated. Market hours don't matter.
        All prices, VIX, RSI, PnL are randomly generated each button press.
        Use it to learn the bot behaviour before going live.
        </div>""", unsafe_allow_html=True)

        for i, (title, body) in enumerate([
            ("Turn ON Paper Mode", "Sidebar → 'Paper Trade Mode' toggle ON (default)."),
            ("Press ▶ START", "Resets session. Capital/trades/PnL go to zero."),
            ("Press ⟳ SCAN + ENTER",
             "Each press: simulates market tick (randomises Spot/VIX/RSI), "
             "detects regime, enters trade if conditions match. "
             "Repeat until a trade is entered."),
            ("Press 📊 SIM PNL TICK (repeat)",
             "Each press moves the open trade PnL by one step (theta decay simulation). "
             "Breakeven locks at 50% target. Trail activates at 75%. "
             "Trade auto-closes when target/stop/trail is hit. "
             "Keep pressing until trade closes."),
            ("Repeat from Step 3",
             "After close, press SCAN again for next trade. "
             "Up to Max Trades/Day. Watch capital grow."),
            ("Review results",
             "Trade Log tab: win rate, history. "
             "P&L Chart tab: equity curve. "
             "Console tab: full log of every action."),
        ], 1):
            st.markdown(f"""
            <div class="step">
              <div class="step-num">Step {i}</div>
              <div class="step-body"><strong style="color:#dde4f0">{title}</strong><br>{body}</div>
            </div>""", unsafe_allow_html=True)

    with cb:
        st.markdown("### 🔴 Live Mode — Real Orders")
        st.markdown("""
        <div class="banner banner-yellow">
        ⚠ Live mode places REAL orders on Upstox.
        Test on paper for at least 2 weeks first.
        Start with 1 lot only.
        </div>""", unsafe_allow_html=True)

        for i, (title, body) in enumerate([
            ("Enable F&O on Upstox",
             "Upstox App → Profile → Segments → Activate F&O."),
            ("Create API App (one-time)",
             "Go to developer.upstox.com → Create New App → "
             "Redirect URL = https://127.0.0.1 exactly. "
             "Save your API Key and API Secret."),
            ("Configure get_token.py",
             "Open get_token.py in a text editor. "
             "Fill in API_KEY and API_SECRET at the top."),
            ("Get token every morning (before 9:15 AM)",
             "Run: python get_token.py\n"
             "Browser opens → Login → After redirect, browser shows error page — NORMAL.\n"
             "Copy full URL from browser address bar (looks like https://127.0.0.1/?code=XXXX).\n"
             "Paste in terminal → token saved to access_token.txt automatically."),
            ("Start the bot",
             "Paste token in sidebar → Turn OFF Paper Mode → Press ▶ START.\n"
             "Bot connects Upstox, fetches live spot/VIX.\n"
             "Press ⟳ SCAN + ENTER — bot checks regime, places real orders if conditions met."),
            ("Monitor & verify",
             "After each entry, check Upstox App → My Orders & Positions.\n"
             "All orders are MIS (intraday) — Upstox auto-squares at 3:20 PM.\n"
             "Press SCAN repeatedly to refresh PnL and check exit conditions.\n"
             "Press ✕ FORCE CLOSE to exit manually at any time."),
            ("Margin needed (approx per lot)",
             "Bull/Bear Spread: ₹18,000–25,000\n"
             "Iron Condor: ₹35,000–45,000\n"
             "Straddle: ₹40,000–55,000\n"
             "(Upstox gives ~40-50% MIS margin benefit on spread strategies)"),
        ], 1):
            st.markdown(f"""
            <div class="step" style="border-left-color:#ff4d6a;">
              <div class="step-num" style="color:#ff4d6a;">Step {i}</div>
              <div class="step-body"><strong style="color:#dde4f0">{title}</strong><br>
              {body.replace(chr(10), "<br>")}</div>
            </div>""", unsafe_allow_html=True)

# ================================================================
# FOOTER
# ================================================================
st.markdown("---")
st.markdown(f"""
<div style="font-family:'Space Mono',monospace;font-size:.6rem;color:#1e2d45;
     display:flex;justify-content:space-between;padding:4px 0;">
  <span>Nifty Options Bot v3.0 — No auto-refresh (JS crash fixed)</span>
  <span>{'PAPER — simulated data' if s.paper_trade else 'LIVE — real Upstox orders'}</span>
  <span>Ticks: {s.tick_count} | {now.strftime('%H:%M:%S')}</span>
</div>""", unsafe_allow_html=True)

# ================================================================
# NOTE: NO time.sleep() + st.rerun() anywhere in this file.
# That pattern is what caused the Wc@ / Xe@ JS crash.
# All updates happen only when the user clicks a button.
# ================================================================
