import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(
    page_title="JARVIS Terminal",
    layout="wide"
)

# =============================
# FUTURISTIC UI STYLE
# =============================
st.markdown("""
<style>
body {
    background-color: #05070f;
    color: #e6e6e6;
}

.block-container {
    padding-top: 1rem;
}

.title {
    font-size: 38px;
    font-weight: 700;
    color: #00ffd0;
    text-shadow: 0 0 15px rgba(0,255,208,0.3);
}

.card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(0,255,200,0.2);
    padding: 16px;
    border-radius: 14px;
    box-shadow: 0 0 20px rgba(0,255,200,0.08);
}

.small {
    opacity: 0.7;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>JARVIS Trading Terminal</div>", unsafe_allow_html=True)
st.caption("AI-style market intelligence system (local mode)")

# =============================
# SIDEBAR CONTROL PANEL
# =============================
st.sidebar.header("Control Panel")

tickers_input = st.sidebar.text_input(
    "Enter tickers",
    "AAPL, MSFT, NVDA, TSLA"
)

run = st.sidebar.button("Run Market Scan 🚀")

tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

# =============================
# DATA LOADER (SAFE)
# =============================
@st.cache_data(ttl=300)
def get_data(ticker):
    try:
        df = yf.Ticker(ticker).history(period="6mo")
        if df.empty:
            return None
        return df.reset_index()
    except:
        return None

# =============================
# INDICATORS
# =============================
def indicators(df):
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    return df

def sentiment_score(news):
    analyzer = SentimentIntensityAnalyzer()
    scores = []

    for n in news:
        title = n.get("title", "")
        scores.append(analyzer.polarity_scores(title)["compound"])

    return np.mean(scores) if scores else 0

# =============================
# SCORING ENGINE
# =============================
def score_stock(df):
    if df is None or len(df) < 50:
        return None

    df = indicators(df)
    last = df.iloc[-1]

    score = 0

    if last["SMA20"] > last["SMA50"]:
        score += 2

    momentum = df["Close"].pct_change(5).iloc[-1]
    score += float(momentum) * 10

    if last["Close"] > last["EMA20"]:
        score += 1

    label = (
        "🟢 STRONG"
        if score > 3
        else "🟡 NEUTRAL"
        if score > 1
        else "🔴 WEAK"
    )

    return score, label, df

# =============================
# MAIN APP
# =============================
if run:

    results = []

    st.markdown("### 🧠 JARVIS SYSTEM ONLINE")
    st.markdown("Scanning global markets...")

    progress = st.progress(0)

    for i, t in enumerate(tickers):

        df = get_data(t)

        if df is None:
            continue

        result = score_stock(df)

        if result is None:
            continue

        score, label, df = result

        results.append({
            "Ticker": t,
            "Score": round(score, 2),
            "Signal": label,
            "Price": round(df["Close"].iloc[-1], 2)
        })

        progress.progress(int((i+1)/len(tickers)*100))

    if not results:
        st.error("No valid stock data found.")
        st.stop()

    results_df = pd.DataFrame(results).sort_values("Score", ascending=False)

    # =============================
    # TOP DASHBOARD
    # =============================
    top = results_df.iloc[0]

    col1, col2, col3 = st.columns(3)

    col1.markdown(f"<div class='card'><h3>TOP ASSET</h3><p>{top['Ticker']}</p></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='card'><h3>SCORE</h3><p>{top['Score']}</p></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='card'><h3>STATUS</h3><p>{top['Signal']}</p></div>", unsafe_allow_html=True)

    st.divider()

    # =============================
    # TABLE
    # =============================
    st.subheader("📊 Market Rankings")
    st.dataframe(results_df, use_container_width=True, hide_index=True)

    # =============================
    # DETAIL VIEW
    # =============================
    st.subheader("📈 Asset Terminal")

    selected = st.selectbox("Select asset", results_df["Ticker"])

    df = get_data(selected)

    if df is not None:

        df = indicators(df)

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], name="Price"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA20"], name="SMA20"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA50"], name="SMA50"))

        fig.update_layout(
            template="plotly_dark",
            height=520,
            paper_bgcolor="#05070f",
            plot_bgcolor="#05070f"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 🧠 JARVIS Insight")

        try:
            news = yf.Ticker(selected).news
            sent = sentiment_score(news)

            st.metric("News Sentiment", round(sent, 2))

            if sent > 0.2:
                st.success("Positive market sentiment")
            elif sent < -0.2:
                st.error("Negative market sentiment")
            else:
                st.info("Neutral sentiment")

        except:
            st.info("News unavailable")
