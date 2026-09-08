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
APP_VERSION = "V8 Smart Portfolio & Fast Scanner"

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


def load_positions(account: str, broker: str | None = None):
    cols = ["Ticker","ISIN","Nom","Courtier","Quantité","PRU","Devise","Date achat","Cours importé","Valeur importée","Instrument"]
    if SUPABASE is None:
        return pd.DataFrame(columns=cols)
    try:
        q = (SUPABASE.table("portfolio_positions")
             .select("ticker,isin,name,broker,quantity,pru,currency,purchase_date,last_price_imported,market_value_imported,instrument_key,source_import_hash")
             .eq("account", account))
        if broker:
            q = q.eq("broker", broker)
        res = q.order("name").execute()
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
            "Cours importé": r.get("last_price_imported"),
            "Valeur importée": r.get("market_value_imported"),
            "Instrument": r.get("instrument_key") or r.get("isin") or r.get("ticker") or r.get("name") or "",
        } for r in rows])
        if not out.empty:
            out["Date achat"] = pd.to_datetime(out["Date achat"], errors="coerce").dt.date
        return out
    except Exception as exc:
        st.error(f"Impossible de charger les positions Supabase : {exc}")
        return pd.DataFrame(columns=cols)

def save_positions(account: str, broker: str, df: pd.DataFrame, source: str = "document_import", source_import_hash: str | None = None):
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
            "source": source,
            "source_import_hash": source_import_hash,
            "updated_at": datetime.utcnow().isoformat(),
        })
    if rows:
        SUPABASE.table("portfolio_positions").insert(rows).execute()
    return len(rows)


def save_transactions(account: str, broker: str, df: pd.DataFrame, source_import_hash: str | None = None):
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
            "source_import_hash": source_import_hash,
            "imported_at": datetime.utcnow().isoformat(),
        })
    if rows:
        SUPABASE.table("transactions").upsert(rows, on_conflict="transaction_id").execute()
    return len(rows)



def _transaction_key(row):
    isin = str(row.get("isin") or "").strip().upper()
    symbol = str(row.get("symbol") or "").strip().upper()
    name = str(row.get("name") or "").strip()
    return isin or symbol or norm_token(name)


def _load_transactions_for_broker(account: str, broker: str):
    if SUPABASE is None:
        return pd.DataFrame()
    try:
        res = (SUPABASE.table("transactions")
               .select("transaction_id,trade_date,occurred_at,type,category,asset_class,name,symbol,isin,quantity,price,amount,fee,tax,currency,broker,account,description")
               .eq("account", account).eq("broker", broker)
               .order("trade_date", desc=False).execute())
        return pd.DataFrame(_sb_data(res))
    except Exception as exc:
        raise RuntimeError(f"Lecture des transactions impossible : {exc}")


def rebuild_positions_from_transactions(account: str, broker: str):
    """Rebuild the current portfolio automatically from the full broker ledger.

    BUY adds cost basis including fees/taxes, SELL reduces quantity and cost basis
    at weighted-average cost, BONUS_ISSUE adds zero-cost units, cancellations remove
    zero-cost units, and paired SPLIT legs transfer cost basis to the replacement
    instrument. This function is deterministic and can safely be rerun after every import.
    """
    tx = _load_transactions_for_broker(account, broker)
    if tx.empty:
        return {"positions": 0, "transactions": 0, "corporate_actions": 0, "issues": []}

    x = tx.copy()
    x["trade_date_dt"] = pd.to_datetime(x.get("trade_date"), errors="coerce")
    x["type_norm"] = x.get("type", "").fillna("").astype(str).str.upper().str.strip()
    for c in ("quantity", "price", "amount", "fee", "tax"):
        x[c+"_num"] = pd.to_numeric(x.get(c), errors="coerce").fillna(0.0)
    x = x.sort_values(["trade_date_dt", "occurred_at", "transaction_id"], na_position="last")

    holdings = {}
    issues = []
    corporate_actions = 0

    def ensure_holding(r):
        key = _transaction_key(r)
        if not key:
            return None, None
        h = holdings.setdefault(key, {
            "quantity": 0.0, "cost": 0.0,
            "ticker": str(r.get("symbol") or "").strip().upper(),
            "isin": str(r.get("isin") or "").strip().upper(),
            "name": str(r.get("name") or "").strip(),
            "currency": str(r.get("currency") or "").strip().upper(),
            "purchase_date": None, "last_price": None,
        })
        # Never treat an ISIN-looking value as a ticker.
        if re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", h["ticker"] or ""):
            h["isin"] = h["isin"] or h["ticker"]
            h["ticker"] = ISIN_TO_TICKER.get(h["isin"], "")
        elif h["isin"] and not h["ticker"]:
            h["ticker"] = ISIN_TO_TICKER.get(h["isin"], "")
        return key, h

    # Process each day in chronological order so corporate actions happen before later trades.
    for day, day_rows in x.groupby(x["trade_date_dt"].dt.date, dropna=False, sort=True):
        split_rows = []
        for _, r in day_rows.iterrows():
            typ = r["type_norm"]
            if typ == "SPLIT":
                split_rows.append(r)
                continue
            if typ not in BUY_TYPES | SELL_TYPES | {"BONUS_ISSUE", "BONUS_ISSUE_CANCELLED"}:
                continue
            key, h = ensure_holding(r)
            if h is None:
                issues.append(f"{typ}: instrument non identifiable")
                continue
            qty = abs(float(r["quantity_num"]))
            signed_qty = float(r["quantity_num"])
            price = abs(float(r["price_num"]))
            amount = float(r["amount_num"])
            fee = abs(float(r["fee_num"]))
            tax = abs(float(r["tax_num"]))
            trade_day = r["trade_date_dt"]

            if typ in BUY_TYPES:
                if qty <= 0:
                    continue
                trade_cost = abs(amount) if amount != 0 else qty * price
                trade_cost += fee + tax
                h["quantity"] += qty
                h["cost"] += trade_cost
                if price > 0:
                    h["last_price"] = price
                if h["purchase_date"] is None and pd.notna(trade_day):
                    h["purchase_date"] = trade_day.date()
            elif typ in SELL_TYPES:
                if qty <= 0 or h["quantity"] <= 0:
                    continue
                sold = min(qty, h["quantity"])
                avg = h["cost"] / h["quantity"] if h["quantity"] > 0 else 0.0
                h["quantity"] -= sold
                h["cost"] = max(0.0, h["cost"] - avg * sold)
                if price > 0:
                    h["last_price"] = price
                if qty - sold > 1e-8:
                    issues.append(f"Vente {key}: {qty-sold:.6g} unité(s) sans position correspondante")
            elif typ == "BONUS_ISSUE":
                corporate_actions += 1
                if signed_qty > 0:
                    h["quantity"] += signed_qty  # zero-cost shares
                elif signed_qty < 0:
                    h["quantity"] = max(0.0, h["quantity"] + signed_qty)
            elif typ == "BONUS_ISSUE_CANCELLED":
                corporate_actions += 1
                # Broker exports generally encode cancellation as a negative quantity.
                delta = signed_qty if signed_qty < 0 else -signed_qty
                h["quantity"] = max(0.0, h["quantity"] + delta)

        # Paired split/replacement legs: transfer cost basis from negative legs to positive legs.
        if split_rows:
            corporate_actions += len(split_rows)
            removed_cost = 0.0
            positives = []
            for r in split_rows:
                key, h = ensure_holding(r)
                if h is None:
                    continue
                q = float(r["quantity_num"])
                if q < 0:
                    remove = min(abs(q), h["quantity"])
                    avg = h["cost"] / h["quantity"] if h["quantity"] > 0 else 0.0
                    removed_cost += avg * remove
                    h["quantity"] -= remove
                    h["cost"] = max(0.0, h["cost"] - avg * remove)
                elif q > 0:
                    positives.append((r, q))
            total_pos = sum(q for _, q in positives)
            for r, q in positives:
                key, h = ensure_holding(r)
                if h is None:
                    continue
                h["quantity"] += q
                if total_pos > 0:
                    h["cost"] += removed_cost * (q / total_pos)
                if h["purchase_date"] is None and pd.notna(r["trade_date_dt"]):
                    h["purchase_date"] = r["trade_date_dt"].date()

    rows = []
    for key, h in holdings.items():
        qty = float(h["quantity"])
        if qty <= 1e-10:
            continue
        pru = h["cost"] / qty if qty > 0 else np.nan
        last_price = h.get("last_price")
        rows.append({
            "instrument_key": key,
            "ticker": h.get("ticker") or "",
            "isin": h.get("isin") or "",
            "name": h.get("name") or key,
            "quantity": qty,
            "average_cost": pru,
            "market_price": last_price if last_price and last_price > 0 else np.nan,
            "market_value": qty * last_price if last_price and last_price > 0 else np.nan,
            "currency": h.get("currency") or "",
            "purchase_date": h.get("purchase_date"),
        })
    positions = pd.DataFrame(rows)
    # Transaction ledger is authoritative for this account+broker snapshot.
    save_positions(account, broker, positions, source="transactions_rebuild", source_import_hash=None)
    st.cache_data.clear()
    return {
        "positions": len(positions),
        "transactions": len(tx),
        "corporate_actions": corporate_actions,
        "issues": issues,
    }


def ensure_transaction_positions(account: str):
    """Automatically materialize positions when a ledger exists but no position snapshot does."""
    tx = load_transactions(account)
    if tx.empty or "broker" not in tx.columns:
        return []
    rebuilt = []
    current = load_positions(account)
    existing_brokers = set(current.get("Courtier", pd.Series(dtype=str)).dropna().astype(str)) if not current.empty else set()
    for broker in sorted(set(tx["broker"].dropna().astype(str))):
        if broker and broker not in existing_brokers:
            stats = rebuild_positions_from_transactions(account, broker)
            rebuilt.append((broker, stats))
    return rebuilt

def load_transactions(account: str | None = None):
    if SUPABASE is None:
        return pd.DataFrame()
    try:
        q = SUPABASE.table("transactions").select("transaction_id,trade_date,occurred_at,type,category,asset_class,name,symbol,isin,quantity,price,amount,fee,tax,currency,broker,account,description")
        if account:
            q = q.eq("account", account)
        res = q.order("trade_date", desc=False).execute()
        return pd.DataFrame(_sb_data(res))
    except Exception as exc:
        st.error(f"Impossible de charger les transactions : {exc}")
        return pd.DataFrame()


# ==========================================================
# DOCUMENTS / DATA MANAGEMENT V8
# ==========================================================
def load_imports(account: str | None = None, broker: str | None = None):
    if SUPABASE is None:
        return pd.DataFrame()
    try:
        q = SUPABASE.table("imports").select("id,file_hash,account,filename,document_type,broker,row_count,status,imported_at,metadata")
        if account:
            q = q.eq("account", account)
        if broker:
            q = q.eq("broker", broker)
        return pd.DataFrame(_sb_data(q.order("imported_at", desc=True).execute()))
    except Exception as exc:
        st.error(f"Impossible de charger l'historique des imports : {exc}")
        return pd.DataFrame()


def available_brokers(account: str):
    brokers = set()
    p = load_positions(account)
    if not p.empty and "Courtier" in p.columns:
        brokers.update(x for x in p["Courtier"].dropna().astype(str) if x)
    t = load_transactions(account)
    if not t.empty and "broker" in t.columns:
        brokers.update(x for x in t["broker"].dropna().astype(str) if x)
    return sorted(brokers)


def delete_import_record(import_row: dict, delete_generated_data: bool = False):
    if SUPABASE is None:
        raise RuntimeError("Supabase n'est pas configuré.")
    import_id = import_row.get("id")
    file_hash = str(import_row.get("file_hash") or "")
    account = str(import_row.get("account") or "")
    broker = str(import_row.get("broker") or "")
    doc_type = str(import_row.get("document_type") or "").upper()

    if delete_generated_data:
        if doc_type == "POSITIONS":
            # New V8 imports are traceable by source_import_hash. For legacy snapshots,
            # delete the account+broker snapshot only when no traceable rows exist.
            linked = (SUPABASE.table("portfolio_positions").select("id")
                      .eq("account", account).eq("broker", broker)
                      .eq("source_import_hash", file_hash).execute())
            linked_rows = _sb_data(linked)
            if linked_rows:
                SUPABASE.table("portfolio_positions").delete().eq("account", account).eq("broker", broker).eq("source_import_hash", file_hash).execute()
            else:
                SUPABASE.table("portfolio_positions").delete().eq("account", account).eq("broker", broker).execute()
        elif doc_type == "TRANSACTIONS":
            linked = (SUPABASE.table("transactions").select("id")
                      .eq("account", account).eq("broker", broker)
                      .eq("source_import_hash", file_hash).execute())
            linked_rows = _sb_data(linked)
            if linked_rows:
                SUPABASE.table("transactions").delete().eq("account", account).eq("broker", broker).eq("source_import_hash", file_hash).execute()
            else:
                # Legacy imports were not traceable per file. In that case only a full
                # broker purge can be deterministic; the UI warns the user before this path.
                SUPABASE.table("transactions").delete().eq("account", account).eq("broker", broker).execute()
            # Always rebuild the current snapshot from what remains.
            try:
                rebuild_positions_from_transactions(account, broker)
            except Exception:
                pass
    if import_id is not None:
        SUPABASE.table("imports").delete().eq("id", import_id).execute()
    else:
        SUPABASE.table("imports").delete().eq("file_hash", file_hash).eq("account", account).execute()
    st.cache_data.clear()


def show_documents_page():
    st.header("📁 Documents & données")
    c1, c2 = st.columns(2)
    account = c1.selectbox("Compte", ["Tous","pea","cto_xtb","cto_trade_republic","cto_autre"], key="docs_account")
    broker_filter = c2.text_input("Courtier (optionnel)", "", key="docs_broker").strip()
    df = load_imports(None if account == "Tous" else account, broker_filter or None)
    if df.empty:
        st.info("Aucun document enregistré pour ce filtre.")
        return
    show_cols = [c for c in ["id","filename","document_type","account","broker","row_count","status","imported_at"] if c in df.columns]
    st.dataframe(df[show_cols], use_container_width=True, hide_index=True)

    options = {}
    for _, r in df.iterrows():
        label = f"#{r.get('id')} • {r.get('filename')} • {r.get('document_type')} • {r.get('account')} • {r.get('broker')}"
        options[label] = r.to_dict()
    selected = st.selectbox("Document à gérer", list(options))
    row = options[selected]
    st.caption("La suppression de l'historique conserve les positions/transactions. La suppression avec données retire aussi ce que le document a généré puis reconstruit automatiquement le portefeuille si nécessaire.")
    a, b = st.columns(2)
    if a.button("🗑️ Supprimer seulement de l'historique", use_container_width=True):
        try:
            delete_import_record(row, delete_generated_data=False)
            st.success("Document supprimé de l'historique. Les données de portefeuille sont conservées.")
            st.rerun()
        except Exception as exc:
            st.error(f"Suppression impossible : {exc}")
    confirm = b.checkbox("Je confirme la suppression des données liées", key=f"confirm_delete_{row.get('id')}")
    if b.button("🧨 Supprimer document + données", type="primary", use_container_width=True, disabled=not confirm):
        try:
            delete_import_record(row, delete_generated_data=True)
            st.success("Document et données liées supprimés. Les états calculés ont été actualisés.")
            st.rerun()
        except Exception as exc:
            st.error(f"Suppression impossible : {exc}")

# ==========================================================
# PERFORMANCE ENGINE V7.1
# ==========================================================
EXTERNAL_IN_TYPES = {"CUSTOMER_INBOUND","TRANSFER_INSTANT_INBOUND","TRANSFER_INBOUND","DEPOSIT","CASH_DEPOSIT","BANK_TRANSFER_IN"}
EXTERNAL_OUT_TYPES = {"CUSTOMER_OUTBOUND","TRANSFER_INSTANT_OUTBOUND","TRANSFER_OUTBOUND","WITHDRAWAL","CASH_WITHDRAWAL","BANK_TRANSFER_OUT"}
DIVIDEND_TYPES = {"DIVIDEND","CASH_DIVIDEND"}
INTEREST_TYPES = {"INTEREST_PAYMENT","INTEREST"}
BUY_TYPES = {"BUY","PURCHASE"}
SELL_TYPES = {"SELL","SALE"}
CORPORATE_ACTION_TYPES = {"SPLIT","BONUS_ISSUE","BONUS_ISSUE_CANCELLED","MERGER","SPIN_OFF","RIGHTS_ISSUE"}


def _num_series(df, col):
    if col not in df.columns:
        return pd.Series(0.0, index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0)


def ledger_summary(df: pd.DataFrame):
    empty = {
        "contributions":0.0,"withdrawals":0.0,"dividends":0.0,"interest":0.0,
        "fees":0.0,"taxes":0.0,"net_cash":0.0,"realized_gross":0.0,
        "buy_volume":0.0,"sell_volume":0.0,"corporate_actions":0,"issues":[]
    }
    if df is None or df.empty:
        return empty, pd.DataFrame(), pd.DataFrame()
    x=df.copy()
    x["type_norm"]=x.get("type","").fillna("").astype(str).str.upper().str.strip()
    x["amount_num"]=_num_series(x,"amount")
    x["fee_num"]=_num_series(x,"fee")
    x["tax_num"]=_num_series(x,"tax")
    x["qty_num"]=_num_series(x,"quantity")
    x["price_num"]=_num_series(x,"price")
    x["trade_date_dt"]=pd.to_datetime(x.get("trade_date"),errors="coerce")
    contributions=float(x.loc[x.type_norm.isin(EXTERNAL_IN_TYPES),"amount_num"].clip(lower=0).sum())
    withdrawals=float((-x.loc[x.type_norm.isin(EXTERNAL_OUT_TYPES),"amount_num"].clip(upper=0)).sum())
    # Some brokers store outbound transfers as positive amounts. Include their absolute values.
    out_vals=x.loc[x.type_norm.isin(EXTERNAL_OUT_TYPES),"amount_num"]
    if not out_vals.empty and withdrawals == 0:
        withdrawals=float(out_vals.abs().sum())
    dividends=float(x.loc[x.type_norm.isin(DIVIDEND_TYPES),"amount_num"].sum())
    interest=float(x.loc[x.type_norm.isin(INTEREST_TYPES),"amount_num"].sum())
    fees=float(-x["fee_num"].sum()) if x["fee_num"].sum() < 0 else float(x["fee_num"].abs().sum())
    taxes=float(-x["tax_num"].sum()) if x["tax_num"].sum() < 0 else float(x["tax_num"].abs().sum())
    net_cash=float((x["amount_num"]+x["fee_num"]+x["tax_num"]).sum())
    buy_volume=float(-x.loc[x.type_norm.isin(BUY_TYPES),"amount_num"].clip(upper=0).sum())
    sell_volume=float(x.loc[x.type_norm.isin(SELL_TYPES),"amount_num"].clip(lower=0).sum())

    # FIFO realized P/L, gross of fees/taxes. Corporate actions are reported separately instead of guessed.
    lots={}; realized=[]; issues=[]
    for idx,r in x.sort_values(["trade_date_dt","transaction_id"], na_position="last").iterrows():
        typ=r["type_norm"]
        if typ not in BUY_TYPES|SELL_TYPES:
            continue
        isin=str(r.get("isin") or "").strip().upper()
        symbol=str(r.get("symbol") or "").strip().upper()
        name=str(r.get("name") or "").strip()
        key=isin or symbol or norm_token(name)
        if not key:
            issues.append("Transaction achat/vente sans identifiant instrument")
            continue
        qty=abs(float(r["qty_num"]))
        price=float(r["price_num"])
        if qty <= 0:
            continue
        if price <= 0 and r["amount_num"] != 0:
            price=abs(float(r["amount_num"]))/qty
        lots.setdefault(key,[])
        if typ in BUY_TYPES:
            lots[key].append([qty,price])
        else:
            remaining=qty; pnl=0.0; matched=0.0
            while remaining>1e-12 and lots[key]:
                lot_qty,lot_cost=lots[key][0]
                take=min(remaining,lot_qty)
                pnl += (price-lot_cost)*take
                matched += take
                lot_qty -= take; remaining -= take
                if lot_qty<=1e-12: lots[key].pop(0)
                else: lots[key][0][0]=lot_qty
            if remaining>1e-8:
                issues.append(f"Vente {key}: {remaining:.6g} unité(s) sans lot d'achat antérieur dans l'export")
            realized.append({"Date":r.get("trade_date"),"Instrument":name or symbol or isin,"Quantité vendue":qty,"Quantité appariée":matched,"Prix vente":price,"P/L réalisé brut":pnl})
    realized_df=pd.DataFrame(realized)
    realized_gross=float(realized_df["P/L réalisé brut"].sum()) if not realized_df.empty else 0.0
    open_rows=[]
    for key,qlots in lots.items():
        oq=sum(q for q,c in qlots); oc=sum(q*c for q,c in qlots)
        if oq>1e-12:
            open_rows.append({"Instrument":key,"Quantité ledger":oq,"Coût FIFO restant":oc,"PRU FIFO":oc/oq if oq else np.nan})
    open_df=pd.DataFrame(open_rows)
    summary={"contributions":contributions,"withdrawals":withdrawals,"dividends":dividends,"interest":interest,
             "fees":fees,"taxes":taxes,"net_cash":net_cash,"realized_gross":realized_gross,
             "buy_volume":buy_volume,"sell_volume":sell_volume,
             "corporate_actions":int(x.type_norm.isin(CORPORATE_ACTION_TYPES).sum()),"issues":issues}
    return summary, realized_df, open_df


def portfolio_valuation(account: str, use_live=True, broker: str | None = None):
    df=load_positions(account, broker=broker)
    rows=[]
    for _,r in df.iterrows():
        ticker=str(r.get("Ticker") or "").strip()
        qty=float(r.get("Quantité") or 0)
        pru=float(r.get("PRU") or 0)
        imported_price=pd.to_numeric(pd.Series([r.get("Cours importé")]),errors="coerce").iloc[0]
        imported_value=pd.to_numeric(pd.Series([r.get("Valeur importée")]),errors="coerce").iloc[0]
        price=None; price_source="Import"
        company=r.get("Nom") or r.get("ISIN") or ticker
        if use_live and ticker:
            q=live_quote(ticker)
            if q.get("price") is not None:
                price=float(q["price"]); company=q.get("name") or company; price_source="Marché"
        if price is None and pd.notna(imported_price): price=float(imported_price)
        if price is not None:
            value=qty*price
        elif pd.notna(imported_value):
            value=float(imported_value); price_source="Valeur importée"
        else: value=np.nan
        cost=qty*pru if pru else np.nan
        pnl=value-cost if pd.notna(value) and pd.notna(cost) else np.nan
        pct=pnl/cost*100 if pd.notna(pnl) and cost else np.nan
        rows.append({"Ticker":ticker,"ISIN":r.get("ISIN"),"Entreprise":company,"Courtier":r.get("Courtier"),"Qté":qty,"PRU":pru,
                     "Cours":price,"Source cours":price_source,"Valeur":value,"Coût":cost,"P/L latent":pnl,"P/L %":pct})
    detail=pd.DataFrame(rows)
    totals={
        "value":float(detail["Valeur"].sum(skipna=True)) if not detail.empty else 0.0,
        "cost":float(detail["Coût"].sum(skipna=True)) if not detail.empty else 0.0,
        "unrealized":float(detail["P/L latent"].sum(skipna=True)) if not detail.empty else 0.0,
        "unpriced":int(detail["Valeur"].isna().sum()) if not detail.empty else 0,
    }
    return totals,detail


def save_performance_snapshot(account: str, metrics: dict):
    if SUPABASE is None: return False
    payload={"account":account,"snapshot_date":date.today().isoformat(),"assets_value":metrics.get("assets_value",0),
             "cash_estimate":metrics.get("cash_estimate"),"equity_estimate":metrics.get("equity_estimate"),
             "net_contributions":metrics.get("net_contributions"),"pnl_estimate":metrics.get("pnl_estimate"),
             "return_pct":metrics.get("return_pct"),"updated_at":datetime.utcnow().isoformat()}
    try:
        SUPABASE.table("performance_snapshots").upsert(payload,on_conflict="account,snapshot_date").execute(); return True
    except Exception:
        return False


def load_performance_snapshots(account: str):
    if SUPABASE is None: return pd.DataFrame()
    try:
        res=(SUPABASE.table("performance_snapshots").select("snapshot_date,assets_value,cash_estimate,equity_estimate,net_contributions,pnl_estimate,return_pct")
             .eq("account",account).order("snapshot_date").execute())
        d=pd.DataFrame(_sb_data(res))
        if not d.empty: d["snapshot_date"]=pd.to_datetime(d["snapshot_date"],errors="coerce")
        return d
    except Exception: return pd.DataFrame()


def performance_metrics(account: str):
    val,positions=portfolio_valuation(account,use_live=True)
    tx=load_transactions(account)
    led,realized,openlots=ledger_summary(tx)
    net_contrib=led["contributions"]-led["withdrawals"]
    # net_cash is an estimate from imported ledger; valid only if history is complete from account inception.
    cash_est=led["net_cash"] if not tx.empty else None
    equity_est=val["value"] + cash_est if cash_est is not None else None
    pnl_est=(equity_est-net_contrib) if equity_est is not None and net_contrib>0 else None
    ret=(pnl_est/net_contrib*100) if pnl_est is not None and net_contrib else None
    metrics={"assets_value":val["value"],"snapshot_cost":val["cost"],"unrealized":val["unrealized"],"unpriced":val["unpriced"],
             "cash_estimate":cash_est,"equity_estimate":equity_est,"net_contributions":net_contrib,"pnl_estimate":pnl_est,"return_pct":ret,
             **led}
    return metrics,positions,tx,realized,openlots


def show_performance_page():
    st.header("📈 Performance")
    account=st.selectbox("Compte analysé",["pea","cto_xtb","cto_trade_republic","cto_autre"],
        format_func=lambda x:{"pea":"PEA","cto_xtb":"CTO XTB","cto_trade_republic":"CTO Trade Republic","cto_autre":"CTO autre"}[x])
    m,pos,tx,realized,openlots=performance_metrics(account)
    save_performance_snapshot(account,m)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Actifs valorisés",f"{m['assets_value']:,.2f} €")
    c2.metric("P/L latent snapshot",f"{m['unrealized']:+,.2f} €")
    c3.metric("Dividendes ledger",f"{m['dividends']:+,.2f} €")
    c4.metric("Frais + taxes",f"{m['fees']+m['taxes']:,.2f} €")
    c5,c6,c7,c8=st.columns(4)
    c5.metric("Apports externes",f"{m['contributions']:,.2f} €")
    c6.metric("Retraits externes",f"{m['withdrawals']:,.2f} €")
    c7.metric("P/L réalisé FIFO brut",f"{m['realized_gross']:+,.2f} €")
    c8.metric("Intérêts",f"{m['interest']:+,.2f} €")
    if m["equity_estimate"] is not None and m["net_contributions"]>0:
        st.subheader("Performance globale estimée")
        a,b,c=st.columns(3)
        a.metric("Cash reconstruit",f"{m['cash_estimate']:+,.2f} €")
        b.metric("Valeur totale estimée",f"{m['equity_estimate']:,.2f} €")
        c.metric("Rendement simple estimé",f"{m['return_pct']:+.2f} %",delta=f"{m['pnl_estimate']:+,.2f} €")
        st.caption("Cette estimation suppose que l'historique de transactions importé est complet depuis l'ouverture du compte. Ce n'est pas encore un rendement pondéré dans le temps (TWR).")
    else:
        st.info("Le rendement global ne peut pas encore être reconstruit pour ce compte : il faut un historique de transactions contenant les apports/retraits et un snapshot de positions valorisable.")
    if m["corporate_actions"]:
        st.warning(f"{m['corporate_actions']} opération(s) sur titres (split/bonus/etc.) détectée(s). Le P/L FIFO ne les transforme pas automatiquement afin d'éviter une reconstruction erronée ; le snapshot courtier reste la référence pour les positions courantes.")
    if m["issues"]:
        with st.expander("⚠️ Contrôles du ledger"):
            for item in m["issues"][:50]: st.write("•",item)
    st.subheader("Positions valorisées")
    if not pos.empty: st.dataframe(pos,use_container_width=True,hide_index=True)
    if not realized.empty:
        st.subheader("P/L réalisé — méthode FIFO")
        st.dataframe(realized,use_container_width=True,hide_index=True)
    hist=load_performance_snapshots(account)
    if not hist.empty:
        st.subheader("Historique VISION FUTURE")
        plot=hist.set_index("snapshot_date")[[c for c in ["equity_estimate","net_contributions"] if c in hist.columns]].apply(pd.to_numeric,errors="coerce")
        if not plot.dropna(how="all").empty: st.line_chart(plot)
        st.caption("La courbe se construit à partir des snapshots enregistrés par VISION FUTURE à compter de V7.1.")


def show_arbitrage_page():
    st.header("⚖️ Arbitrage portefeuille")
    account=st.selectbox("Compte",["pea","cto_xtb","cto_trade_republic","cto_autre"],key="arb_account",
        format_func=lambda x:{"pea":"PEA","cto_xtb":"CTO XTB","cto_trade_republic":"CTO Trade Republic","cto_autre":"CTO autre"}[x])
    _,pos=portfolio_valuation(account,use_live=True)
    if pos.empty:
        st.info("Aucune position à analyser."); return
    total=pos["Valeur"].sum(skipna=True)
    rows=[]; bar=st.progress(0)
    for i,(_,r) in enumerate(pos.iterrows(),1):
        ticker=str(r.get("Ticker") or "").strip()
        if not ticker:
            rows.append({"Ticker":"","Entreprise":r.get("Entreprise"),"Poids %":(r.get("Valeur",0)/total*100 if total else np.nan),"Score":np.nan,"Potentiel %":np.nan,"R/R":np.nan,"Lecture":"Ticker à résoudre"})
            bar.progress(i/max(len(pos),1)); continue
        setup=trade_setup(history(ticker,"6mo","1d"))
        if not setup:
            reading="Données insuffisantes"; score=up=rr=np.nan
        else:
            score,up,rr=setup["score"],setup["upside"],setup["rr"]
            if score>=85 and up>=5 and rr>=2: reading="🟢 Renforcer / conserver — signal technique fort"
            elif score<60 or up<2: reading="🟠 Examiner un allègement — signal faible"
            else: reading="🟡 Conserver / surveiller"
        rows.append({"Ticker":ticker,"Entreprise":r.get("Entreprise"),"Poids %":(r.get("Valeur",0)/total*100 if total else np.nan),"P/L %":r.get("P/L %"),"Score":score,"Potentiel %":up,"R/R":rr,"Lecture":reading})
        bar.progress(i/max(len(pos),1))
    bar.empty(); out=pd.DataFrame(rows)
    st.dataframe(out.sort_values("Score",ascending=False,na_position="last"),use_container_width=True,hide_index=True)
    st.caption("Lecture analytique croisant poids du portefeuille et setup technique. Ce module ne garantit ni performance ni opportunité de marché.")


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



@st.cache_data(ttl=120, show_spinner=False)
def batch_history(symbols, period="6mo", interval="1d"):
    symbols = [str(x).strip().upper() for x in symbols if str(x).strip()]
    if not symbols:
        return {}
    try:
        raw = yf.download(
            tickers=" ".join(symbols), period=period, interval=interval,
            group_by="ticker", auto_adjust=False, threads=True,
            progress=False, prepost=False,
        )
    except Exception:
        return {}
    out = {}
    if raw is None or raw.empty:
        return out
    if len(symbols) == 1:
        one = raw.copy()
        if isinstance(one.columns, pd.MultiIndex):
            one.columns = one.columns.get_level_values(-1)
        req = [c for c in ["Open","High","Low","Close","Volume"] if c in one.columns]
        if all(c in one.columns for c in ["Open","High","Low","Close"]):
            out[symbols[0]] = one.dropna(subset=["Open","High","Low","Close"])
        return out
    for sym in symbols:
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                lvl0 = raw.columns.get_level_values(0)
                lvl1 = raw.columns.get_level_values(1)
                if sym in lvl0:
                    d = raw[sym].copy()
                elif sym in lvl1:
                    d = raw.xs(sym, axis=1, level=1).copy()
                else:
                    continue
            else:
                continue
            if all(c in d.columns for c in ["Open","High","Low","Close"]):
                out[sym] = d.dropna(subset=["Open","High","Low","Close"])
        except Exception:
            continue
    return out


def fast_scan(symbols, min_upside=3.0, min_rr=2.0, min_score=72, top_n=20):
    # Stage 1: one threaded/batched daily download for the whole universe.
    daily = batch_history(symbols, period="6mo", interval="1d")
    candidates = []
    for sym, df in daily.items():
        setup = trade_setup(df)
        if not setup:
            continue
        if setup["upside"] >= min_upside and setup["rr"] >= min_rr and setup["score"] >= min_score:
            candidates.append({"Ticker": sym, **setup})
    candidates = sorted(candidates, key=lambda r: (r["score"], r["rr"], r["upside"]), reverse=True)[:max(top_n, 1)]
    if not candidates:
        return pd.DataFrame()

    # Stage 2: confirm only the finalists on 1h. One more batch call, not N calls.
    finalists = [r["Ticker"] for r in candidates]
    hourly = batch_history(finalists, period="3mo", interval="1h")
    rows = []
    for r in candidates:
        sym = r["Ticker"]
        conf = trade_setup(hourly.get(sym)) if sym in hourly else None
        conf_score = conf["score"] if conf else np.nan
        trend_ok = bool(conf and conf["score"] >= 65 and conf["rr"] >= 1.5)
        combined = round((0.65 * r["score"] + 0.35 * conf_score), 1) if conf else float(r["score"])
        rows.append({
            "Ticker": sym,
            "Score": r["score"],
            "Confirmation 1h": conf_score,
            "Score combiné": combined,
            "Prix": r["price"],
            "Entrée": r["entry"],
            "Stop": r["stop"],
            "TP1": r["tp1"],
            "TP2": r["tp2"],
            "Potentiel %": r["upside"],
            "R/R": r["rr"],
            "Qualité": r["quality"],
            "Confirmé 1h": "✅" if trend_ok else "⚠️",
            "Raisons": " • ".join(r.get("reasons", [])),
        })
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(["Score combiné","R/R","Potentiel %"], ascending=False)
    return out

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
            rebuild_stats = None
            if doc == "POSITIONS":
                count=save_positions(account, broker_override, result["normalized"], source_import_hash=meta["hash"])
            else:
                count=save_transactions(account, broker_override, result["normalized"], source_import_hash=meta["hash"])
                rebuild_stats = rebuild_positions_from_transactions(account, broker_override)
            upsert_import_record({
                "file_hash":meta["hash"],"account":account,"filename":uploaded.name,"document_type":doc,
                "broker":broker_override,"row_count":int(count),"status":"IMPORTED","imported_at":datetime.utcnow().isoformat(),
                "metadata":json.dumps({k:v for k,v in meta.items() if k!="hash"},ensure_ascii=False),
            })
            if rebuild_stats is not None:
                st.success(
                    f"☁️ Import terminé : {count} transaction(s) synchronisée(s). "
                    f"Portefeuille reconstruit automatiquement : {rebuild_stats['positions']} position(s) ouverte(s)."
                )
                if rebuild_stats.get("corporate_actions"):
                    st.caption(f"{rebuild_stats['corporate_actions']} opération(s) sur titres intégrée(s) automatiquement.")
                if rebuild_stats.get("issues"):
                    with st.expander("⚠️ Points à vérifier"):
                        for msg in rebuild_stats["issues"][:20]:
                            st.write("•", msg)
            else:
                st.success(f"☁️ Import terminé : {count} position(s) enregistrée(s). Elles seront rechargées automatiquement aux prochaines connexions.")
            st.cache_data.clear()
        except Exception as exc:
            st.error(f"Échec d'enregistrement Supabase : {exc}")


def show_portfolio_page(account, title, broker: str | None = None):
    st.header(title)
    df=load_positions(account, broker=broker)
    if df.empty:
        try:
            rebuilt = ensure_transaction_positions(account)
            if rebuilt:
                df = load_positions(account, broker=broker)
        except Exception as exc:
            st.warning(f"Les transactions sont présentes mais la reconstruction automatique du portefeuille a échoué : {exc}")
    if df.empty:
        st.info("Aucune position enregistrée pour ce compte. Importe un export de positions ou de transactions depuis « Import documents » ; la reconstruction est ensuite automatique.")
        return
    broker_label = broker or "Tous courtiers"
    st.success(f"☁️ {len(df)} position(s) chargée(s) automatiquement depuis Supabase • {broker_label}.")
    totals,m=portfolio_valuation(account,use_live=True, broker=broker)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Valeur suivie",f"{totals['value']:,.2f} €")
    c2.metric("Coût snapshot",f"{totals['cost']:,.2f} €")
    c3.metric("P/L latent",f"{totals['unrealized']:+,.2f} €")
    c4.metric("Sans valorisation",totals['unpriced'])
    st.dataframe(m,use_container_width=True,hide_index=True)
    st.caption("Le cours de marché est utilisé lorsqu'un ticker est résolu ; sinon VISION FUTURE conserve le cours ou la valorisation du dernier export courtier.")

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
    st.caption("Le ledger V7.1 stocke les opérations sans doublons via transaction_id et alimente désormais le moteur Performance.")

# ==========================================================
# SIDEBAR / ROUTING
# ==========================================================
with st.sidebar:
    st.header(f"🔭 {APP_NAME}")
    mode=st.radio("Navigation", ["🏠 Dashboard","📥 Import documents","📁 Documents & données","🏦 PEA","💼 CTO","💰 Transactions","📈 Performance","⚖️ Arbitrage","🔎 Scanner","📊 Analyse","🧪 Simulation"])
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
    accounts=[("pea","PEA"),("cto_xtb","CTO XTB"),("cto_trade_republic","CTO Trade Republic")]
    cards=[]
    for acc,label in accounts:
        val,_=portfolio_valuation(acc,use_live=False)
        txc=len(load_transactions(acc))
        cards.append((label,val["value"],val["unrealized"],txc,len(load_positions(acc))))
    for row in [cards[:3]]:
        cols=st.columns(len(row))
        for col,(label,value,pnl,txc,npos) in zip(cols,row):
            with col:
                st.metric(label,f"{value:,.2f} €",delta=f"{pnl:+,.2f} € latent")
                st.caption(f"{npos} position(s) • {txc} transaction(s)")
    st.info("VISION FUTURE charge les portefeuilles depuis Supabase. Réimporte seulement lorsqu'un courtier fournit un nouvel export ; les transactions déjà connues sont dédupliquées.")

elif mode=="📥 Import documents":
    show_import_page()

elif mode=="📁 Documents & données":
    show_documents_page()

elif mode=="🏦 PEA":
    brokers = available_brokers("pea")
    broker = st.selectbox("Courtier PEA", brokers if brokers else ["BoursoBank"], key="pea_broker")
    show_portfolio_page("pea","🏦 PEA", broker=broker)

elif mode=="💼 CTO":
    acc=st.selectbox("CTO",["cto_xtb","cto_trade_republic","cto_autre"],format_func=lambda x:{"cto_xtb":"XTB","cto_trade_republic":"Trade Republic","cto_autre":"Autre"}[x])
    expected_broker={"cto_xtb":"XTB","cto_trade_republic":"Trade Republic","cto_autre":None}[acc]
    brokers=available_brokers(acc)
    if expected_broker:
        broker=expected_broker
        st.caption(f"Filtre courtier verrouillé : {broker}")
    else:
        broker=st.selectbox("Courtier",brokers if brokers else ["Autre"],key="cto_other_broker")
    show_portfolio_page(acc,f"💼 CTO — {broker or 'Autre'}", broker=broker)

elif mode=="💰 Transactions":
    show_transactions_page()

elif mode=="📈 Performance":
    show_performance_page()

elif mode=="⚖️ Arbitrage":
    show_arbitrage_page()

elif mode=="🔎 Scanner":
    st.header("⚡ Scanner rapide — configurations favorables")
    st.caption("Le moteur effectue un scan groupé en daily, puis confirme seulement les meilleurs candidats en 1h. Objectif : réduire fortement la latence sans promettre qu'un trade sera gagnant.")
    c1,c2,c3,c4=st.columns(4)
    countries=c1.multiselect("Marchés",list(UNIVERSE),default=["USA","France"])
    min_upside=c2.number_input("Potentiel minimum (%)",1.0,30.0,3.0,.5)
    min_rr=c3.number_input("R/R minimum",1.0,5.0,2.0,.1)
    min_score=c4.slider("Score minimum",50,100,72)
    c5,c6=st.columns(2)
    top_n=c5.slider("Finalistes à confirmer",5,30,15)
    only_confirmed=c6.checkbox("Afficher uniquement les setups confirmés en 1h",False)
    pool=sorted(set(sum([UNIVERSE.get(c,[]) for c in countries],[])))
    st.caption(f"Univers : {len(pool)} titres • Filtre potentiel ≥ {min_upside:.1f}%")
    with st.spinner("Analyse groupée du marché…"):
        out=fast_scan(pool,min_upside=min_upside,min_rr=min_rr,min_score=min_score,top_n=top_n)
    if out.empty:
        st.warning("Aucune configuration ne passe les filtres actuels.")
    else:
        # Company names are fetched only for finalists, never for the whole universe.
        names={sym:live_quote(sym).get("name",sym) for sym in out["Ticker"].tolist()}
        out.insert(1,"Entreprise",out["Ticker"].map(names))
        if only_confirmed:
            out=out[out["Confirmé 1h"]=="✅"]
        st.success(f"{len(out)} configuration(s) retenue(s).")
        visible=["Ticker","Entreprise","Score combiné","Score","Confirmation 1h","Confirmé 1h","Prix","Entrée","Stop","TP1","TP2","Potentiel %","R/R","Qualité"]
        st.dataframe(out[visible],use_container_width=True,hide_index=True)
        st.subheader("Pourquoi ces candidats ?")
        for _,r in out.head(8).iterrows():
            with st.expander(f"{r['Ticker']} • score {r['Score combiné']} • potentiel {r['Potentiel %']:.1f}% • R/R {r['R/R']:.2f}"):
                st.write(r.get("Raisons") or "Analyse technique disponible mais sans justification textuelle détaillée.")
                st.caption("Entrée/SL/TP sont des niveaux analytiques basés sur volatilité, support/résistance et momentum. Ils ne garantissent pas un résultat positif.")

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
st.caption("VISION FUTURE V8 Smart Portfolio & Fast Scanner. Les cours yfinance peuvent être différés. Les scénarios Entrée/SL/TP sont des aides analytiques, pas des garanties de performance.")
