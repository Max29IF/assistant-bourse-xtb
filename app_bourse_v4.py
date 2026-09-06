import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import math
import html
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from datetime import datetime

st.set_page_config(page_title='Trading Command Center V4', page_icon='📈', layout='wide', initial_sidebar_state='expanded')

# ==========================================================
# CONFIG / UNIVERSE
# ==========================================================
UNIVERSE = {
    'USA': 'AAPL MSFT NVDA AMZN META GOOGL GOOG AVGO AMD NFLX TSLA ORCL CRM ADBE QCOM INTC MU AMAT LRCX KLAC NOW PANW CRWD PLTR UBER ABNB COST WMT JPM BAC GS MS V MA XOM CVX COP CAT GE RTX LMT NKE MCD SBUX KO PEP TMO ISRG UNH MRK PFE ABBV LIN DE DHR BKNG LOW HD SPOT SHOP SNOW'.split(),
    'France': 'MC.PA OR.PA AIR.PA TTE.PA SAN.PA BNP.PA AI.PA SU.PA DG.PA SAF.PA DSY.PA CAP.PA ACA.PA VIE.PA EN.PA RI.PA EL.PA KER.PA STM.PA'.split(),
    'Germany': 'SAP.DE SIE.DE ALV.DE DTE.DE AIR.DE MBG.DE BMW.DE VOW3.DE BAS.DE BAYN.DE ADS.DE DHL.DE MUV2.DE IFX.DE RHM.DE DBK.DE DB1.DE'.split(),
    'Netherlands': 'ASML.AS ADYEN.AS PRX.AS ING.AS PHIA.AS HEIA.AS NN.AS'.split(),
    'Switzerland': 'NESN.SW NOVN.SW ROG.SW UBSG.SW ABBN.SW ZURN.SW'.split(),
    'UK': 'SHEL.L AZN.L HSBA.L ULVR.L BP.L GSK.L BAE.L RIO.L REL.L LLOY.L DGE.L NG.L VOD.L'.split(),
    'Spain': 'SAN.MC BBVA.MC ITX.MC IBE.MC REP.MC FER.MC'.split(),
    'Italy': 'ENEL.MI ENI.MI ISP.MI UCG.MI RACE.MI STLA.MI'.split(),
    'Nordics': 'NOVO-B.CO MAERSK-B.CO VWS.CO DSV.V DANSKE.CO EQNR.OL NHY.OL KOG.OL VOLV-B.ST ATCO-A.ST ERIC-B.ST'.split(),
}
INDEXES = {'S&P 500':'^GSPC','NASDAQ':'^IXIC','CAC 40':'^FCHI','DAX':'^GDAXI','Euro Stoxx 50':'^STOXX50E','FTSE 100':'^FTSE'}
TV_MAP = {'MC.PA':'EURONEXT:MC','OR.PA':'EURONEXT:OR','AIR.PA':'EURONEXT:AIR','TTE.PA':'EURONEXT:TTE','SAN.PA':'EURONEXT:SAN','BNP.PA':'EURONEXT:BNP','AI.PA':'EURONEXT:AI','DG.PA':'EURONEXT:DG','SIE.DE':'XETR:SIE','ALV.DE':'XETR:ALV','BMW.DE':'XETR:BMW','SAP.DE':'XETR:SAP','ASML.AS':'EURONEXT:ASML','NESN.SW':'SIX:NESN','SHEL.L':'LSE:SHEL','AZN.L':'LSE:AZN'}

# yfinance limitations: intraday history is much shorter than daily history.
TIMEFRAMES = {
    '1 minute': {'interval':'1m','period':'7d'},
    '5 minutes': {'interval':'5m','period':'30d'},
    '15 minutes': {'interval':'15m','period':'60d'},
    '30 minutes': {'interval':'30m','period':'60d'},
    '1 hour': {'interval':'1h','period':'6mo'},
    '1 day': {'interval':'1d','period':'2y'},
    '1 week': {'interval':'1wk','period':'5y'},
}

# ==========================================================
# DATA
# ==========================================================
@st.cache_data(ttl=120, show_spinner=False)
def get_history(symbol, period, interval):
    try:
        df = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False, threads=False)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).title() for c in df.columns]
        needed = ['Open','High','Low','Close','Volume']
        if not all(c in df.columns for c in needed):
            return None
        return df[needed].dropna()
    except Exception:
        return None

@st.cache_data(ttl=900, show_spinner=False)
def get_info(symbol):
    try:
        return yf.Ticker(symbol).info or {}
    except Exception:
        return {}

@st.cache_data(ttl=600, show_spinner=False)
def get_news(symbol):
    try:
        raw = yf.Ticker(symbol).news or []
        out=[]
        for n in raw[:10]:
            c=n.get('content', n)
            if not isinstance(c, dict):
                continue
            title=c.get('title','')
            provider=c.get('provider',{}) or {}
            publisher=provider.get('displayName','') if isinstance(provider,dict) else ''
            canonical=c.get('canonicalUrl',{}) or {}
            url=canonical.get('url','') if isinstance(canonical,dict) else ''
            if not url and isinstance(n,dict):
                url=n.get('link','') or n.get('url','')
            if title:
                out.append({'title':title,'publisher':publisher,'url':url})
        return out
    except Exception:
        return []

# ==========================================================
# INDICATORS / TRADE ENGINE
# ==========================================================
def indicators(df):
    x=df.copy(); close=x.Close; high=x.High; low=x.Low; vol=x.Volume
    x['SMA20']=close.rolling(20).mean(); x['SMA50']=close.rolling(50).mean(); x['SMA200']=close.rolling(200).mean()
    x['EMA12']=close.ewm(span=12,adjust=False).mean(); x['EMA26']=close.ewm(span=26,adjust=False).mean()
    x['MACD']=x.EMA12-x.EMA26; x['MACD_SIGNAL']=x.MACD.ewm(span=9,adjust=False).mean()
    d=close.diff(); gain=d.clip(lower=0).rolling(14).mean(); loss=(-d.clip(upper=0)).rolling(14).mean(); rs=gain/loss.replace(0,np.nan)
    x['RSI']=100-(100/(1+rs))
    tr=pd.concat([high-low,(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1)
    x['ATR']=tr.rolling(14).mean(); x['VOL20']=vol.rolling(20).mean(); x['ROC20']=close.pct_change(20)*100
    return x.dropna(subset=['SMA20','SMA50','ATR'])

def trade_setup(df):
    x=indicators(df)
    if x.empty: return None
    r=x.iloc[-1]; price=float(r.Close); atr=float(r.ATR)
    recent=x.tail(min(100,len(x)))
    support=float(recent.Low.quantile(.12)); resistance=float(recent.High.quantile(.88))
    support=min(support, price-0.8*atr); support=max(support, price-4*atr)
    resistance=max(resistance, price+1.5*atr)
    entry=max(support+0.15*atr, price-0.35*atr)
    if entry>price: entry=price
    stop=min(support-0.25*atr, entry-1.0*atr)
    risk=max(entry-stop, 0.01*price)
    tp2=min(resistance, entry+2.8*risk); tp1=min(resistance, entry+1.5*risk)
    upside=(tp2/entry-1)*100; rr=(tp2-entry)/risk if risk else 0
    trend=0
    if price>r.SMA20: trend+=15
    if r.SMA20>r.SMA50: trend+=15
    if not pd.isna(r.SMA200) and price>r.SMA200: trend+=10
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
    return int(np.clip(s,0,100)),reasons

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
        x=indicators(df); r=x.iloc[-1]
        bull=bool(r.Close>r.SMA20 and r.SMA20>r.SMA50)
        rows.append({'Marché':name,'Cours':float(r.Close),'SMA20':float(r.SMA20),'SMA50':float(r.SMA50),'Régime':'🟢 BULL' if bull else '🔴 RISK-OFF'})
    return pd.DataFrame(rows)

def multi_timeframe_confirmation(symbol, confirm_interval, confirm_period):
    df=get_history(symbol,confirm_period,confirm_interval)
    if df is None or len(df)<55: return None
    t=trade_setup(df)
    if not t: return None
    return {'score':t['score'],'rsi':t['rsi'],'signal':t['signal'],'trend_ok':t['price']>t['df'].iloc[-1]['SMA20'] and t['df'].iloc[-1]['SMA20']>t['df'].iloc[-1]['SMA50']}

def position_calc(capital,risk_pct,entry,stop,target):
    risk_e=capital*risk_pct/100; dist=abs(entry-stop)
    qty=math.floor(risk_e/dist) if dist>0 else 0
    exposure=qty*entry; profit=qty*abs(target-entry); rr=abs(target-entry)/dist if dist else 0
    return risk_e,dist,qty,exposure,profit,rr

# ==========================================================
# TRADINGVIEW
# ==========================================================
def tradingview_chart(symbol, interval='D'):
    tv=TV_MAP.get(symbol,symbol); wid='tv_'+''.join(c if c.isalnum() else '_' for c in symbol)
    return f'''<div class="tradingview-widget-container"><div id="{wid}"></div><script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script><script>new TradingView.widget({{"autosize":true,"symbol":"{tv}","interval":"{interval}","timezone":"Europe/Paris","theme":"dark","style":"1","locale":"fr","enable_publishing":false,"allow_symbol_change":true,"container_id":"{wid}"}});</script></div>'''

# ==========================================================
# SIDEBAR — SIMPLE / PRECISE
# ==========================================================
with st.sidebar:
    st.header('⚙️ Command Center')
    page=st.radio('Navigation',['🌍 Scanner','🔎 Analyse','🧪 Simulation','📋 Journal'],index=0)
    st.markdown('---')
    st.subheader('⏱️ Données')
    scan_tf=st.selectbox('Unité principale du scan',list(TIMEFRAMES),index=5)
    scan_cfg=TIMEFRAMES[scan_tf]
    confirm_tf=st.selectbox('Confirmation secondaire',list(TIMEFRAMES),index=4)
    confirm_cfg=TIMEFRAMES[confirm_tf]
    history_label=st.selectbox('Historique principal',['Automatique','7d','30d','60d','6mo','1y','2y','5y'],index=0)
    # Automatic history respects the chosen interval. Manual history is clipped by Yahoo limitations.
    history=scan_cfg['period'] if history_label=='Automatique' else history_label
    st.caption(f"Intervalle {scan_cfg['interval']} · historique {history}")
    st.markdown('---')
    st.subheader('🎯 Filtre risque / visibilité')
    min_upside=st.number_input('Potentiel minimum (%)',1.0,30.0,5.0,0.5)
    min_rr=st.number_input('R/R minimum',1.0,5.0,2.0,0.25)
    min_score=st.slider('Score minimum',0,100,75)
    confirm_required=st.checkbox('Confirmation multi-timeframe',True)
    only_long=st.checkbox('Uniquement configurations LONG',True)
    st.markdown('---')
    st.subheader('🌍 Univers')
    countries=st.multiselect('Marchés',list(UNIVERSE),default=['USA','France','Germany','Netherlands','UK'])
    max_candidates=st.slider('Maximum analysé',20,180,100,10)
    capital=st.number_input('Capital de référence (€)',100.0,1000000.0,10000.0,100.0)
    risk_pct=st.number_input('Risque par trade (%)',0.1,3.0,0.50,0.05)
    st.markdown('---')
    st.subheader('🔄 Automatisation')
    refresh_min=st.select_slider('Fréquence du scan (minutes)',options=[1,2,5,10,15,30,60],value=5)
    auto_refresh=st.checkbox('Scanner automatiquement',True)
    if auto_refresh:
        st_autorefresh(interval=refresh_min*60*1000,key='auto_scan_refresh')

st.title('📈 Trading Command Center — V4')
st.caption('Objectif : réduire les décisions inutiles et ne garder que les configurations lisibles, liquides et correctement rémunérées par rapport au risque.')

# ==========================================================
# GLOBAL CONTEXT
# ==========================================================
mr=market_regime()
with st.expander('🌍 Régime des marchés',expanded=False):
    if not mr.empty: st.dataframe(mr,use_container_width=True,hide_index=True)

# ==========================================================
# SCANNER — NO BUTTON: RUNS AUTOMATICALLY
# ==========================================================
def run_scanner():
    pool=[]
    for c in countries: pool.extend(UNIVERSE.get(c,[]))
    pool=sorted(set(pool))[:max_candidates]
    rows=[]; progress=st.progress(0)
    for k,sym in enumerate(pool,1):
        df=get_history(sym,history,scan_cfg['interval'])
        if df is None or len(df)<55:
            progress.progress(k/len(pool)); continue
        t=trade_setup(df)
        if not t: progress.progress(k/len(pool)); continue
        if only_long and t['signal']!='ACHAT':
            progress.progress(k/len(pool)); continue
        if t['upside']<min_upside or t['rr']<min_rr or t['score']<min_score:
            progress.progress(k/len(pool)); continue
        conf=multi_timeframe_confirmation(sym,confirm_cfg['interval'],confirm_cfg['period']) if confirm_required else None
        if confirm_required and (conf is None or not conf['trend_ok'] or conf['score']<65):
            progress.progress(k/len(pool)); continue
        fs,_=fundamental_score(get_info(sym))
        global_score=int(round(.65*t['score']+.35*fs))
        risk_e,dist,qty,exposure,profit,rr=position_calc(capital,risk_pct,t['entry'],t['stop'],t['tp2'])
        rows.append({'Ticker':sym,'Score':global_score,'Tech':t['score'],'Fond.':fs,'Prix':t['price'],'Entrée':t['entry'],'Stop':t['stop'],'TP1':t['tp1'],'TP2':t['tp2'],'Potentiel %':t['upside'],'R/R':rr,'RSI':t['rsi'],'Risque €':risk_e,'Qté':qty,'Qualité':t['quality']})
        progress.progress(k/len(pool))
    progress.empty()
    if not rows: return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(['Score','R/R','Potentiel %'],ascending=[False,False,False]).reset_index(drop=True)

if page=='🌍 Scanner':
    st.header('🌍 Scanner automatique')
    st.info(f"Scan automatique toutes les {refresh_min} min · {scan_tf} / historique {history} · confirmation {confirm_tf} · potentiel ≥ {min_upside:.1f}% · R/R ≥ {min_rr:.2f} · score ≥ {min_score}.")
    results=run_scanner()
    st.session_state['scan_results']=results
    if results.empty:
        st.warning('Aucune configuration ne respecte actuellement tous les filtres. Le scanner continuera automatiquement au prochain cycle.')
    else:
        st.success(f'🎯 {len(results)} configuration(s) lisibles détectées — mise à jour automatique.')
        st.dataframe(results,use_container_width=True,hide_index=True)
        st.subheader('🏆 Priorités')
        for _,r in results.head(5).iterrows():
            c=st.columns([1.4,1,1,1,1,1,1])
            c[0].markdown(f"### {'🟢' if r['Qualité']=='A' else '🔵'} {r['Ticker']}")
            c[1].metric('Score',f"{int(r.Score)}/100")
            c[2].metric('Potentiel',f"{r['Potentiel %']:.1f}%")
            c[3].metric('R/R',f"{r['R/R']:.2f}")
            c[4].metric('Entrée',f"{r['Entrée']:.2f}")
            c[5].metric('Stop',f"{r['Stop']:.2f}")
            c[6].metric('TP2',f"{r['TP2']:.2f}")
        st.caption('Le scanner ne cherche pas à remplir une liste : il peut volontairement retourner zéro opportunité si le marché ne présente pas assez de configurations propres.')

# ==========================================================
# INDIVIDUAL ANALYSIS
# ==========================================================
elif page=='🔎 Analyse':
    st.header('🔎 Analyse multi-timeframe')
    ticker=st.text_input('Ticker / symbole',value='NVDA').strip().upper()
    a,b,c=st.columns(3)
    with a: ana_tf=st.selectbox('Unité d’analyse',list(TIMEFRAMES),index=5)
    with b: ana_period=st.selectbox('Historique',list(['7d','30d','60d','6mo','1y','2y','5y']),index=3)
    with c: ana_confirm=st.selectbox('Confirmation',list(TIMEFRAMES),index=4)
    df=get_history(ticker,ana_period,TIMEFRAMES[ana_tf]['interval'])
    if df is None or len(df)<55:
        st.error('Données insuffisantes ou symbole inconnu.')
    else:
        t=trade_setup(df); info=get_info(ticker); fs,freasons=fundamental_score(info); news=get_news(ticker); ns=news_score(news); global_score=int(round(.55*t['score']+.25*fs+.20*ns))
        conf=multi_timeframe_confirmation(ticker,TIMEFRAMES[ana_confirm]['interval'],TIMEFRAMES[ana_confirm]['period'])
        c=st.columns(7)
        c[0].metric('Score global',f'{global_score}/100'); c[1].metric('Technique',f"{t['score']}/100"); c[2].metric('Prix',f"{t['price']:.2f}"); c[3].metric('Potentiel',f"{t['upside']:.1f}%"); c[4].metric('R/R',f"{t['rr']:.2f}"); c[5].metric('RSI',f"{t['rsi']:.1f}"); c[6].metric('Qualité',t['quality'])
        if conf:
            st.write(f"**Confirmation {ana_confirm} :** {'🟢 tendance confirmée' if conf['trend_ok'] else '🔴 tendance non confirmée'} · score {conf['score']}/100 · RSI {conf['rsi']:.1f}")
        st.subheader('🎯 Plan de trade théorique')
        p=st.columns(7)
        for col,label,val in zip(p,['Entrée','Stop','TP1','TP2','Support','Résistance','ATR'],[t['entry'],t['stop'],t['tp1'],t['tp2'],t['support'],t['resistance'],t['atr']]): col.metric(label,f'{val:.2f}')
        risk_e,dist,qty,exposure,profit,rr=position_calc(capital,risk_pct,t['entry'],t['stop'],t['tp2'])
        st.write(f"**Risque théorique :** {risk_e:.2f} € · **Quantité :** {qty} · **Capital engagé :** {exposure:.2f} € · **Gain au TP2 :** {profit:.2f} €")
        if t['upside']>=min_upside and t['rr']>=min_rr and t['score']>=min_score and (not confirm_required or (conf and conf['trend_ok'])):
            st.success('🟢 Configuration cohérente avec les filtres de prudence.')
        else:
            st.warning('🟠 Configuration à surveiller : au moins un filtre de prudence n’est pas validé.')
        with st.expander('📊 Graphique TradingView',expanded=True):
            tvint={'1m':'1','5m':'5','15m':'15','30m':'30','1h':'60','1d':'D','1wk':'W'}[TIMEFRAMES[ana_tf]['interval']]
            components.html(tradingview_chart(ticker,tvint),height=540)
        x=indicators(df).tail(250)
        st.subheader('📈 Données techniques')
        st.line_chart(x[['Close','SMA20','SMA50','SMA200']].dropna())
        left,right=st.columns(2)
        with left:
            st.subheader('🏢 Fondamentaux'); st.write(f"**Secteur :** {info.get('sector','—')} · **Capitalisation :** {info.get('marketCap','—')}"); st.write(f"**PE :** {info.get('trailingPE','—')} · **Forward PE :** {info.get('forwardPE','—')} · **Croissance CA :** {info.get('revenueGrowth','—')}"); st.write(' · '.join(freasons) if freasons else 'Pas de facteur fondamental dominant détecté.')
        with right:
            st.subheader('📰 Actualités');
            if news:
                for n in news[:5]:
                    st.markdown(f"**{html.escape(n['title'])}** — {html.escape(n['publisher'])}")
            else: st.info('Aucune actualité disponible.')

# ==========================================================
# SIMULATION
# ==========================================================
elif page=='🧪 Simulation':
    st.header('🧪 Simulation / préparation du trade')
    ticker=st.text_input('Valeur',value='NVDA').strip().upper(); direction=st.selectbox('Sens',['LONG','SHORT'])
    sim_tf=st.selectbox('Unité',list(TIMEFRAMES),index=5); sim_period=TIMEFRAMES[sim_tf]['period']
    df=get_history(ticker,sim_period,TIMEFRAMES[sim_tf]['interval'])
    if df is not None and len(df)>=55:
        t=trade_setup(df)
        entry=st.number_input('Prix d’entrée',value=float(round(t['entry'],4)),format='%.4f'); stop=st.number_input('Stop Loss',value=float(round(t['stop'],4)),format='%.4f'); target=st.number_input('Take Profit',value=float(round(t['tp2'],4)),format='%.4f')
        risk_e,dist,qty,exposure,profit,rr=position_calc(capital,risk_pct,entry,stop,target)
        c=st.columns(6); c[0].metric('Risque max',f'{risk_e:.2f} €'); c[1].metric('Distance SL',f'{dist:.2f}'); c[2].metric('Quantité',str(qty)); c[3].metric('Capital engagé',f'{exposure:.2f} €'); c[4].metric('Gain au TP',f'{profit:.2f} €'); c[5].metric('R/R',f'{rr:.2f}')
        if rr>=min_rr and (abs(target/entry-1)*100)>=min_upside: st.success('🟢 Simulation conforme aux règles de prudence.')
        else: st.error('🔴 Simulation rejetée : potentiel ou R/R insuffisant.')
        st.subheader('📋 Ticket prêt à reporter dans xStation')
        st.code(f'''MODE: SIMULATION\nTICKER: {ticker}\nSENS: {direction}\nENTREE: {entry:.4f}\nSTOP: {stop:.4f}\nTAKE PROFIT: {target:.4f}\nQUANTITE: {qty}\nRISQUE MAX: {risk_e:.2f} EUR\nR/R: {rr:.2f}\nCAPITAL: {capital:.2f} EUR''')
    else: st.error('Données insuffisantes.')

# ==========================================================
# JOURNAL
# ==========================================================
else:
    st.header('📋 Journal des setups')
    if 'trade_log' not in st.session_state: st.session_state.trade_log=[]
    with st.form('journal_form'):
        ticker=st.text_input('Ticker'); result=st.selectbox('Résultat',['WIN','LOSS','BE','EN COURS']); pnl=st.number_input('P&L (€)',-100000.0,100000.0,0.0,10.0); note=st.text_input('Note'); save=st.form_submit_button('Ajouter')
    if save and ticker:
        st.session_state.trade_log.append({'Date':datetime.now().strftime('%Y-%m-%d %H:%M'),'Ticker':ticker.upper(),'Résultat':result,'P&L €':pnl,'Note':note})
    if st.session_state.trade_log: st.dataframe(pd.DataFrame(st.session_state.trade_log),use_container_width=True,hide_index=True)
    else: st.info('Aucun trade enregistré dans cette session.')

st.markdown('---')
st.caption('⚠️ Outil d’analyse et de simulation. Les données yfinance peuvent être retardées ou incomplètes. Aucun ordre réel n’est envoyé.')
