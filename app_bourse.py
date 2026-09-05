
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from datetime import datetime

# ==========================================================
# CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Assistant Bourse XTB V2",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📈 Assistant Technique XTB — V2")
st.caption(
    "Scanner technique + fondamentaux + actualités + score global /100. "
    "Outil d'analyse, pas une recommandation financière."
)

# ==========================================================
# LISTES DE VALEURS
# ==========================================================

TICKERS = {
    "Actions US": [
        "AAPL", "TSLA", "NVDA", "MSFT", "AMZN",
        "META", "GOOGL", "AMD", "NFLX", "INTC"
    ],
    "Actions France": [
        "MC.PA", "OR.PA", "SAN.PA", "AIR.PA",
        "TTE.PA", "BNP.PA", "AI.PA", "DG.PA"
    ],
    "Actions Europe": [
        "ASML", "SAP", "SIE.DE", "ALV.DE",
        "BMW.DE", "UNA.AS", "NESN.SW"
    ],
    "Pays émergents": [
        "BABA", "TSM", "PDD", "JD", "BIDU", "NIO"
    ],
    "Matières premières": [
        "GC=F", "SI=F", "CL=F", "NG=F"
    ],
    "Crypto": [
        "BTC-USD", "ETH-USD", "SOL-USD",
        "BNB-USD", "XRP-USD", "ADA-USD"
    ],
}

ALL_TICKERS = sorted(
    list(set(t for group in TICKERS.values() for t in group))
)

# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:
    st.header("⚙️ Scanner")

    if "favorites" not in st.session_state:
        st.session_state.favorites = [
            "AAPL", "TSLA", "NVDA", "BTC-USD"
        ]

    st.subheader("⭐ Favoris")

    favorites = st.multiselect(
        "Tes favoris",
        options=ALL_TICKERS,
        default=st.session_state.favorites,
    )

    st.session_state.favorites = favorites

    st.markdown("---")
    st.subheader("📂 Par catégorie")

    selected_from_categories = []

    for category, tickers in TICKERS.items():
        with st.expander(category):
            chosen = st.multiselect(
                category,
                options=tickers,
                key=f"cat_{category}",
            )
            selected_from_categories.extend(chosen)

    st.markdown("---")

    custom_ticker = st.text_input(
        "Ticker libre",
        placeholder="Ex: MSFT, EURUSD=X, DE40..."
    )

    if custom_ticker:
        custom_ticker = custom_ticker.strip().upper()

    all_selected = list(
        dict.fromkeys(
            favorites
            + selected_from_categories
            + ([custom_ticker] if custom_ticker else [])
        )
    )

    st.markdown("---")

    interval = st.selectbox(
        "Intervalle des données",
        options=["1h", "1d"],
        format_func=lambda x: {
            "1h": "1 heure",
            "1d": "Journalier",
        }[x],
        index=0,
    )

    period = st.selectbox(
        "Historique",
        options=["3mo", "6mo", "1y"],
        index=0,
    )

    refresh_rate = st.selectbox(
        "Rafraîchissement auto",
        options=[0, 30, 60, 120, 300],
        format_func=lambda x: (
            "Désactivé" if x == 0 else f"Toutes les {x}s"
        ),
        index=2,
    )

    min_score = st.slider(
        "Seuil alerte opportunité",
        min_value=50,
        max_value=90,
        value=70,
        step=5,
    )

    show_news = st.checkbox(
        "Afficher les actualités",
        value=True,
    )

    show_chart = st.checkbox(
        "Afficher TradingView",
        value=True,
    )

if refresh_rate > 0:
    st_autorefresh(
        interval=refresh_rate * 1000,
        key="market_refresh"
    )

# ==========================================================
# OUTILS
# ==========================================================

def safe_float(value):
    try:
        if value is None:
            return None
        value = float(value)
        if np.isnan(value) or np.isinf(value):
            return None
        return value
    except Exception:
        return None


def fmt_number(value, decimals=2):
    value = safe_float(value)
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def fmt_percent(value):
    value = safe_float(value)
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%"


def format_market_cap(value):
    value = safe_float(value)

    if value is None:
        return "N/A"

    if value >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.2f} T"

    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f} Md"

    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f} M"

    return f"{value:,.0f}"


def score_bar(score):
    score = max(0, min(100, int(round(score))))
    filled = score // 5
    empty = 20 - filled
    return "█" * filled + "░" * empty


# ==========================================================
# DONNÉES MARCHÉ
# ==========================================================

@st.cache_data(ttl=45, show_spinner=False)
def get_data(symbol, selected_period="3mo", selected_interval="1h"):
    try:
        df = yf.Ticker(symbol).history(
            period=selected_period,
            interval=selected_interval,
            auto_adjust=False,
        )

        if df is None or df.empty:
            return None

        df = df.dropna(subset=["Close"])

        return df

    except Exception:
        return None


# ==========================================================
# INDICATEURS TECHNIQUES
# ==========================================================

def add_indicators(df):
    df = df.copy()

    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["EMA12"] = df["Close"].ewm(
        span=12, adjust=False
    ).mean()
    df["EMA26"] = df["Close"].ewm(
        span=26, adjust=False
    ).mean()

    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["MACD_SIGNAL"] = df["MACD"].ewm(
        span=9, adjust=False
    ).mean()

    delta = df["Close"].diff()

    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    df["RSI"] = 100 - (100 / (1 + rs))

    high_low = df["High"] - df["Low"]
    high_close = abs(
        df["High"] - df["Close"].shift(1)
    )
    low_close = abs(
        df["Low"] - df["Close"].shift(1)
    )

    true_range = pd.concat(
        [high_low, high_close, low_close],
        axis=1,
    ).max(axis=1)

    df["ATR"] = true_range.rolling(14).mean()

    df["VOL_SMA20"] = df["Volume"].rolling(20).mean()

    df["ROC20"] = (
        df["Close"].pct_change(20) * 100
    )

    return df


def technical_analysis(df):
    if df is None or len(df) < 55:
        return {
            "score": 50,
            "signal": "ATTENTE",
            "reasons": ["Données insuffisantes"],
            "entry": None,
            "stop": None,
            "tp1": None,
            "tp2": None,
            "rr1": None,
            "rr2": None,
            "support": None,
            "resistance": None,
            "atr": None,
            "rsi": None,
            "trend": "N/A",
        }

    d = add_indicators(df)

    last = d.iloc[-1]
    prev = d.iloc[-2]

    close = safe_float(last["Close"])
    sma20 = safe_float(last["SMA20"])
    sma50 = safe_float(last["SMA50"])
    rsi = safe_float(last["RSI"])
    macd = safe_float(last["MACD"])
    macd_signal = safe_float(last["MACD_SIGNAL"])
    prev_macd = safe_float(prev["MACD"])
    prev_signal = safe_float(prev["MACD_SIGNAL"])
    atr = safe_float(last["ATR"])
    volume = safe_float(last["Volume"])
    volume_avg = safe_float(last["VOL_SMA20"])

    support = safe_float(
        d["Low"].tail(20).min()
    )

    resistance = safe_float(
        d["High"].tail(20).max()
    )

    score = 50
    reasons = []

    # -----------------------------
    # TENDANCE : +/- 20
    # -----------------------------

    if (
        close is not None
        and sma20 is not None
        and sma50 is not None
    ):
        if close > sma20 > sma50:
            score += 20
            reasons.append("Tendance haussière")
            trend = "HAUSSIÈRE"
        elif close < sma20 < sma50:
            score -= 20
            reasons.append("Tendance baissière")
            trend = "BAISSIÈRE"
        else:
            trend = "NEUTRE"
            reasons.append("Tendance neutre")
    else:
        trend = "N/A"

    # -----------------------------
    # RSI : +/- 15
    # -----------------------------

    if rsi is not None:

        if 50 <= rsi <= 65:
            score += 15
            reasons.append("RSI favorable")
        elif 65 < rsi <= 72:
            score += 5
            reasons.append("RSI élevé")
        elif 30 <= rsi < 50:
            score -= 5
            reasons.append("RSI faible")
        elif rsi < 30:
            score += 8
            reasons.append("RSI survendu")
        elif rsi > 72:
            score -= 10
            reasons.append("RSI suracheté")

    # -----------------------------
    # MACD : +/- 20
    # -----------------------------

    if (
        macd is not None
        and macd_signal is not None
        and prev_macd is not None
        and prev_signal is not None
    ):

        if macd > macd_signal:

            score += 10
            reasons.append("MACD haussier")

            if prev_macd <= prev_signal:
                score += 10
                reasons.append("Croisement MACD haussier")

        else:

            score -= 10
            reasons.append("MACD baissier")

            if prev_macd >= prev_signal:
                score -= 10
                reasons.append("Croisement MACD baissier")

    # -----------------------------
    # VOLUME : +/- 10
    # -----------------------------

    if (
        volume is not None
        and volume_avg is not None
        and volume_avg > 0
    ):

        volume_ratio = volume / volume_avg

        if volume_ratio >= 1.5:
            score += 10
            reasons.append("Volume en forte hausse")
        elif volume_ratio >= 1.1:
            score += 5
            reasons.append("Volume supérieur à la moyenne")
        elif volume_ratio < 0.7:
            score -= 5
            reasons.append("Volume faible")

    # -----------------------------
    # MOMENTUM : +/- 10
    # -----------------------------

    roc20 = safe_float(last["ROC20"])

    if roc20 is not None:

        if roc20 >= 8:
            score += 10
            reasons.append("Momentum fort")
        elif roc20 > 0:
            score += 5
            reasons.append("Momentum positif")
        elif roc20 <= -8:
            score -= 10
            reasons.append("Momentum négatif")
        else:
            score -= 5

    score = max(0, min(100, score))

    # -----------------------------
    # SIGNAL
    # -----------------------------

    if score >= 70:
        signal = "ACHAT"
    elif score <= 30:
        signal = "VENTE"
    else:
        signal = "ATTENTE"

    # -----------------------------
    # NIVEAUX
    # -----------------------------

    entry = close
    stop = None
    tp1 = None
    tp2 = None
    rr1 = None
    rr2 = None

    if (
        entry is not None
        and atr is not None
        and atr > 0
    ):

        if signal == "ACHAT":

            atr_stop = entry - 1.2 * atr

            # On place le SL sous le support
            support_stop = (
                support - 0.15 * atr
                if support is not None
                else atr_stop
            )

            stop = min(
                atr_stop,
                support_stop
            )

            risk = entry - stop

            if risk > 0:
                tp1 = entry + 1.5 * risk
                tp2 = entry + 2.5 * risk

                if (
                    resistance is not None
                    and resistance > entry
                    and resistance < tp1
                ):
                    tp1 = resistance

                rr1 = abs(tp1 - entry) / risk
                rr2 = abs(tp2 - entry) / risk

        elif signal == "VENTE":

            atr_stop = entry + 1.2 * atr

            resistance_stop = (
                resistance + 0.15 * atr
                if resistance is not None
                else atr_stop
            )

            stop = max(
                atr_stop,
                resistance_stop
            )

            risk = stop - entry

            if risk > 0:
                tp1 = entry - 1.5 * risk
                tp2 = entry - 2.5 * risk

                if (
                    support is not None
                    and support < entry
                    and support > tp1
                ):
                    tp1 = support

                rr1 = abs(tp1 - entry) / risk
                rr2 = abs(tp2 - entry) / risk

    return {
        "score": int(score),
        "signal": signal,
        "reasons": reasons,
        "entry": entry,
        "stop": stop,
        "tp1": tp1,
        "tp2": tp2,
        "rr1": rr1,
        "rr2": rr2,
        "support": support,
        "resistance": resistance,
        "atr": atr,
        "rsi": rsi,
        "trend": trend,
    }


# ==========================================================
# FONDAMENTAUX
# ==========================================================

@st.cache_data(ttl=900, show_spinner=False)
def get_fundamentals(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}

        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
        )

        return {
            "name": info.get("longName", symbol),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap"),
            "price": price,
            "currency": info.get("currency", ""),
            "pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg": info.get("pegRatio"),
            "eps": info.get("trailingEps"),
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "debt_equity": info.get("debtToEquity"),
            "free_cashflow": info.get("freeCashflow"),
            "dividend_yield": info.get("dividendYield"),
            "target_mean": info.get("targetMeanPrice"),
            "target_high": info.get("targetHighPrice"),
            "target_low": info.get("targetLowPrice"),
            "recommendation": info.get("recommendationKey"),
            "analyst_count": info.get("numberOfAnalystOpinions"),
            "beta": info.get("beta"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
        }

    except Exception:
        return None


def fundamentals_analysis(f):
    if not f:
        return 50, ["Fondamentaux indisponibles"]

    # Pour matières premières / crypto :
    # Yahoo fournit moins de données fondamentales.
    available = sum(
        x is not None
        for x in [
            f.get("pe"),
            f.get("profit_margin"),
            f.get("revenue_growth"),
            f.get("roe"),
        ]
    )

    if available == 0:
        return 50, [
            "Fondamentaux limités pour cette classe d'actif"
        ]

    score = 50
    reasons = []

    # Rentabilité
    margin = safe_float(f.get("profit_margin"))

    if margin is not None:
        if margin > 0.20:
            score += 10
            reasons.append("Marge bénéficiaire forte")
        elif margin > 0.10:
            score += 5
        elif margin < 0:
            score -= 10
            reasons.append("Marge négative")

    # ROE
    roe = safe_float(f.get("roe"))

    if roe is not None:
        if roe > 0.20:
            score += 10
            reasons.append("ROE élevé")
        elif roe > 0.10:
            score += 5
        elif roe < 0:
            score -= 5

    # Croissance CA
    growth = safe_float(f.get("revenue_growth"))

    if growth is not None:
        if growth > 0.15:
            score += 10
            reasons.append("Croissance du CA forte")
        elif growth > 0:
            score += 5
        elif growth < -0.10:
            score -= 10
            reasons.append("CA en baisse")

    # Croissance bénéfice
    earnings_growth = safe_float(
        f.get("earnings_growth")
    )

    if earnings_growth is not None:
        if earnings_growth > 0.15:
            score += 10
            reasons.append("Bénéfices en croissance")
        elif earnings_growth < -0.15:
            score -= 10
            reasons.append("Bénéfices en baisse")

    # PER
    pe = safe_float(f.get("pe"))

    if pe is not None:

        if 0 < pe <= 20:
            score += 10
            reasons.append("Valorisation raisonnable")
        elif 20 < pe <= 35:
            score += 3
        elif pe > 60:
            score -= 10
            reasons.append("PER élevé")

    # Dette
    debt = safe_float(f.get("debt_equity"))

    if debt is not None:

        if debt < 80:
            score += 5
            reasons.append("Endettement maîtrisé")
        elif debt > 200:
            score -= 10
            reasons.append("Endettement élevé")

    # Consensus analystes
    recommendation = str(
        f.get("recommendation") or ""
    ).lower()

    if recommendation in [
        "strong_buy",
        "strongbuy",
        "buy",
    ]:
        score += 10
        reasons.append("Consensus analystes favorable")

    elif recommendation in [
        "sell",
        "strong_sell",
        "strongsell",
    ]:
        score -= 10
        reasons.append("Consensus analystes défavorable")

    score = max(0, min(100, score))

    return int(score), reasons


# ==========================================================
# ACTUALITÉS
# ==========================================================

@st.cache_data(ttl=300, show_spinner=False)
def get_news(symbol, limit=6):
    try:
        ticker = yf.Ticker(symbol)
        raw_news = ticker.news or []

        articles = []

        for item in raw_news[:limit]:

            content = item.get("content", item)

            title = content.get(
                "title",
                item.get("title", "Titre indisponible")
            )

            provider = content.get(
                "provider",
                {}
            )

            if isinstance(provider, dict):
                publisher = provider.get(
                    "displayName",
                    "Source inconnue"
                )
            else:
                publisher = str(provider)

            canonical = content.get(
                "canonicalUrl",
                {}
            )

            if isinstance(canonical, dict):
                url = canonical.get("url", "")
            else:
                url = content.get("link", "")

            pub_date = content.get(
                "pubDate",
                item.get("providerPublishTime", "")
            )

            articles.append({
                "title": str(title),
                "publisher": str(publisher),
                "url": str(url),
                "date": str(pub_date),
            })

        return articles

    except Exception:
        return []


def news_analysis(news):
    if not news:
        return 50, "NEUTRE", [
            "Aucune actualité exploitable"
        ]

    positive_words = [
        "hausse", "croissance", "profit",
        "profits", "bénéfice", "record",
        "partenariat", "contrat", "succès",
        "buy", "upgrade", "bullish", "beat",
        "growth", "strong", "positive",
        "surge", "raises", "raised",
        "outperform", "revenue"
    ]

    negative_words = [
        "baisse", "perte", "pertes",
        "chute", "crise", "dette",
        "licenciement", "poursuite",
        "amende", "downgrade", "sell",
        "bearish", "miss", "weak",
        "negative", "warning", "lawsuit",
        "cuts", "cut", "decline",
        "underperform"
    ]

    score = 0
    positives = 0
    negatives = 0

    for article in news:

        title = article["title"].lower()

        for word in positive_words:
            if word in title:
                score += 1
                positives += 1

        for word in negative_words:
            if word in title:
                score -= 1
                negatives += 1

    if score >= 3:
        sentiment = "POSITIF"
    elif score <= -3:
        sentiment = "NÉGATIF"
    else:
        sentiment = "NEUTRE"

    news_score = int(
        max(
            0,
            min(
                100,
                50 + score * 8
            )
        )
    )

    reasons = [
        f"{positives} signal(s) positif(s)",
        f"{negatives} signal(s) négatif(s)",
    ]

    return news_score, sentiment, reasons


# ==========================================================
# ÉVÉNEMENTS
# ==========================================================

@st.cache_data(ttl=900, show_spinner=False)
def get_calendar_info(symbol):
    try:
        cal = yf.Ticker(symbol).calendar

        if cal is None:
            return {}

        if isinstance(cal, pd.DataFrame):
            return {}

        if isinstance(cal, dict):
            return cal

        return {}

    except Exception:
        return {}


# ==========================================================
# SCORE GLOBAL
# ==========================================================

def global_analysis(
    technical_score,
    fundamental_score,
    news_score
):
    # Pondération :
    # technique 50 %
    # fondamentaux 30 %
    # actualités 20 %

    global_score = (
        technical_score * 0.50
        + fundamental_score * 0.30
        + news_score * 0.20
    )

    global_score = int(round(global_score))

    if global_score >= 80:
        label = "OPPORTUNITÉ FORTE"
        emoji = "🚀"
    elif global_score >= 70:
        label = "OPPORTUNITÉ"
        emoji = "🟢"
    elif global_score >= 60:
        label = "SURVEILLER"
        emoji = "🟡"
    elif global_score <= 35:
        label = "RISQUE BAISSIER"
        emoji = "🔴"
    else:
        label = "ATTENTE"
        emoji = "⚪"

    return global_score, label, emoji


# ==========================================================
# TRADINGVIEW
# ==========================================================

TV_MAP = {
    "MC.PA": "EURONEXT:MC",
    "OR.PA": "EURONEXT:OR",
    "SAN.PA": "EURONEXT:SAN",
    "AIR.PA": "EURONEXT:AIR",
    "TTE.PA": "EURONEXT:TTE",
    "BNP.PA": "EURONEXT:BNP",
    "AI.PA": "EURONEXT:AI",
    "DG.PA": "EURONEXT:DG",
    "SIE.DE": "XETR:SIE",
    "ALV.DE": "XETR:ALV",
    "BMW.DE": "XETR:BMW",
    "UNA.AS": "EURONEXT:UNA",
    "NESN.SW": "SIX:NESN",
    "ASML": "NASDAQ:ASML",
    "SAP": "NYSE:SAP",
    "GC=F": "COMEX:GC1!",
    "SI=F": "COMEX:SI1!",
    "CL=F": "NYMEX:CL1!",
    "NG=F": "NYMEX:NG1!",
    "BTC-USD": "BINANCE:BTCUSDT",
    "ETH-USD": "BINANCE:ETHUSDT",
    "SOL-USD": "BINANCE:SOLUSDT",
    "BNB-USD": "BINANCE:BNBUSDT",
    "XRP-USD": "BINANCE:XRPUSDT",
    "ADA-USD": "BINANCE:ADAUSDT",
}


def tradingview_chart(symbol, interval="60"):
    tv_symbol = TV_MAP.get(symbol, symbol)

    widget_id = (
        "tv_"
        + symbol.replace("=", "_")
        .replace("-", "_")
        .replace(".", "_")
    )

    widget = f"""
    <div class="tradingview-widget-container">
      <div id="{widget_id}"></div>

      <script
        type="text/javascript"
        src="https://s3.tradingview.com/tv.js">
      </script>

      <script type="text/javascript">

      new TradingView.widget({{
          "autosize": true,
          "symbol": "{tv_symbol}",
          "interval": "{interval}",
          "timezone": "Europe/Paris",
          "theme": "dark",
          "style": "1",
          "locale": "fr",
          "enable_publishing": false,
          "allow_symbol_change": true,
          "hide_side_toolbar": false,
          "container_id": "{widget_id}"
      }});

      </script>
    </div>
    """

    return widget


# ==========================================================
# AFFICHAGE
# ==========================================================

if not all_selected:

    st.warning(
        "Sélectionne au moins une valeur dans la barre latérale."
    )

else:

    st.subheader(
        f"🔎 Scanner de {len(all_selected)} valeur(s)"
    )

    dashboard = []

    for symbol in all_selected:

        df = get_data(
            symbol,
            selected_period=period,
            selected_interval=interval,
        )

        if df is None or len(df) < 55:

            st.error(
                f"{symbol} : données insuffisantes."
            )
            continue

        technical = technical_analysis(df)

        fundamentals = get_fundamentals(symbol)

        fundamental_score, fundamental_reasons = (
            fundamentals_analysis(fundamentals)
        )

        news = (
            get_news(symbol)
            if show_news
            else []
        )

        news_score, news_sentiment, news_reasons = (
            news_analysis(news)
        )

        global_score, global_label, global_emoji = (
            global_analysis(
                technical["score"],
                fundamental_score,
                news_score,
            )
        )

        # --------------------------------------------------
        # DASHBOARD
        # --------------------------------------------------

        dashboard.append({
            "Ticker": symbol,
            "Score": global_score,
            "Technique": technical["score"],
            "Fondamentaux": fundamental_score,
            "Actualités": news_score,
            "Signal": technical["signal"],
            "Sentiment": news_sentiment,
        })

        # --------------------------------------------------
        # ALERTE OPPORTUNITÉ
        # --------------------------------------------------

        if (
            global_score >= min_score
            and technical["signal"] == "ACHAT"
        ):

            st.success(
                f"🚨 {symbol} — {global_label} "
                f"— SCORE {global_score}/100"
            )

        elif (
            global_score <= 35
            and technical["signal"] == "VENTE"
        ):

            st.error(
                f"⚠️ {symbol} — RISQUE BAISSIER "
                f"— SCORE {global_score}/100"
            )

        # --------------------------------------------------
        # TITRE
        # --------------------------------------------------

        name = (
            fundamentals["name"]
            if fundamentals
            else symbol
        )

        st.markdown(
            f"## {global_emoji} {symbol} — {name}"
        )

        # --------------------------------------------------
        # SCORE GLOBAL
        # --------------------------------------------------

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "🎯 SCORE GLOBAL",
                f"{global_score}/100"
            )

        with c2:
            st.metric(
                "📈 Technique",
                f"{technical['score']}/100"
            )

        with c3:
            st.metric(
                "🏢 Fondamentaux",
                f"{fundamental_score}/100"
            )

        with c4:
            st.metric(
                "📰 Actualités",
                f"{news_score}/100"
            )

        st.progress(
            global_score / 100,
            text=(
                f"{global_emoji} {global_label} — "
                f"{score_bar(global_score)}"
            )
        )

        # --------------------------------------------------
        # SIGNAL TECHNIQUE
        # --------------------------------------------------

        if technical["signal"] == "ACHAT":
            st.success(
                f"🟢 ACHAT — "
                f"{', '.join(technical['reasons'])}"
            )

        elif technical["signal"] == "VENTE":
            st.error(
                f"🔴 VENTE — "
                f"{', '.join(technical['reasons'])}"
            )

        else:
            st.info(
                f"⚪ ATTENTE — "
                f"{', '.join(technical['reasons'])}"
            )

        # --------------------------------------------------
        # NIVEAUX
        # --------------------------------------------------

        if technical["signal"] != "ATTENTE":

            n1, n2, n3, n4, n5 = st.columns(5)

            with n1:
                st.metric(
                    "Entrée",
                    fmt_number(technical["entry"])
                )

            with n2:
                st.metric(
                    "Stop Loss",
                    fmt_number(technical["stop"])
                )

            with n3:
                st.metric(
                    "TP1",
                    fmt_number(technical["tp1"])
                )

            with n4:
                st.metric(
                    "TP2",
                    fmt_number(technical["tp2"])
                )

            with n5:
                rr = technical["rr2"]

                st.metric(
                    "R/R TP2",
                    f"1:{rr:.2f}"
                    if rr is not None
                    else "N/A"
                )

        # --------------------------------------------------
        # INDICATEURS TECHNIQUES
        # --------------------------------------------------

        with st.expander(
            "📊 Analyse technique détaillée",
            expanded=True,
        ):

            t1, t2, t3, t4 = st.columns(4)

            with t1:
                st.metric(
                    "RSI",
                    fmt_number(
                        technical["rsi"]
                    )
                )

            with t2:
                st.metric(
                    "ATR",
                    fmt_number(
                        technical["atr"]
                    )
                )

            with t3:
                st.metric(
                    "Support 20",
                    fmt_number(
                        technical["support"]
                    )
                )

            with t4:
                st.metric(
                    "Résistance 20",
                    fmt_number(
                        technical["resistance"]
                    )
                )

            st.write(
                f"**Tendance :** "
                f"{technical['trend']}"
            )

        # --------------------------------------------------
        # FONDAMENTAUX
        # --------------------------------------------------

        with st.expander(
            "🏢 Fondamentaux",
            expanded=False,
        ):

            if fundamentals:

                f1, f2, f3, f4 = st.columns(4)

                with f1:
                    st.metric(
                        "Capitalisation",
                        format_market_cap(
                            fundamentals["market_cap"]
                        )
                    )

                with f2:
                    st.metric(
                        "PER",
                        fmt_number(
                            fundamentals["pe"]
                        )
                    )

                with f3:
                    st.metric(
                        "Forward PER",
                        fmt_number(
                            fundamentals["forward_pe"]
                        )
                    )

                with f4:
                    st.metric(
                        "Dividende",
                        fmt_percent(
                            fundamentals["dividend_yield"]
                        )
                    )

                f1, f2, f3, f4 = st.columns(4)

                with f1:
                    st.metric(
                        "Marge bénéficiaire",
                        fmt_percent(
                            fundamentals["profit_margin"]
                        )
                    )

                with f2:
                    st.metric(
                        "ROE",
                        fmt_percent(
                            fundamentals["roe"]
                        )
                    )

                with f3:
                    st.metric(
                        "Croissance CA",
                        fmt_percent(
                            fundamentals["revenue_growth"]
                        )
                    )

                with f4:
                    st.metric(
                        "Croissance bénéfices",
                        fmt_percent(
                            fundamentals["earnings_growth"]
                        )
                    )

                st.write(
                    f"**Secteur :** "
                    f"{fundamentals['sector']}"
                )

                st.write(
                    f"**Industrie :** "
                    f"{fundamentals['industry']}"
                )

                st.write(
                    "**Lecture :** "
                    + (
                        " | ".join(
                            fundamental_reasons
                        )
                        if fundamental_reasons
                        else "Données insuffisantes"
                    )
                )

                target = fundamentals["target_mean"]
                price = fundamentals["price"]

                if (
                    target is not None
                    and price is not None
                    and price != 0
                ):

                    upside = (
                        (target - price)
                        / price
                        * 100
                    )

                    st.metric(
                        "Potentiel vers objectif analystes",
                        f"{upside:+.2f}%"
                    )

                recommendation = (
                    fundamentals["recommendation"]
                    or "N/A"
                )

                st.write(
                    f"**Consensus analystes :** "
                    f"{str(recommendation).upper()}"
                )

            else:

                st.info(
                    "Fondamentaux indisponibles."
                )

        # --------------------------------------------------
        # ACTUALITÉS
        # --------------------------------------------------

        if show_news:

            with st.expander(
                f"📰 Actualités — {news_sentiment}",
                expanded=False,
            ):

                if news:

                    if news_sentiment == "POSITIF":
                        st.success(
                            "🟢 Sentiment actualités positif"
                        )
                    elif news_sentiment == "NÉGATIF":
                        st.error(
                            "🔴 Sentiment actualités négatif"
                        )
                    else:
                        st.info(
                            "⚪ Sentiment actualités neutre"
                        )

                    st.caption(
                        "Analyse lexicale simple des titres : "
                        "elle ne remplace pas une analyse humaine."
                    )

                    for article in news:

                        st.markdown(
                            f"**{article['title']}**"
                        )

                        st.caption(
                            f"📰 {article['publisher']}"
                        )

                        if article["url"]:
                            st.markdown(
                                f"[Lire la source →]"
                                f"({article['url']})"
                            )

                        st.markdown("---")

                else:

                    st.info(
                        "Aucune actualité récente disponible."
                    )

        # --------------------------------------------------
        # ALERTES / INTERPRÉTATION
        # --------------------------------------------------

        with st.expander(
            "🚨 Diagnostic du scanner",
            expanded=False,
        ):

            if (
                global_score >= min_score
                and technical["signal"] == "ACHAT"
            ):

                st.success(
                    f"🚀 SETUP À SURVEILLER : "
                    f"{global_score}/100"
                )

                st.write(
                    "La combinaison technique + "
                    "fondamentaux + actualités "
                    "est favorable selon les règles "
                    "du scanner."
                )

            elif global_score >= 60:

                st.warning(
                    f"🟡 SETUP INTÉRESSANT MAIS "
                    f"À CONFIRMER : {global_score}/100"
                )

            elif global_score <= 35:

                st.error(
                    f"🔴 RISQUE ÉLEVÉ / BAISSIER : "
                    f"{global_score}/100"
                )

            else:

                st.info(
                    f"⚪ PAS DE SETUP PRIORITAIRE : "
                    f"{global_score}/100"
                )

        # --------------------------------------------------
        # TRADINGVIEW
        # --------------------------------------------------

        if show_chart:

            with st.expander(
                "📈 TradingView",
                expanded=False,
            ):

                tv_interval = (
                    "60"
                    if interval == "1h"
                    else "D"
                )

                components.html(
                    tradingview_chart(
                        symbol,
                        tv_interval
                    ),
                    height=520,
                )

        st.markdown("---")

    # ======================================================
    # TABLEAU RÉCAPITULATIF
    # ======================================================

    if dashboard:

        st.header("🏆 Classement du scanner")

        ranking = pd.DataFrame(
            dashboard
        ).sort_values(
            "Score",
            ascending=False
        )

        st.dataframe(
            ranking,
            use_container_width=True,
            hide_index=True,
        )

        top = ranking.iloc[0]

        st.success(
            f"🏆 Meilleur setup actuellement : "
            f"**{top['Ticker']} — "
            f"{int(top['Score'])}/100**"
        )

# ==========================================================
# FOOTER
# ==========================================================

st.markdown("---")

st.caption(
    "⚠️ Les données proviennent de Yahoo Finance via yfinance. "
    "Les données peuvent être retardées ou indisponibles selon "
    "l'actif. Le score est un modèle indicatif et ne constitue "
    "pas un conseil en investissement."
)
