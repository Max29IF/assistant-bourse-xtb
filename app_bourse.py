import streamlit as st
import yfinance as yf
import mplfinance as mpf
import tempfile
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Assistant Bourse XTB", page_icon="📈", layout="wide")

st.title("📈 Assistant Technique XTB – Multi-Actifs")

# ========== LISTES DE VALEURS ==========
TICKERS = {
    " Actions US": ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "META", "GOOGL", "AMD", "NFLX", "INTC", "BABA"],
    " Actions France": ["MC.PA", "OR.PA", "SAN.PA", "AIR.PA", "TTE.PA", "BNP.PA", "AI.PA", "DG.PA", "SU.PA"],
    " Actions Europe": ["ASML", "SAP", "SIE.DE", "ALV.DE", "BMW.DE", "UNA.AS", "NESN.SW", "ROG.SW"],
    " Pays Émergents": ["BABA", "TSM", "PDD", "JD", "BIDU", "NIO", "XPEV", "LI"],
    " Matières Premières": ["GC=F", "SI=F", "CL=F", "NG=F", "HG=F", "GOLD", "SILVER"],
    " Crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD"]
}

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("Sélection des valeurs")

    # Favoris
    if "favorites" not in st.session_state:
        st.session_state.favorites = ["AAPL", "TSLA", "NVDA", "BTC-USD"]

    st.subheader("Favoris")
    favorites = st.multiselect(
        "Tes favoris (accès rapide)",
        options=sorted(list(set([t for sublist in TICKERS.values() for t in sublist]))),
        default=st.session_state.favorites,
        key="fav_selector"
    )
    st.session_state.favorites = favorites

    st.markdown("---")

    # Sélection par catégorie
    st.subheader("Ajouter par catégorie")
    selected_from_categories = []
    for category, tickers in TICKERS.items():
        with st.expander(category):
            chosen = st.multiselect(
                f"Choisir dans {category}",
                options=tickers,
                key=category
            )
            selected_from_categories.extend(chosen)

    st.markdown("---")

    # Ajout libre
    st.subheader("Ajouter un ticker libre")
    custom_ticker = st.text_input("Ticker personnalisé (ex: MSFT, EURUSD=X, DE40)")
    if custom_ticker:
        custom_ticker = custom_ticker.strip().upper()

    # Construction de la liste finale
    all_selected = list(set(favorites + selected_from_categories + ([custom_ticker] if custom_ticker else [])))
    
    st.markdown("---")
    periode = st.selectbox("Période", ["5d", "1mo", "3mo", "6mo"], index=1)
    intervalle = st.selectbox("Intervalle", ["15m", "30m", "1h", "1d"], index=2)
    
    refresh_rate = st.selectbox(
        "Rafraîchissement auto",
        options=[0, 30, 60, 120],
        format_func=lambda x: "Désactivé" if x == 0 else f"Toutes les {x}s",
        index=2
    )

if refresh_rate > 0:
    st_autorefresh(interval=refresh_rate * 1000, key="refresh")

# ========== FONCTIONS ==========
def get_data(symbol, period, interval):
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval)
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

def generate_chart(df, symbol, period, interval):
    df = df.copy()
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['SMA50'] = df['Close'].rolling(50).mean()
    
    apds = [
        mpf.make_addplot(df['SMA20'], color='blue', width=1),
        mpf.make_addplot(df['SMA50'], color='orange', width=1.2)
    ]
    
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        path = tmp.name
    
    mpf.plot(df, type='candle', style='yahoo',
             title=f"{symbol} | {period} | {interval}",
             volume=True, addplot=apds, figsize=(10, 5),
             savefig=path)
    return path

# ========== AFFICHAGE ==========
if not all_selected:
    st.warning("Sélectionne au moins une valeur dans la barre latérale.")
else:
    st.subheader(f"Tableau des opportunités ({len(all_selected)} valeurs)")
    
    for symbol in all_selected:
        df = get_data(symbol, periode, intervalle)
        signal, explanation, score = calculate_signals(df)
        
        last_price = df['Close'].iloc[-1] if df is not None else None
        change = None
        if df is not None and len(df) > 1:
            change = ((df['Close'].iloc[-1] / df['Close'].iloc[-2]) - 1) * 100
        
        col1, col2, col3, col4 = st.columns([2, 2, 1.5, 4])
        
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
        
        if df is not None:
            with st.expander(f"Graphique {symbol}"):
                chart_path = generate_chart(df, symbol, periode, intervalle)
                st.image(chart_path, use_container_width=True)
        
        st.markdown("---")

st.caption("Outil d'aide à la décision – Ce n'est pas un conseil financier.")
