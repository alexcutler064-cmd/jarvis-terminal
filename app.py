import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# =========================
# PAGE SETUP
# =========================
st.set_page_config(
    page_title="JARVIS Terminal v3",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# FUTURISTIC DARK THEME
# =========================
st.markdown("""
<style>

body {
    background-color: #05070A;
    color: #E6E6E6;
}

/* main spacing */
.block-container {
    padding: 1rem 1.8rem;
}

/* TOP TITLE */
.title {
    font-size: 42px;
    font-weight: 800;
    color: #00f5ff;
    text-shadow: 0 0 18px rgba(0,245,255,0.25);
    letter-spacing: 1px;
}

.sub {
    opacity: 0.6;
    margin-bottom: 20px;
}

/* GLASS PANEL */
.panel {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(0,245,255,0.12);
    border-radius: 14px;
    padding: 14px;
    box-shadow: 0 0 18px rgba(0,245,255,0.05);
}

/* BUTTONS */
.stButton > button {
    background: linear-gradient(90deg, #00f5ff, #6a5cff);
    color: black;
    font-weight: 700;
    border-radius: 10px;
    border: none;
}

.stButton > button:hover {
    transform: scale(1.02);
    box-shadow: 0 0 15px rgba(0,245,255,0.3);
}

/* TABLE */
.dataframe {
    background-color: #0b0f14 !important;
}

</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("<div class='title'>JARVIS TRADING TERMINAL</div>", unsafe_allow_html=True)
st.markdown("<div class='sub'>Market intelligence system • v3 core build</div>", unsafe_allow_html=True)

# =========================
# INPUT BAR
# =========================
colA, colB, colC = st.columns([2, 1, 1])

with colA:
    tickers_input = st.text_input("Enter tickers (comma separated)", "AAPL, MSFT, NVDA, TSLA")

with colB:
    scan = st.button("SCAN MARKET 🚀")

with colC:
    auto = st.checkbox("Live Scan Mode")

tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

# =========================
# DATA LOADER
# =========================
@st.cache_data(ttl=300)
def load_data(ticker):
    try:
        df = yf.Ticker(ticker).history(period="6mo")
        if df.empty:
            return None
        return df.reset_index()
    except:
        return None

# =========================
# INDICATORS
# =========================
def indicators(df):
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["RET5"] = df["Close"].pct_change(5)
    df["RET20"] = df["Close"].pct_change(20)
    return df

# =========================
# SCORING ENGINE (UPGRADED)
# =========================
def score_stock(df):
    if df is None or len(df) < 60:
        return None

    df = indicators(df)
    last = df.iloc[-1]

    score = 0

    # trend alignment
    if last["SMA20"] > last["SMA50"]:
        score += 2

    # price strength
    if last["Close"] > last["EMA20"]:
        score += 1

    # momentum
    if not np.isnan(last["RET5"]):
        score += last["RET5"] * 8

    if not np.isnan(last["RET20"]):
        score += last["RET20"] * 5

    # label system
    if score >= 4:
        label = "🟢 STRONG"
    elif score >= 2:
        label = "🟡 NEUTRAL"
    else:
        label = "🔴 WEAK"

    return score, label, df

# =========================
# RUN SCAN
# =========================
if scan or auto:

    results = []

    st.markdown("### 🧠 JARVIS CORE ONLINE")
    st.markdown("Scanning market structure...")

    progress = st.progress(0)

    for i, t in enumerate(tickers):

        df = load_data(t)
        result = score_stock(df)

        if result:
            score, label, df = result
            price = df["Close"].iloc[-1]

            results.append({
                "Ticker": t,
                "Score": round(score, 2),
                "Signal": label,
                "Price": round(price, 2)
            })

        progress.progress(int((i+1)/len(tickers)*100))

    if not results:
        st.error("No market data available.")
        st.stop()

    results_df = pd.DataFrame(results).sort_values("Score", ascending=False)

    # =========================
    # TOP SUMMARY BAR
    # =========================
    top = results_df.iloc[0]

    c1, c2, c3 = st.columns(3)

    c1.markdown(f"<div class='panel'><h3>TOP ASSET</h3><h2>{top['Ticker']}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='panel'><h3>SCORE</h3><h2>{top['Score']}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='panel'><h3>SIGNAL</h3><h2>{top['Signal']}</h2></div>", unsafe_allow_html=True)

    st.divider()

    # =========================
    # MAIN LAYOUT (3 PANEL SYSTEM)
    # =========================
    left, center, right = st.columns([1.2, 2.2, 1.2])

    # -------------------------
    # LEFT PANEL (WATCHLIST)
    # -------------------------
    with left:
        st.markdown("### 📡 Watch Node")
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.write("Tracked Assets")

        st.dataframe(results_df[["Ticker", "Score"]], hide_index=True, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------
    # CENTER PANEL (MARKET GRID)
    # -------------------------
    with center:
        st.markdown("### 📊 Market Intelligence Grid")

        st.dataframe(results_df, hide_index=True, use_container_width=True)

    # -------------------------
    # RIGHT PANEL (INSIGHT CORE)
    # -------------------------
    with right:
        st.markdown("### 🧠 Insight Core")
        st.markdown("<div class='panel'>", unsafe_allow_html=True)

        selected = st.selectbox("Analyze Asset", results_df["Ticker"])

        df = load_data(selected)

        if df is not None:
            df = indicators(df)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], name="Price"))
            fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA20"], name="SMA20"))
            fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA50"], name="SMA50"))

            fig.update_layout(
                template="plotly_dark",
                height=350,
                paper_bgcolor="#05070A",
                plot_bgcolor="#05070A"
            )

            st.plotly_chart(fig, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

# =========================
# IDLE STATE
# =========================
else:
    st.info("Enter tickers and press SCAN MARKET to activate JARVIS terminal.")
