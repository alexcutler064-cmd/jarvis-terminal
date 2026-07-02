import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="JARVIS Terminal PRO",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# FUTURISTIC UI
# =========================
st.markdown("""
<style>

body {
    background-color: #05070A;
    color: #E6E6E6;
}

/* top title */
.title {
    font-size: 42px;
    font-weight: 800;
    color: #00f5ff;
    text-shadow: 0 0 18px rgba(0,245,255,0.3);
}

/* sub text */
.sub {
    opacity: 0.6;
    margin-bottom: 10px;
}

/* glass tile */
.tile {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(0,245,255,0.12);
    border-radius: 16px;
    padding: 14px;
    box-shadow: 0 0 18px rgba(0,245,255,0.06);
}

/* strong tile glow */
.tile-strong {
    border: 1px solid rgba(0,255,160,0.4);
    box-shadow: 0 0 18px rgba(0,255,160,0.15);
}

/* weak tile glow */
.tile-weak {
    border: 1px solid rgba(255,80,80,0.3);
    box-shadow: 0 0 18px rgba(255,80,80,0.08);
}

/* button */
.stButton > button {
    background: linear-gradient(90deg, #00f5ff, #6a5cff);
    color: black;
    font-weight: 700;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("<div class='title'>JARVIS TRADING TERMINAL PRO</div>", unsafe_allow_html=True)
st.markdown("<div class='sub'>Live market intelligence system</div>", unsafe_allow_html=True)

# =========================
# INPUT BAR
# =========================
col1, col2, col3 = st.columns([2,1,1])

with col1:
    tickers_input = st.text_input("Enter tickers", "AAPL, MSFT, NVDA, TSLA")

with col2:
    run = st.button("SCAN MARKET")

tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

# =========================
# DATA
# =========================
@st.cache_data(ttl=300)
def get_data(ticker):
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
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["RET5"] = df["Close"].pct_change(5)
    return df

# =========================
# SCORING ENGINE (UPGRADED FEEL)
# =========================
def score(df):
    if df is None or len(df) < 60:
        return None

    df = add_indicators(df)
    last = df.iloc[-1]

    s = 0

    if last["SMA20"] > last["SMA50"]:
        s += 2

    if last["Close"] > last["EMA20"]:
        s += 1

    if not np.isnan(last["RET5"]):
        s += last["RET5"] * 10

    if s >= 4:
        label = "STRONG"
    elif s >= 2:
        label = "NEUTRAL"
    else:
        label = "WEAK"

    return s, label, df

# =========================
# SCAN
# =========================
if run:

    st.markdown("### 🧠 JARVIS SCANNING SYSTEM INITIATED")

    progress = st.progress(0)

    results = []

    for i, t in enumerate(tickers):

        df = get_data(t)
        result = score(df)

        if result:
            s, label, df = result
            price = df["Close"].iloc[-1]

            results.append({
                "ticker": t,
                "score": round(s,2),
                "label": label,
                "price": round(price,2)
            })

        # fake smooth scan feel
        progress.progress((i+1)/len(tickers))
        time.sleep(0.1)

    if not results:
        st.error("No data available")
        st.stop()

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    top = results[0]

    # =========================
    # TOP STRIP
    # =========================
    c1, c2, c3 = st.columns(3)

    c1.markdown(f"<div class='tile tile-strong'><h3>TOP ASSET</h3><h2>{top['ticker']}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='tile'><h3>SCORE</h3><h2>{top['score']}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='tile'><h3>SIGNAL</h3><h2>{top['label']}</h2></div>", unsafe_allow_html=True)

    st.divider()

    # =========================
    # MARKET TILES (THIS IS THE BIG UPGRADE)
    # =========================
    st.markdown("### 📊 Market Grid")

    cols = st.columns(4)

    for i, r in enumerate(results):

        style = "tile"
        if r["label"] == "STRONG":
            style = "tile tile-strong"
        elif r["label"] == "WEAK":
            style = "tile tile-weak"

        with cols[i % 4]:
            st.markdown(
                f"""
                <div class="{style}">
                    <h4>{r['ticker']}</h4>
                    <p>Price: {r['price']}</p>
                    <p>Score: {r['score']}</p>
                    <p>{r['label']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.divider()

    # =========================
    # DETAIL VIEW
    # =========================
    st.markdown("### 📈 Deep Analysis Panel")

    pick = st.selectbox("Select asset", [r["ticker"] for r in results])

    df = get_data(pick)

    if df is not None:
        df = add_indicators(df)

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], name="Price"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA20"], name="SMA20"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA50"], name="SMA50"))

        fig.update_layout(
            template="plotly_dark",
            height=450,
            paper_bgcolor="#05070A",
            plot_bgcolor="#05070A"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 🧠 JARVIS OUTPUT")

        if top["ticker"] == pick:
            st.success("Top-ranked asset in current scan")
        elif top["score"] - next(r["score"] for r in results if r["ticker"] == pick) > 1:
            st.warning("Below market leaders")
        else:
            st.info("Neutral positioning in current structure")
