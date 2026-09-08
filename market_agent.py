import json
import math
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf
from supabase import create_client

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def sb_data(resp):
    return getattr(resp, "data", None) or []


def indicators(df):
    x = df.copy()
    c, h, l, v = x["Close"], x["High"], x["Low"], x["Volume"]
    x["SMA20"] = c.rolling(20).mean()
    x["SMA50"] = c.rolling(50).mean()
    x["SMA200"] = c.rolling(200).mean()
    x["EMA12"] = c.ewm(span=12, adjust=False).mean()
    x["EMA26"] = c.ewm(span=26, adjust=False).mean()
    x["MACD"] = x["EMA12"] - x["EMA26"]
    x["MACD_SIGNAL"] = x["MACD"].ewm(span=9, adjust=False).mean()
    d = c.diff()
    gain = d.clip(lower=0).rolling(14).mean()
    loss = (-d.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    x["RSI"] = 100 - (100 / (1 + rs))
    tr = pd.concat([(h-l),(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    x["ATR"] = tr.rolling(14).mean()
    x["VOL20"] = v.rolling(20).mean()
    x["ROC20"] = c.pct_change(20) * 100
    return x.dropna(subset=["SMA20","SMA50","ATR","RSI"])


def trade_setup(df):
    if df is None or df.empty:
        return None
    x = indicators(df)
    if len(x) < 55:
        return None
    r = x.iloc[-1]
    price = float(r["Close"])
    atr = float(r["ATR"])
    recent = x.tail(min(120, len(x)))
    support = min(float(recent["Low"].quantile(.15)), price - .8 * atr)
    support = max(support, price - 4 * atr)
    resistance = max(float(recent["High"].quantile(.85)), price + 1.5 * atr)
    entry = min(price, max(support + .2 * atr, price - .35 * atr))
    stop = min(support - .25 * atr, entry - atr)
    risk = max(entry - stop, .01 * price)
    tp1 = min(resistance, entry + 1.5 * risk)
    tp2 = min(resistance, entry + 2.8 * risk)
    upside = (tp2 / entry - 1) * 100
    rr = (tp2 - entry) / risk if risk else 0

    score = 50
    reasons = []
    if price > r["SMA20"]:
        score += 10; reasons.append("prix > SMA20")
    else:
        score -= 8
    if r["SMA20"] > r["SMA50"]:
        score += 12; reasons.append("SMA20 > SMA50")
    else:
        score -= 10
    if not pd.isna(r["SMA200"]):
        score += 8 if price > r["SMA200"] else -8
    if 45 <= r["RSI"] <= 68:
        score += 8; reasons.append("RSI exploitable")
    elif r["RSI"] > 75:
        score -= 8
    if r["MACD"] > r["MACD_SIGNAL"]:
        score += 10; reasons.append("MACD haussier")
    else:
        score -= 8
    if r["ROC20"] > 0:
        score += 7; reasons.append("momentum positif")
    vol_ratio = float(r["Volume"] / r["VOL20"]) if r["VOL20"] else 1.0
    if vol_ratio >= 1.25:
        score += 5; reasons.append("volume supérieur à la moyenne")

    return {
        "price": price, "entry": entry, "stop": stop, "tp1": tp1, "tp2": tp2,
        "upside": upside, "rr": rr, "score": int(np.clip(score,0,100)),
        "reasons": reasons, "rsi": float(r["RSI"]), "vol_ratio": vol_ratio
    }


def history(symbol, period="6mo", interval="1d"):
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False)
        if df is None or df.empty:
            return None
        return df.dropna(subset=["Open","High","Low","Close"])
    except Exception:
        return None


def universe():
    try:
        rows = sb_data(
            sb.table("broker_universe")
            .select("symbol,name,market,broker,enabled")
            .eq("enabled", True)
            .execute()
        )
        if rows:
            return pd.DataFrame(rows)
    except Exception:
        pass
    return pd.DataFrame()


def positions():
    try:
        return pd.DataFrame(sb_data(
            sb.table("portfolio_positions")
            .select("account,broker,ticker,isin,name,quantity,pru,instrument_key")
            .execute()
        ))
    except Exception:
        return pd.DataFrame()


def recent_duplicate(symbol, alert_type, fingerprint):
    try:
        rows = sb_data(
            sb.table("market_alerts")
            .select("id")
            .eq("symbol", symbol)
            .eq("alert_type", alert_type)
            .eq("fingerprint", fingerprint)
            .limit(1)
            .execute()
        )
        return bool(rows)
    except Exception:
        return False


def ai_context(symbol, technical, position_context=None):
    if not OPENAI_API_KEY or OpenAI is None:
        return {
            "headline": "",
            "analysis": "Analyse technique automatique uniquement : " + ", ".join(technical["reasons"]),
            "news_risk": "UNKNOWN",
        }

    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""
Tu es l'agent d'actualité de VISION FUTURE.
Instrument: {symbol}
Données techniques: {json.dumps(technical, ensure_ascii=False)}
Contexte position: {json.dumps(position_context or {}, ensure_ascii=False)}

Recherche l'actualité mondiale récente susceptible d'affecter cet instrument:
entreprise, secteur, macro, banques centrales, géopolitique, résultats.
Réponds en français en JSON strict avec exactement:
{{
  "headline": "résumé factuel très court",
  "analysis": "2 à 5 phrases expliquant si l'actualité renforce, neutralise ou dégrade le setup",
  "news_risk": "LOW|MEDIUM|HIGH"
}}
Ne présente jamais le résultat comme garanti.
"""
    try:
        resp = client.responses.create(
            model=OPENAI_MODEL,
            tools=[{"type": "web_search"}],
            input=prompt,
            store=False,
        )
        raw = resp.output_text.strip()
        raw = raw[raw.find("{"): raw.rfind("}")+1]
        return json.loads(raw)
    except Exception as exc:
        return {
            "headline": "",
            "analysis": f"Actualité non disponible lors de ce cycle. Analyse technique: {', '.join(technical['reasons'])}.",
            "news_risk": "UNKNOWN",
        }


def create_alert(symbol, alert_type, broker, market, setup, ai, fingerprint):
    if recent_duplicate(symbol, alert_type, fingerprint):
        return False

    payload = {
        "symbol": symbol,
        "alert_type": alert_type,
        "broker": broker or "",
        "market": market or "",
        "score": setup.get("score"),
        "entry": setup.get("entry"),
        "stop": setup.get("stop"),
        "tp1": setup.get("tp1"),
        "tp2": setup.get("tp2"),
        "upside": setup.get("upside"),
        "rr": setup.get("rr"),
        "headline": ai.get("headline",""),
        "analysis": ai.get("analysis",""),
        "news_risk": ai.get("news_risk","UNKNOWN"),
        "status": "NEW",
        "fingerprint": fingerprint,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    sb.table("market_alerts").insert(payload).execute()
    return True


def run():
    uni = universe()
    pos = positions()
    created = 0

    # 1) Existing positions: exits / protection alerts.
    if not pos.empty:
        for _, p in pos.iterrows():
            symbol = str(p.get("ticker") or "").strip().upper()
            if not symbol:
                continue
            daily = trade_setup(history(symbol, "6mo", "1d"))
            hourly = trade_setup(history(symbol, "3mo", "1h"))
            if not daily:
                continue

            qty = float(p.get("quantity") or 0)
            pru = float(p.get("pru") or 0)
            price = daily["price"]
            deterioration = (
                daily["score"] < 58
                or (hourly and hourly["score"] < 52)
                or (pru > 0 and price < pru * 0.94)
            )
            protection = (
                pru > 0 and price > pru * 1.03
                and hourly and hourly["score"] < 58
            )
            if not (deterioration or protection):
                continue

            ctx = {"quantity": qty, "pru": pru, "price": price}
            ai = ai_context(symbol, daily, ctx)
            fingerprint = f"POSITION:{symbol}:{round(price,2)}:{daily['score']}:{ai.get('news_risk')}"
            if create_alert(symbol, "POSITION", p.get("broker",""), "", daily, ai, fingerprint):
                created += 1

    # 2) New entries: broad compatible universe.
    if not uni.empty:
        # Limit deep per-cycle work. Universe can be large, but only strong daily setups reach AI.
        candidates = []
        for _, u in uni.iterrows():
            symbol = str(u.get("symbol") or "").strip().upper()
            if not symbol:
                continue
            s = trade_setup(history(symbol, "6mo", "1d"))
            if not s:
                continue
            if s["upside"] >= 3.0 and s["rr"] >= 2.0 and s["score"] >= 76:
                candidates.append((symbol, u, s))

        candidates.sort(key=lambda x: (x[2]["score"], x[2]["rr"], x[2]["upside"]), reverse=True)
        for symbol, u, daily in candidates[:12]:
            hourly = trade_setup(history(symbol, "3mo", "1h"))
            if not hourly or hourly["score"] < 65:
                continue

            ai = ai_context(symbol, daily)
            # Do not emit ENTRY when world/news context is explicitly high-risk.
            if ai.get("news_risk") == "HIGH":
                continue

            fingerprint = f"ENTRY:{symbol}:{round(daily['entry'],2)}:{round(daily['stop'],2)}:{daily['score']}:{ai.get('news_risk')}"
            if create_alert(
                symbol, "ENTRY", u.get("broker",""), u.get("market",""),
                daily, ai, fingerprint
            ):
                created += 1

    sb.table("agent_runs").insert({
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "created_alerts": created,
        "status": "OK"
    }).execute()
    print(f"VISION FUTURE agent: {created} alert(s) created.")


if __name__ == "__main__":
    run()
