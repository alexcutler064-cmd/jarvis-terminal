def analyze(df):
    if df is None or len(df) < 90:
        return None

    df = indicators(df)
    last = df.iloc[-1]

    # =========================
    # FEATURES
    # =========================
    trend = 1 if last["SMA20"] > last["SMA50"] else -1
    ema_trend = 1 if last["Close"] > last["EMA20"] else -1

    momentum = last["RET5"] if not np.isnan(last["RET5"]) else 0
    volatility = last["VOL"] if not np.isnan(last["VOL"]) else 0

    breakout = last["Close"] > last["HIGH20"]

    volume_ok = False
    if not np.isnan(last["VOL_AVG"]):
        volume_ok = last["Volume"] > last["VOL_AVG"]

    # =========================
    # NORMALIZED SCORING (0–100)
    # =========================

    # trend agreement boost
    trend_score = 25 if trend == ema_trend else 10

    # momentum scaled safely
    momentum_score = np.clip(momentum * 200, -25, 25)  # caps noise

    # volatility penalty (risk control)
    vol_score = np.clip(30 - volatility * 800, 0, 30)

    # breakout strength
    breakout_score = 15 if breakout else 0

    # volume confirmation
    volume_score = 10 if volume_ok else 0

    raw_score = trend_score + momentum_score + vol_score + breakout_score + volume_score

    score = np.clip(raw_score, 0, 100)

    # =========================
    # CONFIDENCE MODEL
    # =========================

    agreement = (trend == ema_trend)
    stable_market = volatility < 0.03

    confidence = 0
    confidence += 40 if agreement else 20
    confidence += 30 if stable_market else 10
    confidence += 20 if volume_ok else 10
    confidence += 10 if breakout else 0

    confidence = np.clip(confidence, 0, 100)

    # =========================
    # REGIME
    # =========================
    if trend == 1 and momentum > 0:
        regime = "BULL"
    elif trend == -1 and momentum < 0:
        regime = "BEAR"
    else:
        regime = "CHOPPY"

    # =========================
    # SMART SIGNAL ENGINE
    # =========================

    if score > 75 and confidence > 70 and regime == "BULL":
        signal = "🟢 HIGH PROBABILITY SETUP"
    elif score > 60 and confidence > 50:
        signal = "🟡 VALID SETUP (LOWER QUALITY)"
    elif regime == "CHOPPY":
        signal = "🟡 NO EDGE (SKIP)"
    else:
        signal = "🔴 AVOID"

    return {
        "score": int(score),
        "confidence": int(confidence),
        "signal": signal,
        "regime": regime,
        "momentum": round(momentum, 4),
        "volatility": round(volatility, 4),
        "breakout": breakout,
        "volume_ok": volume_ok,
        "df": df
    }
