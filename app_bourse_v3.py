import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import math
import html
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from datetime import datetime

st.set_page_config(page_title='Trading Command Center V3', page_icon='📈', layout='wide', initial_sidebar_state='expanded')

# ==========================================================
# UNIVERSE — liquid large/mid caps, US + Europe
# ==========================================================
UNIVERSE = {
    'USA': 'AAPL MSFT NVDA AMZN META GOOGL GOOG AVGO AMD NFLX TSLA ORCL CRM ADBE QCOM INTC MU AMAT LRCX KLAC NOW PANW CRWD PLTR UBER ABNB COST WMT JPM BAC GS MS V MA XOM CVX COP CAT GE RTX LMT NKE MCD SBUX KO PEP TMO ISRG UNH MRK PFE ABBV LIN DE DHR BKNG LOW HD SPOT SHOP SNOW'.split(),
    'France': 'MC.PA OR.PA AIR.PA TTE.PA SAN.PA BNP.PA AI.PA SU.PA DG.PA SAF.PA DSY.PA CAP.PA ACA.PA VIE.PA EN.PA RI.PA EL.PA KER.PA STM.PA'.split(),
    'Germany': 'SAP.DE SIE.DE ALV.DE DTE.DE AIR.DE MBG.DE BMW.DE VOW3.DE BAS.DE BAYN.DE ADS.DE DHL.DE MUV2.DE IFX.DE RHM.DE DBK.DE DB1.DE'.split(),
    'Netherlands': 'ASML.AS ADYEN.AS PRX.AS ING.AS PHIA.AS HEIA.AS NN.AS'.split(),
    'Switzerland': 'NESN.SW NOVN.SW ROG.SW UBSG.SW ABBN.SW ZURN.SW CSGN.SW'.split(),
    'UK': 'SHEL.L AZN.L HSBA.L ULVR.L BP.L GSK.L BAE.L RIO.L REL.L LLOY.L DGE.L NG.L VOD.L'.split(),
    'Spain': 'SAN.MC BBVA.MC ITX.MC IBE.MC REP.MC FER.MC'.split(),
    'Italy': 'ENEL.MI ENI.MI ISP.MI UCG.MI RACE.MI STLA.MI'.split(),
    'Nordics': 'NOVO-B.CO MAERSK-B.CO VWS.CO DSV.V DANSKE.CO EQNR.OL NHY.OL KOG.OL VOLV-B.ST ATCO-A.ST ERIC-B.ST'.split(),
}
ALL_UNIVERSE = sorted(set(x for v in UNIVERSE.values() for x in v))

INDEXES = {'S&P 500':'^GSPC','NASDAQ':'^IXIC','CAC 40':'^FCHI','DAX':'^GDAXI','Euro Stoxx 50':'^STOXX50E','FTSE 100':'^FTSE'}
TV_MAP = {'MC.PA':'EURONEXT:MC','OR.PA':'EURONEXT:OR','AIR.PA':'EURONEXT:AIR','TTE.PA':'EURONEXT:TTE','SAN.PA':'EURONEXT:SAN','BNP.PA':'EURONEXT:BNP','AI.PA':'EURONEXT:AI','DG.PA':'EURONEXT:DG','SIE.DE':'XETR:SIE','ALV.DE':'XETR:ALV','BMW.DE':'XETR:BMW','SAP.DE':'XETR:SAP','ASML.AS':'EURONEXT:ASML','NESN.SW':'SIX:NESN','SHEL.L':'LSE:SHEL','AZN.L':'LSE:AZN'}

# ==========================================================
# DATA
# ==========================================================
@st.cache_data(ttl=90, show_spinner=False)
def get_history(symbol, period='1y', interval='1d'):
    try:
        df = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False, threads=False)
        if df is None or df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.rename(columns=str.title)
        needed = ['Open','High','Low','Close','Volume']
        if not all(c in df.columns for c in needed): return None
        return df[needed].dropna()
    except Exception:
        return None

@st.cache_data(ttl=900, show_spinner=False)
def get_info(symbol):
    try:
        i = yf.Ticker(symbol).info or {}
        return i
    except Exception: return {}

@st.cache_data(ttl=600, show_spinner=False)
def get_news(symbol):
    try:
        raw = yf.Ticker(symbol).news or []
        out=[]
        for n in raw[:10]:
            c=n.get('content', n)
            title=c.get('title','') if isinstance(c,dict) else ''
            publisher=(c.get('provider',{}) or {}).get('displayName','') if isinstance(c,dict) else ''
            url=(c.get('canonicalUrl',{}) or {}).get('url','') if isinstance(c,dict) else ''
            if not url and isinstance(n,dict): url=n.get('link','') or n.get('url','')
            if title: out.append({'title':title,'publisher':publisher,'url':url})
        return out
    except Exception: return []

# ==========================================================
# TECHNICAL ENGINE
# ==========================================================
def indicators(df):
    x=df.copy()
    close=x['Close']; high=x['High']; low=x['Low']; vol=x['Volume']
    x['SMA20']=close.rolling(20).mean(); x['SMA50']=close.rolling(50).mean(); x['SMA200']=close.rolling(200).mean()
    x['EMA12']=close.ewm(span=12,adjust=False).mean(); x['EMA26']=close.ewm(span=26,adjust=False).mean()
    x['MACD']=x['EMA12']-x['EMA26']; x['MACD_SIGNAL']=x['MACD'].ewm(span=9,adjust=False).mean()
    d=close.diff(); gain=d.clip(lower=0).rolling(14).mean(); loss=(-d.clip(upper=0)).rolling(14).mean(); rs=gain/loss.replace(0,np.nan)
    x['RSI']=100-(100/(1+rs)); tr=pd.concat([high-low,(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1)
    x['ATR']=tr.rolling(14).mean(); x['VOL20']=vol.rolling(20).mean(); x['ROC20']=close.pct_change(20)*100
    return x.dropna(subset=['SMA20','SMA50','ATR'])

def trade_setup(df):
    x=indicators(df)
    if x.empty: return None
    r=x.iloc[-1]; price=float(r.Close); atr=float(r.ATR)
    recent=x.tail(80)
    support=float(recent['Low'].quantile(.12)); resistance=float(recent['High'].quantile(.88))
    support=min(support, price-0.8*atr); support=max(support, price-4*atr)
    resistance=max(resistance, price+1.5*atr)
    # Entry slightly above support, but never above current price by more than 0.5 ATR.
    entry=max(support+0.15*atr, price-0.35*atr)
    if entry>price: entry=price
    stop=min(support-0.25*atr, entry-1.0*atr)
    risk=max(entry-stop, 0.01*price)
    # Target = nearest realistic resistance OR 2R, whichever is more conservative.
    tp2=min(resistance, entry+2.8*risk)
    tp1=min(resistance, entry+1.5*risk)
    upside=(tp2/entry-1)*100
    rr=(tp2-entry)/risk if risk>0 else 0
    trend=0
    if price>r.SMA20: trend+=15
    if r.SMA20>r.SMA50: trend+=15
    if price>r.SMA200 if not pd.isna(r.SMA200) else False: trend+=10
    rsi=float(r.RSI); rsi_score=10 if 45<=rsi<=68 else (5 if 35<=rsi<45 or 68<rsi<=75 else -5)
    macd_score=15 if r.MACD>r.MACD_SIGNAL else -10
    vol_score=5 if r.Volume>r.VOL20 else 0
    mom_score=10 if r.ROC20>0 else -5
    score=int(np.clip(50+trend+rsi_score+macd_score+vol_score+mom_score,0,100))
    signal='ACHAT' if score>=70 else ('VENTE' if score<=30 else 'ATTENTE')
    quality='A' if score>=85 and upside>=5 and rr>=2 else ('B' if score>=75 and upside>=5 and rr>=2 else ('SURVEILLER' if upside>=5 else 'REJETE'))
    return {'df':x,'price':price,'entry':entry,'stop':stop,'tp1':tp1,'tp2':tp2,'upside':upside,'rr':rr,'support':support,'resistance':resistance,'score':score,'signal':signal,'quality':quality,'rsi':rsi,'atr':atr,'roc20':float(r.ROC20),'volume_ratio':float(r.Volume/r.VOL20) if r.VOL20 else 0}

def fundamental_score(i):
    if not i: return 50,[]
    s=50; reasons=[]
    pe=i.get('forwardPE') or i.get('trailingPE'); growth=i.get('revenueGrowth'); margin=i.get('profitMargins'); roe=i.get('returnOnEquity'); debt=i.get('debtToEquity')
    if pe is not None:
        if pe<20: s+=8; reasons.append('valorisation raisonnable')
        elif pe>45: s-=8; reasons.append('valorisation élevée')
    if growth is not None:
        if growth>0.10: s+=8; reasons.append('croissance >10%')
        elif growth<0: s-=7; reasons.append('croissance négative')
    if margin is not None and margin>0.15: s+=6; reasons.append('marge solide')
    if roe is not None and roe>0.15: s+=5; reasons.append('ROE solide')
    if debt is not None and debt>150: s-=6; reasons.append('endettement élevé')
    return int(np.clip(s,0,100)), reasons

def news_score(news):
    pos=['beat','raises','upgrade','growth','profit','record','strong','bullish','positive','surge','partnership','buyback']
    neg=['miss','downgrade','loss','lawsuit','weak','cut','warning','recall','fraud','bearish','negative','drop']
    score=50
    for n in news:
        t=n['title'].lower(); score += 5*sum(w in t for w in pos); score -= 5*sum(w in t for w in neg)
    return int(np.clip(score,0,100))

@st.cache_data(ttl=300, show_spinner=False)
def market_regime():
    rows=[]
    for name,sym in INDEXES.items():
        df=get_history(sym,'6mo','1d')
        if df is None or len(df)<50: continue
        x=indicators(df); r=x.iloc[-1]; bull=bool(r.Close>r.SMA20 and r.SMA20>r.SMA50)
        rows.append({'Marché':name,'Cours':float(r.Close),'SMA20':float(r.SMA20),'SMA50':float(r.SMA50),'Régime':'🟢 BULL' if bull else '🔴 RISK-OFF'})
    return pd.DataFrame(rows)

# ==========================================================
# TRADINGVIEW
# ==========================================================
def tradingview_chart(symbol, interval='D'):
    tv=TV_MAP.get(symbol,symbol); wid='tv_'+''.join(c if c.isalnum() else '_' for c in symbol)
    return f'''<div class="tradingview-widget-container"><div id="{wid}"></div><script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script><script>new TradingView.widget({{"autosize":true,"symbol":"{tv}","interval":"{interval}","timezone":"Europe/Paris","theme":"dark","style":"1","locale":"fr","enable_publishing":false,"allow_symbol_change":true,"container_id":"{wid}"}});</script></div>'''

# ==========================================================
# SIDEBAR
# ==========================================================
with st.sidebar:
    st.header('⚙️ Command Center')
    mode=st.radio('Mode',['🌍 Scanner global','🔎 Analyse individuelle','🧪 Trade / Simulation'],index=0)
    st.markdown('---')
    period=st.selectbox('Historique',['6mo','1y','2y'],index=1)
    interval=st.selectbox('Unité',['1d','1h'],index=0)
    st.markdown('---')
    st.subheader('🎯 Filtres scanner')
    min_upside=st.number_input('Potentiel minimum (%)',min_value=1.0,max_value=30.0,value=5.0,step=0.5)
    min_rr=st.number_input('R/R minimum',min_value=1.0,max_value=5.0,value=2.0,step=0.25)
    min_score=st.slider('Score minimum',0,100,75)
    max_candidates=st.slider('Nombre max de valeurs',20,180,80,10)
    countries=st.multiselect('Marchés',list(UNIVERSE),default=['USA','France','Germany','Netherlands','UK'])
    capital=st.number_input('Capital de référence (€)',100.0,1000000.0,10000.0,100.0)
    risk_pct=st.number_input('Risque par trade (%)',0.1,5.0,0.75,0.05)
    auto=st.checkbox('Actualisation automatique',False)
    if auto: st_autorefresh(interval=120000,key='refresh')

st.title('📈 Trading Command Center — V3')
st.caption('Scanner + analyse individuelle + setup + gestion du risque + simulation. Données indicatives via yfinance.')

# ==========================================================
# MARKET REGIME
# ==========================================================
with st.expander('🌍 Contexte des marchés',expanded=False):
    mr=market_regime()
    if not mr.empty: st.dataframe(mr,use_container_width=True,hide_index=True)

# ==========================================================
# SCANNER GLOBAL
# ==========================================================
if mode=='🌍 Scanner global':
    st.header('🌍 Scanner global US + Europe')
    st.info(f'Le scanner cherche uniquement les configurations avec potentiel ≥ {min_upside:.1f}% et R/R ≥ {min_rr:.2f}. Les fondamentaux et news sont calculés après le filtre technique pour limiter les appels de données.')
    pool=[]
    for c in countries: pool += UNIVERSE.get(c,[])
    pool=sorted(set(pool))[:max_candidates]
    if st.button('🚀 Lancer le scan',type='primary'):
        results=[]; progress=st.progress(0)
        for k,sym in enumerate(pool,1):
            df=get_history(sym,period,interval)
            if df is not None and len(df)>=55:
                t=trade_setup(df)
                if t and t['upside']>=min_upside and t['rr']>=min_rr and t['score']>=min_score:
                    fs,_=fundamental_score(get_info(sym)); results.append({'Ticker':sym,'Score':t['score'],'Fondamentaux':fs,'Prix':t['price'],'Entrée':t['entry'],'Stop':t['stop'],'TP1':t['tp1'],'TP2':t['tp2'],'Potentiel %':t['upside'],'R/R':t['rr'],'RSI':t['rsi'],'Qualité':t['quality']})
            progress.progress(k/len(pool))
        progress.empty()
        if results:
            ranking=pd.DataFrame(results).sort_values(['Qualité','Score','Potentiel %'],ascending=[True,False,False])
            st.success(f'🎯 {len(ranking)} configuration(s) répondent aux critères.')
            st.dataframe(ranking,use_container_width=True,hide_index=True)
            st.session_state['scan_results']=ranking
        else:
            st.warning('Aucune configuration ne respecte simultanément les filtres. Diminue le score, le R/R ou élargis les marchés.')
    elif 'scan_results' in st.session_state:
        st.dataframe(st.session_state['scan_results'],use_container_width=True,hide_index=True)

# ==========================================================
# INDIVIDUAL ANALYSIS
# ==========================================================
elif mode=='🔎 Analyse individuelle':
    st.header('🔎 Analyse complète d’une valeur')
    ticker=st.text_input('Ticker / symbole',value='NVDA').strip().upper()
    if st.button('Analyser',type='primary') or ticker:
        df=get_history(ticker,period,interval)
        if df is None or len(df)<55:
            st.error('Données insuffisantes ou ticker inconnu.')
        else:
            t=trade_setup(df); info=get_info(ticker); fs,freasons=fundamental_score(info); news=get_news(ticker); ns=news_score(news); global_score=int(round(.55*t['score']+.25*fs+.20*ns))
            c=st.columns(6)
            c[0].metric('Score global',f'{global_score}/100'); c[1].metric('Technique',f"{t['score']}/100"); c[2].metric('Prix',f"{t['price']:.2f}"); c[3].metric('Potentiel',f"{t['upside']:.1f}%"); c[4].metric('R/R',f"{t['rr']:.2f}"); c[5].metric('Qualité',t['quality'])
            st.subheader('🎯 Plan de trade théorique')
            p=st.columns(6); p[0].metric('Entrée',f"{t['entry']:.2f}"); p[1].metric('Stop',f"{t['stop']:.2f}"); p[2].metric('TP1',f"{t['tp1']:.2f}"); p[3].metric('TP2',f"{t['tp2']:.2f}"); p[4].metric('Support',f"{t['support']:.2f}"); p[5].metric('Résistance',f"{t['resistance']:.2f}")
            st.write(f"**RSI:** {t['rsi']:.1f} · **ATR:** {t['atr']:.2f} · **ROC20:** {t['roc20']:.1f}% · **Volume/20j:** {t['volume_ratio']:.2f}x")
            if t['upside']>=5 and t['rr']>=2 and t['score']>=75: st.success('🟢 Configuration compatible avec le cahier des charges du scanner.')
            else: st.warning('🟠 Configuration non retenue par les filtres stricts du scanner.')
            with st.expander('📊 Graphique TradingView',expanded=True): components.html(tradingview_chart(ticker,'60' if interval=='1h' else 'D'),height=520)
            a,b=st.columns(2)
            with a:
                st.subheader('🏢 Fondamentaux'); st.write(f"**Secteur:** {info.get('sector','—')} · **Capitalisation:** {info.get('marketCap','—')}"); st.write(f"**PE:** {info.get('trailingPE','—')} · **Forward PE:** {info.get('forwardPE','—')} · **Croissance CA:** {info.get('revenueGrowth','—')}"); st.write(' · '.join(freasons) if freasons else 'Pas de facteur fondamental dominant détecté.')
            with b:
                st.subheader('📰 Actualités');
                if news:
                    for n in news[:5]: st.markdown(f"**{html.escape(n['title'])}**  \n{html.escape(n['publisher'])}")
                else: st.info('Aucune actualité disponible.')

# ==========================================================
# SIMULATION / RISK
# ==========================================================
else:
    st.header('🧪 Trade / Simulation')
    st.info('Cette V3 ne passe aucun ordre réel. XTB a supprimé son accès API le 14 mars 2025 ; la V3 reste donc en simulation et peut préparer le ticket à reproduire dans xStation.')
    ticker=st.text_input('Valeur',value='NVDA').strip().upper(); direction=st.selectbox('Sens',['LONG','SHORT'])
    df=get_history(ticker,period,interval)
    if df is not None and len(df)>=55:
        t=trade_setup(df); price=t['price']
        entry=st.number_input('Prix d’entrée',value=float(round(t['entry'],2)),format='%.4f')
        stop=st.number_input('Stop Loss',value=float(round(t['stop'],2)),format='%.4f')
        target=st.number_input('Take Profit',value=float(round(t['tp2'],2)),format='%.4f')
        risk_e=capital*risk_pct/100; distance=abs(entry-stop); qty=math.floor(risk_e/distance) if distance>0 else 0; exposure=qty*entry; profit=qty*abs(target-entry); rr=abs(target-entry)/distance if distance else 0
        c=st.columns(5); c[0].metric('Risque max',f'{risk_e:.2f} €'); c[1].metric('Distance SL',f'{distance:.2f}'); c[2].metric('Quantité',str(qty)); c[3].metric('Capital engagé',f'{exposure:.2f} €'); c[4].metric('Gain au TP',f'{profit:.2f} €')
        if rr>=2: st.success(f'🟢 R/R {rr:.2f} — simulation conforme')
        else: st.error(f'🔴 R/R {rr:.2f} — simulation rejetée')
        st.subheader('📋 Ticket de trade')
        st.code(f'''MODE: SIMULATION\nTICKER: {ticker}\nSENS: {direction}\nENTREE: {entry:.4f}\nSTOP: {stop:.4f}\nTAKE PROFIT: {target:.4f}\nQUANTITE: {qty}\nRISQUE MAX: {risk_e:.2f} EUR\nR/R: {rr:.2f}\nCAPITAL: {capital:.2f} EUR''')
        st.warning('Avant tout passage réel : vérifier le prix XTB, le spread, la taille minimale, les frais et la disponibilité de l’instrument dans xStation.')
    else: st.error('Données insuffisantes.')

st.markdown('---')
st.caption('⚠️ Outil d’analyse et de simulation. Il ne constitue pas un conseil en investissement. Les données de marché peuvent être retardées, incomplètes ou indisponibles.')
