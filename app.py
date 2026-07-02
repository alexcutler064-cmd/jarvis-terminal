import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="JARVIS Strategy Engine", layout="wide")

st.markdown("""
<style>
body { background-color: #05070A; color: #E6E6E6; }

.title {
    font-size: 42px;
    font-weight: 800;
    color: #00f5ff;
}

.card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(0,245,255,0.15);
    padding: 14px;
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>JARVIS STRATEGY ENGINE</div>", unsafe_allow_html=True)
st.caption("Backtest + decision filter system (not financial advice)")

# =========================
# INPUT
# =========================
tickers_input = st.text_input("Tickers", "AAPL, MSFT, NVDA, TSLA")
run = st.button("Run Strategy")

tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

# =========================
# DATA
# =========================
@st.cache_data(ttl=300)
def load(ticker):
    df = yf.Ticker(ticker).history(period="1y")
    if df.empty:
        return None
    return df.reset_index()

def indicators(df):
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["RET5"] = df["Close"].pct_change(5)
    df["VOL"] = df["Close"].pct_change().rolling(10).std()
    return df

# =========================
# STRATEGY LOGIC
# =========================
def generate_signals(df):
    df = indicators(df)

    signals = []

    for i in range(60, len(df)):
        row = df.iloc[i]

        if np.isnan(row["SMA20"]) or np.isnan(row["SMA50"]):
            continue

        trend = row["SMA20"] > row["SMA50"]
        momentum = row["RET5"] if not np.isnan(row["RET5"]) else 0
        vol = row["VOL"] if not np.isnan(row["VOL"]) else 0

        buy = trend and momentum > 0 and vol < 0.03

        signals.append({
            "date": row["Date"],
            "close": row["Close"],
            "buy": buy
        })

    return pd.DataFrame(signals)

# =========================
# BACKTEST ENGINE
# =========================
def backtest(signals):
    position = 0
    entry = 0
    equity = 10000
    equity_curve = []

    wins = 0
    trades = 0

    for i in range(len(signals)):
        price = signals.iloc[i]["close"]
        buy = signals.iloc[i]["buy"]

        if buy and position == 0:
            position = 1
            entry = price
            trades += 1

        elif position == 1:
            change = (price - entry) / entry

            # exit rule (simple)
            if change > 0.05 or change < -0.03:
                equity *= (1 + change)
                equity_curve.append(equity)

                if change > 0:
                    wins += 1

                position = 0

    win_rate = wins / trades if trades > 0 else 0

    return {
        "equity": equity,
        "win_rate": win_rate,
        "trades": trades,
        "curve": equity_curve
    }

# =========================
# RUN
# =========================
if run:

    st.markdown("### Running strategy backtest...")

    results = []

    for t in tickers:

        df = load(t)

        if df is None:
            continue

        signals = generate_signals(df)
        stats = backtest(signals)

        results.append({
            "ticker": t,
            "final_equity": round(stats["equity"], 2),
            "win_rate": round(stats["win_rate"] * 100, 2),
            "trades": stats["trades"]
        })

    results = sorted(results, key=lambda x: x["final_equity"], reverse=True)

    st.markdown("### Strategy Results")

    for r in results:
        st.markdown(f"""
        <div class="card">
            <h3>{r['ticker']}</h3>
            <p><b>Final Equity:</b> ${r['final_equity']}</p>
            <p><b>Win Rate:</b> {r['win_rate']}%</p>
            <p><b>Trades:</b> {r['trades']}</p>
        </div>
        """, unsafe_allow_html=True)

    # =========================
    # EQUITY CURVE (BEST TICKER)
    # =========================
    best = results[0]["ticker"]

    df = load(best)
    signals = generate_signals(df)
    stats = backtest(signals)

    if stats["curve"]:
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=stats["curve"], name="Equity Curve"))
        fig.update_layout(template="plotly_dark", height=400)

        st.markdown("### Equity Curve (Best Strategy)")
        st.plotly_chart(fig, use_container_width=True)
