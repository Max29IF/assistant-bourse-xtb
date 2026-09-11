import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import os
from datetime import datetime, timezone, timedelta

import numpy as np
import pandas as pd
import yfinance as yf
from supabase import create_client

try:
    from google import genai
except Exception:
    genai = None


SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

MIN_UPSIDE = 3.0
MIN_RR = 2.0
MIN_ENTRY_SCORE = 76
MIN_HOURLY_SCORE = 65
CRYPTO_MIN_UPSIDE = 5.0
CRYPTO_MIN_ENTRY_SCORE = 76
ALERT_TYPES = {
    "ENTRY", "EXIT", "TAKE_PROFIT", "PROTECT", "RISK", "NEWS_RISK",
    "INVALIDATED", "PRICE_ABOVE", "PRICE_BELOW",
}

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



DISCOVERY_REGION_GROUPS = [
    [("USA","us"), ("Canada","ca"), ("Royaume-Uni","gb")],
    [("France","fr"), ("Allemagne","de"), ("Pays-Bas","nl")],
    [("Espagne","es"), ("Italie","it"), ("Suisse","ch")],
    [("Japon","jp"), ("Australie","au"), ("Suède","se")],
]


def discover_region_equities(region_label, region_code, size=12):
    rows = []
    try:
        q = yf.EquityQuery("and", [
            yf.EquityQuery("eq", ["region", region_code]),
            yf.EquityQuery("gte", ["intradaymarketcap", 500_000_000]),
            yf.EquityQuery("gte", ["intradayprice", 2]),
            yf.EquityQuery("gte", ["avgdailyvol3m", 100_000]),
        ])
        resp = yf.screen(q, size=size, sortField="dayvolume", sortAsc=False)
        quotes = (resp or {}).get("quotes", []) if isinstance(resp, dict) else []
        for x in quotes:
            symbol = clean_symbol(x.get("symbol"))
            if not symbol:
                continue
            qtype = str(x.get("quoteType") or "").upper()
            if qtype and qtype not in {"EQUITY","ETF"}:
                continue
            rows.append({
                "symbol": symbol,
                "name": str(x.get("longName") or x.get("shortName") or ""),
                "isin": "",
                "market": region_label,
                "broker": "À vérifier",
                "enabled": True,
                "source": "DISCOVERY",
            })
    except Exception as exc:
        diagnostics.append(f"discovery:{region_code}:{type(exc).__name__}:{str(exc)[:150]}")
    return rows


def rotating_discovery():
    """
    Scans 3 regions per scheduled run. At a 15-minute cadence, all 12 regions
    are revisited roughly once per hour without exploding network traffic.
    """
    now = datetime.now(timezone.utc)
    slot = (now.minute // 15) % len(DISCOVERY_REGION_GROUPS)
    group = DISCOVERY_REGION_GROUPS[slot]
    rows = []
    for label, code in group:
        rows.extend(discover_region_equities(label, code, size=12))
    return pd.DataFrame(rows), [x[0] for x in group]



def universe():
    frames = []
    try:
        rows = sb_data(
            sb.table("broker_universe")
            .select("symbol,name,isin,market,asset_type,broker,enabled")
            .eq("enabled", True)
            .execute()
        )
        base = pd.DataFrame(rows)
        if not base.empty:
            base["source"] = "BROKER_UNIVERSE"
            frames.append(base)
    except Exception as exc:
        diagnostics.append(f"universe:{type(exc).__name__}:{str(exc)[:180]}")

    try:
        watched = pd.DataFrame(sb_data(
            sb.table("crypto_watchlist")
            .select("symbol,name,enabled")
            .eq("enabled", True)
            .execute()
        ))
        if not watched.empty:
            watched["isin"] = ""
            watched["market"] = "Crypto"
            watched["asset_type"] = "CRYPTO"
            watched["broker"] = "Crypto"
            watched["source"] = "CRYPTO_WATCHLIST"
            frames.append(watched)
    except Exception as exc:
        diagnostics.append(f"crypto_watchlist:{type(exc).__name__}:{str(exc)[:180]}")

    discovered, regions = rotating_discovery()
    if not discovered.empty:
        frames.append(discovered)

    if not frames:
        return pd.DataFrame(), regions

    out = pd.concat(frames, ignore_index=True, sort=False)
    out["symbol"] = out["symbol"].map(clean_symbol)
    out = out[out["symbol"].astype(bool)]
    out["_priority"] = out["source"].map({"BROKER_UNIVERSE": 0, "DISCOVERY": 1}).fillna(2)
    out = out.sort_values("_priority").drop_duplicates("symbol").drop(columns="_priority")
    return out.reset_index(drop=True), regions

def positions():
    try:
        rows = sb_data(
            sb.table("portfolio_positions")
            .select("user_id,account,broker,ticker,isin,name,quantity,pru,instrument_key")
            .execute()
        )
        return pd.DataFrame(rows)
    except Exception as exc:
        diagnostics.append(f"positions:{type(exc).__name__}:{str(exc)[:180]}")
        return pd.DataFrame()


def state_key(symbol, scope, user_id=None):
    owner = f"USER:{user_id}" if user_id else "GLOBAL"
    return f"{owner}:{scope}:{symbol}"


def get_state(symbol, scope, user_id=None):
    try:
        rows = sb_data(
            sb.table("market_agent_state").select("*")
            .eq("state_key", state_key(symbol, scope, user_id))
            .limit(1).execute()
        )
        return rows[0] if rows else None
    except Exception as exc:
        diagnostics.append(f"state_read:{symbol}:{type(exc).__name__}")
        return None


def save_state(symbol, scope, state, score=None, price=None, user_id=None, asset_class="EQUITY"):
    payload = {
        "symbol": symbol, "scope": scope, "state": state,
        "score": score, "price": price, "user_id": user_id,
        "asset_class": asset_class, "state_key": state_key(symbol, scope, user_id),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    sb.table("market_agent_state").upsert(payload, on_conflict="state_key").execute()


def recent_event(symbol, alert_type, hours=24, user_id=None):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    try:
        query = (
            sb.table("market_alerts").select("id")
            .eq("symbol", symbol).eq("alert_type", alert_type)
            .gte("created_at", cutoff)
        )
        query = query.eq("user_id", user_id) if user_id else query.is_("user_id", "null")
        rows = sb_data(query.limit(1).execute())
        return bool(rows)
    except Exception:
        return False



def gemini_healthcheck():
    """
    Runs only for a manual GitHub Actions launch (workflow_dispatch).
    Scheduled runs do not spend an extra Gemini request just for diagnostics.
    """
    if os.getenv("GITHUB_EVENT_NAME", "") != "workflow_dispatch":
        return None

    if not GEMINI_API_KEY:
        diagnostics.append("gemini_healthcheck:API_KEY_MISSING")
        return "GEMINI_ERROR: API_KEY_MISSING"

    if genai is None:
        diagnostics.append("gemini_healthcheck:GOOGLE_GENAI_NOT_INSTALLED")
        return "GEMINI_ERROR: GOOGLE_GENAI_NOT_INSTALLED"

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents="Réponds uniquement avec GEMINI_OK"
        )
        text = str(getattr(response, "text", "") or "").strip()

        if "GEMINI_OK" in text.upper():
            return f"GEMINI_OK | model={GEMINI_MODEL}"

        diagnostics.append(f"gemini_healthcheck:UNEXPECTED_RESPONSE:{text[:120]}")
        return f"GEMINI_ERROR: UNEXPECTED_RESPONSE | {text[:120]}"

    except Exception as exc:
        msg = f"{type(exc).__name__}: {str(exc)[:220]}"
        diagnostics.append(f"gemini_healthcheck:{msg}")
        return f"GEMINI_ERROR: {msg}"


def _extract_yahoo_news(symbol, limit=6):
    try:
        items = yf.Ticker(symbol).news or []
    except Exception as exc:
        diagnostics.append(f"news_yahoo:{symbol}:{type(exc).__name__}")
        return []
    out = []
    for item in items[:limit]:
        content = item.get("content") if isinstance(item, dict) else None
        content = content if isinstance(content, dict) else item
        title = str(content.get("title") or "").strip()
        summary = str(content.get("summary") or content.get("description") or "").strip()
        if title or summary:
            out.append({"title": title, "summary": summary, "source": "Yahoo Finance"})
    return out


def _extract_google_news_rss(symbol, name="", limit=6):
    """
    Free fallback: Google News RSS search.
    No API key and no payment method required.
    We use feed metadata only (title/source/date/link), not full article scraping.
    """
    topic = "crypto" if clean_symbol(symbol).endswith(("-USD", "-EUR")) else "stock"
    query = f'"{name}" {topic}' if name and str(name).strip() else f"{symbol} {topic}"
    params = urllib.parse.urlencode({
        "q": query,
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    })
    url = "https://news.google.com/rss/search?" + params
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "VISION-FUTURE/37.2 (+market-news-rss)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            raw = response.read()
        root = ET.fromstring(raw)
        out = []
        for item in root.findall(".//item")[:limit]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
            source_el = item.find("source")
            source = ((source_el.text or "").strip() if source_el is not None else "Google News")
            if title:
                out.append({
                    "title": title,
                    "summary": "",
                    "source": source,
                    "published": pub_date,
                    "url": link,
                })
        return out
    except Exception as exc:
        diagnostics.append(f"news_google_rss:{symbol}:{type(exc).__name__}:{str(exc)[:160]}")
        return []



def free_news_healthcheck():
    """Manual-run diagnostic for the no-card news chain."""
    if os.getenv("GITHUB_EVENT_NAME", "") != "workflow_dispatch":
        return None
    test = _extract_google_news_rss("AAPL", "Apple Inc.", 1)
    return "NEWS_RSS_OK" if test else "NEWS_RSS_EMPTY"



def _deterministic_news_risk(items):
    text = " ".join((x.get("title","") + " " + x.get("summary","")) for x in items).lower()
    high = ["bankruptcy","insolvency","fraud","accounting probe","default","delisting",
            "profit warning","guidance cut","investigation","sanction","war","explosion",
            "recall","data breach","cyberattack","suspends dividend"]
    medium = ["lawsuit","downgrade","strike","regulation","tariff","fine","earnings miss",
              "margin pressure","layoff","restructuring","rate hike","geopolitical"]
    if any(k in text for k in high):
        return "HIGH"
    if any(k in text for k in medium):
        return "MEDIUM"
    return "LOW" if items else "UNAVAILABLE"


def ai_context(symbol, technical, position_context=None, instrument_name=''):
    # Zero-card design:
    # 1) Yahoo Finance news first
    # 2) Google News RSS fallback (no API key)
    # 3) Gemini interprets only the retrieved headlines/metadata
    items = _extract_yahoo_news(symbol, 6)
    if len(items) < 3:
        items.extend(_extract_google_news_rss(symbol, instrument_name, 6))

    # Deduplicate headlines while preserving order.
    deduped = []
    seen_titles = set()
    for item in items:
        key = str(item.get("title", "")).strip().lower()
        if key and key not in seen_titles:
            seen_titles.add(key)
            deduped.append(item)
    items = deduped[:8]

    fallback_risk = _deterministic_news_risk(items)
    fallback_headline = items[0]["title"] if items else ""
    fallback_analysis = (
        "Filtre d'actualité déterministe utilisé. "
        + ("Sources récentes trouvées : " + " | ".join(x["title"] for x in items[:3]) if items
           else "Aucune actualité exploitable n'a été récupérée lors de ce cycle.")
    )

    if not GEMINI_API_KEY or genai is None:
        return {
            "headline": fallback_headline[:500],
            "analysis": fallback_analysis[:3000],
            "news_risk": fallback_risk,
        }

    prompt = f"""
Tu es le filtre d'actualité de VISION FUTURE.
Instrument: {symbol}
Technique: {json.dumps(technical, ensure_ascii=False)}
Position: {json.dumps(position_context or {}, ensure_ascii=False)}
Actualités récupérées: {json.dumps(items[:8], ensure_ascii=False)}

Analyse uniquement ces informations. Ne fabrique aucun événement.
Retourne UNIQUEMENT un JSON valide :
{{"headline":"résumé factuel court","analysis":"2 à 4 phrases","news_risk":"LOW|MEDIUM|HIGH"}}
HIGH = événement susceptible d'invalider fortement le signal.
MEDIUM = incertitude notable.
LOW = aucun risque d'actualité significatif identifié dans les éléments fournis.
"""
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        raw = str(getattr(resp, "text", "") or "").strip()
        start, end = raw.find("{"), raw.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("JSON absent")
        data = json.loads(raw[start:end+1])
        risk = str(data.get("news_risk", "")).upper()
        if risk not in {"LOW","MEDIUM","HIGH"}:
            raise ValueError(f"news_risk invalide:{risk}")
        return {
            "headline": str(data.get("headline", fallback_headline))[:500],
            "analysis": str(data.get("analysis", fallback_analysis))[:3000],
            "news_risk": risk,
        }
    except Exception as exc:
        diagnostics.append(f"gemini:{symbol}:{type(exc).__name__}:{str(exc)[:220]}")
        return {
            "headline": fallback_headline[:500],
            "analysis": fallback_analysis[:3000],
            "news_risk": fallback_risk,
        }

def create_alert(
    symbol, alert_type, broker, market, setup, ai, event_key,
    name="", isin="", user_id=None, asset_class="EQUITY",
):
    if alert_type not in ALERT_TYPES or not symbol:
        return False
    # Stable event key: never contains price or score.
    owner_key = str(user_id) if user_id else "GLOBAL"
    fingerprint = f"V37.3:{owner_key}:{alert_type}:{symbol}:{event_key}"
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
            "user_id": user_id, "asset_class": asset_class,
            "fingerprint": fingerprint, "created_at": datetime.now(timezone.utc).isoformat(),
        }
        sb.table("market_alerts").insert(payload).execute()
        return True
    except Exception as exc:
        diagnostics.append(f"alert_insert:{symbol}:{alert_type}:{type(exc).__name__}:{str(exc)[:180]}")
        return False



def setup_confidence(daily, hourly=None, news_risk="UNAVAILABLE"):
    """
    Composite confidence score used only for ranking/decision support.
    Does not replace the existing technical score stored in alerts.
    """
    if not daily:
        return 0
    score = float(daily.get("score", 0))
    score += min(max(float(daily.get("rr", 0)) - 2.0, 0), 2.0) * 4
    score += min(max(float(daily.get("upside", 0)) - 3.0, 0), 7.0) * 1.2
    vol_ratio = float(daily.get("vol_ratio", 1.0) or 1.0)
    if vol_ratio >= 1.25:
        score += 3
    if hourly:
        score = score * 0.78 + float(hourly.get("score", 0)) * 0.22

    risk = str(news_risk or "").upper()
    if risk == "HIGH":
        score -= 30
    elif risk == "MEDIUM":
        score -= 10
    elif risk == "LOW":
        score += 2

    return int(np.clip(round(score), 0, 100))


def market_regime():
    """
    Lightweight global regime filter.
    Uses broad liquid ETFs and returns RISK_ON / NEUTRAL / RISK_OFF.
    Failure never blocks the agent.
    """
    proxies = ["SPY", "QQQ", "VGK", "EWJ"]
    votes = []
    for symbol in proxies:
        try:
            s = trade_setup(history(symbol, "6mo", "1d"))
            if not s:
                continue
            if s["score"] >= 65:
                votes.append(1)
            elif s["score"] <= 45:
                votes.append(-1)
            else:
                votes.append(0)
        except Exception:
            continue

    if not votes:
        return {"state": "NEUTRAL", "score": 50, "votes": 0}

    avg = sum(votes) / len(votes)
    if avg >= 0.45:
        state = "RISK_ON"
    elif avg <= -0.45:
        state = "RISK_OFF"
    else:
        state = "NEUTRAL"
    return {"state": state, "score": int(round((avg + 1) * 50)), "votes": len(votes)}


def is_existing_position(symbol, pos_df):
    if pos_df is None or pos_df.empty:
        return False
    syms = {clean_symbol(x) for x in pos_df.get("ticker", pd.Series(dtype=str)).tolist()}
    return symbol in syms


def candidate_rank(daily, hourly, regime_state):
    """
    Ranking score for the global opportunity queue.
    Higher is better; no new database column required.
    """
    hscore = float(hourly.get("score", 0)) if hourly else 0
    rank = (
        float(daily.get("score", 0)) * 0.48
        + hscore * 0.22
        + min(float(daily.get("rr", 0)), 4.0) * 5
        + min(float(daily.get("upside", 0)), 10.0) * 1.4
        + min(float(daily.get("vol_ratio", 1.0)), 2.0) * 3
    )
    if regime_state == "RISK_ON":
        rank += 4
    elif regime_state == "RISK_OFF":
        rank -= 7
    return round(rank, 2)


def enriched_analysis(base_ai, daily, hourly, regime, confidence):
    ai = dict(base_ai or {})
    technical = (
        f"Score journalier {daily.get('score','—')}/100, "
        f"confirmation 1H {hourly.get('score','—') if hourly else '—'}/100, "
        f"potentiel {daily.get('upside',0):.1f} %, R/R {daily.get('rr',0):.2f}. "
        f"Régime global {regime.get('state','NEUTRAL')}. "
        f"Confiance composite {confidence}/100."
    )
    base = str(ai.get("analysis") or "").strip()
    ai["analysis"] = (technical + (" " + base if base else ""))[:3000]
    return ai


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


def crypto_threshold_alerts():
    """Create private alerts when a user's configured crypto threshold is reached."""
    created = 0
    try:
        rows = sb_data(
            sb.table("crypto_watchlist")
            .select("user_id,symbol,name,price_below,price_above,enabled")
            .eq("enabled", True)
            .execute()
        )
    except Exception as exc:
        diagnostics.append(f"crypto_thresholds:{type(exc).__name__}:{str(exc)[:180]}")
        return created

    price_cache = {}
    for row in rows:
        symbol = clean_symbol(row.get("symbol"))
        user_id = row.get("user_id")
        if not symbol or not user_id:
            continue
        if symbol not in price_cache:
            price_cache[symbol] = trade_setup(history(symbol, "6mo", "1d"))
        setup = price_cache.get(symbol)
        if not setup:
            continue

        price = fnum(setup.get("price"))
        below = fnum(row.get("price_below"))
        above = fnum(row.get("price_above"))
        checks = []
        if below > 0 and price <= below:
            checks.append(("PRICE_BELOW", below, f"Cours sous le seuil personnel de {below:,.4f} USD"))
        if above > 0 and price >= above:
            checks.append(("PRICE_ABOVE", above, f"Cours au-dessus du seuil personnel de {above:,.4f} USD"))

        for alert_type, threshold, headline in checks:
            if recent_event(symbol, alert_type, hours=12, user_id=user_id):
                continue
            bucket = datetime.now(timezone.utc).strftime("%Y%m%d%H")
            if create_alert(
                symbol, alert_type, "Crypto", "Crypto", setup,
                {
                    "headline": headline,
                    "analysis": f"{symbol} cote {price:,.4f} USD. Seuil configuré : {threshold:,.4f} USD.",
                    "news_risk": "UNAVAILABLE",
                },
                f"THRESHOLD_{threshold:g}_{bucket}",
                name=row.get("name", ""), user_id=user_id, asset_class="CRYPTO",
            ):
                created += 1
    return created


def run():
    uni, discovery_regions = universe()
    pos = positions()
    created = 0
    regime = market_regime()
    created += crypto_threshold_alerts()

    # 1) Existing positions: alert only on meaningful STATE CHANGES.
    if not pos.empty:
        for _, p in pos.iterrows():
            symbol = clean_symbol(p.get("ticker"))
            if not symbol:
                continue

            user_id = p.get("user_id")
            is_crypto = str(p.get("account") or "").lower() == "crypto" or symbol.endswith(("-USD", "-EUR"))
            asset_class = "CRYPTO" if is_crypto else "EQUITY"

            daily = trade_setup(history(symbol, "6mo", "1d"))
            if not daily:
                continue
            hourly = trade_setup(history(symbol, "3mo", "1h"))

            pru, qty = fnum(p.get("pru")), fnum(p.get("quantity"))
            current_state = classify_position(daily, hourly, pru)
            previous = get_state(symbol, "POSITION", user_id=user_id)
            previous_state = previous.get("state") if previous else None

            # First observation = silent baseline.
            if previous_state is None:
                save_state(symbol, "POSITION", current_state, daily["score"], daily["price"], user_id, asset_class)
                continue

            if current_state != previous_state:
                if current_state in {"EXIT", "RISK", "PROTECT", "TAKE_PROFIT"}:
                    ctx = {
                        "quantity": qty,
                        "pru": pru,
                        "price": daily["price"],
                        "previous_state": previous_state,
                        "new_state": current_state,
                    }
                    ai = ai_context(
                        symbol,
                        daily,
                        position_context=ctx,
                        instrument_name=str(p.get("name") or ""),
                    )
                    confidence = setup_confidence(daily, hourly, ai.get("news_risk"))
                    ai = enriched_analysis(ai, daily, hourly, regime, confidence)

                    event_key = f"{previous_state}_TO_{current_state}"
                    if create_alert(
                        symbol,
                        current_state,
                        p.get("broker", ""),
                        "",
                        daily,
                        ai,
                        event_key,
                        name=p.get("name", ""),
                        isin=p.get("isin", ""),
                        user_id=user_id,
                        asset_class=asset_class,
                    ):
                        created += 1

                save_state(symbol, "POSITION", current_state, daily["score"], daily["price"], user_id, asset_class)
            else:
                save_state(symbol, "POSITION", current_state, daily["score"], daily["price"], user_id, asset_class)

    # 2) Global new entries.
    # Daily gate first to keep requests light.
    preliminary = []
    if not uni.empty:
        for _, u in uni.iterrows():
            symbol = clean_symbol(u.get("symbol"))
            if not symbol:
                continue
            asset_class = str(u.get("asset_type") or "EQUITY").upper()
            if u.get("market") == "Crypto" or symbol.endswith(("-USD", "-EUR")):
                asset_class = "CRYPTO"

            # Never propose an ENTRY for something already held.
            if is_existing_position(symbol, pos):
                continue

            daily = trade_setup(history(symbol, "6mo", "1d"))
            if not daily:
                continue

            required_upside = CRYPTO_MIN_UPSIDE if asset_class == "CRYPTO" else MIN_UPSIDE
            required_score = CRYPTO_MIN_ENTRY_SCORE if asset_class == "CRYPTO" else MIN_ENTRY_SCORE
            qualifies_daily = (
                daily["upside"] >= required_upside
                and daily["rr"] >= MIN_RR
                and daily["score"] >= required_score
            )

            if not qualifies_daily:
                prev = get_state(symbol, "ENTRY")
                if prev and prev.get("state") == "QUALIFIED":
                    if create_alert(
                        symbol,
                        "INVALIDATED",
                        u.get("broker", ""),
                        u.get("market", ""),
                        daily,
                        {
                            "headline": "",
                            "analysis": "Le setup technique ne satisfait plus les critères d'entrée VISION FUTURE.",
                            "news_risk": "UNAVAILABLE",
                        },
                        "QUALIFIED_TO_INVALID",
                        name=u.get("name", ""),
                        isin=u.get("isin", ""),
                        asset_class=asset_class,
                    ):
                        created += 1
                save_state(symbol, "ENTRY", "INVALID", daily["score"], daily["price"], asset_class=asset_class)
                continue

            preliminary.append((symbol, u, daily))

    # Highest daily quality first. Hourly/news checks are only done for the best.
    preliminary.sort(
        key=lambda x: (x[2]["score"], x[2]["rr"], x[2]["upside"], x[2]["vol_ratio"]),
        reverse=True,
    )

    confirmed = []
    equity_preliminary = [
        x for x in preliminary
        if str(x[1].get("asset_type") or "EQUITY").upper() != "CRYPTO"
        and x[1].get("market") != "Crypto"
    ]
    crypto_preliminary = [
        x for x in preliminary
        if str(x[1].get("asset_type") or "").upper() == "CRYPTO"
        or x[1].get("market") == "Crypto"
    ]
    # Reserve capacity for crypto so it cannot be crowded out by equity candidates.
    finalists = equity_preliminary[:18] + crypto_preliminary[:8]
    for symbol, u, daily in finalists:
        asset_class = str(u.get("asset_type") or "EQUITY").upper()
        if u.get("market") == "Crypto" or symbol.endswith(("-USD", "-EUR")):
            asset_class = "CRYPTO"
        hourly = trade_setup(history(symbol, "3mo", "1h"))
        if not hourly or hourly["score"] < MIN_HOURLY_SCORE:
            save_state(symbol, "ENTRY", "INVALID", daily["score"], daily["price"], asset_class=asset_class)
            continue

        rank = candidate_rank(daily, hourly, regime["state"])
        confirmed.append((rank, symbol, u, daily, hourly))

    confirmed.sort(key=lambda x: x[0], reverse=True)

    # Only the strongest candidates receive a news/Gemini call, with a crypto quota.
    confirmed_equities = [
        x for x in confirmed
        if str(x[2].get("asset_type") or "EQUITY").upper() != "CRYPTO"
        and x[2].get("market") != "Crypto"
    ]
    confirmed_crypto = [
        x for x in confirmed
        if str(x[2].get("asset_type") or "").upper() == "CRYPTO"
        or x[2].get("market") == "Crypto"
    ]
    alert_finalists = confirmed_equities[:8] + confirmed_crypto[:4]
    for rank, symbol, u, daily, hourly in alert_finalists:
        asset_class = str(u.get("asset_type") or "EQUITY").upper()
        if u.get("market") == "Crypto" or symbol.endswith(("-USD", "-EUR")):
            asset_class = "CRYPTO"
        prev = get_state(symbol, "ENTRY")
        previous_state = prev.get("state") if prev else None

        if previous_state == "QUALIFIED":
            save_state(symbol, "ENTRY", "QUALIFIED", daily["score"], daily["price"], asset_class=asset_class)
            continue

        ai = ai_context(
            symbol,
            daily,
            instrument_name=str(u.get("name") or ""),
        )

        confidence = setup_confidence(daily, hourly, ai.get("news_risk"))
        ai = enriched_analysis(ai, daily, hourly, regime, confidence)

        # News gate.
        if ai.get("news_risk") == "HIGH":
            save_state(symbol, "ENTRY", "BLOCKED_NEWS", daily["score"], daily["price"], asset_class=asset_class)
            continue

        # In a broad RISK_OFF regime, require a stronger setup.
        if regime["state"] == "RISK_OFF" and confidence < 84:
            save_state(symbol, "ENTRY", "WAIT_REGIME", daily["score"], daily["price"], asset_class=asset_class)
            continue

        # MEDIUM news is allowed only for very strong setups.
        if ai.get("news_risk") == "MEDIUM" and confidence < 84:
            save_state(symbol, "ENTRY", "WAIT_NEWS", daily["score"], daily["price"], asset_class=asset_class)
            continue

        if confidence < 78:
            save_state(symbol, "ENTRY", "WATCH", daily["score"], daily["price"], asset_class=asset_class)
            continue

        ai["analysis"] = (
            f"Classement opportunité {rank:.1f}. " + str(ai.get("analysis") or "")
        )[:3000]

        if create_alert(
            symbol,
            "ENTRY",
            u.get("broker", ""),
            u.get("market", ""),
            daily,
            ai,
            "NEW_QUALIFIED_SETUP",
            name=u.get("name", ""),
            isin=u.get("isin", ""),
            asset_class=asset_class,
        ):
            created += 1

        save_state(symbol, "ENTRY", "QUALIFIED", daily["score"], daily["price"], asset_class=asset_class)

    # Manual launch diagnostics only.
    health = gemini_healthcheck()
    news_health = free_news_healthcheck()

    parts = [
        f"REGIME={regime['state']}({regime['score']}/100)",
        f"UNIVERSE={len(uni)}",
        f"DISCOVERY_REGIONS={','.join(discovery_regions)}",
        f"POSITIONS={len(pos)}",
        f"PRELIMINARY={len(preliminary)}",
        f"CONFIRMED={len(confirmed)}",
        f"CRYPTO_PRELIMINARY={len(crypto_preliminary)}",
        f"CRYPTO_CONFIRMED={len(confirmed_crypto)}",
    ]
    if health:
        parts.append(health)
    if news_health:
        parts.append(news_health)
    if diagnostics:
        parts.append("DIAGNOSTICS: " + "; ".join(diagnostics[-20:]))

    details = " | ".join(parts)

    sb.table("agent_runs").insert({
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "created_alerts": created,
        "status": "OK" if not diagnostics else "OK_WITH_DIAGNOSTICS",
        "details": details,
    }).execute()

    print(
        f"VISION FUTURE V37.3: {created} actionable alert(s) | "
        f"regime={regime['state']} | confirmed={len(confirmed)} | regions={','.join(discovery_regions)}"
    )


if __name__ == "__main__":
    run()
