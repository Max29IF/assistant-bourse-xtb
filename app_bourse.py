
import hashlib
import math
import os
import sqlite3

try:
    from supabase import create_client
except Exception:
    create_client = None
from datetime import datetime, date, timedelta

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Trading Command Center — V6.2",
    page_icon="📈",
    layout="wide",
)

# ==========================================================
# AUTHENTICATION
# ==========================================================
def password_ok(password: str) -> bool:
    expected = st.secrets.get("APP_PASSWORD", os.getenv("APP_PASSWORD", ""))
    expected_hash = st.secrets.get("APP_PASSWORD_HASH", os.getenv("APP_PASSWORD_HASH", ""))
    if expected_hash:
        return hashlib.sha256(password.encode()).hexdigest() == expected_hash
    return bool(expected) and password == expected


def login_gate():
    if st.session_state.get("authenticated", False):
        return True

    st.markdown(
        """
        <style>
        .login-box {max-width:520px;margin:7vh auto 0 auto;padding:2rem;border:1px solid #ddd;border-radius:18px;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.title("🔐 Trading Command Center")
    st.caption("Accès privé. Le mot de passe est lu depuis les Secrets Streamlit ou la variable APP_PASSWORD.")
    with st.form("login_form"):
        password = st.text_input("Code / mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter", type="primary")
        if submitted:
            if password_ok(password):
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Code incorrect.")
    st.markdown("</div>", unsafe_allow_html=True)
    return False


if not login_gate():
    st.stop()

# ==========================================================
# PERSISTENCE — SUPABASE (fallback SQLite local)
# ==========================================================
DB_PATH = os.getenv("PORTFOLIO_DB_PATH", "portfolio_data.db")

def get_supabase():
    url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
    key = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))
    if not url or not key or create_client is None:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None

SUPABASE = get_supabase()

def db_conn():
    conn=sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS journal (id INTEGER PRIMARY KEY AUTOINCREMENT, account TEXT, date TEXT, ticker TEXT, setup TEXT, result TEXT, note TEXT)")
    conn.commit(); return conn

def load_portfolio_db(account):
    """Charge automatiquement le portefeuille persistant.
    Aucun bouton Enregistrer n'est nécessaire à chaque connexion.
    """
    if SUPABASE is not None:
        try:
            res = (SUPABASE.table("portfolio_positions")
                   .select("ticker,quantity,pru,purchase_date")
                   .eq("account", account)
                   .order("ticker")
                   .execute())
            rows = getattr(res, "data", None) or []
            if rows:
                return normalize_portfolio(pd.DataFrame([
                    {
                        "Ticker": r.get("ticker", ""),
                        "Quantité": r.get("quantity", 0),
                        "PRU": r.get("pru", 0),
                        "Date achat": r.get("purchase_date", ""),
                    } for r in rows
                ]))
            return default_portfolio()
        except Exception as exc:
            st.error(f"Supabase indisponible pour {account} : {exc}")
            return default_portfolio()
    return default_portfolio()

def save_portfolio_db(account, portfolio):
    """Remplace proprement les lignes d'un compte dans Supabase.
    L'appel est fait automatiquement après un import CSV ou une modification validée.
    """
    portfolio = normalize_portfolio(portfolio)
    if SUPABASE is None:
        st.error("Supabase n'est pas configuré : ajoute SUPABASE_URL et SUPABASE_KEY dans les Secrets Streamlit.")
        return False
    try:
        # On remplace uniquement le portefeuille du compte concerné.
        SUPABASE.table("portfolio_positions").delete().eq("account", account).execute()
        rows = []
        for _, row in portfolio.iterrows():
            d = row["Date achat"]
            d = d.isoformat() if pd.notna(d) else None
            rows.append({
                "account": account,
                "ticker": str(row["Ticker"]),
                "quantity": float(row["Quantité"]),
                "pru": float(row["PRU"]),
                "purchase_date": d,
            })
        if rows:
            SUPABASE.table("portfolio_positions").insert(rows).execute()
        return True
    except Exception as exc:
        st.error(f"Échec de sauvegarde Supabase : {exc}")
        return False

def save_import_metadata(account, filename, file_hash, row_count, skipped_count):
    """Enregistre la dernière synchronisation CSV pour pouvoir la tracer."""
    if SUPABASE is None:
        return False
    try:
        payload = {
            "account": account,
            "filename": filename,
            "file_hash": file_hash,
            "row_count": int(row_count),
            "skipped_count": int(skipped_count),
            "imported_at": datetime.utcnow().isoformat(),
        }
        SUPABASE.table("portfolio_imports").upsert(payload, on_conflict="account").execute()
        return True
    except Exception as exc:
        st.warning(f"Portefeuille enregistré, mais historique de synchronisation indisponible : {exc}")
        return False

def load_import_metadata(account):
    if SUPABASE is None:
        return None
    try:
        res = (SUPABASE.table("portfolio_imports")
               .select("filename,file_hash,row_count,skipped_count,imported_at")
               .eq("account", account)
               .limit(1)
               .execute())
        rows = getattr(res, "data", None) or []
        return rows[0] if rows else None
    except Exception:
        return None

def load_journal_db():
    if SUPABASE is not None:
        try:
            res=SUPABASE.table("journal").select("date,ticker,setup,result,note").order("id",desc=True).execute()
            rows=getattr(res,"data",None) or []
            return [{"Date":r.get("date",""),"Ticker":r.get("ticker",""),"Setup":r.get("setup",""),"Résultat":r.get("result",""),"Note":r.get("note","")} for r in rows]
        except Exception: pass
    conn=db_conn(); rows=conn.execute("SELECT date,ticker,setup,result,note FROM journal ORDER BY id DESC").fetchall(); conn.close()
    return [{"Date":r[0],"Ticker":r[1],"Setup":r[2],"Résultat":r[3],"Note":r[4]} for r in rows]

def save_journal_db(sym,setup,result,note):
    now=datetime.now().strftime("%d/%m/%Y %H:%M")
    if SUPABASE is not None:
        try:
            SUPABASE.table("journal").insert({"account":"global","date":now,"ticker":sym,"setup":setup,"result":result,"note":note}).execute(); return True
        except Exception as exc:
            st.error(f"Échec d'enregistrement du journal dans Supabase : {exc}"); return False
    conn=db_conn(); conn.execute("INSERT INTO journal(account,date,ticker,setup,result,note) VALUES(?,?,?,?,?,?)",("global",now,sym,setup,result,note)); conn.commit(); conn.close(); return True

# ==========================================================
# UNIVERSE
# ==========================================================
UNIVERSE = {
    "USA": ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","AVGO","AMD","NFLX","ADBE","CRM","ORCL","QCOM","INTC","MU","AMAT","LRCX","PANW","CRWD","PLTR","NOW","SNOW","UBER","ABNB","SHOP","COIN","MSTR","JPM","BAC","GS","MS","V","MA","PYPL","WMT","COST","HD","MCD","KO","PEP","NKE","CAT","DE","GE","HON","RTX","BA","LMT","XOM","CVX","COP","SLB","LLY","JNJ","PFE","MRK","ABBV","UNH","TMO","ISRG","SPOT","DIS","CMCSA","T","VZ","LIN","UPS","LOW","BKNG","INTU","CSCO","IBM","TXN","SBUX","ORLY","CVS"],
    "France": ["MC.PA","OR.PA","AIR.PA","SAN.PA","SU.PA","TTE.PA","BNP.PA","AI.PA","SAF.PA","DG.PA","CS.PA","CAP.PA","ACA.PA","GLE.PA","VIV.PA","KER.PA","RMS.PA","ENGI.PA","ORA.PA","STMPA.PA","EL.PA","RI.PA"],
    "Germany": ["SAP.DE","SIE.DE","ALV.DE","DTE.DE","AIR.DE","MBG.DE","BMW.DE","VOW3.DE","BAS.DE","BAYN.DE","ADS.DE","IFX.DE","DBK.DE","DB1.DE","MUV2.DE","RWE.DE","VNA.DE","HEN3.DE"],
    "Netherlands": ["ASML.AS","ADYEN.AS","INGA.AS","PRX.AS","PHIA.AS","HEIA.AS","DSM.AS"],
    "UK": ["SHEL.L","AZN.L","HSBA.L","ULVR.L","BP.L","GSK.L","RIO.L","LSEG.L","REL.L","BARC.L","VOD.L","DGE.L","BA.L"],
    "Spain": ["IBE.MC","ITX.MC","SAN.MC","BBVA.MC","TEF.MC","REP.MC"],
    "Italy": ["ENEL.MI","ENI.MI","ISP.MI","UCG.MI","STLAM.MI","RACE.MI"],
    "Switzerland": ["NESN.SW","NOVN.SW","ROG.SW","UBSG.SW","ZURN.SW","CFR.SW"],
    "Nordics": ["NOVO-B.CO","MAERSK-B.CO","EQNR.OL","DNB.OL","VOLV-B.ST","ATCO-A.ST","ERIC-B.ST","NOKIA.HE","KNEBV.HE","ORNBV.HE","NDA-FI.HE"],
}

INDEXES = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "CAC 40": "^FCHI",
    "DAX": "^GDAXI",
    "Euro Stoxx 50": "^STOXX50E",
    "FTSE 100": "^FTSE",
}

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
@st.cache_data(ttl=90, show_spinner=False)
def history(symbol, period, interval, auto_adjust=False):
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=auto_adjust)
        if df is None or df.empty:
            return None
        return df.dropna(subset=["Open","High","Low","Close"])
    except Exception:
        return None


@st.cache_data(ttl=900, show_spinner=False)
def info(symbol):
    try:
        return yf.Ticker(symbol).info or {}
    except Exception:
        return {}


@st.cache_data(ttl=60, show_spinner=False)
def live_quote(symbol):
    try:
        t = yf.Ticker(symbol)
        fi = getattr(t, "fast_info", None)
        price = None
        currency = None
        if fi:
            try:
                price = fi.get("last_price")
            except Exception:
                price = None
            try:
                currency = fi.get("currency")
            except Exception:
                currency = None
        if price is None:
            df = t.history(period="1d", interval="1m", auto_adjust=False)
            if df is not None and not df.empty:
                price = float(df["Close"].dropna().iloc[-1])
        inf = info(symbol)
        name = inf.get("longName") or inf.get("shortName") or symbol
        currency = currency or inf.get("currency") or ""
        return {"price": float(price) if price is not None else None, "currency": currency, "name": name, "timestamp": datetime.now()}
    except Exception:
        return {"price": None, "currency": "", "name": symbol, "timestamp": datetime.now()}


@st.cache_data(ttl=600, show_spinner=False)
def dividends(symbol, start_date):
    try:
        d = yf.Ticker(symbol).dividends
        if d is None or d.empty:
            return pd.Series(dtype=float)
        d.index = pd.to_datetime(d.index).tz_localize(None)
        return d[d.index >= pd.Timestamp(start_date)]
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(ttl=600, show_spinner=False)
def news(symbol):
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
    rr = (tp2 - entry) / risk if risk else 0
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
        "reasons": reasons, "dist_res": dist_res,
    }


def fundamental_score(i):
    if not i:
        return 50, []
    s = 50
    reasons = []
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
        if df is None or len(df) < 50:
            continue
        x = indicators(df)
        r = x.iloc[-1]
        bull = bool(r.Close > r.SMA20 > r.SMA50)
        rows.append({"Marché": name, "Cours": round(float(r.Close), 2), "Régime": "🟢 BULL" if bull else "🔴 RISK-OFF"})
    return pd.DataFrame(rows)


def confirmation(symbol, interval, period):
    df = history(symbol, period, interval)
    if df is None or len(df) < 55:
        return None
    t = trade_setup(df)
    if not t:
        return None
    x = t["df"].iloc[-1]
    trend_ok = bool(t["price"] > x.SMA20 > x.SMA50)
    return {"score": t["score"], "trend_ok": trend_ok, "signal": t["signal"], "rsi": t["rsi"]}

# ==========================================================
# PORTFOLIO ENGINE
# ==========================================================

# ==========================================================
# IMPORT PEA — FORMAT EXPORT BROKER (name / isin / quantity...)
# ==========================================================
# ==========================================================
# UNIVERSAL BROKER IMPORT
# ==========================================================
# Known mappings for the user's current PEA export. The importer does not
# depend on these mappings: if a ticker/symbol is present in the broker file,
# it uses it directly. ISIN/name mappings are only a fallback.
ISIN_TO_TICKER = {
    "FR0013341781": "2CRSI.PA", "FR0000120073": "AI.PA",
    "FR0000120628": "CS.PA", "FR0011550185": "ESE.PA",
    "FR0000045072": "ACA.PA", "FR0010208488": "ENGI.PA",
    "FR0000062671": "EXA.PA", "FR0014010QE1": "MLHPI.PA",
    "FR0014001PM5": "ALHRS.PA", "FR001400SF56": "LOUP.PA",
    "FR0000038242": "LBIRD.PA", "FR0000121014": "MC.PA",
    "FR0011049824": "ALMDT.PA", "FR0013269123": "RUI.PA",
    "FR0000125007": "SGO.PA", "FR0000121972": "SU.PA",
    "FR0010528059": "ALSTW.PA", "NL0014559478": "TE.PA",
    "FR0000120271": "TTE.PA", "FR0000124141": "VIE.PA",
}
NAME_TO_TICKER = {
    "2CRSI": "2CRSI.PA", "AIR LIQUIDE": "AI.PA", "AXA": "CS.PA",
    "BNPP EASY S&P 500 ETF EUR C": "ESE.PA", "CREDIT AGRICOLE SA": "ACA.PA",
    "ENGIE": "ENGI.PA", "EXAIL TECHNOLOGIES": "EXA.PA", "HOPIUM": "MLHPI.PA",
    "HRS (HYDROGEN REFUELING SOL.)": "ALHRS.PA", "LDC": "LOUP.PA",
    "LUMIBIRD": "LBIRD.PA", "LVMH": "MC.PA", "MEDIAN TECHNOLOGIES": "ALMDT.PA",
    "RUBIS": "RUI.PA", "SAINT-GOBAIN": "SGO.PA", "SCHNEIDER ELECTRIC": "SU.PA",
    "STREAMWIDE": "ALSTW.PA", "TECHNIP ENERGIES": "TE.PA",
    "TOTALENERGIES": "TTE.PA", "VEOLIA": "VIE.PA",
}

FIELD_ALIASES = {
    "ticker": ["ticker","symbol","symbole","code","codevaleur","instrumentcode","securitycode",
               "securityid","instrumentid","stockcode","stockticker","mnemonic","valor","valoris"],
    "isin": ["isin","isincode","isin code","identifiantisin","isinvalue"],
    "name": ["name","nom","libelle","libellé","instrument","instrumentname","security",
             "securityname","product","productname","asset","assetname","designation"],
    "quantity": ["quantity","qty","quantite","quantité","shares","share","units","unit",
                 "position","positions","numberofshares","nombre","nbtitres","titres"],
    "pru": ["buyingprice","buyprice","purchaseprice","purchase_price","averageprice","avgprice",
            "averagecost","avgcost","costbasis","costbasisprice","prixmoyen","prix moyen",
            "pru","prixderevient","prixderevientunitaire","prixachat","prixdachat"],
    "last_price": ["lastprice","last_price","currentprice","current_price","marketprice",
                   "market_price","price","cours","coursactuel","prixactuel","currentvalueprice"],
    "value": ["amount","marketvalue","market_value","value","valorisation","valorisationposition",
              "positionvalue","valeur","valeurposition","netvalue"],
    "currency": ["currency","devise","ccy","monnaie"],
    "date": ["purchasedate","buydate","acquisitiondate","tradedate","dateachat","dateachat",
             "date","lastmovementdate","lastmovement","dateoperation"],
}

def _norm_text(value):
    import unicodedata
    s = str(value or "").replace("\ufeff","").replace("\x00","").strip().lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", s)

def _clean_num(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan
    s = str(value).strip().replace("\u00a0"," ").replace("€","").replace("$","").replace("£","")
    if not s or s.lower() in {"nan","none","null","-","—","n/a","na"}:
        return np.nan
    s = s.replace(" ","")
    # Negative parentheses: (123,45) -> -123.45
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    if "," in s and "." in s:
        s = s.replace(".","").replace(",",".") if s.rfind(",") > s.rfind(".") else s.replace(",","")
    elif "," in s:
        s = s.replace(",",".")
    try:
        return float(s)
    except Exception:
        return np.nan

def _read_universal_csv(uploaded_file):
    """Lecteur universel : inspecte les octets, jamais l'extension du fichier.
    Accepte CSV/TSV même avec une extension .xls/.txt/.csv.xls.
    Reconnaît UTF-8 BOM, UTF-8, UTF-16, cp1252 et latin1.
    """
    from io import StringIO, BytesIO
    raw = uploaded_file.getvalue()
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    if not raw:
        raise ValueError("Le fichier est vide.")

    # Vrai Excel : signature OLE2 (.xls) ou ZIP (.xlsx/.xlsm)
    if raw[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" or raw[:4] == b"PK\x03\x04":
        try:
            xls = pd.ExcelFile(BytesIO(raw))
            frames=[]
            for sheet in xls.sheet_names:
                d=pd.read_excel(xls, sheet_name=sheet, dtype=str)
                if d is not None and not d.empty:
                    frames.append(d)
            if frames:
                return max(frames, key=lambda d: len(d.columns))
        except Exception as exc:
            raise ValueError(f"Vrai fichier Excel détecté mais impossible à lire : {exc}")

    # Décodage direct des octets.
    encodings=[]
    if raw.startswith(b"\xef\xbb\xbf"):
        encodings.append("utf-8-sig")
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        encodings.append("utf-16")
    encodings += ["utf-8", "cp1252", "latin1"]
    text=None
    used_encoding=None
    for enc in dict.fromkeys(encodings):
        try:
            text=raw.decode(enc)
            used_encoding=enc
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text=raw.decode("utf-8", errors="replace")
        used_encoding="utf-8-replace"
    text=text.replace("\x00", "").lstrip("\ufeff")
    if not text.strip():
        raise ValueError("Le fichier est vide après décodage.")

    # Détection robuste du séparateur sur l'en-tête + premières lignes.
    sample="\n".join(text.splitlines()[:8])
    separators=[";", "\t", ",", "|", ":"]
    candidates=[]
    for sep in separators:
        try:
            d=pd.read_csv(StringIO(text), sep=sep, dtype=str, engine="python",
                          keep_default_na=False, quotechar='"', on_bad_lines="skip")
            if len(d.columns) < 2:
                continue
            # Un séparateur est crédible s'il produit plusieurs colonnes et des champs connus.
            normcols=[_norm_text(c) for c in d.columns]
            useful=sum(1 for aliases in FIELD_ALIASES.values()
                       if any(a==n for a in aliases for n in normcols))
            header_count=sample.splitlines()[0].count(sep) if sample.splitlines() else 0
            score=useful*10 + min(len(d.columns),30) + min(header_count,30)*0.2
            candidates.append((score, len(d.columns), d, sep))
        except Exception:
            pass

    if not candidates:
        preview=repr(raw[:240])
        raise ValueError(
            f"Impossible de lire '{getattr(uploaded_file,'name','fichier')}' comme CSV/texte délimité. "
            f"Début du fichier : {preview}"
        )
    _, _, df, sep = max(candidates, key=lambda x:(x[0],x[1]))
    df.columns=[str(c).replace("\ufeff","").replace("\x00","").strip().strip('"') for c in df.columns]
    # Retire les lignes entièrement vides.
    df=df.dropna(how="all").reset_index(drop=True)
    if df.empty or len(df.columns)<2:
        raise ValueError("Le fichier a été décodé mais aucune donnée tabulaire exploitable n'a été trouvée.")
    return df

def _find_field(columns, field):
    """Fuzzy, accent/space/case independent field detection."""
    normalized = {_norm_text(c): c for c in columns}
    aliases = {_norm_text(a) for a in FIELD_ALIASES.get(field, [])}
    # Exact normalized aliases first.
    for a in aliases:
        if a in normalized:
            return normalized[a]
    # Then safe contains matching for broker-specific verbose headers.
    for n, original in normalized.items():
        if len(n) >= 4 and any(a in n or n in a for a in aliases if len(a) >= 4):
            return original
    return None

def detect_file_type(df):
    fields = {f:_find_field(df.columns,f) for f in FIELD_ALIASES}
    found = {k:v for k,v in fields.items() if v}
    accounting = sum(_norm_text(c) in {"date","label","debit","credit"} for c in df.columns)
    position_score = sum(bool(found.get(k)) for k in ("name","isin","ticker","quantity","pru","last_price","value"))
    if accounting >= 3 and position_score < 3:
        return "comptabilite", fields
    if position_score >= 2 and (found.get("quantity") or found.get("value")):
        return "positions", fields
    return "inconnu", fields

def _resolve_ticker(ticker, isin, name):
    t = str(ticker or "").strip().upper()
    if t and t not in {"NAN","NONE","NULL","-"}:
        # Common broker formats: remove exchange suffix only when clearly present?
        # Keep the broker ticker; yfinance accepts many exchange-qualified symbols.
        return t
    i = str(isin or "").strip().upper()
    if i in ISIN_TO_TICKER:
        return ISIN_TO_TICKER[i]
    n = str(name or "").strip().upper()
    if n in NAME_TO_TICKER:
        return NAME_TO_TICKER[n]
    return ""

def _parse_date(value):
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip()
    # ISO dates (YYYY-MM-DD / timestamps) must be parsed without dayfirst.
    if re.match(r"^\d{4}-\d{2}-\d{2}", text):
        d = pd.to_datetime(text, errors="coerce")
    else:
        d = pd.to_datetime(text, dayfirst=True, errors="coerce")
    return d.date() if pd.notna(d) else None

def detect_broker(df, fields):
    """Best-effort broker detection from headers. It never controls the import."""
    cols = {_norm_text(c) for c in df.columns}
    if {"name","isin","quantity","buyingprice"} <= cols:
        return "BoursoBank / export positions compatible"
    if any(x in cols for x in {"averagebuyin","averagebuyprice","totalreturn","netreturn"}) and (
        "isin" in cols or "instrument" in cols
    ):
        return "Trade Republic / format proche"
    if any(x in cols for x in {"openprice","closeprice","profitloss","profit","swap"}) and (
        "symbol" in cols or "instrument" in cols
    ):
        return "XTB / format proche"
    if {"date","label","debit","credit"} <= cols:
        return "Comptabilité"
    return "Courtier non identifié — format universel"


def import_universal_broker_file(uploaded_file):
    """
    Universal importer:
      - detects accounting vs positions
      - detects columns using aliases/fuzzy matching
      - accepts ticker OR ISIN OR known company name
      - accepts PRU under many broker names
      - accepts European number formats
      - does not invent ambiguous rows
    """
    df = _read_universal_csv(uploaded_file)
    file_type, fields = detect_file_type(df)

    if file_type == "comptabilite":
        raise ValueError("Fichier comptable détecté (DATE/LABEL/DEBIT/CREDIT). Ce fichier ne contient pas de positions de portefeuille.")

    if file_type != "positions":
        raise ValueError(
            "Type de fichier non reconnu automatiquement. "
            "Il faut au minimum une identification du titre (Ticker, ISIN ou Nom) "
            "et une information de position (Quantité ou Valeur)."
        )

    # Quantity can be absent when a broker export contains only value; we refuse
    # to invent a quantity because portfolio analytics would then be wrong.
    if not fields.get("quantity"):
        raise ValueError(
            "Le fichier est bien un portefeuille, mais la colonne Quantité n'a pas été identifiée. "
            "Je préfère bloquer plutôt que d'inventer une position."
        )

    rows, errors = [], []
    for idx, r in df.iterrows():
        name = str(r.get(fields.get("name"), "")).strip() if fields.get("name") else ""
        isin = str(r.get(fields.get("isin"), "")).strip().upper() if fields.get("isin") else ""
        raw_ticker = r.get(fields.get("ticker"), "") if fields.get("ticker") else ""
        ticker = _resolve_ticker(raw_ticker, isin, name)

        qty = _clean_num(r.get(fields["quantity"]))
        raw_pru = _clean_num(r.get(fields["pru"])) if fields.get("pru") else np.nan
        raw_last = _clean_num(r.get(fields["last_price"])) if fields.get("last_price") else np.nan
        raw_value = _clean_num(r.get(fields["value"])) if fields.get("value") else np.nan
        currency = str(r.get(fields.get("currency"), "")).strip().upper() if fields.get("currency") else ""
        dt = _parse_date(r.get(fields["date"])) if fields.get("date") else None

        if not ticker:
            errors.append({"Ligne":idx+2,"Nom":name,"ISIN":isin,"Motif":"Titre non identifié (Ticker/ISIN/Nom inconnus)"})
            continue
        if not np.isfinite(qty) or qty <= 0:
            errors.append({"Ligne":idx+2,"Nom":name,"ISIN":isin,"Ticker":ticker,"Motif":"Quantité invalide"})
            continue

        # A missing PRU is allowed: position can still be imported, but flagged.
        pru = raw_pru if np.isfinite(raw_pru) and raw_pru > 0 else 0.0
        if pru == 0:
            errors.append({"Ligne":idx+2,"Nom":name,"ISIN":isin,"Ticker":ticker,"Motif":"PRU absent : position importée mais PRU à compléter"})

        rows.append({
            "Ticker": ticker, "Quantité": qty, "PRU": pru, "Date achat": dt,
            "_Nom": name, "_ISIN": isin, "_Devise": currency,
            "_Cours import": raw_last if np.isfinite(raw_last) else np.nan,
            "_Valeur import": raw_value if np.isfinite(raw_value) else np.nan,
        })

    if not rows:
        return default_portfolio(), pd.DataFrame(errors), {"type":file_type, "fields":fields, "rows_read":len(df)}

    out = pd.DataFrame(rows)
    # Aggregate duplicates by ticker with weighted PRU. Preserve metadata.
    grouped = []
    for ticker, g in out.groupby("Ticker", sort=True):
        q = g["Quantité"].sum()
        positive_cost = g["PRU"] > 0
        weighted_pru = ((g.loc[positive_cost,"Quantité"] * g.loc[positive_cost,"PRU"]).sum() /
                        g.loc[positive_cost,"Quantité"].sum()) if positive_cost.any() else 0.0
        dates = [d for d in g["Date achat"] if pd.notna(d)]
        first = g.iloc[0]
        grouped.append({
            "Ticker":ticker, "Quantité":q, "PRU":weighted_pru,
            "Date achat":min(dates) if dates else None,
        })
    portfolio = normalize_portfolio(pd.DataFrame(grouped))
    meta = {"type":file_type, "broker":detect_broker(df, fields), "fields":fields, "rows_read":len(df), "rows_imported":len(portfolio)}
    return portfolio, pd.DataFrame(errors), meta

# Backward-compatible name used by the page.
def import_broker_pea(uploaded_file):
    portfolio, errors, meta = import_universal_broker_file(uploaded_file)
    return portfolio, errors, meta

def default_portfolio():
    return pd.DataFrame(columns=["Ticker","Quantité","PRU","Date achat"])


def normalize_portfolio(df):
    if df is None or df.empty:
        return default_portfolio()
    x = df.copy()
    for col in ["Ticker","Quantité","PRU","Date achat"]:
        if col not in x.columns:
            x[col] = "" if col in ["Ticker","Date achat"] else 0.0
    x = x[["Ticker","Quantité","PRU","Date achat"]]
    x["Ticker"] = x["Ticker"].astype(str).str.upper().str.strip()
    x["Quantité"] = pd.to_numeric(x["Quantité"], errors="coerce").fillna(0.0)
    x["PRU"] = pd.to_numeric(x["PRU"], errors="coerce").fillna(0.0)
    x["Date achat"] = pd.to_datetime(x["Date achat"], errors="coerce").dt.date
    return x[x["Ticker"] != ""].reset_index(drop=True)


def portfolio_metrics(portfolio):
    rows = []
    for _, p in portfolio.iterrows():
        sym = p["Ticker"]
        qty = float(p["Quantité"])
        pru = float(p["PRU"])
        if qty <= 0 or pru <= 0:
            continue
        q = live_quote(sym)
        price = q["price"]
        name = q["name"]
        currency = q["currency"]
        if price is None:
            continue
        value = qty * price
        cost = qty * pru
        pnl = value - cost
        pnl_pct = pnl / cost * 100 if cost else 0
        start = p["Date achat"] if pd.notna(p["Date achat"]) else date.today() - timedelta(days=365)
        div = dividends(sym, start)
        div_total = float(div.sum() * qty) if not div.empty else 0.0
        total_pnl = pnl + div_total
        total_pct = total_pnl / cost * 100 if cost else 0
        rows.append({
            "Ticker": sym, "Entreprise": name, "Devise": currency, "Qté": qty,
            "PRU": pru, "Cours": price, "Valeur": value, "Investi": cost,
            "Plus-value": pnl, "Perf cours %": pnl_pct,
            "Dividendes": div_total, "Perf totale": total_pnl, "Perf totale %": total_pct,
            "Date": q["timestamp"].strftime("%d/%m/%Y %H:%M"),
        })
    out = pd.DataFrame(rows)
    if not out.empty:
        out["Poids %"] = out["Valeur"] / out["Valeur"].sum() * 100
    return out


def portfolio_curve(portfolio):
    if portfolio.empty:
        return None
    series = []
    total_cost = 0.0
    for _, p in portfolio.iterrows():
        sym = p["Ticker"]
        qty = float(p["Quantité"])
        pru = float(p["PRU"])
        if qty <= 0 or pru <= 0:
            continue
        start = p["Date achat"] if pd.notna(p["Date achat"]) else date.today() - timedelta(days=365)
        df = history(sym, "10y", "1d", auto_adjust=False)
        if df is None or df.empty:
            continue
        df = df[df.index.tz_localize(None) >= pd.Timestamp(start)]
        if df.empty:
            continue
        close = df["Close"].astype(float) * qty
        div = df["Dividends"].fillna(0).astype(float) * qty if "Dividends" in df else pd.Series(0.0, index=df.index)
        cum_div = div.cumsum()
        value = close + cum_div
        value.name = sym
        series.append(value)
        total_cost += qty * pru
    if not series or total_cost <= 0:
        return None
    curve = pd.concat(series, axis=1).ffill().sum(axis=1) + (total_cost - sum(float(p["Quantité"]) * float(p["PRU"]) for _, p in portfolio.iterrows()))
    # Rebase at invested capital. This curve includes cash dividends but does not reinvest them.
    curve = curve.dropna()
    return curve / total_cost * 100 - 100


def arbitrage_table(metrics):
    if metrics.empty:
        return pd.DataFrame()
    rows = []
    for _, r in metrics.iterrows():
        t = trade_setup(history(r["Ticker"], "6mo", "1d"))
        score = t["score"] if t else 50
        upside = t["upside"] if t else 0
        if score >= 85 and upside >= 5:
            action = "🟢 Renforcer / conserver"
        elif score < 60 or upside < 2:
            action = "🟠 Examiner un allègement"
        else:
            action = "🟡 Conserver / surveiller"
        rows.append({
            "Ticker": r["Ticker"], "Entreprise": r["Entreprise"], "Poids %": r["Poids %"],
            "Score technique": score, "Potentiel setup %": upside,
            "Piste d'arbitrage": action,
        })
    return pd.DataFrame(rows).sort_values(["Score technique","Poids %"], ascending=[False, False])


def show_portfolio_page(title, key):
    st.header(title)
    st.caption("Import universel multi-courtiers : détection automatique du format, des colonnes, de l’encodage et du séparateur. Les cours et noms sont ensuite actualisés depuis la source de marché.")

    if key not in st.session_state:
        st.session_state[key] = load_portfolio_db(key)

    sync_meta = load_import_metadata(key)
    if sync_meta:
        st.success(
            f"☁️ Portefeuille chargé automatiquement depuis Supabase — "
            f"{sync_meta.get('row_count', 0)} ligne(s) — "
            f"dernière synchro : {sync_meta.get('imported_at', 'inconnue')}"
        )
    else:
        st.info("☁️ Aucun import CSV enregistré pour ce portefeuille. Le premier import sera sauvegardé automatiquement.")

    upload = st.file_uploader(
        "📥 Importer ton export CSV PEA",
        type=["csv","xls","xlsx","txt"],
        key=f"{key}_upload",
        help="Import universel : l’application détecte automatiquement le courtier, les colonnes, l’encodage et le séparateur.",
    )

    if upload is not None:
        raw = upload.getvalue()
        file_hash = hashlib.sha256(raw).hexdigest()
        file_signature = f"{upload.name}_{len(raw)}_{file_hash}"
        already_imported = (
            sync_meta is not None
            and sync_meta.get("file_hash") == file_hash
            and sync_meta.get("filename") == upload.name
        )

        if already_imported:
            st.success("✅ Ce CSV est déjà enregistré. Aucun nouvel enregistrement n'est nécessaire.")
        elif st.session_state.get(f"{key}_last_import") != file_signature:
            try:
                imported, errors, import_meta = import_broker_pea(upload)
                st.session_state[key] = imported
                st.session_state[f"{key}_last_import"] = file_signature
                st.session_state[f"{key}_import_errors"] = errors
                st.session_state[f"{key}_import_meta"] = import_meta

                st.info(
                    f"🔎 Format détecté : **{import_meta.get('broker','Universel')}** · "
                    f"{import_meta.get('rows_read',0)} ligne(s) analysée(s) · "
                    f"{len(imported)} position(s) reconnue(s)"
                )

                if imported.empty:
                    st.error("❌ 0 ligne importée. Vérifie le format de l'export.")
                else:
                    # IMPORTANT : sauvegarde automatique. L'utilisateur n'a plus à cliquer
                    # sur Enregistrer à chaque connexion.
                    ok = save_portfolio_db(key, imported)
                    if ok:
                        save_import_metadata(key, upload.name, file_hash, len(imported), len(errors))
                        st.success(
                            f"☁️ Synchronisation terminée : {len(imported)} ligne(s) enregistrée(s) définitivement dans Supabase."
                        )
                    else:
                        st.error("❌ Les données ont été lues mais n'ont pas pu être enregistrées dans Supabase.")
                if not errors.empty:
                    st.warning(f"⚠️ {len(errors)} ligne(s) nécessitent une vérification.")
            except Exception as exc:
                st.error(f"❌ CSV invalide : {exc}")

    errors = st.session_state.get(f"{key}_import_errors")
    if isinstance(errors, pd.DataFrame) and not errors.empty:
        with st.expander("⚠️ Lignes non importées / à vérifier"):
            st.dataframe(errors, use_container_width=True, hide_index=True)

    edited = st.data_editor(
        st.session_state[key],
        num_rows="dynamic",
        use_container_width=True,
        key=f"{key}_editor",
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker"),
            "Quantité": st.column_config.NumberColumn("Quantité", min_value=0.0),
            "PRU": st.column_config.NumberColumn("PRU", min_value=0.0, format="%.4f"),
            "Date achat": st.column_config.DateColumn("Date achat"),
        },
    )
    normalized = normalize_portfolio(edited)
    st.session_state[key] = normalized
    if st.button("💾 Enregistrer définitivement", key=f"{key}_save", type="primary"):
        save_portfolio_db(key, normalized)
        st.success("Portefeuille enregistré. Il sera récupéré automatiquement à la prochaine ouverture.")

    if st.session_state[key].empty:
        st.info("Importe ton export broker ou ajoute une ligne manuellement : Ticker | Quantité | PRU | Date achat")
        return

    metrics = portfolio_metrics(st.session_state[key])
    if metrics.empty:
        st.warning("Aucun cours exploitable pour les lignes saisies.")
        return

    total_value = metrics["Valeur"].sum()
    total_cost = metrics["Investi"].sum()
    total_pnl = metrics["Plus-value"].sum()
    total_div = metrics["Dividendes"].sum()
    total_perf = metrics["Perf totale"].sum()
    total_pct = total_perf / total_cost * 100 if total_cost else 0

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Valeur", f"{total_value:,.2f} €")
    c2.metric("Investi", f"{total_cost:,.2f} €")
    c3.metric("PV latente", f"{total_pnl:,.2f} €")
    c4.metric("Dividendes", f"{total_div:,.2f} €")
    c5.metric("Performance totale", f"{total_pct:+.2f}%")

    st.subheader("📊 Positions — cours et entreprise")
    st.dataframe(
        metrics[["Ticker","Entreprise","Devise","Qté","PRU","Cours","Valeur","Poids %","Plus-value","Perf cours %","Dividendes","Perf totale","Perf totale %","Date"]],
        use_container_width=True, hide_index=True,
    )

    st.subheader("📈 Courbe de rendement")
    curve = portfolio_curve(st.session_state[key])
    if curve is not None and not curve.empty:
        st.line_chart(curve.rename("Rendement total (%)"))
        st.caption("Courbe = évolution de la valeur des positions + dividendes encaissés, sans réinvestissement automatique des dividendes. Les conversions de devises ne sont pas encore modélisées finement.")
    else:
        st.info("Ajoute une date d'achat pour obtenir une courbe historique plus pertinente.")

    st.subheader("⚖️ Pistes d'arbitrage")
    arb = arbitrage_table(metrics)
    if not arb.empty:
        st.dataframe(arb, use_container_width=True, hide_index=True)
        st.caption("Ces pistes sont des alertes analytiques basées sur le moteur technique. Elles ne constituent pas une recommandation et doivent être validées avec ton allocation, ta fiscalité et ton horizon.")

    st.subheader("📰 Actualités des principales lignes")
    for sym in metrics["Ticker"].head(8):
        st.markdown(f"**{sym} — {metrics.loc[metrics['Ticker']==sym, 'Entreprise'].iloc[0]}**")
        for n in news(sym)[:3]:
            st.caption(f"{n['title']} — {n['publisher']}")

    csv = st.session_state[key].to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exporter le portefeuille CSV", csv, f"{key}.csv", "text/csv")


# ==========================================================
# SIDEBAR
# ==========================================================
with st.sidebar:
    st.header("⚙️ Command Center")
    mode = st.radio(
        "Navigation",
        ["🔎 Scanner", "📊 Analyse", "💼 CTO XTB", "🏦 PEA", "🧪 Simulation", "📓 Journal"],
    )
    if st.button("🔒 Déconnexion"):
        st.session_state["authenticated"] = False
        st.rerun()
    st.markdown("---")

    scan_tf_label = st.selectbox("Timeframe principal", list(TF), index=4)
    scan_interval = TF[scan_tf_label]["interval"]
    scan_period = st.selectbox("Historique principal", TF[scan_tf_label]["periods"], index=min(3, len(TF[scan_tf_label]["periods"])-1))
    confirm_tf_label = st.selectbox("Timeframe confirmation", ["15 minutes","30 minutes","1 hour","1 day","1 week"], index=2)
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
st.title("📈 Trading Command Center — V5")
st.caption("Scanner + suivi CTO/PEA + performance + dividendes + pistes d'arbitrage. Outil d'analyse, pas une recommandation financière.")

# ==========================================================
# GLOBAL MARKET
# ==========================================================
with st.expander("🌍 Contexte des marchés", expanded=False):
    mr = market_regime()
    if not mr.empty:
        st.dataframe(mr, use_container_width=True, hide_index=True)

# ==========================================================
# SCANNER
# ==========================================================
def run_scanner():
    pool = []
    for c in countries:
        pool.extend(UNIVERSE.get(c, []))
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
        fs, _ = fundamental_score(info(sym))
        global_score = int(round(0.55*t["score"] + 0.30*fs + 0.15*(100 if conf is None else conf["score"])))
        name = info(sym).get("longName") or info(sym).get("shortName") or sym
        rows.append({
            "Ticker": sym, "Entreprise": name, "Score": global_score, "Tech": t["score"], "Fond.": fs,
            "Prix": t["price"], "Entrée": t["entry"], "Stop": t["stop"], "TP1": t["tp1"], "TP2": t["tp2"],
            "Potentiel %": t["upside"], "R/R": t["rr"], "ATR %": t["atr_pct"], "Vol x20": t["volume_ratio"],
            "Qualité": t["quality"],
        })
        bar.progress(k/len(pool))
    bar.empty()
    return pd.DataFrame(rows)


if mode == "🔎 Scanner":
    st.header("🔎 Meilleures opportunités")
    ranking = run_scanner()
    if ranking.empty:
        st.warning("Aucune configuration ne passe actuellement tous les filtres.")
    else:
        ranking = ranking.sort_values(["Score","R/R","Potentiel %"], ascending=False).reset_index(drop=True)
        st.success(f"🎯 {len(ranking)} configuration(s) qualifiée(s)")
        st.subheader("🏆 Top 5")
        top = ranking.head(5)
        cols = st.columns(min(5, len(top)))
        for col, (_, r) in zip(cols, top.iterrows()):
            with col:
                st.metric(r["Ticker"], f"{r['Potentiel %']:.1f}%", f"Score {int(r['Score'])}")
                st.caption(f"{r['Entreprise']} • R/R {r['R/R']:.2f} • {r['Qualité']}")
        st.dataframe(ranking, use_container_width=True, hide_index=True)

elif mode == "📊 Analyse":
    st.header("📊 Analyse détaillée")
    pool = sorted(set(sum([UNIVERSE.get(c, []) for c in countries], [])))
    symbol = st.selectbox("Valeur", pool if pool else ["AAPL"])
    a_tf = st.selectbox("Timeframe", list(TF), index=4)
    a_period = st.selectbox("Historique", TF[a_tf]["periods"], index=min(3, len(TF[a_tf]["periods"])-1))
    q = live_quote(symbol)
    df = history(symbol, a_period, TF[a_tf]["interval"])
    t = trade_setup(df) if df is not None else None
    c0,c1,c2,c3,c4 = st.columns(5)
    c0.metric("Entreprise", q["name"])
    c1.metric("Cours", f"{q['price']:.2f}" if q["price"] else "N/A")
    c2.metric("Score", f"{t['score']}/100" if t else "N/A")
    c3.metric("Potentiel", f"{t['upside']:.1f}%" if t else "N/A")
    c4.metric("R/R", f"{t['rr']:.2f}" if t else "N/A")
    if t:
        a,b,c,d,e = st.columns(5)
        a.metric("Entrée", f"{t['entry']:.2f}")
        b.metric("Stop", f"{t['stop']:.2f}")
        c.metric("TP1", f"{t['tp1']:.2f}")
        d.metric("TP2", f"{t['tp2']:.2f}")
        e.metric("Qualité", t["quality"])
        with st.expander("🔬 Détails techniques", True):
            st.write(f"RSI **{t['rsi']:.1f}** • ATR **{t['atr']:.2f} ({t['atr_pct']:.1f}%) • Volume **{t['volume_ratio']:.2f}x**")
            st.write(" • ".join(t["reasons"]))
    with st.expander("🏢 Fondamentaux + actualités", False):
        fs, fr = fundamental_score(info(symbol))
        st.write(f"Score fondamentaux : **{fs}/100**")
        if fr: st.write(" • ".join(fr))
        for n in news(symbol)[:8]:
            st.markdown(f"**{n['title']}** — {n['publisher']}")

elif mode == "💼 CTO XTB":
    st.header("💼 CTO XTB")
    st.warning("La synchronisation directe avec XTB n'est pas utilisée : XTB indique que son accès API a été arrêté le 14 mars 2025. Les positions peuvent donc être saisies ou importées en CSV, puis les cours/actualités sont actualisés séparément.")
    show_portfolio_page("💼 Suivi du CTO XTB", "cto_xtb")

elif mode == "🏦 PEA":
    st.header("🏦 Suivi PEA")
    st.info("Les lignes PEA sont saisies manuellement : ticker, quantité, PRU et date d'achat. Le moteur enrichit ensuite les lignes avec le nom de l'entreprise, le cours de marché, les dividendes et les indicateurs techniques.")
    show_portfolio_page("🏦 Suivi PEA", "pea")

elif mode == "🧪 Simulation":
    st.header("🧪 Simulation / ticket de trade")
    symbol = st.text_input("Ticker", "AAPL").upper().strip()
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
        st.code(f"LONG {symbol} | Entrée {entry:.4f} | SL {stop:.4f} | TP {target:.4f} | Qté {qty}")

else:
    st.header("📓 Journal de trading")
    if "journal" not in st.session_state:
        st.session_state["journal"] = load_journal_db()
    with st.form("journal_form"):
        sym = st.text_input("Ticker", "AAPL").upper()
        setup = st.text_input("Configuration", "Breakout / pullback")
        result = st.selectbox("Résultat", ["Ouvert","Gagnant","Perdant","Annulé"])
        note = st.text_area("Note")
        submitted = st.form_submit_button("Ajouter")
        if submitted:
            save_journal_db(sym, setup, result, note)
            st.session_state["journal"] = load_journal_db()
    if st.session_state["journal"]:
        st.dataframe(pd.DataFrame(st.session_state["journal"]), use_container_width=True, hide_index=True)
    else:
        st.info("Aucune opération enregistrée.")

st.markdown("---")
st.caption("V6 — Portefeuilles persistants + données de marché via yfinance. Les cours peuvent être différés selon le marché et la source. Aucun mot de passe XTB n'est demandé ni stocké par cette application.")
