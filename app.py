import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# =========================
# PAGE SETUP
# =========================
st.set_page_config(page_title="Trading Decision Filter", layout="wide")

st.markdown("""
<style>
body { background-color: #05070A; color: #E6E6E6; }

.title {
    font-size: 40px;
    font-weight: 800;
    color: #00f5ff;
    text-shadow: 0 0 18px rgba(0,245,255,0.3);
}

.card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(0,245,255,0.15);
    padding: 14px;
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>TRADING DECISION FILTER PRO</div>", unsafe_allow_html=True)
st.caption("Signal filtering system — not financial advice")

# =========================
# INPUT
# =========================
tickers_input = st.text_input("Enter tickers (comma separated)", "AAPL, MSFT, NVDA, TSLA")
run = st.button("Analyze")

tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

# =========================
# DATA
# =========================
@st.cache_data(ttl=300)
def load(ticker):
    df = yf.Ticker(ticker).history(period="6mo")
    if df.empty:
        return None
    return df.reset_index()

def indicators(df):
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["RET5"] = df["Close"].pct_change(5)
    df["VOL"] = df["Close"].pct_change().rolling(10).std()
    df["HIGH20"] = df["Close"].rolling(20).max()
    df["VOL_AVG"] = df["Volume"].rolling(20).mean()
    return df

# =========================
# CORE ENGINE
# =========================
def analyze(df):
    if df is None or len(df) < 80:
        return None

    df = indicators(df)
    last = df.iloc[-1]

    trend_up = last["SMA20"] > last["SMA50"]
    momentum = last["RET5"] if not np.isnan(last["RET5"]) else 0
    vol = last["VOL"] if not np.isnan(last["VOL"]) else 0
    volume_ok = last["Volume"] > last["VOL_AVG"] if not np.isnan(last["VOL_AVG"]) else False
    breakout = last["Close"] > last["HIGH20"]

    # REGIME
    if trend_up and momentum > 0:
        regime = "BULL"
    elif not trend_up and momentum < 0:
        regime = "BEAR"
    else:
        regime = "CHOPPY"

    # SCORE (balanced, not overreactive)
    score = 0
    score += 2 if trend_up else -2
    score += momentum * 20
    score -= vol * 50
    score += 1 if breakout else 0
    score += 1 if volume_ok else 0

    # DECISION LOGIC (FILTER SYSTEM)
    if regime == "BULL" and breakout and volume_ok and vol < 0.03:
        signal = "🟢 HIGH QUALITY BREAKOUT (TRADE SETUP)"
    elif regime == "BULL" and volume_ok:
        signal = "🟡 TREND CONTINUATION (WATCH FOR ENTRY)"
    elif regime == "CHOPPY":
        signal = "🟡 NO EDGE (AVOID NEW TRADES)"
    else:
        signal = "🔴 RISK OFF"

    return {
        "score": round(score, 2),
        "signal": signal,
        "regime": regime,
        "momentum": round(momentum, 4),
        "volatility": round(vol, 4),
        "breakout": breakout,
        "volume_ok": volume_ok,
        "df": df
    }

# =========================
# RUN ANALYSIS
# =========================
if run:

    results = []
    st.markdown("### Scanning market conditions...")

    for t in tickers:

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
                "volume_ok": r["volume_ok"],
                "price": round(df["Close"].iloc[-1], 2)
            })

    if not results:
        st.error("No data")
        st.stop()

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    top = results[0]

    # =========================
    # SUMMARY
    # =========================
    c1, c2, c3 = st.columns(3)

    c1.markdown(f"<div class='card'><h3>TOP TICKER</h3><h2>{top['ticker']}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><h3>SCORE</h3><h2>{top['score']}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card'><h3>REGIME</h3><h2>{top['regime']}</h2></div>", unsafe_allow_html=True)

    st.divider()

    # =========================
    # GRID
    # =========================
    st.markdown("### Market Filter Results")

    cols = st.columns(3)

    for i, r in enumerate(results):

        with cols[i % 3]:

            st.markdown(f"""
            <div class='card'>
                <h3>{r['ticker']}</h3>
                <p><b>Price:</b> {r['price']}</p>
                <p><b>Signal:</b> {r['signal']}</p>
                <p><b>Score:</b> {r['score']}</p>
                <p><b>Momentum:</b> {r['momentum']}</p>
                <p><b>Volatility:</b> {r['volatility']}</p>
                <p><b>Breakout:</b> {r['breakout']}</p>
                <p><b>Volume Confirmed:</b> {r['volume_ok']}</p>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # =========================
    # DETAIL VIEW
    # =========================
    pick = st.selectbox("Deep analysis", [r["ticker"] for r in results])

    df = load(pick)

    if df is not None:
        df = indicators(df)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], name="Price"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA20"], name="SMA20"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA50"], name="SMA50"))

        fig.update_layout(template="plotly_dark", height=500)

        st.plotly_chart(fig, use_container_width=True)

        match = next(r for r in results if r["ticker"] == pick)

        st.markdown("### Decision Output")

        st.markdown(f"""
        <div class='card'>
            <h2>{match['signal']}</h2>
            <p><b>Regime:</b> {match['regime']}</p>
            <p><b>Score:</b> {match['score']}</p>
            <p><b>Momentum:</b> {match['momentum']}</p>
            <p><b>Volatility:</b> {match['volatility']}</p>
        </div>
        """, unsafe_allow_html=True)
