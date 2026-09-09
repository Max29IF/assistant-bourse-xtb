import json
import os
from datetime import datetime, timezone, timedelta

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

MIN_UPSIDE = 3.0
MIN_RR = 2.0
MIN_ENTRY_SCORE = 76
MIN_HOURLY_SCORE = 65
ALERT_TYPES = {"ENTRY", "EXIT", "TAKE_PROFIT", "PROTECT", "RISK", "NEWS_RISK", "INVALIDATED"}

sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
diagnostics = []


def sb_data(resp):
    return getattr(resp, "data", None) or []


def clean_symbol(value):
    if value is None:
        return ""
    s = str(value).strip().upper()
    if s in {"", "NAN", "NONE", "NULL", "<NA>", "N/A"}:
        return ""
    return s


def fnum(value, default=0.0):
    try:
        x = float(value)
        return x if np.isfinite(x) else default
    except Exception:
        return default


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
    tr = pd.concat([(h-l), (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    x["ATR"] = tr.rolling(14).mean()
    x["VOL20"] = v.rolling(20).mean()
    x["ROC20"] = c.pct_change(20) * 100
    return x.dropna(subset=["SMA20", "SMA50", "ATR", "RSI"])


def trade_setup(df):
    if df is None or df.empty:
        return None
    x = indicators(df)
    if len(x) < 55:
        return None
    r = x.iloc[-1]
    price, atr = float(r["Close"]), float(r["ATR"])
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

    score, reasons = 50, []
    if price > r["SMA20"]: score += 10; reasons.append("prix > SMA20")
    else: score -= 8
    if r["SMA20"] > r["SMA50"]: score += 12; reasons.append("SMA20 > SMA50")
    else: score -= 10
    if not pd.isna(r["SMA200"]): score += 8 if price > r["SMA200"] else -8
    if 45 <= r["RSI"] <= 68: score += 8; reasons.append("RSI exploitable")
    elif r["RSI"] > 75: score -= 8
    if r["MACD"] > r["MACD_SIGNAL"]: score += 10; reasons.append("MACD haussier")
    else: score -= 8
    if r["ROC20"] > 0: score += 7; reasons.append("momentum positif")
    vol_ratio = float(r["Volume"] / r["VOL20"]) if r["VOL20"] else 1.0
    if vol_ratio >= 1.25: score += 5; reasons.append("volume supérieur à la moyenne")

    return {
        "price": price, "entry": entry, "stop": stop, "tp1": tp1, "tp2": tp2,
        "upside": upside, "rr": rr, "score": int(np.clip(score, 0, 100)),
        "reasons": reasons, "rsi": float(r["RSI"]), "vol_ratio": vol_ratio
    }


def history(symbol, period="6mo", interval="1d"):
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False)
        if df is None or df.empty:
            return None
        return df.dropna(subset=["Open", "High", "Low", "Close"])
    except Exception as exc:
        diagnostics.append(f"market_data:{symbol}:{type(exc).__name__}")
        return None


def universe():
    try:
        rows = sb_data(sb.table("broker_universe").select("symbol,name,isin,market,broker,enabled").eq("enabled", True).execute())
        return pd.DataFrame(rows)
    except Exception as exc:
        diagnostics.append(f"universe:{type(exc).__name__}:{str(exc)[:180]}")
        return pd.DataFrame()


def positions():
    try:
        rows = sb_data(sb.table("portfolio_positions").select("account,broker,ticker,isin,name,quantity,pru,instrument_key").execute())
        return pd.DataFrame(rows)
    except Exception as exc:
        diagnostics.append(f"positions:{type(exc).__name__}:{str(exc)[:180]}")
        return pd.DataFrame()


def get_state(symbol, scope):
    try:
        rows = sb_data(sb.table("market_agent_state").select("*").eq("symbol", symbol).eq("scope", scope).limit(1).execute())
        return rows[0] if rows else None
    except Exception as exc:
        diagnostics.append(f"state_read:{symbol}:{type(exc).__name__}")
        return None


def save_state(symbol, scope, state, score=None, price=None):
    payload = {
        "symbol": symbol, "scope": scope, "state": state,
        "score": score, "price": price, "updated_at": datetime.now(timezone.utc).isoformat()
    }
    sb.table("market_agent_state").upsert(payload, on_conflict="symbol,scope").execute()


def recent_event(symbol, alert_type, hours=24):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    try:
        rows = sb_data(
            sb.table("market_alerts").select("id")
            .eq("symbol", symbol).eq("alert_type", alert_type)
            .gte("created_at", cutoff).limit(1).execute()
        )
        return bool(rows)
    except Exception:
        return False


def ai_context(symbol, technical, position_context=None):
    if not OPENAI_API_KEY:
        diagnostics.append("openai:OPENAI_API_KEY missing")
        return {"headline": "", "analysis": "", "news_risk": "UNAVAILABLE"}
    if OpenAI is None:
        diagnostics.append("openai:python package unavailable")
        return {"headline": "", "analysis": "", "news_risk": "UNAVAILABLE"}

    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""
Tu es le filtre d'actualité de VISION FUTURE.
Instrument: {symbol}
Technique: {json.dumps(technical, ensure_ascii=False)}
Position: {json.dumps(position_context or {}, ensure_ascii=False)}

Recherche sur le web les actualités récentes réellement susceptibles d'affecter cet instrument
(entreprise, résultats, secteur, macro, banque centrale, réglementation, géopolitique).
Retourne UNIQUEMENT un objet JSON valide:
{{"headline":"résumé factuel court","analysis":"2 à 4 phrases","news_risk":"LOW|MEDIUM|HIGH"}}
LOW = pas de risque d'actualité significatif identifié.
MEDIUM = incertitude notable.
HIGH = événement susceptible d'invalider fortement le signal.
"""
    try:
        resp = client.responses.create(
            model=OPENAI_MODEL,
            tools=[{"type": "web_search"}],
            input=prompt,
            store=False,
        )
        raw = (resp.output_text or "").strip()
        start, end = raw.find("{"), raw.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("JSON absent de la réponse")
        data = json.loads(raw[start:end+1])
        risk = str(data.get("news_risk", "")).upper()
        if risk not in {"LOW", "MEDIUM", "HIGH"}:
            raise ValueError(f"news_risk invalide: {risk}")
        return {
            "headline": str(data.get("headline", ""))[:500],
            "analysis": str(data.get("analysis", ""))[:3000],
            "news_risk": risk,
        }
    except Exception as exc:
        diagnostics.append(f"openai:{symbol}:{type(exc).__name__}:{str(exc)[:240]}")
        return {"headline": "", "analysis": "", "news_risk": "UNAVAILABLE"}


def create_alert(symbol, alert_type, broker, market, setup, ai, event_key, name="", isin=""):
    if alert_type not in ALERT_TYPES or not symbol:
        return False
    # Stable event key: never contains price or score.
    fingerprint = f"V10:{alert_type}:{symbol}:{event_key}"
    try:
        rows = sb_data(sb.table("market_alerts").select("id").eq("fingerprint", fingerprint).limit(1).execute())
        if rows:
            return False
        payload = {
            "symbol": symbol, "name": name or "", "isin": isin or "",
            "alert_type": alert_type, "broker": broker or "", "market": market or "",
            "score": setup.get("score"), "entry": setup.get("entry"), "stop": setup.get("stop"),
            "tp1": setup.get("tp1"), "tp2": setup.get("tp2"), "upside": setup.get("upside"),
            "rr": setup.get("rr"), "headline": ai.get("headline", ""), "analysis": ai.get("analysis", ""),
            "news_risk": ai.get("news_risk", "UNAVAILABLE"), "status": "NEW",
            "fingerprint": fingerprint, "created_at": datetime.now(timezone.utc).isoformat(),
        }
        sb.table("market_alerts").insert(payload).execute()
        return True
    except Exception as exc:
        diagnostics.append(f"alert_insert:{symbol}:{alert_type}:{type(exc).__name__}:{str(exc)[:180]}")
        return False


def classify_position(daily, hourly, pru):
    price = daily["price"]
    hscore = hourly["score"] if hourly else None

    # Priority from strongest action to weakest.
    if pru > 0 and price <= pru * 0.94:
        return "EXIT"
    if daily["score"] < 45 or (hscore is not None and hscore < 42):
        return "RISK"
    if pru > 0 and price >= pru * 1.08 and hscore is not None and hscore < 58:
        return "PROTECT"
    if pru > 0 and price >= pru * 1.06 and daily["score"] >= 65:
        return "TAKE_PROFIT"
    return "HOLD"


def run():
    uni, pos = universe(), positions()
    created = 0

    # 1) Existing positions: only STATE CHANGES become alerts.
    if not pos.empty:
        for _, p in pos.iterrows():
            symbol = clean_symbol(p.get("ticker"))
            if not symbol:
                continue
            daily = trade_setup(history(symbol, "6mo", "1d"))
            if not daily:
                continue
            hourly = trade_setup(history(symbol, "3mo", "1h"))
            pru, qty = fnum(p.get("pru")), fnum(p.get("quantity"))
            current_state = classify_position(daily, hourly, pru)
            previous = get_state(symbol, "POSITION")
            previous_state = previous.get("state") if previous else None

            # First observation establishes baseline silently.
            if previous_state is None:
                save_state(symbol, "POSITION", current_state, daily["score"], daily["price"])
                continue

            if current_state != previous_state:
                if current_state in {"EXIT", "RISK", "PROTECT", "TAKE_PROFIT"}:
                    ctx = {"quantity": qty, "pru": pru, "price": daily["price"],
                           "previous_state": previous_state, "new_state": current_state}
                    ai = ai_context(symbol, daily, ctx)
                    # News is context for position risk; technical event can still be emitted if news is unavailable.
                    event_key = f"{previous_state}_TO_{current_state}"
                    if create_alert(symbol, current_state, p.get("broker", ""), "", daily, ai, event_key,
                                    name=p.get("name", ""), isin=p.get("isin", "")):
                        created += 1
                save_state(symbol, "POSITION", current_state, daily["score"], daily["price"])
            else:
                save_state(symbol, "POSITION", current_state, daily["score"], daily["price"])

    # 2) New entries: technical gate -> hourly confirmation -> news gate -> state transition.
    if not uni.empty:
        candidates = []
        for _, u in uni.iterrows():
            symbol = clean_symbol(u.get("symbol"))
            if not symbol:
                continue
            s = trade_setup(history(symbol, "6mo", "1d"))
            if not s:
                continue
            qualifies = s["upside"] >= MIN_UPSIDE and s["rr"] >= MIN_RR and s["score"] >= MIN_ENTRY_SCORE
            if qualifies:
                candidates.append((symbol, u, s))
            else:
                prev = get_state(symbol, "ENTRY")
                if prev and prev.get("state") == "QUALIFIED":
                    # A previously qualified setup is now invalidated.
                    if create_alert(symbol, "INVALIDATED", u.get("broker", ""), u.get("market", ""),
                                    s, {"headline": "", "analysis": "Le setup technique ne satisfait plus les critères V10.",
                                        "news_risk": "UNAVAILABLE"}, "QUALIFIED_TO_INVALID",
                                    name=u.get("name", ""), isin=u.get("isin", "")):
                        created += 1
                save_state(symbol, "ENTRY", "INVALID", s["score"], s["price"])

        candidates.sort(key=lambda x: (x[2]["score"], x[2]["rr"], x[2]["upside"]), reverse=True)
        for symbol, u, daily in candidates[:12]:
            hourly = trade_setup(history(symbol, "3mo", "1h"))
            if not hourly or hourly["score"] < MIN_HOURLY_SCORE:
                save_state(symbol, "ENTRY", "INVALID", daily["score"], daily["price"])
                continue

            prev = get_state(symbol, "ENTRY")
            previous_state = prev.get("state") if prev else None

            # Already qualified: no repeated alert and no repeated AI call.
            if previous_state == "QUALIFIED":
                save_state(symbol, "ENTRY", "QUALIFIED", daily["score"], daily["price"])
                continue

            ai = ai_context(symbol, daily)
            # New ENTRY requires a successful news check. HIGH or unavailable => no entry alert.
            if ai["news_risk"] == "HIGH":
                save_state(symbol, "ENTRY", "BLOCKED_NEWS", daily["score"], daily["price"])
                continue
            if ai["news_risk"] == "UNAVAILABLE":
                save_state(symbol, "ENTRY", "WAITING_NEWS", daily["score"], daily["price"])
                continue

            if create_alert(symbol, "ENTRY", u.get("broker", ""), u.get("market", ""),
                            daily, ai, "NEW_QUALIFIED_SETUP",
                            name=u.get("name", ""), isin=u.get("isin", "")):
                created += 1
            save_state(symbol, "ENTRY", "QUALIFIED", daily["score"], daily["price"])

    details = "; ".join(diagnostics[-20:]) if diagnostics else None
    sb.table("agent_runs").insert({
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "created_alerts": created,
        "status": "OK" if not diagnostics else "OK_WITH_DIAGNOSTICS",
        "details": details
    }).execute()
    print(f"VISION FUTURE V10: {created} actionable alert(s).")
    if details:
        print("Diagnostics:", details)


if __name__ == "__main__":
    run()
