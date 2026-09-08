import csv
import hashlib
import io
import json
import math
import os
import re
import unicodedata
from datetime import datetime, date, timedelta

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

try:
    from supabase import create_client
except Exception:
    create_client = None

st.set_page_config(page_title="VISION FUTURE — Trading & Portfolio Intelligence", page_icon="🔭", layout="wide")

APP_NAME = "VISION FUTURE"
APP_SUBTITLE = "Trading & Portfolio Intelligence"
APP_VERSION = "V7 Core"

# ==========================================================
# AUTHENTICATION
# ==========================================================
def _secret(name, default=""):
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)


def password_ok(password: str) -> bool:
    expected = _secret("APP_PASSWORD")
    expected_hash = _secret("APP_PASSWORD_HASH")
    if expected_hash:
        return hashlib.sha256(password.encode()).hexdigest() == expected_hash
    return bool(expected) and password == expected


def login_gate():
    if st.session_state.get("authenticated", False):
        return True
    st.title(f"🔭 {APP_NAME}")
    st.caption(APP_SUBTITLE)
    with st.form("login_form"):
        password = st.text_input("Code / mot de passe", type="password")
        if st.form_submit_button("Se connecter", type="primary"):
            if password_ok(password):
                st.session_state["authenticated"] = True
                st.rerun()
            st.error("Code incorrect.")
    return False


if not login_gate():
    st.stop()

# ==========================================================
# SUPABASE
# ==========================================================
def get_supabase():
    url = _secret("SUPABASE_URL")
    # Prefer a server-side service key in Streamlit secrets; fallback keeps compatibility.
    key = _secret("SUPABASE_SERVICE_KEY") or _secret("SUPABASE_KEY")
    if not url or not key or create_client is None:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None


SUPABASE = get_supabase()


def _sb_data(result):
    return getattr(result, "data", None) or []


def upsert_import_record(payload: dict):
    if SUPABASE is None:
        return False
    SUPABASE.table("imports").upsert(payload, on_conflict="file_hash,account").execute()
    return True


def import_exists(file_hash: str, account: str):
    if SUPABASE is None:
        return None
    try:
        res = (SUPABASE.table("imports").select("id,filename,document_type,imported_at")
               .eq("file_hash", file_hash).eq("account", account).limit(1).execute())
        rows = _sb_data(res)
        return rows[0] if rows else None
    except Exception:
        return None


def load_positions(account: str):
    if SUPABASE is None:
        return pd.DataFrame(columns=["Ticker","ISIN","Nom","Courtier","Quantité","PRU","Devise","Date achat"])
    try:
        res = (SUPABASE.table("portfolio_positions")
               .select("ticker,isin,name,broker,quantity,pru,currency,purchase_date")
               .eq("account", account).order("name").execute())
        rows = _sb_data(res)
        out = pd.DataFrame([{
            "Ticker": r.get("ticker") or "",
            "ISIN": r.get("isin") or "",
            "Nom": r.get("name") or "",
            "Courtier": r.get("broker") or "",
            "Quantité": r.get("quantity") or 0,
            "PRU": r.get("pru") or 0,
            "Devise": r.get("currency") or "",
            "Date achat": r.get("purchase_date") or None,
        } for r in rows])
        if not out.empty:
            out["Date achat"] = pd.to_datetime(out["Date achat"], errors="coerce").dt.date
        return out
    except Exception as exc:
        st.error(f"Impossible de charger les positions Supabase : {exc}")
        return pd.DataFrame(columns=["Ticker","ISIN","Nom","Courtier","Quantité","PRU","Devise","Date achat"])


def save_positions(account: str, broker: str, df: pd.DataFrame):
    if SUPABASE is None:
        raise RuntimeError("Supabase n'est pas configuré.")
    # A positions export is a snapshot: replace this account+broker snapshot atomically enough for a personal app.
    SUPABASE.table("portfolio_positions").delete().eq("account", account).eq("broker", broker).execute()
    rows = []
    for _, r in df.iterrows():
        instrument_key = str(r.get("instrument_key") or r.get("isin") or r.get("ticker") or r.get("name") or "").strip()
        if not instrument_key:
            continue
        purchase_date = r.get("purchase_date")
        if pd.notna(purchase_date):
            purchase_date = pd.Timestamp(purchase_date).date().isoformat()
        else:
            purchase_date = None
        rows.append({
            "account": account,
            "broker": broker,
            "instrument_key": instrument_key,
            "ticker": str(r.get("ticker") or "") or None,
            "isin": str(r.get("isin") or "") or None,
            "name": str(r.get("name") or "") or None,
            "quantity": float(r.get("quantity") or 0),
            "pru": float(r.get("average_cost") or 0) if pd.notna(r.get("average_cost")) else None,
            "currency": str(r.get("currency") or "") or None,
            "last_price_imported": float(r.get("market_price")) if pd.notna(r.get("market_price")) else None,
            "market_value_imported": float(r.get("market_value")) if pd.notna(r.get("market_value")) else None,
            "purchase_date": purchase_date,
            "source": "document_import",
            "updated_at": datetime.utcnow().isoformat(),
        })
    if rows:
        SUPABASE.table("portfolio_positions").insert(rows).execute()
    return len(rows)


def save_transactions(account: str, broker: str, df: pd.DataFrame):
    if SUPABASE is None:
        raise RuntimeError("Supabase n'est pas configuré.")
    rows = []
    for _, r in df.iterrows():
        txid = str(r.get("transaction_id") or "").strip()
        if not txid:
            txid = hashlib.sha256(json.dumps(r.fillna("").astype(str).to_dict(), sort_keys=True).encode()).hexdigest()
        rows.append({
            "transaction_id": txid,
            "account": account,
            "broker": broker,
            "occurred_at": str(r.get("datetime") or r.get("date") or "") or None,
            "trade_date": str(r.get("date") or "") or None,
            "category": str(r.get("category") or "") or None,
            "type": str(r.get("type") or "") or None,
            "asset_class": str(r.get("asset_class") or "") or None,
            "name": str(r.get("name") or "") or None,
            "symbol": str(r.get("symbol") or "") or None,
            "isin": str(r.get("isin") or "") or None,
            "quantity": float(r.get("quantity")) if pd.notna(r.get("quantity")) else None,
            "price": float(r.get("price")) if pd.notna(r.get("price")) else None,
            "amount": float(r.get("amount")) if pd.notna(r.get("amount")) else None,
            "fee": float(r.get("fee")) if pd.notna(r.get("fee")) else None,
            "tax": float(r.get("tax")) if pd.notna(r.get("tax")) else None,
            "currency": str(r.get("currency") or "") or None,
            "description": str(r.get("description") or "") or None,
            "raw": r.fillna("").astype(str).to_dict(),
            "imported_at": datetime.utcnow().isoformat(),
        })
    if rows:
        SUPABASE.table("transactions").upsert(rows, on_conflict="transaction_id").execute()
    return len(rows)


def load_transactions(account: str | None = None):
    if SUPABASE is None:
        return pd.DataFrame()
    try:
        q = SUPABASE.table("transactions").select("trade_date,type,asset_class,name,symbol,quantity,price,amount,fee,tax,currency,broker,account,description")
        if account:
            q = q.eq("account", account)
        res = q.order("trade_date", desc=True).execute()
        return pd.DataFrame(_sb_data(res))
    except Exception as exc:
        st.error(f"Impossible de charger les transactions : {exc}")
        return pd.DataFrame()

# ==========================================================
# DOCUMENT ENGINE
# ==========================================================
POSITION_HINTS = {"name","isin","quantity","buyingprice","lastprice","marketvalue","pru","averagecost"}
TRANSACTION_HINTS = {"datetime","date","accounttype","category","type","assetclass","shares","price","amount","fee","tax","transactionid"}
ACCOUNTING_HINTS = {"date","label","debit","credit"}

ALIASES = {
    "name": ["name","nom","libelle","libellé","securityname","instrumentname","assetname","designation","désignation"],
    "isin": ["isin","isincode","securityid","instrumentid","valor"],
    "ticker": ["ticker","symbol","symbole","code","codevaleur"],
    "quantity": ["quantity","quantite","quantité","qty","shares","units","unités","nombre","nombredetitres","position"],
    "average_cost": ["buyingprice","averageprice","avgprice","averagecost","purchaseprice","pru","prixmoyen","prixderevient","prixdacquisition","costbasis"],
    "market_price": ["lastprice","currentprice","marketprice","cours","coursactuel","prixactuel","last"],
    "market_value": ["marketvalue","amount","value","valorisation","valeur","positionvalue"],
    "currency": ["currency","devise","ccy"],
    "purchase_date": ["purchasedate","buydate","acquisitiondate","dateachat","lastmovementdate"],
    "datetime": ["datetime","timestamp","occurredat","executiontime"],
    "date": ["date","tradedate","bookingdate","valuedate"],
    "category": ["category","categorie","catégorie"],
    "type": ["type","transactiontype","operationtype","opération","operation"],
    "asset_class": ["assetclass","asset_class","classedactif","classeactif"],
    "price": ["price","tradeprice","executionprice","prix"],
    "amount": ["amount","montant","cashamount","netamount"],
    "fee": ["fee","fees","frais","commission"],
    "tax": ["tax","taxes","impot","impôt","prelevement","prélèvement"],
    "description": ["description","details","détails","memo","comment"],
    "transaction_id": ["transactionid","transaction_id","id","operationid","tradeid"],
    "label": ["label","libelle","libellé"],
    "debit": ["debit","débit"],
    "credit": ["credit","crédit"],
}

ISIN_TO_TICKER = {
    "FR0013341781":"2CRSI.PA","FR0000120073":"AI.PA","FR0000120628":"CS.PA",
    "FR0000045072":"ACA.PA","FR0010208488":"ENGI.PA","FR0000062671":"EXA.PA",
    "FR001400SF56":"LOUP.PA","FR0000038242":"LBIRD.PA","FR0000121014":"MC.PA",
    "FR0013269123":"RUI.PA","FR0000125007":"SGO.PA","FR0000121972":"SU.PA",
    "FR0010528059":"ALSTW.PA","NL0014559478":"TE.PA","FR0000120271":"TTE.PA",
    "FR0000124141":"VIE.PA",
}


def norm_token(value):
    s = str(value or "").replace("\ufeff", "").strip().lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", s)


ALIAS_LOOKUP = {}
for canonical, names in ALIASES.items():
    for name in names + [canonical]:
        ALIAS_LOOKUP[norm_token(name)] = canonical


def parse_number(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan
    if isinstance(value, (int, float, np.number)):
        return float(value)
    s = str(value).strip().replace("\u00a0", " ").replace("€", "").replace("$", "").replace("£", "")
    if not s:
        return np.nan
    s = s.replace(" ", "")
    # European 1.234,56 vs US 1,234.56
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    s = re.sub(r"[^0-9eE+\-.]", "", s)
    try:
        return float(s)
    except Exception:
        return np.nan


def decode_bytes(raw: bytes):
    if not raw:
        raise ValueError("Le fichier est vide.")
    candidates = []
    for enc in ("utf-8-sig","utf-8","utf-16","utf-16-le","utf-16-be","cp1252","latin1"):
        try:
            text = raw.decode(enc).replace("\x00", "")
            printable = sum(ch.isprintable() or ch in "\r\n\t" for ch in text) / max(len(text),1)
            candidates.append((printable, enc, text))
        except Exception:
            pass
    if not candidates:
        raise ValueError("Encodage texte non reconnu.")
    candidates.sort(reverse=True, key=lambda x: x[0])
    return candidates[0][1], candidates[0][2]


def is_excel_bytes(raw: bytes):
    return raw.startswith(b"PK\x03\x04") or raw.startswith(bytes.fromhex("D0CF11E0A1B11AE1"))


def read_excel_bytes(raw: bytes):
    bio = io.BytesIO(raw)
    try:
        sheets = pd.read_excel(bio, sheet_name=None, dtype=str)
    except Exception as exc:
        raise ValueError(f"Fichier Excel détecté mais lecture impossible : {exc}")
    usable = [(name, df) for name, df in sheets.items() if df is not None and not df.empty]
    if not usable:
        raise ValueError("Le classeur Excel ne contient aucune feuille exploitable.")
    # Choose the sheet with the most data.
    name, df = max(usable, key=lambda x: x[1].shape[0] * max(x[1].shape[1],1))
    return df, {"format":"excel","encoding":"n/a","separator":"n/a","sheet":name}


def read_delimited_text(raw: bytes):
    encoding, text = decode_bytes(raw)
    # Remove only empty leading lines; preserve quoted content.
    text = text.lstrip("\r\n\ufeff")
    if not text.strip():
        raise ValueError("Le fichier texte est vide après décodage.")

    separators = [";", ",", "\t", "|", ":"]
    candidates = []
    for sep in separators:
        try:
            df = pd.read_csv(io.StringIO(text), sep=sep, dtype=str, engine="python", keep_default_na=False, on_bad_lines="skip")
            cols = [str(c) for c in df.columns]
            if len(cols) < 2:
                continue
            normalized = [norm_token(c) for c in cols]
            known = sum(c in ALIAS_LOOKUP for c in normalized)
            nonempty = int(df.astype(str).apply(lambda x: x.str.strip().ne("")).sum().sum()) if not df.empty else 0
            score = known * 100 + len(cols) * 5 + min(len(df), 100) + min(nonempty, 1000) / 1000
            candidates.append((score, sep, df))
        except Exception:
            continue
    if not candidates:
        # Sniffer fallback.
        try:
            sample = text[:8192]
            sep = csv.Sniffer().sniff(sample, delimiters=";,\t|:").delimiter
            df = pd.read_csv(io.StringIO(text), sep=sep, dtype=str, engine="python", keep_default_na=False, on_bad_lines="skip")
            if len(df.columns) < 2:
                raise ValueError("une seule colonne détectée")
            return df, {"format":"delimited_text","encoding":encoding,"separator":repr(sep),"sheet":None}
        except Exception as exc:
            raise ValueError(f"Impossible d'interpréter le texte comme tableau délimité : {exc}")
    score, sep, df = max(candidates, key=lambda x: x[0])
    return df, {"format":"delimited_text","encoding":encoding,"separator":repr(sep),"sheet":None}


def read_document(uploaded_file):
    raw = uploaded_file.getvalue()
    meta = {"filename": uploaded_file.name, "size": len(raw), "hash": hashlib.sha256(raw).hexdigest()}
    if is_excel_bytes(raw):
        df, m = read_excel_bytes(raw)
    else:
        df, m = read_delimited_text(raw)
    meta.update(m)
    df.columns = [str(c).replace("\ufeff", "").strip().strip('"') for c in df.columns]
    return df, meta


def canonical_column_map(columns):
    mapping = {}
    for col in columns:
        token = norm_token(col)
        if token in ALIAS_LOOKUP and ALIAS_LOOKUP[token] not in mapping:
            mapping[ALIAS_LOOKUP[token]] = col
    return mapping


def classify_document(df: pd.DataFrame):
    cmap = canonical_column_map(df.columns)
    keys = set(cmap)
    pos_score = sum(k in keys for k in ("quantity","average_cost","market_price","market_value","isin","ticker","name"))
    tx_score = sum(k in keys for k in ("type","amount","date","datetime","price","fee","tax","transaction_id","asset_class"))
    acct_score = sum(k in keys for k in ("date","label","debit","credit"))

    # Strong structural rules first.
    if {"debit","credit","label"}.issubset(keys):
        return "ACCOUNTING", min(0.99, 0.75 + 0.05 * acct_score), cmap
    if "type" in keys and ("amount" in keys or "price" in keys) and ("date" in keys or "datetime" in keys):
        return "TRANSACTIONS", min(0.99, 0.65 + 0.04 * tx_score), cmap
    if "quantity" in keys and ("average_cost" in keys or "market_price" in keys or "market_value" in keys) and ("isin" in keys or "ticker" in keys or "name" in keys):
        return "POSITIONS", min(0.99, 0.65 + 0.04 * pos_score), cmap
    best = max([("POSITIONS", pos_score), ("TRANSACTIONS", tx_score), ("ACCOUNTING", acct_score)], key=lambda x:x[1])
    confidence = min(0.70, 0.20 + 0.08 * best[1])
    return (best[0] if best[1] >= 3 else "UNKNOWN"), confidence, cmap


def detect_broker(df: pd.DataFrame, doc_type: str):
    cols = {norm_token(c) for c in df.columns}
    if {"buyingprice","lastprice","intradayvariation","amountvariation","lastmovementdate"}.issubset(cols):
        return "BoursoBank", 0.98
    if {"accounttype","assetclass","transactionid","originalamount","originalcurrency","fxrate"}.issubset(cols):
        return "Trade Republic", 0.96
    return "Inconnu / générique", 0.35


def value_from(row, cmap, key, default=""):
    col = cmap.get(key)
    return row.get(col, default) if col else default


def normalize_positions(df: pd.DataFrame, cmap: dict):
    rows, issues = [], []
    for idx, row in df.iterrows():
        name = str(value_from(row, cmap, "name", "")).strip()
        isin = str(value_from(row, cmap, "isin", "")).strip().upper()
        ticker = str(value_from(row, cmap, "ticker", "")).strip().upper()
        qty = parse_number(value_from(row, cmap, "quantity", np.nan))
        cost = parse_number(value_from(row, cmap, "average_cost", np.nan))
        market_price = parse_number(value_from(row, cmap, "market_price", np.nan))
        market_value = parse_number(value_from(row, cmap, "market_value", np.nan))
        # In position snapshots, many brokers call the position value simply "amount".
        if not np.isfinite(market_value):
            amount_col = next((c for c in df.columns if norm_token(c) in {"amount","montant","value","valeur","valorisation"}), None)
            if amount_col is not None:
                market_value = parse_number(row.get(amount_col, np.nan))
        currency = str(value_from(row, cmap, "currency", "")).strip().upper()
        pdate_raw = str(value_from(row, cmap, "purchase_date", "")).strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", pdate_raw):
            pdate = pd.to_datetime(pdate_raw, format="%Y-%m-%d", errors="coerce")
        else:
            pdate = pd.to_datetime(pdate_raw, errors="coerce", dayfirst=True)
        if not ticker and isin:
            ticker = ISIN_TO_TICKER.get(isin, "")
        # Keep line even without ticker; ISIN/name is enough for persistent identification.
        key = isin or ticker or norm_token(name)
        if not key:
            issues.append({"ligne": idx+2, "motif":"Instrument non identifiable"})
            continue
        if not np.isfinite(qty):
            issues.append({"ligne": idx+2, "instrument": name or isin or ticker, "motif":"Quantité absente/invalide"})
            continue
        rows.append({
            "instrument_key": key,
            "ticker": ticker,
            "isin": isin,
            "name": name,
            "quantity": qty,
            "average_cost": cost,
            "market_price": market_price,
            "market_value": market_value,
            "currency": currency,
            "purchase_date": pdate.date() if pd.notna(pdate) else None,
        })
    out = pd.DataFrame(rows)
    return out, pd.DataFrame(issues)


def normalize_transactions(df: pd.DataFrame, cmap: dict):
    rows = []
    for _, row in df.iterrows():
        name = str(value_from(row, cmap, "name", "")).strip()
        symbol = str(value_from(row, cmap, "ticker", "")).strip().upper()
        # Many brokers put an ISIN in a column named symbol. Detect it explicitly.
        isin = symbol if re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", symbol or "") else ""
        if isin:
            symbol = ISIN_TO_TICKER.get(isin, "")
        tx_type = str(value_from(row, cmap, "type", "")).strip().upper()
        quantity = parse_number(value_from(row, cmap, "quantity", np.nan))
        rows.append({
            "datetime": str(value_from(row, cmap, "datetime", "")).strip(),
            "date": str(value_from(row, cmap, "date", "")).strip(),
            "category": str(value_from(row, cmap, "category", "")).strip().upper(),
            "type": tx_type,
            "asset_class": str(value_from(row, cmap, "asset_class", "")).strip().upper(),
            "name": name,
            "symbol": symbol,
            "isin": isin,
            "quantity": quantity,
            "price": parse_number(value_from(row, cmap, "price", np.nan)),
            "amount": parse_number(value_from(row, cmap, "amount", np.nan)),
            "fee": parse_number(value_from(row, cmap, "fee", np.nan)),
            "tax": parse_number(value_from(row, cmap, "tax", np.nan)),
            "currency": str(value_from(row, cmap, "currency", "")).strip().upper(),
            "description": str(value_from(row, cmap, "description", "")).strip(),
            "transaction_id": str(value_from(row, cmap, "transaction_id", "")).strip(),
        })
    return pd.DataFrame(rows)


def normalize_accounting(df: pd.DataFrame, cmap: dict):
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "date": str(value_from(row, cmap, "date", "")).strip(),
            "label": str(value_from(row, cmap, "label", "")).strip(),
            "debit": parse_number(value_from(row, cmap, "debit", np.nan)),
            "credit": parse_number(value_from(row, cmap, "credit", np.nan)),
        })
    return pd.DataFrame(rows)


def interpret_document(uploaded_file):
    df, meta = read_document(uploaded_file)
    doc_type, confidence, cmap = classify_document(df)
    broker, broker_conf = detect_broker(df, doc_type)
    result = {
        "raw_df": df, "meta": meta, "document_type": doc_type, "confidence": confidence,
        "column_map": cmap, "broker": broker, "broker_confidence": broker_conf,
        "issues": pd.DataFrame(), "normalized": pd.DataFrame(),
    }
    if doc_type == "POSITIONS":
        result["normalized"], result["issues"] = normalize_positions(df, cmap)
    elif doc_type == "TRANSACTIONS":
        result["normalized"] = normalize_transactions(df, cmap)
    elif doc_type == "ACCOUNTING":
        result["normalized"] = normalize_accounting(df, cmap)
    return result

# ==========================================================
# MARKET / TRADING ENGINE
# ==========================================================
UNIVERSE = {
    "USA": ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","AVGO","AMD","NFLX","ADBE","CRM","ORCL","QCOM","INTC","PLTR","JPM","V","MA","XOM","CVX","LLY","JNJ"],
    "France": ["MC.PA","OR.PA","AIR.PA","SAN.PA","SU.PA","TTE.PA","BNP.PA","AI.PA","SAF.PA","DG.PA","CS.PA","CAP.PA","ACA.PA","ENGI.PA","SGO.PA","VIE.PA"],
    "Germany": ["SAP.DE","SIE.DE","ALV.DE","DTE.DE","MBG.DE","BMW.DE","BAS.DE","IFX.DE","DBK.DE"],
    "Netherlands": ["ASML.AS","ADYEN.AS","INGA.AS","PRX.AS","PHIA.AS"],
    "UK": ["SHEL.L","AZN.L","HSBA.L","ULVR.L","BP.L","GSK.L","RIO.L"],
}
TF = {
    "15 minutes": {"interval":"15m","periods":["5d","1mo","3mo"]},
    "1 hour": {"interval":"1h","periods":["1mo","3mo","6mo","1y"]},
    "1 day": {"interval":"1d","periods":["3mo","6mo","1y","2y","5y"]},
    "1 week": {"interval":"1wk","periods":["1y","2y","5y","10y"]},
}

@st.cache_data(ttl=90, show_spinner=False)
def history(symbol, period, interval, auto_adjust=False):
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=auto_adjust)
        return None if df is None or df.empty else df.dropna(subset=["Open","High","Low","Close"])
    except Exception:
        return None

@st.cache_data(ttl=900, show_spinner=False)
def info(symbol):
    try: return yf.Ticker(symbol).info or {}
    except Exception: return {}

@st.cache_data(ttl=60, show_spinner=False)
def live_quote(symbol):
    try:
        t = yf.Ticker(symbol); fi = getattr(t,"fast_info",None); price=None; currency=""
        if fi:
            try: price = fi.get("last_price")
            except Exception: pass
            try: currency = fi.get("currency") or ""
            except Exception: pass
        inf = info(symbol)
        if price is None:
            h = t.history(period="1d",interval="1m",auto_adjust=False)
            if h is not None and not h.empty: price=float(h["Close"].dropna().iloc[-1])
        return {"price": float(price) if price is not None else None, "currency":currency or inf.get("currency","") or "", "name":inf.get("longName") or inf.get("shortName") or symbol}
    except Exception:
        return {"price":None,"currency":"","name":symbol}


def indicators(df):
    x=df.copy(); c=x.Close; h=x.High; l=x.Low; v=x.Volume
    x["SMA20"]=c.rolling(20).mean(); x["SMA50"]=c.rolling(50).mean(); x["SMA200"]=c.rolling(200).mean()
    x["EMA12"]=c.ewm(span=12,adjust=False).mean(); x["EMA26"]=c.ewm(span=26,adjust=False).mean(); x["MACD"]=x.EMA12-x.EMA26; x["MACD_SIGNAL"]=x.MACD.ewm(span=9,adjust=False).mean()
    d=c.diff(); gain=d.clip(lower=0).rolling(14).mean(); loss=(-d.clip(upper=0)).rolling(14).mean(); rs=gain/loss.replace(0,np.nan); x["RSI"]=100-(100/(1+rs))
    tr=pd.concat([(h-l),(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1); x["ATR"]=tr.rolling(14).mean(); x["ATR_PCT"]=x.ATR/c*100; x["VOL20"]=v.rolling(20).mean(); x["ROC20"]=c.pct_change(20)*100
    return x.dropna(subset=["SMA20","SMA50","ATR","RSI"])


def trade_setup(df):
    if df is None: return None
    x=indicators(df)
    if len(x)<55: return None
    r=x.iloc[-1]; price=float(r.Close); atr=float(r.ATR); recent=x.tail(min(120,len(x)))
    support=min(float(recent.Low.quantile(.15)), price-.8*atr); support=max(support,price-4*atr)
    resistance=max(float(recent.High.quantile(.85)),price+1.5*atr)
    entry=min(price,max(support+.2*atr,price-.35*atr)); stop=min(support-.25*atr,entry-atr); risk=max(entry-stop,.01*price)
    tp1=min(resistance,entry+1.5*risk); tp2=min(resistance,entry+2.8*risk); upside=(tp2/entry-1)*100; rr=(tp2-entry)/risk if risk else 0
    score=50; reasons=[]
    if price>r.SMA20: score+=10; reasons.append("prix > SMA20")
    else: score-=8
    if r.SMA20>r.SMA50: score+=12; reasons.append("SMA20 > SMA50")
    else: score-=10
    if not pd.isna(r.SMA200): score += 8 if price>r.SMA200 else -8
    if 45<=r.RSI<=68: score+=8; reasons.append("RSI exploitable")
    elif r.RSI>75: score-=8
    if r.MACD>r.MACD_SIGNAL: score+=10; reasons.append("MACD haussier")
    else: score-=8
    if r.ROC20>0: score+=7; reasons.append("momentum positif")
    score=int(np.clip(score,0,100)); quality="A" if score>=85 and upside>=5 and rr>=2 else ("B" if score>=75 and upside>=5 and rr>=2 else "SURVEILLER")
    return {"price":price,"entry":entry,"stop":stop,"tp1":tp1,"tp2":tp2,"upside":upside,"rr":rr,"score":score,"quality":quality,"rsi":float(r.RSI),"atr_pct":float(r.ATR_PCT),"reasons":reasons}


def position_calc(capital,risk_pct,entry,stop,target):
    risk_e=capital*risk_pct/100; dist=abs(entry-stop); qty=math.floor(risk_e/dist) if dist>0 else 0
    return risk_e,qty,qty*entry,qty*abs(target-entry),(abs(target-entry)/dist if dist else 0)

# ==========================================================
# PAGES
# ==========================================================
def show_import_page():
    st.header("📥 Import intelligent de documents")
    st.caption("Dépose un export. VISION FUTURE détecte d'abord le format réel, puis le type de document et ses champs. L'extension du fichier n'impose pas le lecteur.")
    account = st.selectbox("Compte cible", ["pea","cto_xtb","cto_trade_republic","cto_autre"], format_func=lambda x:{"pea":"PEA","cto_xtb":"CTO XTB","cto_trade_republic":"CTO Trade Republic","cto_autre":"CTO / autre"}[x])
    uploaded = st.file_uploader("Document", type=None, accept_multiple_files=False)
    if uploaded is None:
        st.info("Formats tabulaires pris en charge : CSV, CSV renommé .xls, TSV, TXT, XLSX et XLS. Les PDF seront ajoutés au moteur documentaire dans une étape dédiée.")
        return
    try:
        result = interpret_document(uploaded)
    except Exception as exc:
        raw = uploaded.getvalue()
        st.error(f"Lecture impossible : {exc}")
        st.code(repr(raw[:240]))
        return

    meta=result["meta"]; doc=result["document_type"]; broker=result["broker"]
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Type", doc)
    c2.metric("Confiance", f"{result['confidence']*100:.0f}%")
    c3.metric("Courtier probable", broker)
    c4.metric("Lignes", len(result["raw_df"]))
    st.caption(f"Format réel : {meta['format']} • encodage : {meta['encoding']} • séparateur : {meta['separator']} • taille : {meta['size']} octets")

    with st.expander("🔎 Champs reconnus", expanded=True):
        if result["column_map"]:
            mapping_df=pd.DataFrame([{"Champ interne":k,"Colonne détectée":v} for k,v in result["column_map"].items()])
            st.dataframe(mapping_df,use_container_width=True,hide_index=True)
        else:
            st.warning("Aucun champ financier connu n'a été reconnu.")

    broker_override=st.text_input("Courtier / source", value=broker)
    with st.expander("Aperçu normalisé", expanded=True):
        st.dataframe(result["normalized"].head(100),use_container_width=True,hide_index=True)
    if not result["issues"].empty:
        st.warning(f"{len(result['issues'])} ligne(s) nécessitent une vérification.")
        st.dataframe(result["issues"],use_container_width=True,hide_index=True)

    duplicate = import_exists(meta["hash"], account)
    if duplicate:
        st.success(f"✅ Ce fichier a déjà été importé ({duplicate.get('document_type','')}, {duplicate.get('imported_at','')}).")
        return

    if doc == "UNKNOWN":
        st.error("Document non reconnu avec assez de certitude. Aucune donnée ne sera enregistrée.")
        return
    if doc == "ACCOUNTING":
        st.info("Document comptable reconnu. Il est volontairement exclu du portefeuille et du ledger boursier dans cette V7 Core.")
        return

    if st.button("☁️ Valider et enregistrer dans Supabase", type="primary"):
        try:
            if doc == "POSITIONS":
                count=save_positions(account, broker_override, result["normalized"])
            else:
                count=save_transactions(account, broker_override, result["normalized"])
            upsert_import_record({
                "file_hash":meta["hash"],"account":account,"filename":uploaded.name,"document_type":doc,
                "broker":broker_override,"row_count":int(count),"status":"IMPORTED","imported_at":datetime.utcnow().isoformat(),
                "metadata":json.dumps({k:v for k,v in meta.items() if k!="hash"},ensure_ascii=False),
            })
            st.success(f"☁️ Import terminé : {count} ligne(s) enregistrée(s). Elles seront rechargées automatiquement aux prochaines connexions.")
            st.cache_data.clear()
        except Exception as exc:
            st.error(f"Échec d'enregistrement Supabase : {exc}")


def show_portfolio_page(account, title):
    st.header(title)
    df=load_positions(account)
    if df.empty:
        st.info("Aucune position enregistrée. Utilise la page « Import documents » une seule fois avec ton export de positions.")
        return
    st.success(f"☁️ {len(df)} position(s) chargée(s) automatiquement depuis Supabase.")
    st.dataframe(df,use_container_width=True,hide_index=True)

    metrics=[]
    for _,r in df.iterrows():
        ticker=str(r.get("Ticker") or "").strip()
        qty=float(r.get("Quantité") or 0); pru=float(r.get("PRU") or 0)
        if not ticker:
            metrics.append({"Ticker":"","Entreprise":r.get("Nom") or r.get("ISIN"),"Qté":qty,"PRU":pru,"Cours":np.nan,"Valeur":np.nan,"P/L":np.nan,"P/L %":np.nan,"Statut":"Ticker à résoudre"})
            continue
        q=live_quote(ticker); price=q["price"]
        value=qty*price if price is not None else np.nan; cost=qty*pru if pru else np.nan
        pnl=value-cost if pd.notna(value) and pd.notna(cost) else np.nan; pct=pnl/cost*100 if pd.notna(pnl) and cost else np.nan
        metrics.append({"Ticker":ticker,"Entreprise":q["name"],"Qté":qty,"PRU":pru,"Cours":price,"Valeur":value,"P/L":pnl,"P/L %":pct,"Statut":"OK" if price is not None else "Cours indisponible"})
    m=pd.DataFrame(metrics)
    st.subheader("📊 Valorisation")
    if not m.empty:
        c1,c2,c3=st.columns(3)
        c1.metric("Valeur suivie", f"{m['Valeur'].sum(skipna=True):,.2f} €")
        c2.metric("Coût suivi", f"{(m['Qté']*m['PRU']).sum(skipna=True):,.2f} €")
        c3.metric("P/L latent suivi", f"{m['P/L'].sum(skipna=True):+,.2f} €")
        st.dataframe(m,use_container_width=True,hide_index=True)


def show_transactions_page():
    st.header("💰 Transactions / Ledger")
    account=st.selectbox("Compte", ["Tous","pea","cto_xtb","cto_trade_republic","cto_autre"])
    df=load_transactions(None if account=="Tous" else account)
    if df.empty:
        st.info("Aucune transaction enregistrée. Importe un export de transactions depuis « Import documents ».")
        return
    st.success(f"{len(df)} transaction(s) persistante(s) chargée(s) depuis Supabase.")
    if "type" in df:
        summary=df["type"].fillna("INCONNU").value_counts().rename_axis("Type").reset_index(name="Nombre")
        st.dataframe(summary,use_container_width=True,hide_index=True)
    c1,c2,c3=st.columns(3)
    amount=pd.to_numeric(df.get("amount"),errors="coerce") if "amount" in df else pd.Series(dtype=float)
    fees=pd.to_numeric(df.get("fee"),errors="coerce") if "fee" in df else pd.Series(dtype=float)
    taxes=pd.to_numeric(df.get("tax"),errors="coerce") if "tax" in df else pd.Series(dtype=float)
    c1.metric("Flux net importé", f"{amount.sum(skipna=True):+,.2f}")
    c2.metric("Frais", f"{fees.sum(skipna=True):+,.2f}")
    c3.metric("Taxes", f"{taxes.sum(skipna=True):+,.2f}")
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.caption("Le ledger V7 stocke les opérations sans doublons via transaction_id. Le calcul de rendement corrigé des apports/retraits sera la couche Performance V7.1.")

# ==========================================================
# SIDEBAR / ROUTING
# ==========================================================
with st.sidebar:
    st.header(f"🔭 {APP_NAME}")
    mode=st.radio("Navigation", ["🏠 Dashboard","📥 Import documents","🏦 PEA","💼 CTO","💰 Transactions","🔎 Scanner","📊 Analyse","🧪 Simulation"])
    if st.button("🔒 Déconnexion"):
        st.session_state["authenticated"]=False; st.rerun()
    st.markdown("---")
    capital=st.number_input("Capital de référence (€)",100.0,1_000_000.0,10_000.0,100.0)
    risk_pct=st.number_input("Risque par trade (%)",0.1,3.0,0.5,0.05)
    refresh_min=st.select_slider("Actualisation scanner (min)",[1,2,5,10,15,30,60],value=5)
    auto_refresh=st.checkbox("Actualisation automatique",False)
    if auto_refresh: st_autorefresh(interval=refresh_min*60*1000,key="auto_refresh")
    if SUPABASE is None:
        st.error("Supabase non connecté")
    else:
        st.success("Supabase connecté")

st.title(f"🔭 {APP_NAME}")
st.caption(f"{APP_SUBTITLE} — {APP_VERSION} • Import adaptatif + stockage persistant + analyse de marché")

if mode=="🏠 Dashboard":
    st.header("🏠 Vue d'ensemble")
    pea=load_positions("pea"); cto=load_positions("cto_xtb"); tr=load_positions("cto_trade_republic")
    tx=load_transactions()
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Positions PEA",len(pea)); c2.metric("Positions CTO XTB",len(cto)); c3.metric("Positions CTO Trade Republic",len(tr)); c4.metric("Transactions",len(tx))
    st.info("Flux recommandé : Import documents → validation → Supabase → chargement automatique. Tu ne réimportes un fichier que lorsque le courtier fournit un export plus récent.")

elif mode=="📥 Import documents":
    show_import_page()

elif mode=="🏦 PEA":
    show_portfolio_page("pea","🏦 PEA")

elif mode=="💼 CTO":
    acc=st.selectbox("CTO",["cto_xtb","cto_trade_republic","cto_autre"],format_func=lambda x:{"cto_xtb":"XTB","cto_trade_republic":"Trade Republic","cto_autre":"Autre"}[x])
    show_portfolio_page(acc,"💼 CTO")

elif mode=="💰 Transactions":
    show_transactions_page()

elif mode=="🔎 Scanner":
    st.header("🔎 Scanner")
    countries=st.multiselect("Marchés",list(UNIVERSE),default=["USA","France"])
    timeframe=st.selectbox("Timeframe",list(TF),index=2); period=st.selectbox("Historique",TF[timeframe]["periods"],index=min(1,len(TF[timeframe]["periods"])-1))
    min_upside=st.number_input("Potentiel minimum (%)",1.0,30.0,5.0,.5); min_rr=st.number_input("R/R minimum",1.0,5.0,2.0,.1); min_score=st.slider("Score minimum",50,100,75)
    pool=sorted(set(sum([UNIVERSE.get(c,[]) for c in countries],[])))
    rows=[]; bar=st.progress(0)
    for i,sym in enumerate(pool,1):
        t=trade_setup(history(sym,period,TF[timeframe]["interval"]))
        if t and t["upside"]>=min_upside and t["rr"]>=min_rr and t["score"]>=min_score:
            q=live_quote(sym); rows.append({"Ticker":sym,"Entreprise":q["name"],"Score":t["score"],"Prix":t["price"],"Entrée":t["entry"],"Stop":t["stop"],"TP1":t["tp1"],"TP2":t["tp2"],"Potentiel %":t["upside"],"R/R":t["rr"],"Qualité":t["quality"]})
        bar.progress(i/max(len(pool),1))
    bar.empty(); out=pd.DataFrame(rows)
    if out.empty: st.warning("Aucune configuration ne passe les filtres.")
    else: st.dataframe(out.sort_values(["Score","R/R"],ascending=False),use_container_width=True,hide_index=True)

elif mode=="📊 Analyse":
    st.header("📊 Analyse détaillée")
    symbol=st.text_input("Ticker","AAPL").upper().strip(); timeframe=st.selectbox("Timeframe",list(TF),index=2); period=st.selectbox("Historique",TF[timeframe]["periods"],index=min(1,len(TF[timeframe]["periods"])-1))
    t=trade_setup(history(symbol,period,TF[timeframe]["interval"])); q=live_quote(symbol)
    if not t: st.warning("Données insuffisantes pour calculer le setup.")
    else:
        c=st.columns(7); c[0].metric("Cours",f"{t['price']:.2f}"); c[1].metric("Entrée",f"{t['entry']:.2f}"); c[2].metric("SL",f"{t['stop']:.2f}"); c[3].metric("TP1",f"{t['tp1']:.2f}"); c[4].metric("TP2",f"{t['tp2']:.2f}"); c[5].metric("Potentiel",f"{t['upside']:.1f}%"); c[6].metric("R/R",f"{t['rr']:.2f}")
        st.write(f"**{q['name']}** • Score {t['score']}/100 • {t['quality']}")
        st.write(" • ".join(t["reasons"]))

else:
    st.header("🧪 Simulation")
    symbol=st.text_input("Ticker","AAPL").upper().strip(); t=trade_setup(history(symbol,"6mo","1d"))
    if t:
        entry=st.number_input("Entrée",value=float(t["entry"])); stop=st.number_input("Stop",value=float(t["stop"])); target=st.number_input("TP2",value=float(t["tp2"]))
        risk_e,qty,exposure,profit,rr=position_calc(capital,risk_pct,entry,stop,target)
        c=st.columns(5); c[0].metric("Risque max",f"{risk_e:.2f} €"); c[1].metric("Quantité",qty); c[2].metric("Exposition",f"{exposure:.2f} €"); c[3].metric("Gain cible",f"{profit:.2f} €"); c[4].metric("R/R",f"{rr:.2f}")
    else: st.warning("Setup indisponible.")

st.markdown("---")
st.caption("VISION FUTURE V7 Core. Les cours yfinance peuvent être différés. Les scénarios Entrée/SL/TP sont des aides analytiques, pas des garanties de performance.")
