import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="JARVIS Decision Core",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# DARK INSTITUTIONAL UI
# =========================
st.markdown("""
<style>

body {
    background-color: #05070A;
    color: #E6E6E6;
}

.block-container {
    padding: 1.2rem 2rem;
}

.title {
    font-size: 44px;
    font-weight: 800;
    color: #00f5ff;
    text-shadow: 0 0 20px rgba(0,245,255,0.3);
}

.sub {
    opacity: 0.6;
    margin-bottom: 15px;
}

.card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(0,245,255,0.12);
    border-radius: 16px;
    padding: 14px;
    box-shadow: 0 0 18px rgba(0,245,255,0.06);
}

.good {
    border: 1px solid rgba(0,255,150,0.4);
}

.bad {
    border: 1px solid rgba(255,80,80,0.3);
}

.warn {
    border: 1px solid rgba(255,200,0,0.3);
}

</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("<div class='title'>JARVIS DECISION CORE</div>", unsafe_allow_html=True)
st.markdown("<div class='sub'>Market regime + risk-based decision system</div>", unsafe_allow_html=True)

# =========================
# INPUT
# =========================
col1, col2 = st.columns([2,1])

with col1:
    tickers_input = st.text_input("Tickers", "AAPL, MSFT, NVDA, TSLA")

with col2:
    run = st.button("RUN ANALYSIS")

tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

# =========================
# DATA
# =========================
@st.cache_data(ttl=300)
def load(ticker):
    try:
        df = yf.Ticker(ticker).history(period="6mo")
        if df.empty:
            return None
        return df.reset_index()
    except:
        return None

def add_indicators(df):
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["RET5"] = df["Close"].pct_change(5)
    df["VOL"] = df["Close"].pct_change().rolling(10).std()
    df["HIGH20"] = df["Close"].rolling(20).max()
    df["LOW20"] = df["Close"].rolling(20).min()
    return df

# =========================
# FINAL DECISION ENGINE
# =========================
def analyze(df):
    if df is None or len(df) < 80:
        return None

    df = add_indicators(df)
    last = df.iloc[-1]

    trend_up = last["SMA20"] > last["SMA50"]
    momentum = last["RET5"] if not np.isnan(last["RET5"]) else 0
    vol = last["VOL"] if not np.isnan(last["VOL"]) else 0

    # Breakout detection
    breakout = last["Close"] > last["HIGH20"]

    # REGIME
    if trend_up and momentum > 0:
        regime = "BULL"
    elif not trend_up and momentum < 0:
        regime = "BEAR"
    else:
        regime = "CHOPPY"

    # SCORE MODEL
    score = 0
    score += 2 if trend_up else -2
    score += momentum * 15
    score -= vol * 40
    score += 1 if breakout else 0

    # DECISION LOGIC
    if regime == "BULL" and breakout and vol < 0.03:
        signal = "🟢 HIGH QUALITY BREAKOUT SETUP"
        style = "good"
    elif regime == "BULL":
        signal = "🟡 WATCH (trend intact)"
        style = "warn"
    elif regime == "CHOPPY":
        signal = "🟡 AVOID NEW TRADES (uncertain structure)"
        style = "warn"
    else:
        signal = "🔴 RISK OFF"
        style = "bad"

    return {
        "score": round(score, 2),
        "signal": signal,
        "regime": regime,
        "momentum": round(momentum, 4),
        "volatility": round(vol, 4),
        "breakout": breakout,
        "df": df,
        "style": style
    }

# =========================
# RUN
# =========================
if run:

    results = []

    st.markdown("### 🧠 Scanning Market Structure...")

    prog = st.progress(0)

    for i, t in enumerate(tickers):

        df = load(t)
        r = analyze(df)

        if r:
            results.append({
                "ticker": t,
                "score": r["score"],
                "signal": r["signal"],
                "regime": r["regime"],
                "momentum": r["momentum"],
                "volatility": r["volatility"],
                "breakout": r["breakout"],
                "price": round(df["Close"].iloc[-1], 2)
            })

        prog.progress((i+1)/len(tickers))

    if not results:
        st.error("No valid market data")
        st.stop()

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    top = results[0]

    # =========================
    # TOP SUMMARY
    # =========================
    c1, c2, c3 = st.columns(3)

    c1.markdown(f"<div class='card'><h3>TOP ASSET</h3><h2>{top['ticker']}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><h3>SCORE</h3><h2>{top['score']}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card'><h3>REGIME</h3><h2>{top['regime']}</h2></div>", unsafe_allow_html=True)

    st.divider()

    # =========================
    # MARKET GRID
    # =========================
    st.markdown("### 📊 Market Intelligence Grid")

    cols = st.columns(4)

    for i, r in enumerate(results):

        with cols[i % 4]:

            st.markdown(
                f"""
                <div class="card">
                    <h3>{r['ticker']}</h3>
                    <p><b>Price:</b> {r['price']}</p>
                    <p><b>Signal:</b> {r['signal']}</p>
                    <p><b>Regime:</b> {r['regime']}</p>
                    <p><b>Momentum:</b> {r['momentum']}</p>
                    <p><b>Volatility:</b> {r['volatility']}</p>
                    <p><b>Breakout:</b> {r['breakout']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.divider()

    # =========================
    # DEEP ANALYSIS PANEL
    # =========================
    st.markdown("### 📈 Deep Analysis")

    pick = st.selectbox("Select asset", [r["ticker"] for r in results])

    df = load(pick)

    if df is not None:
        df = add_indicators(df)

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], name="Price"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA20"], name="SMA20"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA50"], name="SMA50"))

        fig.update_layout(
            template="plotly_dark",
            height=500,
            paper_bgcolor="#05070A",
            plot_bgcolor="#05070A"
        )

        st.plotly_chart(fig, use_container_width=True)

        match = next(r for r in results if r["ticker"] == pick)

        st.markdown("### 🧠 Decision Output")

        st.markdown(f"""
        <div class="card">
            <h2>{match['signal']}</h2>
            <p><b>Regime:</b> {match['regime']}</p>
            <p><b>Score:</b> {match['score']}</p>
            <p><b>Momentum:</b> {match['momentum']}</p>
            <p><b>Volatility:</b> {match['volatility']}</p>
        </div>
        """, unsafe_allow_html=True)
