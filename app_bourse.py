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

    for symbol in all_selected:
        df = get_data(symbol)
        signal, explanation, score = calculate_signals(df)

        last_price = df['Close'].iloc[-1] if df is not None else None
        change = None
        if df is not None and len(df) > 1:
            change = ((df['Close'].iloc[-1] / df['Close'].iloc[-2]) - 1) * 100

        # En-tête de chaque actif
        col1, col2, col3, col4 = st.columns([2, 2, 1.5, 3])
        with col1:
            st.metric(symbol, f"{last_price:.4f}" if last_price else "N/A",
                      f"{change:+.2f}%" if change is not None else None)
        with col2:
            color = "🟢" if signal == "ACHAT" else "🔴" if signal == "VENTE" else "⚪"
            st.markdown(f"### {color} {signal}")
        with col3:
            st.write(f"**Score :** {score}")
        with col4:
            st.caption(explanation)

        # Emplacement réservé pour Entrée / SL / TP (on l'activera plus tard)
        # st.info("Entrée : - | Stop Loss : - | TP1 : - | TP2 : -")

        # Graphique TradingView
        components.html(tradingview_chart(symbol, timeframe), height=520)

        st.markdown("---")

st.caption("Graphiques TradingView + Signaux automatiques – Outil d'aide à la décision uniquement.")
