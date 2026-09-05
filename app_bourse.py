import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

st.set_page_config(page_title="Assistant Bourse XTB", page_icon="📈", layout="wide")

st.title("📈 Assistant Technique XTB – TradingView")

# ========== LISTES DE VALEURS ==========
TICKERS = {
    "Actions US": ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "META", "GOOGL", "AMD", "NFLX", "INTC"],
    "Actions France": ["MC.PA", "OR.PA", "SAN.PA", "AIR.PA", "TTE.PA", "BNP.PA", "AI.PA", "DG.PA"],
    "Actions Europe": ["ASML", "SAP", "SIE.DE", "ALV.DE", "BMW.DE", "UNA.AS", "NESN.SW"],
    "Pays Émergents": ["BABA", "TSM", "PDD", "JD", "BIDU", "NIO"],
    "Matières Premières": ["GC=F", "SI=F", "CL=F", "NG=F", "GOLD", "SILVER"],
    "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD"]
}

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("Sélection des valeurs")

    if "favorites" not in st.session_state:
        st.session_state.favorites = ["AAPL", "TSLA", "NVDA", "BTC-USD"]

    st.subheader("Favoris")
    favorites = st.multiselect(
        "Tes favoris",
        options=sorted(list(set([t for sublist in TICKERS.values() for t in sublist]))),
        default=st.session_state.favorites
    )
    st.session_state.favorites = favorites

    st.markdown("---")
    st.subheader("Par catégorie")
    selected_from_categories = []
    for category, tickers in TICKERS.items():
        with st.expander(category):
            chosen = st.multiselect(f"{category}", options=tickers, key=category)
            selected_from_categories.extend(chosen)

    st.markdown("---")
    custom_ticker = st.text_input("Ticker libre (ex: MSFT, EURUSD=X, DE40)")
    if custom_ticker:
        custom_ticker = custom_ticker.strip().upper()

    all_selected = list(set(favorites + selected_from_categories + ([custom_ticker] if custom_ticker else [])))

    st.markdown("---")
    timeframe = st.selectbox(
        "Timeframe TradingView",
        options=["1", "5", "15", "30", "60", "240", "D", "W"],
        format_func=lambda x: {
            "1": "1 minute", "5": "5 minutes", "15": "15 minutes", "30": "30 minutes",
            "60": "1 heure", "240": "4 heures", "D": "Journalier", "W": "Hebdomadaire"
        }[x],
        index=4
    )

    refresh_rate = st.selectbox(
        "Rafraîchissement auto",
        options=[0, 30, 60, 120],
        format_func=lambda x: "Désactivé" if x == 0 else f"Toutes les {x}s",
        index=2
    )

if refresh_rate > 0:
    st_autorefresh(interval=refresh_rate * 1000, key="refresh")

# ========== FONCTIONS ==========
def get_data(symbol):
    try:
        df = yf.Ticker(symbol).history(period="1mo", interval="1h")
        if df.empty or len(df) < 30:
            return None
        return df
    except:
        return None

def calculate_signals(df):
    if df is None or len(df) < 50:
        return "ATTENTE", "Données insuffisantes", 0

    df = df.copy()
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['SMA50'] = df['Close'].rolling(50).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    score = 0
    reasons = []

    if last['RSI'] < 30:
        score += 2
        reasons.append("RSI survendu")
    elif last['RSI'] > 70:
        score -= 2
        reasons.append("RSI suracheté")

    if prev['MACD'] < prev['Signal'] and last['MACD'] > last['Signal']:
        score += 2
        reasons.append("Croisement MACD haussier")
    elif prev['MACD'] > prev['Signal'] and last['MACD'] < last['Signal']:
        score -= 2
        reasons.append("Croisement MACD baissier")

    if last['Close'] > last['SMA20'] > last['SMA50']:
        score += 1
        reasons.append("Tendance haussière")
    elif last['Close'] < last['SMA20'] < last['SMA50']:
        score -= 1
        reasons.append("Tendance baissière")

    if score >= 3:
        signal = "ACHAT"
    elif score <= -3:
        signal = "VENTE"
    else:
        signal = "ATTENTE"

    explanation = " | ".join(reasons) if reasons else "Pas de signal fort"
    return signal, explanation, score

def tradingview_chart(symbol, interval="60"):
    # Convertit certains symboles pour TradingView
    tv_symbol = symbol
    if symbol.endswith("=X"):
        tv_symbol = symbol.replace("=X", "")
    if symbol == "GC=F":
        tv_symbol = "GOLD"
    if symbol == "SI=F":
        tv_symbol = "SILVER"
    if symbol == "CL=F":
        tv_symbol = "USOIL"

    widget = f"""
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container">
      <div id="tradingview_{symbol}"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "width": "100%",
        "height": 500,
        "symbol": "{tv_symbol}",
        "interval": "{interval}",
        "timezone": "Europe/Paris",
        "theme": "dark",
        "style": "1",
        "locale": "fr",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_{symbol}"
      }}
      );
      </script>
    </div>
    <!-- TradingView Widget END -->
    """
    return widget

# ========== AFFICHAGE ==========
if not all_selected:
    st.warning("Sélectionne au moins une valeur dans la barre latérale.")
else:
    st.subheader(f"Suivi de {len(all_selected)} valeur(s)")

    for symbol in all_selected:# ========== Niveaux proposés ==========
if df is not None and len(df) > 20:
    last_close = df['Close'].iloc[-1]
    recent_high = df['High'].tail(20).max()
    recent_low = df['Low'].tail(20).min()
    atr = (df['High'] - df['Low']).tail(14).mean()  # ATR simplifié

    if signal == "ACHAT":
        entry = last_close
        stop_loss = round(last_close - (1.2 * atr), 4)
        tp1 = round(last_close + (1.5 * atr), 4)
        tp2 = round(last_close + (2.5 * atr), 4)
    elif signal == "VENTE":
        entry = last_close
        stop_loss = round(last_close + (1.2 * atr), 4)
        tp1 = round(last_close - (1.5 * atr), 4)
        tp2 = round(last_close - (2.5 * atr), 4)
    else:
        entry = stop_loss = tp1 = tp2 = "-"

    # Affichage des niveaux
    st.markdown(f"""
    <div style="background-color:#1e1e1e; padding:12px 18px; border-radius:10px; margin-bottom:10px; border-left: 5px solid {'#00c853' if signal=='ACHAT' else '#ff1744' if signal=='VENTE' else '#9e9e9e'};">
        <b>Signal :</b> {signal} &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>Entrée :</b> {entry} &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>Stop Loss :</b> {stop_loss} &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>TP1 :</b> {tp1} &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>TP2 :</b> {tp2}
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("Pas assez de données pour proposer des niveaux.")
       
