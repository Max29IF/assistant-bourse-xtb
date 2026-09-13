"""VISION FUTURE V38 — crypto engine independent from R/R.

This module wraps the stable market_agent_core worker and changes only the
crypto decision engine. Equity/ETF rules remain untouched.
"""

import numpy as np
import pandas as pd

import market_agent_core as base


CRYPTO_MIN_SCORE = 68

_orig_history = base.history
_orig_trade_setup = base.trade_setup
_orig_setup_confidence = base.setup_confidence
_orig_candidate_rank = base.candidate_rank
_orig_enriched_analysis = base.enriched_analysis
_orig_create_alert = base.create_alert


def _is_crypto_symbol(symbol):
    s = base.clean_symbol(symbol)
    return s.endswith(("-USD", "-EUR"))


def history(symbol, period="6mo", interval="1d"):
    """Preserve the symbol on the dataframe so trade_setup knows the asset class."""
    df = _orig_history(symbol, period, interval)
    if df is not None:
        try:
            df.attrs["vf_symbol"] = base.clean_symbol(symbol)
        except Exception:
            pass
    return df


def crypto_setup(df):
    """Crypto score: trend + momentum + RSI + MACD + volatility + volume.

    R/R and minimum upside are not decision criteria. `rr` and `upside` are
    neutral internal sentinels only because the legacy run loop still reads
    those two keys. They are stripped/restored before an alert is persisted.
    """
    if df is None or getattr(df, "empty", True) or len(df) < 60:
        return None

    x = base.indicators(df)
    if x is None or len(x) < 40:
        return None

    r = x.iloc[-1]
    price = float(r["Close"])
    atr = float(r["ATR"])
    if not np.isfinite(price) or price <= 0 or not np.isfinite(atr) or atr <= 0:
        return None

    sma20 = float(r["SMA20"])
    sma50 = float(r["SMA50"])
    sma200 = float(r["SMA200"]) if pd.notna(r.get("SMA200")) else np.nan
    rsi = float(r["RSI"])
    roc20 = float(r["ROC20"]) if pd.notna(r.get("ROC20")) else 0.0
    macd = float(r["MACD"])
    macd_signal = float(r["MACD_SIGNAL"])
    atr_pct = atr / price * 100.0

    closes = pd.to_numeric(x["Close"], errors="coerce")
    volumes = pd.to_numeric(x["Volume"], errors="coerce")

    def momentum(back):
        if len(closes) <= back:
            return np.nan
        prev = float(closes.iloc[-(back + 1)])
        return ((price / prev) - 1.0) * 100.0 if prev > 0 else np.nan

    mom_1 = momentum(1)
    mom_7 = momentum(7)
    mom_30 = momentum(30)

    vol20 = float(r["VOL20"]) if pd.notna(r.get("VOL20")) else np.nan
    current_volume = float(volumes.iloc[-1]) if len(volumes) else np.nan
    vol_ratio = (
        current_volume / vol20
        if np.isfinite(current_volume) and np.isfinite(vol20) and vol20 > 0
        else 1.0
    )

    distance_sma20 = ((price / sma20) - 1.0) * 100.0 if sma20 > 0 else np.nan
    recent = x.tail(min(30, len(x)))
    high_30 = float(pd.to_numeric(recent["High"], errors="coerce").max())
    drawdown_30 = ((price / high_30) - 1.0) * 100.0 if high_30 > 0 else np.nan

    score = 50
    reasons, risks = [], []

    if price > sma20:
        score += 10; reasons.append("prix > SMA20")
    else:
        score -= 10; risks.append("prix sous SMA20")

    if sma20 > sma50:
        score += 12; reasons.append("SMA20 > SMA50")
    else:
        score -= 10; risks.append("SMA20 sous SMA50")

    if np.isfinite(sma200):
        if price > sma200:
            score += 6; reasons.append("prix > SMA200")
        else:
            score -= 6; risks.append("prix sous SMA200")

    if np.isfinite(mom_7):
        if mom_7 >= 5:
            score += 10; reasons.append("momentum court fort")
        elif mom_7 > 0:
            score += 5; reasons.append("momentum court positif")
        elif mom_7 <= -8:
            score -= 10; risks.append("momentum court négatif")

    if roc20 > 0:
        score += 8; reasons.append("ROC20 positif")
    else:
        score -= 6; risks.append("ROC20 négatif")

    if 48 <= rsi <= 70:
        score += 8; reasons.append("RSI constructif")
    elif 40 <= rsi < 48:
        score += 2
    elif rsi > 78:
        score -= 10; risks.append("RSI très tendu")
    elif rsi < 35:
        score -= 8; risks.append("RSI faible")

    if macd > macd_signal:
        score += 9; reasons.append("MACD haussier")
    else:
        score -= 7; risks.append("MACD baissier")

    if 2 <= atr_pct <= 10:
        score += 6; reasons.append("volatilité exploitable")
    elif atr_pct > 15:
        score -= 8; risks.append("volatilité extrême")
    elif atr_pct < 1:
        score -= 3

    if vol_ratio >= 1.35:
        score += 7; reasons.append("volume renforcé")
    elif vol_ratio < 0.65:
        score -= 4; risks.append("volume faible")

    if np.isfinite(distance_sma20) and distance_sma20 > 15:
        score -= 7; risks.append("extension forte au-dessus SMA20")
    if np.isfinite(drawdown_30) and drawdown_30 > -3 and rsi > 72:
        score -= 5; risks.append("proche plus haut récent + RSI élevé")

    score = int(np.clip(score, 0, 100))
    signal = (
        "ACCELERATION" if score >= 82 else
        "HAUSSIER" if score >= 72 else
        "SURVEILLANCE" if score >= 62 else
        "FAIBLE"
    )

    # ATR levels remain informative only.
    entry = price
    stop = max(price - 1.8 * atr, price * 0.70)
    tp1 = price + 1.5 * atr
    tp2 = price + 3.0 * atr
    display_upside = ((tp2 / entry) - 1.0) * 100.0 if entry > 0 else None

    return {
        "price": price,
        "entry": entry,
        "stop": stop,
        "tp1": tp1,
        "tp2": tp2,
        # Neutral legacy sentinels: constant for every crypto, therefore they
        # cannot select/rank one crypto against another.
        "upside": 0.0,
        "rr": float(base.MIN_RR),
        "display_upside": display_upside,
        "asset_class": "CRYPTO",
        "score": score,
        "signal": signal,
        "reasons": reasons,
        "risks": risks,
        "rsi": rsi,
        "vol_ratio": vol_ratio,
        "atr_pct": atr_pct,
        "mom_1": mom_1,
        "mom_7": mom_7,
        "mom_30": mom_30,
        "distance_sma20": distance_sma20,
        "drawdown_30": drawdown_30,
    }


def trade_setup(df):
    symbol = ""
    try:
        symbol = base.clean_symbol(df.attrs.get("vf_symbol"))
    except Exception:
        pass
    if _is_crypto_symbol(symbol):
        return crypto_setup(df)
    return _orig_trade_setup(df)


def setup_confidence(daily, hourly=None, news_risk="UNAVAILABLE"):
    if not daily or daily.get("asset_class") != "CRYPTO":
        return _orig_setup_confidence(daily, hourly, news_risk)

    score = float(daily.get("score", 0))
    if hourly:
        score = score * 0.72 + float(hourly.get("score", 0)) * 0.28

    vol_ratio = float(daily.get("vol_ratio", 1.0) or 1.0)
    if vol_ratio >= 1.35:
        score += 3

    mom7 = daily.get("mom_7")
    if mom7 is not None and np.isfinite(mom7):
        if mom7 > 5:
            score += 3
        elif mom7 < -8:
            score -= 5

    risk = str(news_risk or "").upper()
    if risk == "HIGH":
        score -= 30
    elif risk == "MEDIUM":
        score -= 10
    elif risk == "LOW":
        score += 2

    return int(np.clip(round(score), 0, 100))


def candidate_rank(daily, hourly, regime_state):
    if not daily or daily.get("asset_class") != "CRYPTO":
        return _orig_candidate_rank(daily, hourly, regime_state)

    hscore = float(hourly.get("score", 0)) if hourly else 0.0
    mom7 = daily.get("mom_7")
    mom7 = float(mom7) if mom7 is not None and np.isfinite(mom7) else 0.0
    vol_ratio = float(daily.get("vol_ratio", 1.0) or 1.0)
    atr_pct = float(daily.get("atr_pct", 0.0) or 0.0)

    rank = (
        float(daily.get("score", 0)) * 0.62
        + hscore * 0.25
        + np.clip(mom7, -15, 20) * 0.35
        + min(max(vol_ratio, 0), 2.0) * 3.0
    )
    if 2 <= atr_pct <= 10:
        rank += 2
    elif atr_pct > 15:
        rank -= 4
    if regime_state == "RISK_ON":
        rank += 3
    elif regime_state == "RISK_OFF":
        rank -= 4
    return round(float(rank), 2)


def enriched_analysis(base_ai, daily, hourly, regime, confidence):
    if not daily or daily.get("asset_class") != "CRYPTO":
        return _orig_enriched_analysis(base_ai, daily, hourly, regime, confidence)

    ai = dict(base_ai or {})
    mom7 = daily.get("mom_7")
    mom7_text = f"{mom7:+.1f} %" if mom7 is not None and np.isfinite(mom7) else "—"
    technical = (
        f"Moteur crypto indépendant du R/R : score journalier {daily.get('score','—')}/100, "
        f"confirmation 1H {hourly.get('score','—') if hourly else '—'}/100, "
        f"momentum court {mom7_text}, RSI {daily.get('rsi',0):.1f}, "
        f"ATR {daily.get('atr_pct',0):.1f} %, volume x{daily.get('vol_ratio',1):.2f}. "
        f"Régime global {regime.get('state','NEUTRAL')}. "
        f"Confiance composite {confidence}/100. "
        "Les niveaux d'invalidation et d'objectif sont des repères ATR, pas un filtre R/R."
    )
    current = str(ai.get("analysis") or "").strip()
    ai["analysis"] = (technical + (" " + current if current else ""))[:3000]
    return ai


def create_alert(
    symbol, alert_type, broker, market, setup, ai, event_key,
    name="", isin="", user_id=None, asset_class="EQUITY",
):
    # Never persist the neutral legacy R/R sentinel used internally by base.run.
    clean_setup = dict(setup or {})
    if asset_class == "CRYPTO" or clean_setup.get("asset_class") == "CRYPTO":
        clean_setup["rr"] = None
        clean_setup["upside"] = clean_setup.get("display_upside")
    return _orig_create_alert(
        symbol, alert_type, broker, market, clean_setup, ai, event_key,
        name=name, isin=isin, user_id=user_id, asset_class=asset_class,
    )


def install_crypto_engine():
    # Daily crypto gate is score-only. `upside=0` and `rr=MIN_RR` are constants
    # used solely to pass legacy reads in base.run and have no ranking effect.
    base.CRYPTO_MIN_UPSIDE = 0.0
    base.CRYPTO_MIN_ENTRY_SCORE = CRYPTO_MIN_SCORE

    base.history = history
    base.trade_setup = trade_setup
    base.setup_confidence = setup_confidence
    base.candidate_rank = candidate_rank
    base.enriched_analysis = enriched_analysis
    base.create_alert = create_alert

    # The base loop keeps its existing 1H confirmation threshold.


def run():
    install_crypto_engine()
    print(
        "VISION FUTURE V38 — Crypto engine active | "
        f"min_score={CRYPTO_MIN_SCORE} | R/R gate=OFF | upside gate=OFF"
    )
    return base.run()
