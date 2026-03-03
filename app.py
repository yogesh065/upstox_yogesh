# ================================================================
# NIFTY OPTIONS PRO BOT — STREAMLIT DASHBOARD
# Run: streamlit run app.py
# ================================================================

import streamlit as st
import pandas as pd
import numpy as np
import datetime
import time
import math
import threading
import queue
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ================================================================
# PAGE CONFIG (must be first)
# ================================================================

st.set_page_config(
    page_title="Nifty Options Pro Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ================================================================
# CUSTOM CSS — Dark trading terminal aesthetic
# ================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg-primary:    #0a0d14;
    --bg-card:       #111827;
    --bg-panel:      #161d2e;
    --border:        #1e2d45;
    --accent-green:  #00d4aa;
    --accent-red:    #ff4d6a;
    --accent-yellow: #f5c842;
    --accent-blue:   #4f9cf9;
    --accent-purple: #a78bfa;
    --text-primary:  #e8ecf4;
    --text-muted:    #6b7894;
    --text-dim:      #3d4f6e;
    --green-glow:    0 0 20px rgba(0,212,170,0.25);
    --red-glow:      0 0 20px rgba(255,77,106,0.25);
}

html, body, .stApp {
    background: var(--bg-primary) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--text-primary);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }

/* Remove default streamlit padding/margins */
.block-container { padding: 1rem 2rem !important; max-width: 100% !important; }
.element-container { margin-bottom: 0.5rem !important; }

/* Header */
.bot-header {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a2744 50%, #0d1b2a 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
}
.bot-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent-green), transparent);
}
.bot-title {
    font-family: 'Space Mono', monospace;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--accent-green);
    letter-spacing: -0.5px;
    margin: 0;
}
.bot-subtitle {
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-top: 4px;
    font-family: 'Space Mono', monospace;
}

/* Status pill */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    font-family: 'Space Mono', monospace;
    letter-spacing: 0.5px;
}
.status-running {
    background: rgba(0,212,170,0.12);
    border: 1px solid rgba(0,212,170,0.4);
    color: var(--accent-green);
}
.status-stopped {
    background: rgba(107,120,148,0.12);
    border: 1px solid rgba(107,120,148,0.3);
    color: var(--text-muted);
}
.status-paper {
    background: rgba(245,200,66,0.12);
    border: 1px solid rgba(245,200,66,0.4);
    color: var(--accent-yellow);
}

/* KPI Cards */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin-bottom: 16px;
}
.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 18px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}
.kpi-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent-color, var(--border));
    opacity: 0.6;
}
.kpi-label {
    font-size: 0.68rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-family: 'Space Mono', monospace;
    margin-bottom: 6px;
}
.kpi-value {
    font-family: 'Space Mono', monospace;
    font-size: 1.45rem;
    font-weight: 700;
    line-height: 1;
}
.kpi-sub {
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-top: 4px;
}
.green  { color: var(--accent-green); --accent-color: var(--accent-green); }
.red    { color: var(--accent-red);   --accent-color: var(--accent-red); }
.yellow { color: var(--accent-yellow);--accent-color: var(--accent-yellow);}
.blue   { color: var(--accent-blue);  --accent-color: var(--accent-blue); }
.purple { color: var(--accent-purple);--accent-color: var(--accent-purple);}

/* Panel */
.panel {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px;
    height: 100%;
}
.panel-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--text-muted);
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
}

/* Trade log rows */
.trade-row {
    display: flex;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid var(--bg-panel);
    gap: 12px;
}
.trade-num {
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    color: var(--text-dim);
    width: 24px;
}
.trade-strategy {
    font-size: 0.8rem;
    font-weight: 500;
    flex: 1;
}
.trade-pnl {
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    font-weight: 700;
    text-align: right;
    min-width: 80px;
}
.trade-badge {
    font-size: 0.65rem;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: 'Space Mono', monospace;
    background: rgba(79,156,249,0.12);
    color: var(--accent-blue);
    border: 1px solid rgba(79,156,249,0.3);
}

/* Regime chip */
.regime-chip {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 6px;
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}
.regime-bull   { background: rgba(0,212,170,0.1); color: #00d4aa; border: 1px solid rgba(0,212,170,0.3); }
.regime-bear   { background: rgba(255,77,106,0.1); color: #ff4d6a; border: 1px solid rgba(255,77,106,0.3); }
.regime-range  { background: rgba(167,139,250,0.1); color: #a78bfa; border: 1px solid rgba(167,139,250,0.3); }
.regime-spike  { background: rgba(245,200,66,0.1); color: #f5c842; border: 1px solid rgba(245,200,66,0.3); }

/* Progress bar */
.prog-bar-wrap {
    background: var(--bg-panel);
    border-radius: 4px;
    height: 6px;
    overflow: hidden;
    margin-top: 6px;
}
.prog-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
}

/* Indicator row */
.ind-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 0;
    border-bottom: 1px solid var(--bg-panel);
    font-size: 0.82rem;
}
.ind-label { color: var(--text-muted); font-family: 'Space Mono', monospace; font-size: 0.72rem; }
.ind-value { font-family: 'Space Mono', monospace; font-weight: 600; }

/* Log console */
.log-console {
    background: #080c14;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 16px;
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    line-height: 1.7;
    max-height: 260px;
    overflow-y: auto;
    color: var(--text-muted);
}
.log-info    { color: #4f9cf9; }
.log-success { color: #00d4aa; }
.log-warn    { color: #f5c842; }
.log-error   { color: #ff4d6a; }

/* Streamlit overrides */
.stButton > button {
    background: var(--accent-green) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.5px !important;
    padding: 10px 24px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #00bfa0 !important;
    box-shadow: var(--green-glow) !important;
    transform: translateY(-1px) !important;
}
[data-testid="stButton"][aria-label="stop"] > button {
    background: var(--accent-red) !important;
    color: #fff !important;
}
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] select,
div.stSlider {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 6px !important;
}
div[data-testid="stSelectbox"] > div > div {
    background: var(--bg-panel) !important;
    border-color: var(--border) !important;
}
label, .stSelectbox label, .stNumberInput label, .stSlider label {
    color: var(--text-muted) !important;
    font-size: 0.78rem !important;
    font-family: 'Space Mono', monospace !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
}
div[data-testid="stMetricValue"] { color: var(--text-primary) !important; }
.stTabs [data-baseweb="tab"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.75rem !important;
    color: var(--text-muted) !important;
}
.stTabs [aria-selected="true"] { color: var(--accent-green) !important; }
hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)

# ================================================================
# STATE INIT
# ================================================================

def init_state():
    defaults = {
        "bot_running":       False,
        "paper_trade":       True,
        "access_token":      "",
        "start_capital":     200_000,
        "lot_size":          50,
        "max_trades":        3,
        "daily_profit_lock": 6_000,
        "daily_loss_limit":  4_000,
        "target_pct":        40,
        "sl_multiplier":     1.8,
        "min_vix":           13.5,
        "max_vix":           30.0,
        "vix_straddle":      22.0,
        "spread_min":        100,
        "spread_max":        400,
        "condor_wing":       200,
        "ema_fast":          9,
        "ema_slow":          21,
        "ema_trend":         50,
        "reentry_wait":      120,

        # Live data (simulated in paper mode)
        "spot_price":        24_580.0,
        "vix":               16.8,
        "iv_rank":           52.0,
        "rsi":               58.5,
        "atr":               145.0,
        "bb_width":          1.2,
        "vwap":              24_550.0,
        "regime":            "Trending Up",
        "strategy":          "Bull Put Spread",

        # Session state
        "session_pnl":       0.0,
        "trade_count":       0,
        "current_capital":   200_000,
        "peak_capital":      200_000,
        "drawdown":          0.0,

        # Trade log
        "trades":            [],

        # PnL chart data
        "pnl_series":        [],
        "pnl_times":         [],

        # Log messages
        "log_messages":      [],

        # Current open trade
        "open_trade":        None,
        "open_pnl":          0.0,
        "be_active":         False,
        "trail_active":      False,
        "partial_done":      False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ================================================================
# MOCK SIMULATION HELPERS (paper trade)
# ================================================================

def simulate_market_tick():
    """Simulate realistic market movement for paper trading."""
    s = st.session_state
    # Random walk on spot
    change = np.random.normal(0, 15)
    s.spot_price = max(20000, s.spot_price + change)

    # VIX mean-revert
    vix_change = np.random.normal(0, 0.2)
    s.vix = max(10, min(35, s.vix + vix_change * 0.3 + (16 - s.vix) * 0.05))
    s.iv_rank = max(0, min(100, (s.vix - 11) / (35 - 11) * 100))

    # RSI drift
    rsi_change = np.random.normal(0, 1.5)
    s.rsi = max(20, min(80, s.rsi + rsi_change * 0.5 + (50 - s.rsi) * 0.02))

    # Determine regime
    if s.vix >= 22 and s.iv_rank >= 60:
        s.regime = "High IV Spike"
        s.strategy = "Short Straddle"
    elif s.rsi > 55 and s.spot_price > s.vwap:
        s.regime = "Trending Up"
        s.strategy = "Bull Put Spread"
    elif s.rsi < 45 and s.spot_price < s.vwap:
        s.regime = "Trending Down"
        s.strategy = "Bear Call Spread"
    elif 42 < s.rsi < 58 and s.bb_width < 1.5:
        s.regime = "Range Bound"
        s.strategy = "Iron Condor"
    else:
        s.regime = "Unknown"
        s.strategy = "Scanning..."

def simulate_pnl_tick(credit):
    """Simulate PnL movement for an open trade."""
    # Random PnL walk biased slightly positive (theta decay)
    change = np.random.normal(30, 80)
    st.session_state.open_pnl = min(
        st.session_state.open_pnl + change,
        credit * 0.45
    )

def add_log(msg, level="info"):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.log_messages.insert(0, {"ts": ts, "msg": msg, "level": level})
    if len(st.session_state.log_messages) > 80:
        st.session_state.log_messages = st.session_state.log_messages[:80]

# ================================================================
# STRATEGY COLOR MAP
# ================================================================

STRATEGY_COLORS = {
    "Bull Put Spread":  "#00d4aa",
    "Bear Call Spread": "#ff4d6a",
    "Iron Condor":      "#a78bfa",
    "Short Straddle":   "#f5c842",
    "0DTE Theta Burn":  "#4f9cf9",
    "Scanning...":      "#6b7894",
}

REGIME_CLASS = {
    "Trending Up":   "regime-bull",
    "Trending Down": "regime-bear",
    "Range Bound":   "regime-range",
    "High IV Spike": "regime-spike",
    "Unknown":       "regime-range",
}

# ================================================================
# SIDEBAR — CONFIG
# ================================================================

with st.sidebar:
    st.markdown("""
    <div style='font-family:Space Mono,monospace; font-size:0.85rem;
         color:#00d4aa; font-weight:700; padding:12px 0 4px; letter-spacing:1px;'>
        ⚙ CONFIGURATION
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # API Token
    st.session_state.access_token = st.text_input(
        "Access Token", value=st.session_state.access_token,
        type="password", placeholder="YOUR_UPSTOX_TOKEN"
    )

    st.session_state.paper_trade = st.toggle(
        "📄 Paper Trade Mode", value=st.session_state.paper_trade
    )

    st.markdown("---")
    st.markdown("<div class='panel-title'>CAPITAL & LIMITS</div>", unsafe_allow_html=True)

    st.session_state.start_capital = st.number_input(
        "Start Capital (₹)", value=st.session_state.start_capital,
        step=10_000, min_value=50_000, max_value=10_000_000
    )
    st.session_state.daily_profit_lock = st.number_input(
        "Daily Profit Lock (₹)", value=st.session_state.daily_profit_lock,
        step=500, min_value=1_000
    )
    st.session_state.daily_loss_limit = st.number_input(
        "Daily Loss Limit (₹)", value=st.session_state.daily_loss_limit,
        step=500, min_value=500
    )
    st.session_state.max_trades = st.slider(
        "Max Trades / Day", 1, 5, st.session_state.max_trades
    )

    st.markdown("---")
    st.markdown("<div class='panel-title'>TRADE EXITS</div>", unsafe_allow_html=True)

    st.session_state.target_pct = st.slider(
        "Target % of Credit", 20, 70, st.session_state.target_pct,
        help="Exit trade when PnL = X% of collected credit"
    )
    st.session_state.sl_multiplier = st.slider(
        "Stop Loss Multiplier", 1.0, 3.0, st.session_state.sl_multiplier, 0.1,
        help="Hard stop = credit × multiplier"
    )

    st.markdown("---")
    st.markdown("<div class='panel-title'>VIX THRESHOLDS</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.min_vix = st.number_input("Min VIX", value=st.session_state.min_vix, step=0.5)
    with col2:
        st.session_state.max_vix = st.number_input("Max VIX", value=st.session_state.max_vix, step=0.5)

    st.session_state.vix_straddle = st.number_input(
        "Straddle VIX Trigger", value=st.session_state.vix_straddle, step=0.5
    )

    st.markdown("---")
    st.markdown("<div class='panel-title'>STRIKE CONFIG</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.spread_min = st.number_input("Spread Min", value=st.session_state.spread_min, step=50)
    with col2:
        st.session_state.spread_max = st.number_input("Spread Max", value=st.session_state.spread_max, step=50)
    st.session_state.condor_wing = st.number_input(
        "Condor Wing Width", value=st.session_state.condor_wing, step=50
    )

    st.markdown("---")
    st.markdown("<div class='panel-title'>INDICATORS</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.ema_fast  = st.number_input("EMA Fast",  value=st.session_state.ema_fast,  step=1, min_value=3)
    with col2:
        st.session_state.ema_slow  = st.number_input("EMA Slow",  value=st.session_state.ema_slow,  step=1, min_value=5)
    with col3:
        st.session_state.ema_trend = st.number_input("EMA Trend", value=st.session_state.ema_trend, step=1, min_value=10)

# ================================================================
# MAIN DASHBOARD
# ================================================================

s = st.session_state

# ── Header ────────────────────────────────────────────────────
paper_label = "PAPER MODE" if s.paper_trade else "LIVE MODE"
paper_class = "status-paper" if s.paper_trade else "status-running"
run_status  = "● RUNNING" if s.bot_running else "○ IDLE"
run_class   = "status-running" if s.bot_running else "status-stopped"

st.markdown(f"""
<div class="bot-header">
  <div>
    <div class="bot-title">◈ NIFTY OPTIONS PRO BOT</div>
    <div class="bot-subtitle">5-Strategy Adaptive Engine · Upstox · NSE/FO</div>
  </div>
  <div style="display:flex; gap:10px; align-items:center;">
    <span class="status-pill {paper_class}">{paper_label}</span>
    <span class="status-pill {run_class}">{run_status}</span>
    <span class="status-pill status-stopped" style="color:#6b7894">
        {datetime.datetime.now().strftime("%d %b %Y")}
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Control buttons ───────────────────────────────────────────
ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([1, 1, 1, 5])
with ctrl_col1:
    if st.button("▶  START BOT", disabled=s.bot_running):
        st.session_state.bot_running = True
        st.session_state.session_pnl = 0.0
        st.session_state.trade_count = 0
        st.session_state.trades = []
        st.session_state.pnl_series = [0.0]
        st.session_state.pnl_times  = [datetime.datetime.now().strftime("%H:%M")]
        st.session_state.current_capital = s.start_capital
        st.session_state.peak_capital    = s.start_capital
        st.session_state.open_trade = None
        st.session_state.open_pnl   = 0.0
        st.session_state.be_active  = False
        st.session_state.trail_active = False
        add_log("Bot started. Scanning market conditions...", "info")
        add_log(f"Capital: ₹{s.start_capital:,} | Mode: {'PAPER' if s.paper_trade else 'LIVE'}", "info")
        st.rerun()

with ctrl_col2:
    if st.button("■  STOP BOT", disabled=not s.bot_running):
        st.session_state.bot_running = False
        if s.open_trade:
            add_log("Manual stop — closing all positions", "warn")
            st.session_state.open_trade = None
        add_log("Bot stopped by user.", "warn")
        st.rerun()

with ctrl_col3:
    if st.button("⟳  SIM TICK", disabled=not s.bot_running):
        simulate_market_tick()
        if s.open_trade:
            simulate_pnl_tick(s.open_trade["credit"])
            # Check exit conditions
            credit  = s.open_trade["credit"]
            target  = credit * s.target_pct / 100
            hardstop = -credit * s.sl_multiplier
            pnl     = s.open_pnl

            if not s.be_active and pnl >= target * 0.5:
                st.session_state.be_active = True
                add_log(f"🔒 Breakeven trail activated at ₹{pnl:+.0f}", "success")
            if not s.trail_active and pnl >= target * 0.75:
                st.session_state.trail_active = True
                add_log(f"🚀 Trailing stop activated at ₹{pnl:+.0f}", "success")

            if pnl >= target:
                add_log(f"✅ Target hit! PnL ₹{pnl:+.0f}", "success")
                st.session_state.session_pnl += pnl
                st.session_state.current_capital += pnl
                st.session_state.peak_capital = max(s.peak_capital, s.current_capital + pnl)
                st.session_state.trade_count += 1
                t = s.open_trade
                st.session_state.trades.append({
                    "num": s.trade_count, "strategy": t["strategy"],
                    "pnl": pnl, "reason": "Target Hit",
                    "time": datetime.datetime.now().strftime("%H:%M"),
                    "credit": credit,
                })
                st.session_state.pnl_series.append(s.session_pnl + pnl)
                st.session_state.pnl_times.append(datetime.datetime.now().strftime("%H:%M:%S"))
                st.session_state.open_trade  = None
                st.session_state.open_pnl    = 0.0
                st.session_state.be_active   = False
                st.session_state.trail_active = False

            elif pnl <= hardstop:
                add_log(f"🛑 Hard stop hit! PnL ₹{pnl:+.0f}", "error")
                st.session_state.session_pnl += pnl
                st.session_state.current_capital += pnl
                st.session_state.trade_count += 1
                t = s.open_trade
                st.session_state.trades.append({
                    "num": s.trade_count, "strategy": t["strategy"],
                    "pnl": pnl, "reason": "Hard Stop",
                    "time": datetime.datetime.now().strftime("%H:%M"),
                    "credit": credit,
                })
                st.session_state.pnl_series.append(s.session_pnl + pnl)
                st.session_state.pnl_times.append(datetime.datetime.now().strftime("%H:%M:%S"))
                st.session_state.open_trade   = None
                st.session_state.open_pnl     = 0.0
                st.session_state.be_active    = False
                st.session_state.trail_active = False

        else:
            # Try to enter new trade
            now = datetime.datetime.now().time()
            if (datetime.time(9,20) <= now <= datetime.time(13,30)
                    and s.trade_count < s.max_trades
                    and s.strategy not in ("Scanning...",)):
                # Simulate a new trade entry
                credit = np.random.uniform(2500, 6000)
                st.session_state.open_trade  = {"strategy": s.strategy, "credit": credit}
                st.session_state.open_pnl    = 0.0
                st.session_state.be_active   = False
                st.session_state.trail_active = False
                add_log(f"📋 NEW TRADE: {s.strategy} | Credit: ₹{credit:,.0f}", "success")
                add_log(f"   Target: ₹{credit*s.target_pct/100:,.0f} | "
                        f"Stop: ₹{-credit*s.sl_multiplier:,.0f}", "info")
        st.rerun()

# ── KPI Cards ─────────────────────────────────────────────────
pnl_color = "green" if s.session_pnl >= 0 else "red"
dd = (s.peak_capital - s.current_capital) / s.peak_capital * 100 if s.peak_capital > 0 else 0
profit_progress = min(100, s.session_pnl / s.daily_profit_lock * 100) if s.daily_profit_lock > 0 else 0
loss_progress   = min(100, -s.session_pnl / s.daily_loss_limit * 100) if s.daily_loss_limit > 0 else 0

st.markdown(f"""
<div class="kpi-grid">
  <div class="kpi-card" style="--accent-color:{'#00d4aa' if s.session_pnl>=0 else '#ff4d6a'}">
    <div class="kpi-label">Session P&L</div>
    <div class="kpi-value {pnl_color}">₹{s.session_pnl:+,.0f}</div>
    <div class="prog-bar-wrap"><div class="prog-bar-fill"
      style="width:{profit_progress if s.session_pnl>=0 else loss_progress}%;
             background:{'#00d4aa' if s.session_pnl>=0 else '#ff4d6a'}"></div></div>
    <div class="kpi-sub">Target ₹{s.daily_profit_lock:,}</div>
  </div>
  <div class="kpi-card" style="--accent-color:#4f9cf9">
    <div class="kpi-label">Capital</div>
    <div class="kpi-value blue">₹{s.current_capital:,.0f}</div>
    <div class="kpi-sub">Peak ₹{s.peak_capital:,.0f}</div>
  </div>
  <div class="kpi-card" style="--accent-color:{'#ff4d6a' if dd>5 else '#6b7894'}">
    <div class="kpi-label">Drawdown</div>
    <div class="kpi-value {'red' if dd>5 else ''}">
      {dd:.1f}%
    </div>
    <div class="prog-bar-wrap"><div class="prog-bar-fill"
      style="width:{min(100,dd/15*100):.0f}%;
             background:{'#ff4d6a' if dd>10 else '#f5c842' if dd>5 else '#6b7894'}"></div></div>
    <div class="kpi-sub">Limit 15%</div>
  </div>
  <div class="kpi-card" style="--accent-color:#a78bfa">
    <div class="kpi-label">Trades Today</div>
    <div class="kpi-value purple">{s.trade_count} / {s.max_trades}</div>
    <div class="prog-bar-wrap"><div class="prog-bar-fill"
      style="width:{s.trade_count/s.max_trades*100 if s.max_trades>0 else 0:.0f}%;
             background:#a78bfa"></div></div>
    <div class="kpi-sub">Max {s.max_trades}/day</div>
  </div>
  <div class="kpi-card" style="--accent-color:#f5c842">
    <div class="kpi-label">Live PnL</div>
    <div class="kpi-value {'green' if s.open_pnl>=0 else 'red'}">
      {'₹'+f'{s.open_pnl:+,.0f}' if s.open_trade else '—'}
    </div>
    <div class="kpi-sub">{'Active trade open' if s.open_trade else 'No open trade'}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Main content tabs ──────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊  LIVE MONITOR",
    "📈  P&L CHART",
    "🧠  MARKET REGIME",
    "📋  TRADE LOG",
    "📟  CONSOLE",
])

# ==============================================================
# TAB 1 — LIVE MONITOR
# ==============================================================

with tab1:
    col_left, col_mid, col_right = st.columns([1.2, 1.4, 1.2])

    # ── Market Snapshot ──────────────────────────────────────
    with col_left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">◈ MARKET SNAPSHOT</div>', unsafe_allow_html=True)

        def ind_row(label, value, color=""):
            return f"""
            <div class="ind-row">
                <span class="ind-label">{label}</span>
                <span class="ind-value" style="color:{color or 'var(--text-primary)'}">
                    {value}
                </span>
            </div>"""

        vix_color = "#f5c842" if s.vix > 20 else "#ff4d6a" if s.vix > 25 else "#00d4aa"
        rsi_color = "#00d4aa" if s.rsi > 55 else "#ff4d6a" if s.rsi < 45 else "#6b7894"

        st.markdown(f"""
        {ind_row("NIFTY SPOT",   f"₹{s.spot_price:,.2f}", "#4f9cf9")}
        {ind_row("INDIA VIX",    f"{s.vix:.2f}", vix_color)}
        {ind_row("IV RANK",      f"{s.iv_rank:.0f}%", vix_color)}
        {ind_row("RSI (14)",     f"{s.rsi:.1f}", rsi_color)}
        {ind_row("ATR (14)",     f"{s.atr:.1f} pts")}
        {ind_row("BB WIDTH",     f"{s.bb_width:.2f}%")}
        {ind_row("VWAP",         f"₹{s.vwap:,.1f}")}
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Active Trade ─────────────────────────────────────────
    with col_mid:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">◈ ACTIVE TRADE</div>', unsafe_allow_html=True)

        if s.open_trade:
            credit  = s.open_trade["credit"]
            target  = credit * s.target_pct / 100
            hardstop = -credit * s.sl_multiplier
            pnl_pct = (s.open_pnl / target * 100) if target > 0 else 0
            bar_fill = min(100, max(-100, pnl_pct))
            bar_color = "#00d4aa" if s.open_pnl >= 0 else "#ff4d6a"
            strategy = s.open_trade["strategy"]
            strat_color = STRATEGY_COLORS.get(strategy, "#6b7894")

            be_badge = (
                f'<span style="background:rgba(0,212,170,0.15); '
                f'color:#00d4aa; padding:2px 8px; border-radius:4px; '
                f'font-size:0.68rem; font-family:Space Mono,monospace; '
                f'border:1px solid rgba(0,212,170,0.3); margin-left:6px;">🔒 BE</span>'
                if s.be_active else ""
            )
            trail_badge = (
                f'<span style="background:rgba(245,200,66,0.15); '
                f'color:#f5c842; padding:2px 8px; border-radius:4px; '
                f'font-size:0.68rem; font-family:Space Mono,monospace; '
                f'border:1px solid rgba(245,200,66,0.3); margin-left:6px;">🚀 TRAIL</span>'
                if s.trail_active else ""
            )

            st.markdown(f"""
            <div style="margin-bottom:14px;">
              <span style="background:rgba({
                  '0,212,170' if 'Bull' in strategy else
                  '255,77,106' if 'Bear' in strategy else
                  '167,139,250' if 'Condor' in strategy else
                  '79,156,249' if '0DTE' in strategy else
                  '245,200,66'
              },0.12); color:{strat_color}; padding:5px 12px;
              border-radius:6px; font-family:Space Mono,monospace;
              font-size:0.8rem; font-weight:700;
              border:1px solid rgba(255,255,255,0.1);">
                {strategy}
              </span>
              {be_badge}{trail_badge}
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:16px;">
              <div style="background:#0d1520; border-radius:8px; padding:12px;">
                <div style="font-size:0.65rem; color:var(--text-muted); font-family:Space Mono,monospace; margin-bottom:4px;">CREDIT RECEIVED</div>
                <div style="font-family:Space Mono,monospace; font-size:1.1rem; color:#4f9cf9;">₹{credit:,.0f}</div>
              </div>
              <div style="background:#0d1520; border-radius:8px; padding:12px;">
                <div style="font-size:0.65rem; color:var(--text-muted); font-family:Space Mono,monospace; margin-bottom:4px;">LIVE PnL</div>
                <div style="font-family:Space Mono,monospace; font-size:1.1rem; color:{bar_color};">
                  ₹{s.open_pnl:+,.0f}
                </div>
              </div>
              <div style="background:#0d1520; border-radius:8px; padding:12px;">
                <div style="font-size:0.65rem; color:var(--text-muted); font-family:Space Mono,monospace; margin-bottom:4px;">TARGET</div>
                <div style="font-family:Space Mono,monospace; font-size:1.1rem; color:#00d4aa;">₹{target:,.0f}</div>
              </div>
              <div style="background:#0d1520; border-radius:8px; padding:12px;">
                <div style="font-size:0.65rem; color:var(--text-muted); font-family:Space Mono,monospace; margin-bottom:4px;">HARD STOP</div>
                <div style="font-family:Space Mono,monospace; font-size:1.1rem; color:#ff4d6a;">₹{hardstop:,.0f}</div>
              </div>
            </div>
            <div style="margin-bottom:6px; font-size:0.7rem; color:var(--text-muted); font-family:Space Mono,monospace; display:flex; justify-content:space-between;">
              <span>PROGRESS TO TARGET</span>
              <span>{max(0,pnl_pct):.0f}%</span>
            </div>
            <div style="background:#0d1520; border-radius:6px; height:10px; overflow:hidden; border:1px solid #1e2d45;">
              <div style="height:100%; width:{max(0,min(100,pnl_pct)):.0f}%;
                   background:linear-gradient(90deg, #004d3d, {bar_color});
                   border-radius:6px; transition:width 0.5s;">
              </div>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:4px; font-size:0.65rem; color:var(--text-dim); font-family:Space Mono,monospace;">
              <span>0%</span><span>25% PARTIAL</span><span>50% BE</span><span>75% TRAIL</span><span>100%</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center; padding:40px 20px; color:var(--text-dim);">
              <div style="font-size:2.5rem; margin-bottom:12px; opacity:0.3;">◎</div>
              <div style="font-family:Space Mono,monospace; font-size:0.8rem; letter-spacing:1px;">
                NO ACTIVE TRADE
              </div>
              <div style="font-size:0.75rem; margin-top:8px; color:var(--text-dim);">
                Bot is scanning market conditions
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # ── Session risk meter ────────────────────────────────────
    with col_right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">◈ SESSION RISK METER</div>', unsafe_allow_html=True)

        profit_pct = min(100, s.session_pnl / s.daily_profit_lock * 100) if s.session_pnl > 0 and s.daily_profit_lock > 0 else 0
        loss_pct   = min(100, -s.session_pnl / s.daily_loss_limit * 100) if s.session_pnl < 0 and s.daily_loss_limit > 0 else 0
        lot_scale  = 3 if dd < 5 else 2 if dd < 10 else 1 if dd < 15 else 0

        st.markdown(f"""
        <div style="margin-bottom:18px;">
          <div class="ind-row">
            <span class="ind-label">PROFIT PROGRESS</span>
            <span class="ind-value green">₹{max(0,s.session_pnl):,.0f} / ₹{s.daily_profit_lock:,}</span>
          </div>
          <div class="prog-bar-wrap" style="height:8px; margin-top:4px;">
            <div class="prog-bar-fill" style="width:{profit_pct:.0f}%; background:linear-gradient(90deg,#003d2e,#00d4aa);"></div>
          </div>
        </div>
        <div style="margin-bottom:18px;">
          <div class="ind-row">
            <span class="ind-label">LOSS EXPOSURE</span>
            <span class="ind-value {'red' if loss_pct>50 else 'yellow' if loss_pct>25 else ''}">
              ₹{min(0,s.session_pnl):,.0f} / -₹{s.daily_loss_limit:,}
            </span>
          </div>
          <div class="prog-bar-wrap" style="height:8px; margin-top:4px;">
            <div class="prog-bar-fill" style="width:{loss_pct:.0f}%;
              background:linear-gradient(90deg,#3d001a,#ff4d6a);"></div>
          </div>
        </div>
        <div class="ind-row">
          <span class="ind-label">LOT SCALE</span>
          <span class="ind-value {'green' if lot_scale==3 else 'yellow' if lot_scale==2 else 'red' if lot_scale==1 else ''}">
            {lot_scale} LOTS {'✅' if lot_scale==3 else '⚠️' if lot_scale>0 else '🛑'}
          </span>
        </div>
        <div class="ind-row">
          <span class="ind-label">DRAWDOWN</span>
          <span class="ind-value {'red' if dd>10 else 'yellow' if dd>5 else 'green'}">{dd:.2f}%</span>
        </div>
        <div class="ind-row">
          <span class="ind-label">SESSION TRADES</span>
          <span class="ind-value purple">{s.trade_count} / {s.max_trades}</span>
        </div>
        <div class="ind-row">
          <span class="ind-label">BREAKEVEN STATUS</span>
          <span class="ind-value {'green' if s.be_active else ''}">
            {'🔒 LOCKED' if s.be_active else '⏳ ARMED'}
          </span>
        </div>
        <div class="ind-row">
          <span class="ind-label">TRAILING STOP</span>
          <span class="ind-value {'yellow' if s.trail_active else ''}">
            {'🚀 ACTIVE' if s.trail_active else '— WAITING'}
          </span>
        </div>
        <div class="ind-row">
          <span class="ind-label">MARKET OPEN</span>
          <span class="ind-value {'green' if datetime.time(9,20)<=datetime.datetime.now().time()<=datetime.time(15,30) else 'red'}">
            {'✅ YES' if datetime.time(9,20)<=datetime.datetime.now().time()<=datetime.time(15,30) else '🔴 CLOSED'}
          </span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================
# TAB 2 — P&L CHART
# ==============================================================

with tab2:
    if len(s.pnl_series) > 1:
        fig = go.Figure()
        times  = s.pnl_times
        values = s.pnl_series
        colors = ["#00d4aa" if v >= 0 else "#ff4d6a" for v in values]

        # Area fill
        fig.add_trace(go.Scatter(
            x=times, y=values,
            mode="lines",
            fill="tozeroy",
            fillcolor="rgba(0,212,170,0.07)",
            line=dict(color="#00d4aa", width=2.5),
            name="Session P&L",
            hovertemplate="<b>%{x}</b><br>P&L: ₹%{y:+,.0f}<extra></extra>",
        ))

        # Profit lock line
        fig.add_hline(
            y=s.daily_profit_lock,
            line=dict(color="#f5c842", width=1.2, dash="dot"),
            annotation_text=f"Profit Lock ₹{s.daily_profit_lock:,}",
            annotation_font_color="#f5c842",
            annotation_font_size=11,
        )
        # Loss limit line
        fig.add_hline(
            y=-s.daily_loss_limit,
            line=dict(color="#ff4d6a", width=1.2, dash="dot"),
            annotation_text=f"Loss Limit -₹{s.daily_loss_limit:,}",
            annotation_font_color="#ff4d6a",
            annotation_font_size=11,
        )
        # Zero line
        fig.add_hline(y=0, line=dict(color="#1e2d45", width=1))

        fig.update_layout(
            paper_bgcolor="#0a0d14",
            plot_bgcolor="#0a0d14",
            font_family="Space Mono",
            font_color="#6b7894",
            height=420,
            margin=dict(l=60, r=40, t=30, b=40),
            xaxis=dict(
                showgrid=False, zeroline=False,
                color="#3d4f6e",
                tickfont_size=10,
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="#111827",
                zeroline=False,
                color="#3d4f6e",
                tickprefix="₹",
                tickfont_size=10,
            ),
            hovermode="x unified",
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                bordercolor="#1e2d45",
                font_color="#6b7894",
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.markdown("""
        <div style="text-align:center; padding:80px; color:var(--text-dim);">
          <div style="font-family:Space Mono,monospace; font-size:0.9rem; letter-spacing:1px;">
            ◎ NO P&L DATA YET<br>
            <span style="font-size:0.75rem; opacity:0.6;">Start the bot and simulate ticks</span>
          </div>
        </div>""", unsafe_allow_html=True)

    # Strategy breakdown pie
    if s.trades:
        st.markdown("---")
        col_pie, col_bar = st.columns(2)

        with col_pie:
            strategy_pnl = {}
            for t in s.trades:
                strategy_pnl[t["strategy"]] = strategy_pnl.get(t["strategy"], 0) + t["pnl"]

            fig2 = go.Figure(data=[go.Pie(
                labels=list(strategy_pnl.keys()),
                values=[abs(v) for v in strategy_pnl.values()],
                hole=0.6,
                marker=dict(colors=[STRATEGY_COLORS.get(k, "#6b7894") for k in strategy_pnl.keys()],
                            line=dict(color="#0a0d14", width=2)),
                textfont=dict(family="Space Mono", size=10, color="#e8ecf4"),
                hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<extra></extra>",
            )])
            fig2.update_layout(
                paper_bgcolor="#0a0d14", plot_bgcolor="#0a0d14",
                font_color="#6b7894", height=260,
                margin=dict(l=20, r=20, t=20, b=20),
                title=dict(text="Strategy Mix", font=dict(size=11, family="Space Mono", color="#6b7894")),
                showlegend=True,
                legend=dict(font=dict(size=9, family="Space Mono"), bgcolor="rgba(0,0,0,0)"),
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col_bar:
            trade_nums = [str(t["num"]) for t in s.trades]
            pnls       = [t["pnl"] for t in s.trades]
            bar_colors = ["#00d4aa" if p >= 0 else "#ff4d6a" for p in pnls]
            fig3 = go.Figure(data=[go.Bar(
                x=trade_nums, y=pnls,
                marker=dict(color=bar_colors, line=dict(width=0)),
                hovertemplate="Trade #%{x}<br>₹%{y:+,.0f}<extra></extra>",
            )])
            fig3.update_layout(
                paper_bgcolor="#0a0d14", plot_bgcolor="#0a0d14",
                font_color="#6b7894", height=260,
                margin=dict(l=50, r=20, t=40, b=30),
                title=dict(text="P&L Per Trade", font=dict(size=11, family="Space Mono", color="#6b7894")),
                xaxis=dict(showgrid=False, tickfont=dict(size=10, family="Space Mono")),
                yaxis=dict(showgrid=True, gridcolor="#111827", tickprefix="₹", tickfont=dict(size=10, family="Space Mono")),
            )
            st.plotly_chart(fig3, use_container_width=True)

# ==============================================================
# TAB 3 — MARKET REGIME
# ==============================================================

with tab3:
    col_r1, col_r2, col_r3 = st.columns([1.5, 1.5, 1])

    with col_r1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">◈ REGIME DETECTION</div>', unsafe_allow_html=True)

        regime_css = REGIME_CLASS.get(s.regime, "regime-range")
        strat_color = STRATEGY_COLORS.get(s.strategy, "#6b7894")

        st.markdown(f"""
        <div style="margin-bottom:20px;">
          <div style="font-size:0.7rem; color:var(--text-muted); font-family:Space Mono,monospace; margin-bottom:8px; text-transform:uppercase; letter-spacing:1px;">Current Regime</div>
          <span class="regime-chip {regime_css}" style="font-size:0.9rem;">
            {s.regime.upper()}
          </span>
        </div>
        <div style="margin-bottom:20px;">
          <div style="font-size:0.7rem; color:var(--text-muted); font-family:Space Mono,monospace; margin-bottom:8px; text-transform:uppercase; letter-spacing:1px;">Selected Strategy</div>
          <div style="font-family:Space Mono,monospace; font-size:1.1rem; font-weight:700; color:{strat_color};">
            {s.strategy}
          </div>
        </div>
        <div style="margin-top:20px;">
          <div style="font-size:0.7rem; color:var(--text-muted); font-family:Space Mono,monospace; margin-bottom:10px; text-transform:uppercase; letter-spacing:1px;">Regime Logic</div>
          <div style="font-size:0.78rem; color:var(--text-muted); line-height:1.8;">
            {'🟢 Price > VWAP (' + f'{s.spot_price:.0f} > {s.vwap:.0f}' + ')' if s.spot_price > s.vwap else '🔴 Price < VWAP (' + f'{s.spot_price:.0f} < {s.vwap:.0f}' + ')'}
            <br>
            {'🟢 RSI Bullish (' + f'{s.rsi:.1f}' + ' > 55)' if s.rsi > 55 else '🔴 RSI Bearish (' + f'{s.rsi:.1f}' + ' < 45)' if s.rsi < 45 else '🟡 RSI Neutral (' + f'{s.rsi:.1f}' + ')'}
            <br>
            {'🟡 High IV (' + f'VIX {s.vix:.1f}' + ' ≥ 22)' if s.vix >= 22 else '🟢 Normal IV (' + f'VIX {s.vix:.1f}' + ')'}
            <br>
            {'🟢 Tight BB (' + f'{s.bb_width:.2f}' + '% < 1.5 — Range)' if s.bb_width < 1.5 else '🟡 Wide BB (' + f'{s.bb_width:.2f}' + '% — Trend)'}
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">◈ STRATEGY SELECTOR MAP</div>', unsafe_allow_html=True)

        strategies_info = [
            ("Bull Put Spread",  "Trending Up",   "RSI>55, Price>VWAP, EMA aligned up",   "VIX 13-22"),
            ("Bear Call Spread", "Trending Down", "RSI<45, Price<VWAP, EMA aligned down",  "VIX 13-22"),
            ("Iron Condor",      "Range Bound",   "BB tight (<1.5%), RSI 42-58",           "VIX ≥14"),
            ("Short Straddle",   "High IV Spike", "VIX ≥22, IV Rank ≥65%",                "VIX 22-30"),
            ("0DTE Theta Burn",  "Expiry Day",    "Thursday/weekly expiry day",            "Any VIX"),
        ]
        active_strategy = s.strategy

        for name, regime, cond, vix_req in strategies_info:
            is_active = name == active_strategy
            color = STRATEGY_COLORS.get(name, "#6b7894")
            bg = f"rgba({','.join(str(int(c,16)) for c in [color[1:3],color[3:5],color[5:]])},0.08)" if color.startswith("#") and len(color)==7 else "rgba(0,0,0,0)"
            border = f"1px solid {color}66" if is_active else "1px solid var(--border)"

            st.markdown(f"""
            <div style="background:{'rgba(0,0,0,0)' if not is_active else bg};
                        border:{border}; border-radius:8px; padding:10px 14px;
                        margin-bottom:8px; {'box-shadow: 0 0 15px ' + color + '22;' if is_active else ''}">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-family:Space Mono,monospace; font-size:0.78rem;
                       font-weight:700; color:{color}; {'text-shadow: 0 0 10px ' + color + '88;' if is_active else ''}">
                  {'▶ ' if is_active else '   '}{name}
                </span>
                <span style="font-size:0.65rem; color:var(--text-dim); font-family:Space Mono,monospace;">{vix_req}</span>
              </div>
              <div style="font-size:0.7rem; color:var(--text-dim); margin-top:3px;">{cond}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r3:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">◈ VIX GAUGE</div>', unsafe_allow_html=True)

        vix_pct = (s.vix - 10) / (35 - 10) * 100
        vix_zone = ("SAFE", "#00d4aa") if s.vix < 16 else ("MODERATE","#4f9cf9") if s.vix < 22 else ("HIGH","#f5c842") if s.vix < 28 else ("DANGER","#ff4d6a")

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=s.vix,
            number=dict(font=dict(family="Space Mono", size=28, color=vix_zone[1])),
            gauge=dict(
                axis=dict(range=[10, 35], tickfont=dict(family="Space Mono", size=9, color="#3d4f6e")),
                bar=dict(color=vix_zone[1], thickness=0.25),
                bgcolor="#0d1520",
                borderwidth=0,
                steps=[
                    dict(range=[10, 13.5], color="#1a0808"),
                    dict(range=[13.5, 22], color="#0a1a10"),
                    dict(range=[22, 28],   color="#1a1500"),
                    dict(range=[28, 35],   color="#1a0808"),
                ],
                threshold=dict(line=dict(color="#ff4d6a", width=2), thickness=0.75, value=28),
            ),
            title=dict(text=f"INDIA VIX · {vix_zone[0]}", font=dict(family="Space Mono", size=10, color="#6b7894")),
        ))
        fig_gauge.update_layout(
            paper_bgcolor="#111827", height=200,
            margin=dict(l=20, r=20, t=30, b=20),
            font_color="#6b7894",
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown(f"""
        <div class="ind-row"><span class="ind-label">IV RANK</span>
          <span class="ind-value" style="color:{vix_zone[1]}">{s.iv_rank:.0f}%</span></div>
        <div class="ind-row"><span class="ind-label">STRADDLE THRESHOLD</span>
          <span class="ind-value">{s.vix_straddle:.1f}</span></div>
        <div class="ind-row"><span class="ind-label">CONDOR FLOOR</span>
          <span class="ind-value">14.0</span></div>
        <div class="ind-row"><span class="ind-label">MAX SAFE VIX</span>
          <span class="ind-value red">{s.max_vix:.1f}</span></div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================
# TAB 4 — TRADE LOG
# ==============================================================

with tab4:
    if not s.trades:
        st.markdown("""
        <div style="text-align:center; padding:60px; color:var(--text-dim);">
          <div style="font-family:Space Mono,monospace; font-size:0.85rem; letter-spacing:1px;">
            ◎ NO TRADES YET<br>
            <span style="font-size:0.72rem; opacity:0.6;">Trades will appear here after execution</span>
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        # Summary bar
        wins   = sum(1 for t in s.trades if t["pnl"] > 0)
        losses = len(s.trades) - wins
        total_pnl = sum(t["pnl"] for t in s.trades)
        win_rate = wins / len(s.trades) * 100 if s.trades else 0
        avg_win  = sum(t["pnl"] for t in s.trades if t["pnl"]>0) / wins if wins else 0
        avg_loss = sum(t["pnl"] for t in s.trades if t["pnl"]<0) / losses if losses else 0

        st.markdown(f"""
        <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:20px;">
          <div style="background:#111827; border:1px solid #1e2d45; border-radius:8px; padding:14px; text-align:center;">
            <div class="kpi-label" style="text-align:center">WIN RATE</div>
            <div style="font-family:Space Mono,monospace; font-size:1.3rem; color:#00d4aa; font-weight:700;">{win_rate:.0f}%</div>
            <div style="font-size:0.7rem; color:#3d4f6e;">{wins}W / {losses}L</div>
          </div>
          <div style="background:#111827; border:1px solid #1e2d45; border-radius:8px; padding:14px; text-align:center;">
            <div class="kpi-label" style="text-align:center">AVG WIN</div>
            <div style="font-family:Space Mono,monospace; font-size:1.3rem; color:#00d4aa; font-weight:700;">₹{avg_win:,.0f}</div>
          </div>
          <div style="background:#111827; border:1px solid #1e2d45; border-radius:8px; padding:14px; text-align:center;">
            <div class="kpi-label" style="text-align:center">AVG LOSS</div>
            <div style="font-family:Space Mono,monospace; font-size:1.3rem; color:#ff4d6a; font-weight:700;">₹{avg_loss:,.0f}</div>
          </div>
          <div style="background:#111827; border:1px solid #1e2d45; border-radius:8px; padding:14px; text-align:center;">
            <div class="kpi-label" style="text-align:center">TOTAL PnL</div>
            <div style="font-family:Space Mono,monospace; font-size:1.3rem;
              color:{'#00d4aa' if total_pnl>=0 else '#ff4d6a'}; font-weight:700;">
              ₹{total_pnl:+,.0f}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Trade rows
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">◈ TRADE HISTORY</div>', unsafe_allow_html=True)
        header = """
        <div style="display:grid; grid-template-columns:40px 1fr 1fr 120px 120px 100px;
             gap:8px; padding:8px 0; border-bottom:1px solid #1e2d45;
             font-family:Space Mono,monospace; font-size:0.65rem;
             color:#3d4f6e; text-transform:uppercase; letter-spacing:1px;">
          <span>#</span><span>STRATEGY</span><span>EXIT REASON</span>
          <span>CREDIT</span><span>P&L</span><span>TIME</span>
        </div>"""
        st.markdown(header, unsafe_allow_html=True)

        for t in reversed(s.trades):
            pnl_color = "#00d4aa" if t["pnl"] >= 0 else "#ff4d6a"
            strat_color = STRATEGY_COLORS.get(t["strategy"], "#6b7894")
            reason_color = "#00d4aa" if "Target" in t["reason"] else "#ff4d6a" if "Stop" in t["reason"] else "#6b7894"
            st.markdown(f"""
            <div style="display:grid; grid-template-columns:40px 1fr 1fr 120px 120px 100px;
                 gap:8px; padding:10px 0; border-bottom:1px solid #0d1520;
                 align-items:center;">
              <span style="font-family:Space Mono,monospace; font-size:0.72rem; color:#3d4f6e;">#{t['num']}</span>
              <span style="font-family:Space Mono,monospace; font-size:0.78rem; color:{strat_color}; font-weight:600;">{t['strategy']}</span>
              <span style="font-size:0.75rem; color:{reason_color};">{t['reason']}</span>
              <span style="font-family:Space Mono,monospace; font-size:0.8rem; color:#4f9cf9;">₹{t['credit']:,.0f}</span>
              <span style="font-family:Space Mono,monospace; font-size:0.85rem; color:{pnl_color}; font-weight:700;">₹{t['pnl']:+,.0f}</span>
              <span style="font-family:Space Mono,monospace; font-size:0.72rem; color:#3d4f6e;">{t['time']}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================
# TAB 5 — CONSOLE LOG
# ==============================================================

with tab5:
    col_con, col_stats = st.columns([2, 1])

    with col_con:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">◈ BOT CONSOLE</div>', unsafe_allow_html=True)

        if s.log_messages:
            log_html = "<div class='log-console'>"
            for entry in s.log_messages:
                level_class = {
                    "info": "log-info", "success": "log-success",
                    "warn": "log-warn", "error": "log-error"
                }.get(entry["level"], "")
                log_html += f'<div><span style="color:#1e2d45">[{entry["ts"]}]</span> <span class="{level_class}">{entry["msg"]}</span></div>'
            log_html += "</div>"
            st.markdown(log_html, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='log-console'>
              <span style='color:#1e2d45'>[--:--:--]</span>
              <span class='log-info'> Waiting for bot to start...</span>
            </div>""", unsafe_allow_html=True)

        if st.button("🗑  Clear Console"):
            st.session_state.log_messages = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_stats:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">◈ STRATEGY GUIDE</div>', unsafe_allow_html=True)

        guides = {
            "Bull Put Spread": ("Sell OTM Put + Buy lower Put", "Profit: Price stays above short strike", "Trend + VWAP + RSI>55"),
            "Bear Call Spread": ("Sell OTM Call + Buy higher Call", "Profit: Price stays below short strike", "Downtrend + RSI<45"),
            "Iron Condor": ("4 legs: Put spread + Call spread", "Profit: Price stays in range", "Range + VIX≥14"),
            "Short Straddle": ("Sell ATM Call + ATM Put (hedged)", "Profit: IV collapses, price stays near ATM", "VIX≥22 + IVR≥65%"),
            "0DTE Theta Burn": ("Iron Fly on expiry day", "Profit: Fast theta decay to zero", "Expiry day only"),
        }

        for name, (struct, profit, cond) in guides.items():
            color = STRATEGY_COLORS.get(name, "#6b7894")
            is_active = name == s.strategy
            st.markdown(f"""
            <div style="margin-bottom:14px; padding:10px 12px;
                 background:{'rgba(0,0,0,0.3)' if is_active else 'transparent'};
                 border-left:2px solid {color if is_active else '#1e2d45'};
                 border-radius:0 6px 6px 0;">
              <div style="font-family:Space Mono,monospace; font-size:0.75rem;
                   font-weight:700; color:{color}; margin-bottom:5px;">{name}</div>
              <div style="font-size:0.7rem; color:#6b7894; line-height:1.6;">
                🔧 {struct}<br>
                💰 {profit}<br>
                ✅ {cond}
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ================================================================
# FOOTER
# ================================================================

st.markdown("---")
st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center;
     padding:10px 0; font-family:Space Mono,monospace; font-size:0.65rem; color:#1e2d45;">
  <span>◈ NIFTY OPTIONS PRO BOT v2.0 · Upstox API</span>
  <span>⚠ PAPER MODE ACTIVE — NOT REAL MONEY</span>
  <span>Last refresh: {datetime.datetime.now().strftime('%H:%M:%S')}</span>
</div>
""", unsafe_allow_html=True)

# Auto-refresh when bot running
if s.bot_running:
    time.sleep(1)
    st.rerun()
