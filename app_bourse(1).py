import math
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Trading Command Center — V4.1", page_icon="📈", layout="wide")

# ==========================================================
# UNIVERSE
# ==========================================================
UNIVERSE = {
    "USA": [
        "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","AVGO","AMD","NFLX","ADBE","CRM","ORCL","QCOM","INTC","MU","AMAT","LRCX","PANW","CRWD","PLTR","NOW","SNOW","UBER","ABNB","SHOP","COIN","MSTR","JPM","BAC","GS","MS","V","MA","PYPL","WMT","COST","HD","MCD","KO","PEP","NKE","CAT","DE","GE","HON","RTX","BA","LMT","XOM","CVX","COP","SLB","LLY","JNJ","PFE","MRK","ABBV","UNH","TMO","ISRG","SPOT","DIS","CMCSA","T","VZ","LIN","UPS","LOW","BKNG","INTU","CSCO","IBM","TXN","SBUX","ORLY","CVS"
    ],
    "France": [
        "MC.PA","OR.PA","AIR.PA","SAN.PA","SU.PA","TTE.PA","BNP.PA","AI.PA","SAF.PA","DG.PA","CS.PA","CAP.PA","ACA.PA","GLE.PA","VIV.PA","KER.PA","RMS.PA","ENGI.PA","ORA.PA","STMPA.PA","EL.PA","RI.PA"
    ],
    "Germany": [
        "SAP.DE","SIE.DE","ALV.DE","DTE.DE","AIR.DE","MBG.DE","BMW.DE","VOW3.DE","BAS.DE","BAYN.DE","ADS.DE","IFX.DE","DBK.DE","DB1.DE","MUV2.DE","RWE.DE","VNA.DE","HEN3.DE"
    ],
    "Netherlands": ["ASML.AS","ADYEN.AS","INGA.AS","PRX.AS","PHIA.AS","HEIA.AS","DSM.AS"],
    "UK": ["SHEL.L","AZN.L","HSBA.L","ULVR.L","BP.L","GSK.L","RIO.L","LSEG.L","REL.L","BARC.L","VOD.L","DGE.L","BA.L"],
    "Spain": ["IBE.MC","ITX.MC","SAN.MC","BBVA.MC","TEF.MC","REP.MC"],
    "Italy": ["ENEL.MI","ENI.MI","ISP.MI","UCG.MI","STLAM.MI","RACE.MI"],
    "Switzerland": ["NESN.SW","NOVN.SW","ROG.SW","UBSG.SW","ZURN.SW","CFR.SW"],
    "Nordics": ["NOVO-B.CO","MAERSK-B.CO","EQNR.OL","DNB.OL","VOLV-B.ST","ATCO-A.ST","ERIC-B.ST","NOKIA.HE","KNEBV.HE","ORNBV.HE","NDA-FI.HE"],
}

INDEXES = {
    "S&P 500": "^GSPC", "NASDAQ": "^IXIC", "CAC 40": "^FCHI",
    "DAX": "^GDAXI", "Euro Stoxx 50": "^STOXX50E", "FTSE 100": "^FTSE"
}

# yfinance valid ranges depend on interval. The UI only exposes coherent combinations.
TF = {
    "1 minute": {"interval": "1m", "periods": ["1d","5d","7d"]},
    "5 minutes": {"interval": "5m", "periods": ["5d","1mo"]},
    "15 minutes": {"interval": "15m", "periods": ["5d","1mo","3mo","6mo"]},
    "30 minutes": {"interval": "30m", "periods": ["5d","1mo","3mo","6mo"]},
    "1 hour": {"interval": "1h", "periods": ["5d","1mo","3mo","6mo","1y"]},
    "1 day": {"interval": "1d", "periods": ["1mo","3mo","6mo","1y","2y","5y","10y"]},
    "1 week": {"interval": "1wk", "periods": ["1y","2y","5y","10y"]},
}

# ==========================================================
# DATA
# ==========================================================
@st.cache_data(ttl=120, show_spinner=False)
def history(symbol: str, period: str, interval: str):
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=True)
        if df is None or df.empty:
            return None
        df = df.dropna(subset=["Open","High","Low","Close"])
        return df
    except Exception:
        return None

@st.cache_data(ttl=900, show_spinner=False)
def info(symbol: str):
    try:
        return yf.Ticker(symbol).info or {}
    except Exception:
        return {}

@st.cache_data(ttl=600, show_spinner=False)
def news(symbol: str):
    try:
        raw = yf.Ticker(symbol).news or []
        out = []
        for item in raw[:12]:
            content = item.get("content", item) if isinstance(item, dict) else {}
            title = content.get("title") or item.get("title") or ""
            publisher = content.get("provider", {}).get("displayName") if isinstance(content.get("provider"), dict) else item.get("publisher", "")
            link = content.get("canonicalUrl", {}).get("url") if isinstance(content.get("canonicalUrl"), dict) else item.get("link", "")
            if title:
                out.append({"title": title, "publisher": publisher or "", "link": link or ""})
        return out
    except Exception:
        return []

# ==========================================================
# TECHNICAL ENGINE
# ==========================================================
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
    x["ATR_PCT"] = x["ATR"] / c * 100
    x["VOL20"] = v.rolling(20).mean()
    x["ROC20"] = c.pct_change(20) * 100
    return x.dropna(subset=["SMA20","SMA50","ATR","RSI"])


def trade_setup(df):
    x = indicators(df)
    if len(x) < 55:
        return None
    r = x.iloc[-1]
    price = float(r.Close)
    atr = float(r.ATR)
    recent = x.tail(min(120, len(x)))

    # Robust zones rather than a single arbitrary candle.
    support = float(recent.Low.quantile(0.15))
    resistance = float(recent.High.quantile(0.85))
    support = min(support, price - 0.8 * atr)
    support = max(support, price - 4.0 * atr)
    resistance = max(resistance, price + 1.5 * atr)

    entry = min(price, max(support + 0.20 * atr, price - 0.35 * atr))
    stop = min(support - 0.25 * atr, entry - 1.0 * atr)
    risk = max(entry - stop, 0.01 * price)
    tp1 = min(resistance, entry + 1.5 * risk)
    tp2 = min(resistance, entry + 2.8 * risk)
    upside = (tp2 / entry - 1) * 100
    rr = (tp2 - entry) / risk if risk > 0 else 0
    dist_res = (resistance / entry - 1) * 100

    score = 50
    reasons = []
    if price > r.SMA20: score += 10; reasons.append("prix > SMA20")
    else: score -= 8; reasons.append("prix sous SMA20")
    if r.SMA20 > r.SMA50: score += 12; reasons.append("SMA20 > SMA50")
    else: score -= 10; reasons.append("SMA20 < SMA50")
    if not pd.isna(r.SMA200):
        if price > r.SMA200: score += 8; reasons.append("au-dessus SMA200")
        else: score -= 8
    if 45 <= r.RSI <= 68: score += 8; reasons.append("RSI exploitable")
    elif r.RSI < 35: score += 2; reasons.append("RSI faible")
    elif r.RSI > 75: score -= 8; reasons.append("RSI trop haut")
    if r.MACD > r.MACD_SIGNAL: score += 10; reasons.append("MACD haussier")
    else: score -= 8
    vol_ratio = float(r.Volume / r.VOL20) if r.VOL20 and r.VOL20 > 0 else 0
    if vol_ratio >= 1.10: score += 5; reasons.append("volume confirmé")
    if r.ROC20 > 0: score += 7; reasons.append("momentum positif")
    else: score -= 5
    if dist_res < 5: score -= 10; reasons.append("résistance trop proche")
    score = int(np.clip(score, 0, 100))
    signal = "ACHAT" if score >= 70 else ("VENTE" if score <= 30 else "ATTENTE")
    quality = "A" if score >= 85 and upside >= 5 and rr >= 2 else ("B" if score >= 75 and upside >= 5 and rr >= 2 else ("SURVEILLER" if upside >= 5 else "REJETE"))
    return {
        "df": x, "price": price, "entry": entry, "stop": stop, "tp1": tp1, "tp2": tp2,
        "upside": upside, "rr": rr, "support": support, "resistance": resistance,
        "score": score, "signal": signal, "quality": quality, "rsi": float(r.RSI),
        "atr": atr, "atr_pct": float(r.ATR_PCT), "volume_ratio": vol_ratio,
        "reasons": reasons, "dist_res": dist_res
    }


def fundamental_score(i):
    if not i:
        return 50, []
    s = 50; reasons = []
    pe = i.get("forwardPE") or i.get("trailingPE")
    growth = i.get("revenueGrowth")
    margin = i.get("profitMargins")
    roe = i.get("returnOnEquity")
    debt = i.get("debtToEquity")
    if pe is not None:
        if pe < 20: s += 8; reasons.append("valorisation raisonnable")
        elif pe > 45: s -= 8; reasons.append("valorisation élevée")
    if growth is not None:
        if growth > 0.10: s += 8; reasons.append("croissance >10%")
        elif growth < 0: s -= 7; reasons.append("croissance négative")
    if margin is not None and margin > 0.15: s += 6; reasons.append("marge solide")
    if roe is not None and roe > 0.15: s += 5; reasons.append("ROE solide")
    if debt is not None and debt > 150: s -= 6; reasons.append("endettement élevé")
    return int(np.clip(s, 0, 100)), reasons


def position_calc(capital, risk_pct, entry, stop, target):
    risk_e = capital * risk_pct / 100
    dist = abs(entry - stop)
    qty = math.floor(risk_e / dist) if dist > 0 else 0
    exposure = qty * entry
    profit = qty * abs(target - entry)
    rr = abs(target - entry) / dist if dist else 0
    return risk_e, dist, qty, exposure, profit, rr


@st.cache_data(ttl=300, show_spinner=False)
def market_regime():
    rows = []
    for name, sym in INDEXES.items():
        df = history(sym, "6mo", "1d")
        if df is None or len(df) < 50: continue
        x = indicators(df); r = x.iloc[-1]
        bull = bool(r.Close > r.SMA20 > r.SMA50)
        rows.append({"Marché": name, "Cours": round(float(r.Close), 2), "Régime": "🟢 BULL" if bull else "🔴 RISK-OFF"})
    return pd.DataFrame(rows)


def confirmation(symbol, interval, period):
    df = history(symbol, period, interval)
    if df is None or len(df) < 55: return None
    t = trade_setup(df)
    if not t: return None
    x = t["df"].iloc[-1]
    trend_ok = bool(t["price"] > x.SMA20 > x.SMA50)
    return {"score": t["score"], "trend_ok": trend_ok, "signal": t["signal"], "rsi": t["rsi"]}

# ==========================================================
# SIDEBAR
# ==========================================================
with st.sidebar:
    st.header("⚙️ Command Center")
    mode = st.radio("Navigation", ["🔎 Scanner", "📊 Analyse", "🧪 Simulation", "📓 Journal"])
    st.markdown("---")

    scan_tf_label = st.selectbox("Timeframe principal", list(TF), index=4)
    scan_interval = TF[scan_tf_label]["interval"]
    scan_period = st.selectbox("Historique principal", TF[scan_tf_label]["periods"], index=min(3, len(TF[scan_tf_label]["periods"])-1))

    confirm_tf_label = st.selectbox("Timeframe de confirmation", ["15 minutes","30 minutes","1 hour","1 day","1 week"], index=2)
    confirm_interval = TF[confirm_tf_label]["interval"]
    confirm_period = st.selectbox("Historique confirmation", TF[confirm_tf_label]["periods"], index=min(2, len(TF[confirm_tf_label]["periods"])-1))

    st.markdown("---")
    min_upside = st.number_input("Potentiel minimum (%)", 1.0, 30.0, 5.0, 0.5)
    min_rr = st.number_input("R/R minimum", 1.0, 5.0, 2.0, 0.1)
    min_score = st.slider("Score minimum", 50, 100, 75)
    min_price = st.number_input("Prix minimum", 0.0, 100000.0, 5.0, 1.0)
    min_volume = st.number_input("Volume moyen minimum", 0, 1000000000, 500000, 100000)
    max_atr_pct = st.number_input("ATR maximum (% prix)", 0.5, 30.0, 8.0, 0.5)
    confirm_required = st.checkbox("Confirmation multi-timeframe", True)
    only_long = st.checkbox("Uniquement LONG", True)

    st.markdown("---")
    countries = st.multiselect("Marchés", list(UNIVERSE), default=["USA","France","Germany","Netherlands","UK"])
    max_candidates = st.slider("Maximum analysé", 20, 180, 100, 10)
    capital = st.number_input("Capital de référence (€)", 100.0, 1000000.0, 10000.0, 100.0)
    risk_pct = st.number_input("Risque par trade (%)", 0.1, 3.0, 0.50, 0.05)

    st.markdown("---")
    refresh_min = st.select_slider("Fréquence du scan", [1,2,5,10,15,30,60], value=5)
    auto_refresh = st.checkbox("Scan automatique", True)
    if auto_refresh:
        st_autorefresh(interval=refresh_min * 60 * 1000, key="auto_scan")

# ==========================================================
# HEADER
# ==========================================================
st.title("📈 Trading Command Center — V4.1")
st.caption("Détection automatique de configurations lisibles : potentiel ≥ seuil, R/R ≥ seuil, liquidité, volatilité et confirmation multi-timeframe. Outil d'analyse, pas une recommandation financière.")

with st.expander("🌍 Contexte des marchés", expanded=False):
    mr = market_regime()
    if not mr.empty: st.dataframe(mr, use_container_width=True, hide_index=True)

# ==========================================================
# SCANNER
# ==========================================================
def run_scanner():
    pool = []
    for c in countries: pool.extend(UNIVERSE.get(c, []))
    pool = sorted(set(pool))[:max_candidates]
    rows = []
    bar = st.progress(0)
    for k, sym in enumerate(pool, 1):
        df = history(sym, scan_period, scan_interval)
        if df is None or len(df) < 55:
            bar.progress(k/len(pool)); continue
        t = trade_setup(df)
        if not t:
            bar.progress(k/len(pool)); continue
        avg_vol = float(df["Volume"].tail(20).mean()) if "Volume" in df else 0
        if t["price"] < min_price or avg_vol < min_volume or t["atr_pct"] > max_atr_pct:
            bar.progress(k/len(pool)); continue
        if only_long and t["signal"] != "ACHAT":
            bar.progress(k/len(pool)); continue
        if t["upside"] < min_upside or t["rr"] < min_rr or t["score"] < min_score:
            bar.progress(k/len(pool)); continue
        conf = confirmation(sym, confirm_interval, confirm_period) if confirm_required else None
        if confirm_required and (conf is None or not conf["trend_ok"] or conf["score"] < 65):
            bar.progress(k/len(pool)); continue
        fs, freasons = fundamental_score(info(sym))
        global_score = int(round(0.55*t["score"] + 0.30*fs + 0.15*(100 if conf is None else conf["score"])))
        risk_e, dist, qty, exposure, profit, rr = position_calc(capital, risk_pct, t["entry"], t["stop"], t["tp2"])
        rows.append({
            "Ticker": sym, "Score": global_score, "Tech": t["score"], "Fond.": fs,
            "Prix": t["price"], "Entrée": t["entry"], "Stop": t["stop"], "TP1": t["tp1"], "TP2": t["tp2"],
            "Potentiel %": t["upside"], "R/R": t["rr"], "ATR %": t["atr_pct"], "Vol x20": t["volume_ratio"],
            "Qualité": t["quality"], "Confirmation": "OK" if not confirm_required else "OK"
        })
        bar.progress(k/len(pool))
    bar.empty()
    return pd.DataFrame(rows)

if mode == "🔎 Scanner":
    st.header("🔎 Meilleures opportunités")
    st.info(f"Le moteur écarte les configurations sous {min_upside:.1f}% de potentiel, sous {min_rr:.1f}R/R, sous {min_score}/100, trop volatiles ou insuffisamment liquides.")
    ranking = run_scanner()
    if ranking.empty:
        st.warning("Aucune configuration ne passe actuellement tous les filtres. C'est volontaire : l'absence de trade est préférable à un setup médiocre.")
    else:
        ranking = ranking.sort_values(["Score","R/R","Potentiel %"], ascending=False).reset_index(drop=True)
        st.success(f"🎯 {len(ranking)} configuration(s) qualifiée(s)")
        top = ranking.head(5)
        st.subheader("🏆 Top 5")
        cols = st.columns(min(5, len(top)))
        for col, (_, r) in zip(cols, top.iterrows()):
            with col:
                st.metric(r["Ticker"], f"{r['Potentiel %']:.1f}%", f"Score {int(r['Score'])}")
                st.caption(f"R/R {r['R/R']:.2f} • {r['Qualité']} • Entrée {r['Entrée']:.2f}")
        st.subheader("Classement complet")
        st.dataframe(ranking, use_container_width=True, hide_index=True)
        st.session_state["scan_results"] = ranking
        st.caption(f"Dernier scan : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# ==========================================================
# ANALYSE
# ==========================================================
elif mode == "📊 Analyse":
    st.header("📊 Analyse détaillée")
    pool = sorted(set(sum([UNIVERSE.get(c, []) for c in countries], [])))
    symbol = st.selectbox("Valeur", pool if pool else ["AAPL"])
    a_tf = st.selectbox("Timeframe", list(TF), index=4)
    a_period = st.selectbox("Historique", TF[a_tf]["periods"], index=min(3, len(TF[a_tf]["periods"])-1))
    df = history(symbol, a_period, TF[a_tf]["interval"])
    t = trade_setup(df) if df is not None else None
    if not t:
        st.warning("Données insuffisantes pour cette configuration.")
    else:
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Prix", f"{t['price']:.2f}")
        c2.metric("Score", f"{t['score']}/100")
        c3.metric("Potentiel", f"{t['upside']:.1f}%")
        c4.metric("R/R", f"{t['rr']:.2f}")
        c5.metric("Qualité", t['quality'])
        st.divider()
        a,b,c,d,e = st.columns(5)
        a.metric("Entrée", f"{t['entry']:.2f}")
        b.metric("Stop", f"{t['stop']:.2f}")
        c.metric("TP1", f"{t['tp1']:.2f}")
        d.metric("TP2", f"{t['tp2']:.2f}")
        e.metric("Résistance", f"{t['resistance']:.2f}")
        with st.expander("🔬 Détails techniques", True):
            st.write(f"RSI : **{t['rsi']:.1f}** • ATR : **{t['atr']:.2f}** ({t['atr_pct']:.1f}%) • Volume : **{t['volume_ratio']:.2f}x**")
            st.write(" • ".join(t["reasons"]))
        with st.expander("🏢 Fondamentaux et actualités", False):
            fs, fr = fundamental_score(info(symbol)); st.write(f"Score fondamentaux : **{fs}/100**")
            if fr: st.write(" • ".join(fr))
            for n in news(symbol)[:8]:
                st.markdown(f"**{n['title']}** — {n['publisher']}")

# ==========================================================
# SIMULATION
# ==========================================================
elif mode == "🧪 Simulation":
    st.header("🧪 Simulation / ticket de trade")
    symbol = st.text_input("Ticker", "AAPL").upper().strip()
    direction = st.radio("Sens", ["LONG"], horizontal=True)
    df = history(symbol, "6mo", "1d")
    t = trade_setup(df) if df is not None else None
    if not t:
        st.warning("Impossible de calculer un setup pour ce ticker.")
    else:
        entry = st.number_input("Entrée", value=float(t["entry"]), format="%.4f")
        stop = st.number_input("Stop", value=float(t["stop"]), format="%.4f")
        target = st.number_input("Objectif TP2", value=float(t["tp2"]), format="%.4f")
        risk_e, dist, qty, exposure, profit, rr = position_calc(capital, risk_pct, entry, stop, target)
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Risque max", f"{risk_e:.2f} €")
        c2.metric("Quantité", str(qty))
        c3.metric("Exposition", f"{exposure:.2f} €")
        c4.metric("Gain cible", f"{profit:.2f} €")
        c5.metric("R/R", f"{rr:.2f}")
        st.info("Le calcul de quantité limite la perte théorique au risque choisi si le stop est exécuté au niveau prévu. L'exécution réelle peut différer.")
        st.code(f"{direction} {symbol} | Entrée {entry:.4f} | SL {stop:.4f} | TP {target:.4f} | Qté {qty}")

# ==========================================================
# JOURNAL
# ==========================================================
else:
    st.header("📓 Journal de trading")
    st.caption("Journal conservé pendant la session Streamlit actuelle.")
    if "journal" not in st.session_state: st.session_state["journal"] = []
    with st.form("journal_form"):
        sym = st.text_input("Ticker", "AAPL").upper()
        setup = st.text_input("Configuration", "Breakout / pullback")
        result = st.selectbox("Résultat", ["Ouvert","Gagnant","Perdant","Annulé"])
        note = st.text_area("Note")
        submitted = st.form_submit_button("Ajouter")
        if submitted:
            st.session_state["journal"].append({"Date": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ticker": sym, "Setup": setup, "Résultat": result, "Note": note})
    if st.session_state["journal"]:
        st.dataframe(pd.DataFrame(st.session_state["journal"]), use_container_width=True, hide_index=True)
    else:
        st.info("Aucune opération enregistrée.")

st.markdown("---")
st.caption("V4.1 — analyse indicative via yfinance. Pas d'exécution automatique d'ordres. Toujours vérifier les données, le contexte et les conditions d'exécution avant toute décision.")
