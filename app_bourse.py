import streamlit as st
import yfinance as yf
import mplfinance as mpf
import tempfile
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Assistant Bourse XTB Pro", page_icon="📈", layout="wide")

st.title("📈 Assistant Technique XTB – Multi-Actifs + Opportunités")

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("Paramètres")
    
    # Liste d'actifs à suivre
    default_tickers = ["AAPL", "TSLA", "NVDA", "BTC-USD", "EURUSD=X"]
    tickers_input = st.text_area(
        "Symboles à suivre (un par ligne)",
        value="\n".join(default_tickers),
        height=150
    )
    tickers = [t.strip().upper() for t in tickers_input.split("\n") if t.strip()]
    
    periode = st.selectbox("Période", ["5d", "1mo", "3mo", "6mo"], index=1)
    intervalle = st.selectbox("Intervalle", ["15m", "30m", "1h", "1d"], index=2)
    
    refresh_rate = st.selectbox(
        "Rafraîchissement automatique",
        options=[0, 30, 60, 120],
        format_func=lambda x: "Désactivé" if x == 0 else f"Toutes les {x} secondes",
        index=2
    )
    
    st.markdown("---")
    st.info("Les signaux sont basés sur RSI + MACD + SMA. Ce n'est pas un conseil financier.")

# Auto-refresh
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
    """Retourne un signal simple + explication"""
    if df is None or len(df) < 50:
        return "ATTENTE", "Données insuffisantes", 0
    
    df = df.copy()
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['SMA50'] = df['Close'].rolling(50).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    score = 0
    reasons = []
    
    # RSI
    if last['RSI'] < 30:
        score += 2
        reasons.append("RSI survendu")
    elif last['RSI'] > 70:
        score -= 2
        reasons.append("RSI suracheté")
    
    # MACD croisement
    if prev['MACD'] < prev['Signal'] and last['MACD'] > last['Signal']:
        score += 2
        reasons.append("Croisement MACD haussier")
    elif prev['MACD'] > prev['Signal'] and last['MACD'] < last['Signal']:
        score -= 2
        reasons.append("Croisement MACD baissier")
    
    # Tendance SMA
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
    
    mpf.plot(df, type='candle', style='yahoo', title=f"{symbol} | {period} | {interval}",
             volume=True, addplot=apds, figsize=(10, 5), savefig=path)
    return path

# ========== AFFICHAGE ==========
if not tickers:
    st.warning("Ajoute au moins un symbole dans la barre latérale.")
else:
    st.subheader("Tableau des opportunités")
    
    results = []
    for symbol in tickers:
        df = get_data(symbol, periode, intervalle)
        signal, explanation, score = calculate_signals(df)
        
        last_price = df['Close'].iloc[-1] if df is not None else None
        change = None
        if df is not None and len(df) > 1:
            change = ((df['Close'].iloc[-1] / df['Close'].iloc[-2]) - 1) * 100
        
        results.append({
            "Symbole": symbol,
            "Prix": f"{last_price:.4f}" if last_price else "N/A",
            "Variation": f"{change:+.2f}%" if change is not None else "N/A",
            "Signal": signal,
            "Score": score,
            "Raison": explanation,
            "df": df
        })
    
    # Affichage du tableau
    for res in results:
        col1, col2, col3, col4 = st.columns([2, 2, 2, 4])
        
        with col1:
            st.metric(res["Symbole"], res["Prix"], res["Variation"])
        
        with col2:
            color = "🟢" if res["Signal"] == "ACHAT" else "🔴" if res["Signal"] == "VENTE" else "⚪"
            st.write(f"### {color} {res['Signal']}")
        
        with col3:
            st.write(f"Score : **{res['Score']}**")
        
        with col4:
            st.caption(res["Raison"])
        
        # Graphique
        if res["df"] is not None:
            with st.expander(f"Voir le graphique de {res['Symbole']}"):
                chart_path = generate_chart(res["df"], res["Symbole"], periode, intervalle)
                st.image(chart_path, use_container_width=True)
        
        st.markdown("---")

st.caption("Les signaux sont automatiques et basés sur des règles techniques simples. Toujours confirmer avec une analyse complète avant de trader.")