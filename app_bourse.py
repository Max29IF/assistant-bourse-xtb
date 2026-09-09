import base64
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
import altair as alt
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

try:
    from supabase import create_client
except Exception:
    create_client = None

st.set_page_config(page_title="VISION FUTURE — Trading & Portfolio Intelligence", page_icon="🔭", layout="wide")

APP_NAME = "VISION FUTURE"
APP_SUBTITLE = "Trading & Portfolio Intelligence"
APP_VERSION = "V26 Vision Future Identity"
APP_TAGLINE = "Build the Future of Your Capital"


# ==========================================================
# V11 VISUAL SYSTEM
# ==========================================================
st.markdown("""
<style>
:root{
  --vf-bg:#f4f7fb;
  --vf-card:#ffffff;
  --vf-card-soft:#f8fbff;
  --vf-text:#101827;
  --vf-muted:#667085;
  --vf-border:#dfe7f1;
  --vf-line:#e8eef6;
  --vf-blue:#2f6fed;
  --vf-blue-soft:#eaf2ff;
  --vf-green:#0f9f6e;
  --vf-green-soft:#e7f8f1;
  --vf-red:#d64545;
  --vf-red-soft:#fdeeee;
  --vf-amber:#d68b16;
  --vf-amber-soft:#fff4da;
  --vf-violet:#7657e6;
  --vf-violet-soft:#f0ecff;
  --vf-shadow:0 10px 30px rgba(15,23,42,.055);
}
.stApp { background:var(--vf-bg); color:var(--vf-text); }
.block-container { padding-top:1rem; padding-bottom:3rem; max-width:1540px; }
h1,h2,h3,h4 { color:var(--vf-text); letter-spacing:-.025em; }
hr { border-color:var(--vf-line); }

section[data-testid="stSidebar"]{
  background:#fbfcfe;
  border-right:1px solid var(--vf-border);
}
section[data-testid="stSidebar"] .block-container{padding-top:1rem;}
section[data-testid="stSidebar"] [data-testid="stRadio"] label{
  border-radius:11px;
  padding:.25rem .35rem;
}

div[data-testid="stMetric"]{
  background:var(--vf-card);
  border:1px solid var(--vf-border);
  border-radius:18px;
  padding:14px 16px;
  box-shadow:0 5px 18px rgba(15,23,42,.035);
}
div[data-testid="stMetricLabel"] p{
  color:var(--vf-muted);
  font-weight:650;
  font-size:.82rem;
}
div[data-testid="stMetricValue"]{
  color:var(--vf-text);
  font-weight:800;
  letter-spacing:-.035em;
}
div[data-testid="stMetricDelta"]{font-weight:700;}

div[data-testid="stDataFrame"]{
  background:#fff;
  border:1px solid var(--vf-border);
  border-radius:16px;
  overflow:hidden;
  box-shadow:0 4px 14px rgba(15,23,42,.025);
}
div[data-testid="stExpander"]{
  background:var(--vf-card);
  border:1px solid var(--vf-border);
  border-radius:18px;
  overflow:hidden;
  box-shadow:0 5px 18px rgba(15,23,42,.03);
}
button[kind="secondary"]{
  border-radius:12px!important;
  border-color:var(--vf-border)!important;
}
button[kind="primary"]{
  border-radius:12px!important;
}

.vf-hero{
  background:
    radial-gradient(circle at 92% 15%, rgba(47,111,237,.10), transparent 22%),
    linear-gradient(135deg,#ffffff 0%,#f9fbff 55%,#eef5ff 100%);
  border:1px solid var(--vf-border);
  border-radius:24px;
  padding:24px 26px;
  margin:2px 0 18px 0;
  box-shadow:var(--vf-shadow);
}
.vf-hero-title{
  font-size:1.62rem;
  font-weight:850;
  color:var(--vf-text);
  line-height:1.1;
}
.vf-hero-sub{
  color:var(--vf-muted);
  margin-top:7px;
  font-size:.96rem;
}
.vf-eyebrow{
  color:var(--vf-blue);
  text-transform:uppercase;
  letter-spacing:.12em;
  font-size:.69rem;
  font-weight:850;
  margin-bottom:6px;
}
.vf-section-title{
  font-size:1.13rem;
  font-weight:820;
  color:var(--vf-text);
  margin:8px 0 2px 0;
}
.vf-section-sub{
  color:var(--vf-muted);
  font-size:.86rem;
  margin-bottom:10px;
}
.vf-name{font-size:1.05rem;font-weight:820;color:var(--vf-text);}
.vf-isin{font-size:.82rem;color:var(--vf-muted);margin-top:2px;}
.vf-badge{
  display:inline-block;
  padding:5px 10px;
  border-radius:999px;
  font-weight:780;
  font-size:.76rem;
  margin:4px 5px 0 0;
}
.vf-blue{background:var(--vf-blue-soft);color:#205dc7;}
.vf-green{background:var(--vf-green-soft);color:#087a56;}
.vf-red{background:var(--vf-red-soft);color:#b83333;}
.vf-amber{background:var(--vf-amber-soft);color:#9a650f;}
.vf-violet{background:var(--vf-violet-soft);color:#6243c7;}
.vf-muted-badge{background:#eef2f6;color:#5d6b7a;}

.vf-command-card{
  background:var(--vf-card);
  border:1px solid var(--vf-border);
  border-radius:20px;
  padding:16px 17px;
  box-shadow:0 7px 24px rgba(15,23,42,.035);
  min-height:100%;
}
.vf-command-title{
  color:var(--vf-muted);
  font-size:.76rem;
  font-weight:760;
  text-transform:uppercase;
  letter-spacing:.05em;
}
.vf-command-value{
  color:var(--vf-text);
  font-size:1.45rem;
  font-weight:850;
  letter-spacing:-.04em;
  margin-top:5px;
}
.vf-command-note{
  color:var(--vf-muted);
  font-size:.78rem;
  margin-top:5px;
}
.vf-cardline{
  background:#fff;
  border:1px solid var(--vf-border);
  border-radius:18px;
  padding:15px 16px;
  margin-bottom:10px;
  box-shadow:0 5px 18px rgba(15,23,42,.025);
}
.vf-alert-row{
  background:#fff;
  border:1px solid var(--vf-border);
  border-radius:18px;
  padding:14px 15px;
  margin-bottom:9px;
}
.vf-alert-title{font-size:.97rem;font-weight:820;color:var(--vf-text);}
.vf-alert-meta{font-size:.78rem;color:var(--vf-muted);margin-top:2px;}
.vf-alert-analysis{font-size:.86rem;color:#475467;margin-top:7px;line-height:1.45;}
.vf-chip{
  display:inline-block;
  padding:4px 9px;
  border-radius:999px;
  font-size:.72rem;
  font-weight:800;
  white-space:nowrap;
}
.vf-chip-entry{background:var(--vf-green-soft);color:#087a56;}
.vf-chip-risk{background:var(--vf-amber-soft);color:#9a650f;}
.vf-chip-exit{background:var(--vf-red-soft);color:#b83333;}
.vf-chip-info{background:var(--vf-blue-soft);color:#205dc7;}

div[data-testid="stTabs"] button{
  font-weight:720;
}
</style>
""", unsafe_allow_html=True)

st.markdown('\n<style>\n@import url(\'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@500;600;700&display=swap\');\n\n:root{\n  --vf-ivory:#FAF8F3;\n  --vf-mineral:#E7E8EB;\n  --vf-blue:#2563EB;\n  --vf-graphite:#0F172A;\n  --vf-violet:#8B5CF6;\n  --vf-gold:#D4B36A;\n  --vf-horizon:#8CA3C7;\n  --vf-stone:#EADFCF;\n  --vf-white:#FFFFFF;\n  --vf-green:#17855F;\n  --vf-red:#B64B4B;\n}\n\nhtml,body,.stApp,[data-testid="stAppViewContainer"]{\n  background:var(--vf-ivory)!important;\n  color:var(--vf-graphite)!important;\n  font-family:\'Inter\',sans-serif!important;\n}\n\n[data-testid="stMainBlockContainer"]{\n  max-width:1500px!important;\n  padding:1.2rem 1.7rem 4rem!important;\n}\n\nh1,h2,h3,.vf-display,.vf-hero-title,.vf-editorial-title{\n  font-family:\'Playfair Display\',Georgia,serif!important;\n  color:var(--vf-graphite)!important;\n  letter-spacing:-.025em!important;\n}\n\n/* ---------------- SIDEBAR ---------------- */\nsection[data-testid="stSidebar"]{\n  background:#FBFAF7!important;\n  border-right:1px solid #E7E2D9!important;\n  box-shadow:none!important;\n}\nsection[data-testid="stSidebar"] .block-container{\n  padding-top:1rem!important;\n}\n.vf-group-title{\n  color:#8A847B!important;\n  font-size:.65rem!important;\n  letter-spacing:.13em!important;\n  text-transform:uppercase!important;\n  margin-top:1rem!important;\n}\nsection[data-testid="stSidebar"] button[kind="secondary"]{\n  background:transparent!important;\n  color:#3B4250!important;\n  border:1px solid transparent!important;\n  box-shadow:none!important;\n}\nsection[data-testid="stSidebar"] button[kind="secondary"]:hover{\n  background:#F2EEE7!important;\n}\nsection[data-testid="stSidebar"] button[kind="primary"]{\n  background:#EEF3FF!important;\n  color:#244DB8!important;\n  border:1px solid #DBE4FF!important;\n  box-shadow:none!important;\n}\n\n/* ---------------- TOPBAR ---------------- */\n.vf-topbar{\n  background:rgba(255,255,255,.88)!important;\n  border:1px solid #E8E3DA!important;\n  box-shadow:none!important;\n  border-radius:14px!important;\n  backdrop-filter:blur(12px)!important;\n}\n.vf-brand{\n  font-family:\'Playfair Display\',Georgia,serif!important;\n  letter-spacing:.15em!important;\n  font-weight:600!important;\n  font-size:1.08rem!important;\n}\n.vf-brand-sub{\n  color:#8C857B!important;\n  letter-spacing:.08em!important;\n  text-transform:uppercase!important;\n  font-size:.61rem!important;\n}\n.vf-badge{\n  box-shadow:none!important;\n  border:1px solid #E7E2D9!important;\n  background:#FBFAF7!important;\n  color:#66605A!important;\n}\n\n/* ---------------- HERO / MANIFESTO ---------------- */\n.vf-page-shell{\n  background:transparent!important;\n  border:none!important;\n  padding:0!important;\n}\n.vf-hero{\n  position:relative!important;\n  min-height:190px!important;\n  border-radius:18px!important;\n  overflow:hidden!important;\n  padding:34px 36px!important;\n  border:1px solid rgba(213,207,195,.8)!important;\n  box-shadow:none!important;\n  background:\n    linear-gradient(90deg,rgba(250,248,243,.97) 0%,rgba(250,248,243,.87) 39%,rgba(250,248,243,.18) 68%,rgba(15,23,42,.10) 100%),\n    url("data:image/jpeg;base64,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") center/cover no-repeat!important;\n}\n.vf-hero::after{\n  content:"DISCIPLINE · CONVICTION · PERFORMANCE";\n  position:absolute;\n  top:25px;\n  right:28px;\n  color:#FFFFFF;\n  text-shadow:0 1px 8px rgba(15,23,42,.38);\n  letter-spacing:.16em;\n  font-size:.63rem;\n  font-weight:700;\n  white-space:nowrap;\n}\n.vf-hero-title{\n  max-width:650px!important;\n  font-size:2.45rem!important;\n  line-height:1.02!important;\n  font-weight:600!important;\n  color:var(--vf-graphite)!important;\n}\n.vf-hero-sub{\n  max-width:580px!important;\n  color:#384152!important;\n  font-size:.95rem!important;\n  line-height:1.55!important;\n}\n.vf-eyebrow{\n  color:#65718B!important;\n  font-size:.64rem!important;\n  letter-spacing:.18em!important;\n  font-weight:700!important;\n  text-transform:uppercase!important;\n}\n.vf-premium-divider{\n  height:2px!important;\n  width:72px!important;\n  background:linear-gradient(90deg,var(--vf-blue) 0 73%,var(--vf-violet) 73% 90%,var(--vf-gold) 90% 100%)!important;\n  border:0!important;\n  opacity:1!important;\n  margin:13px 0 17px!important;\n}\n\n/* ---------------- BRAND STRIP ---------------- */\n.vf-future-strip{\n  background:#FFFDF9!important;\n  border:1px solid #E8E3DA!important;\n  border-radius:14px!important;\n  box-shadow:none!important;\n  padding:15px 17px!important;\n}\n.vf-future-strip-title{\n  color:#8F887E!important;\n  font-size:.64rem!important;\n  letter-spacing:.15em!important;\n  text-transform:uppercase!important;\n}\n.vf-future-strip-text{\n  font-family:\'Playfair Display\',Georgia,serif!important;\n  color:#1B2435!important;\n  font-size:1rem!important;\n  font-weight:500!important;\n}\n.vf-brand-line{\n  height:2px!important;\n  width:64px!important;\n  background:linear-gradient(90deg,var(--vf-blue) 0 72%,var(--vf-violet) 72% 89%,var(--vf-gold) 89% 100%)!important;\n}\n\n/* ---------------- 3 PILLARS ---------------- */\n.vf-editorial-level{\n  background:#FFFDF9!important;\n  border:1px solid #E8E3DA!important;\n  border-radius:16px!important;\n  padding:18px 20px!important;\n  box-shadow:none!important;\n}\n.vf-editorial-index{\n  background:#EEF3FF!important;\n  color:var(--vf-blue)!important;\n  border:1px solid #DCE5FF!important;\n  width:32px!important;\n  height:32px!important;\n}\n.vf-editorial-title{\n  font-size:1.2rem!important;\n  font-weight:600!important;\n}\n.vf-editorial-copy{\n  color:#76706A!important;\n  font-size:.84rem!important;\n}\n\n/* ---------------- CARDS / METRICS ---------------- */\ndiv[data-testid="stMetric"],\ndiv[data-testid="stVerticalBlockBorderWrapper"],\ndiv[data-testid="stDataFrame"],\ndiv[data-testid="stExpander"],\ndiv[data-testid="stForm"]{\n  background:#FFFDF9!important;\n  border:1px solid #E8E3DA!important;\n  box-shadow:0 2px 12px rgba(15,23,42,.025)!important;\n}\ndiv[data-testid="stMetric"]{\n  border-radius:14px!important;\n  padding:.75rem .85rem!important;\n}\ndiv[data-testid="stMetric"] label{\n  color:#7A746C!important;\n  font-weight:600!important;\n  font-size:.73rem!important;\n}\ndiv[data-testid="stMetricValue"]{\n  font-family:\'Playfair Display\',Georgia,serif!important;\n  color:var(--vf-graphite)!important;\n  font-size:1.78rem!important;\n  font-weight:600!important;\n}\ndiv[data-testid="stMetricDelta"]{\n  font-size:.76rem!important;\n}\n\n/* ---------------- SECTION TITLES ---------------- */\n.vf-section-title{\n  font-family:\'Playfair Display\',Georgia,serif!important;\n  font-size:1.18rem!important;\n  font-weight:600!important;\n  color:var(--vf-graphite)!important;\n}\n.vf-section-title::before{\n  width:2px!important;\n  height:14px!important;\n  background:var(--vf-gold)!important;\n}\n.vf-section-sub{\n  color:#817A71!important;\n  font-size:.82rem!important;\n}\n\n/* ---------------- IDENTITY / LOGOS ---------------- */\n.vf-logo-shell{\n  background:#FFFFFF!important;\n  border:1px solid #E7E2D9!important;\n  border-radius:13px!important;\n  box-shadow:none!important;\n}\n.vf-name{\n  font-family:\'Playfair Display\',Georgia,serif!important;\n  color:var(--vf-graphite)!important;\n  font-weight:600!important;\n  font-size:1rem!important;\n}\n.vf-isin{\n  color:#858079!important;\n}\n.vf-goldline{\n  width:46px!important;\n  height:2px!important;\n  background:linear-gradient(90deg,var(--vf-blue) 0 68%,var(--vf-violet) 68% 88%,var(--vf-gold) 88% 100%)!important;\n}\n\n/* ---------------- BUTTONS ---------------- */\nbutton[kind="primary"]{\n  background:var(--vf-blue)!important;\n  border:none!important;\n  border-radius:10px!important;\n  box-shadow:none!important;\n  font-weight:700!important;\n}\nbutton[kind="secondary"]{\n  background:#FFFDF9!important;\n  border:1px solid #E5DFD5!important;\n  color:#414955!important;\n  border-radius:10px!important;\n  box-shadow:none!important;\n}\nbutton[kind="secondary"]:hover{\n  background:#F7F3EC!important;\n}\n\n/* ---------------- INPUTS / TABS ---------------- */\ndiv[data-baseweb="select"]>div,input,textarea{\n  background:#FFFDF9!important;\n  border-color:#E4DED4!important;\n  border-radius:10px!important;\n  box-shadow:none!important;\n}\ndiv[data-testid="stTabs"] [data-baseweb="tab-list"]{\n  background:#FFFDF9!important;\n  border:1px solid #E6E0D7!important;\n  border-radius:12px!important;\n  padding:4px!important;\n}\ndiv[data-testid="stTabs"] button[aria-selected="true"]{\n  background:#EEF3FF!important;\n  color:#2850BB!important;\n}\n\n/* ---------------- BADGES ---------------- */\n.vf-blue,.vf-chip-info{\n  background:#EEF3FF!important;color:#3157C7!important;\n}\n.vf-violet{\n  background:#F3EEFF!important;color:#7252C8!important;\n}\n.vf-amber,.vf-chip-risk{\n  background:#F8F0E0!important;color:#8C6A2E!important;\n}\n.vf-green,.vf-chip-entry{\n  background:#ECF7F1!important;color:#167555!important;\n}\n.vf-red,.vf-chip-exit{\n  background:#FCEEEE!important;color:#B54141!important;\n}\n.vf-muted-badge{\n  background:#F0F1F3!important;color:#68707B!important;\n}\n\n/* ---------------- AGENT ---------------- */\n.vf-agent-callout{\n  background:#FFFDF9!important;\n  border:1px solid #E6DFD5!important;\n  border-left:3px solid var(--vf-blue)!important;\n  box-shadow:none!important;\n}\n.vf-agent-title{\n  color:var(--vf-blue)!important;\n}\n.vf-agent-copy{\n  color:#4B5260!important;\n}\n\n/* ---------------- TABLES / ALERTS ---------------- */\ndiv[data-testid="stDataFrame"],div[data-testid="stExpander"]{\n  border-radius:13px!important;\n}\n[data-testid="stAlert"]{\n  border-radius:11px!important;\n  box-shadow:none!important;\n}\n\n/* ---------------- SMALL LUXURY DETAILS ---------------- */\n.vf-command-card{\n  background:#FFFDF9!important;\n  border:1px solid #E7E1D8!important;\n  box-shadow:none!important;\n}\n.vf-command-title{\n  color:#8A8379!important;\n  letter-spacing:.08em!important;\n  text-transform:uppercase!important;\n  font-size:.66rem!important;\n}\n.vf-command-value{\n  font-family:\'Playfair Display\',Georgia,serif!important;\n  color:var(--vf-graphite)!important;\n}\n</style>\n', unsafe_allow_html=True)


st.markdown('\n<style>\n/* =========================================================\n   V25 — EDITORIAL CAPITAL\n   Sober, premium, investment-house aesthetic\n   ========================================================= */\n\n:root{\n  --vf-bg:#f5f6f8;\n  --vf-paper:#ffffff;\n  --vf-ink:#171a21;\n  --vf-ink-2:#303642;\n  --vf-muted:#737b89;\n  --vf-line:#e3e6eb;\n  --vf-blue:#2f5bea;\n  --vf-violet:#6655c7;\n  --vf-gold:#a98548;\n  --vf-green:#177c5e;\n  --vf-red:#b84747;\n}\n\n/* Overall composition */\n[data-testid="stAppViewContainer"]{\n  background:#f5f6f8 !important;\n}\n[data-testid="stMainBlockContainer"]{\n  max-width:1440px !important;\n  padding:1.2rem 1.7rem 4rem !important;\n}\n\n/* Sidebar — quiet investment-house navigation */\nsection[data-testid="stSidebar"]{\n  background:#fafafa !important;\n  border-right:1px solid #e7e9ed !important;\n  box-shadow:none !important;\n}\nsection[data-testid="stSidebar"] .block-container{\n  padding-top:1.15rem !important;\n}\nsection[data-testid="stSidebar"] button{\n  min-height:38px !important;\n  font-weight:650 !important;\n}\nsection[data-testid="stSidebar"] button[kind="primary"]{\n  background:#eef2ff !important;\n  color:#2448b5 !important;\n  border:1px solid #dde5ff !important;\n}\nsection[data-testid="stSidebar"] button[kind="secondary"]{\n  background:transparent !important;\n  color:#3f4652 !important;\n}\nsection[data-testid="stSidebar"] button[kind="secondary"]:hover{\n  background:#f2f3f5 !important;\n}\n\n/* Global page title hierarchy */\n.vf-page-shell{\n  margin-bottom:1rem !important;\n}\n.vf-hero{\n  background:#fff !important;\n  border:1px solid #e4e7ec !important;\n  border-radius:16px !important;\n  min-height:88px !important;\n  padding:20px 22px !important;\n}\n.vf-hero-title{\n  color:#171a21 !important;\n  font-size:1.48rem !important;\n  font-weight:820 !important;\n}\n.vf-hero-sub{\n  color:#747c89 !important;\n  font-size:.89rem !important;\n  max-width:900px !important;\n}\n.vf-premium-divider{\n  background:#e8eaee !important;\n  height:1px !important;\n}\n\n/* Editorial labels */\n.vf-eyebrow{\n  color:#7f8793 !important;\n  letter-spacing:.14em !important;\n  font-size:.65rem !important;\n  font-weight:850 !important;\n}\n.vf-section-title{\n  color:#20242c !important;\n  font-size:1.08rem !important;\n  font-weight:780 !important;\n  margin-top:14px !important;\n}\n.vf-section-title::before{\n  width:2px !important;\n  height:13px !important;\n  background:#2f5bea !important;\n  border-radius:0 !important;\n}\n.vf-section-sub{\n  color:#7b838f !important;\n  font-size:.82rem !important;\n}\n\n/* Cards — flatter and more editorial */\ndiv[data-testid="stVerticalBlockBorderWrapper"]{\n  background:#fff !important;\n  border:1px solid #e2e5ea !important;\n  border-radius:14px !important;\n  box-shadow:none !important;\n}\ndiv[data-testid="stMetric"]{\n  background:#fff !important;\n  border:1px solid #e2e5ea !important;\n  border-radius:13px !important;\n  box-shadow:none !important;\n  padding:.7rem .8rem !important;\n}\ndiv[data-testid="stMetric"] label{\n  color:#777f8c !important;\n  font-size:.75rem !important;\n  font-weight:700 !important;\n}\ndiv[data-testid="stMetricValue"]{\n  color:#171a21 !important;\n  font-size:1.65rem !important;\n  font-weight:820 !important;\n  letter-spacing:-.035em !important;\n}\ndiv[data-testid="stMetricDelta"]{\n  font-size:.78rem !important;\n}\n\n/* Editorial blocks */\n.vf-editorial-level{\n  background:#fff;\n  border:1px solid #e2e5ea;\n  border-radius:16px;\n  padding:16px 18px;\n  margin:.55rem 0 1rem;\n}\n.vf-editorial-level-head{\n  display:flex;\n  align-items:center;\n  gap:11px;\n  margin-bottom:5px;\n}\n.vf-editorial-index{\n  width:28px;\n  height:28px;\n  border-radius:50%;\n  display:flex;\n  align-items:center;\n  justify-content:center;\n  font-weight:820;\n  font-size:.78rem;\n  color:#2448b5;\n  background:#eef2ff;\n  border:1px solid #dce5ff;\n}\n.vf-editorial-title{\n  font-size:1.06rem;\n  font-weight:820;\n  color:#1d2129;\n  letter-spacing:-.02em;\n}\n.vf-editorial-copy{\n  color:#777f8b;\n  font-size:.84rem;\n  margin-left:39px;\n}\n\n/* Brand line — discrete */\n.vf-brand-line{\n  height:2px;\n  width:72px;\n  background:linear-gradient(90deg,#2f5bea 0 75%,#6655c7 75% 92%,#a98548 92% 100%);\n  border-radius:99px;\n  margin-top:8px;\n}\n\n/* Future strip toned down into a manifesto */\n.vf-future-strip{\n  background:#fff !important;\n  border:1px solid #e2e5ea !important;\n  border-radius:14px !important;\n  box-shadow:none !important;\n  padding:14px 16px !important;\n}\n.vf-future-strip-title{\n  color:#8a919d !important;\n  font-size:.68rem !important;\n  letter-spacing:.12em !important;\n}\n.vf-future-strip-text{\n  color:#2d333d !important;\n  font-size:.91rem !important;\n  font-weight:620 !important;\n}\n\n/* Identity cards */\n.vf-logo-shell{\n  border-radius:12px !important;\n  border:1px solid #e1e4e8 !important;\n  box-shadow:none !important;\n}\n.vf-name{\n  color:#171a21 !important;\n  font-weight:820 !important;\n}\n.vf-isin{\n  color:#7d8591 !important;\n}\n.vf-goldline{\n  width:42px !important;\n  height:2px !important;\n  background:linear-gradient(90deg,#2f5bea 0 70%,#6655c7 70% 88%,#a98548 88% 100%) !important;\n}\n\n/* Buttons */\nbutton[kind="primary"]{\n  background:#2f5bea !important;\n  border:none !important;\n  box-shadow:none !important;\n  border-radius:10px !important;\n}\nbutton[kind="secondary"]{\n  background:#fff !important;\n  border:1px solid #e1e4e8 !important;\n  color:#3c4350 !important;\n  box-shadow:none !important;\n  border-radius:10px !important;\n}\nbutton[kind="secondary"]:hover{\n  background:#f8f9fa !important;\n}\n\n/* Tabs */\ndiv[data-testid="stTabs"] [data-baseweb="tab-list"]{\n  background:#fff !important;\n  border:1px solid #e2e5ea !important;\n  border-radius:12px !important;\n  padding:4px !important;\n}\ndiv[data-testid="stTabs"] button[aria-selected="true"]{\n  background:#f1f4ff !important;\n  color:#2c4eb4 !important;\n}\n\n/* Tables and expanders */\ndiv[data-testid="stDataFrame"],\ndiv[data-testid="stExpander"]{\n  background:#fff !important;\n  border:1px solid #e2e5ea !important;\n  border-radius:13px !important;\n  box-shadow:none !important;\n}\n\n/* Alerts */\n[data-testid="stAlert"]{\n  border-radius:11px !important;\n  box-shadow:none !important;\n}\n\n/* Command cards */\n.vf-command-card{\n  background:#fff !important;\n  border:1px solid #e2e5ea !important;\n  border-radius:14px !important;\n  box-shadow:none !important;\n}\n.vf-command-title{\n  color:#7a828e !important;\n  font-size:.70rem !important;\n  letter-spacing:.08em !important;\n}\n.vf-command-value{\n  color:#181c24 !important;\n}\n\n/* Agent panel */\n.vf-agent-callout{\n  background:#fff !important;\n  border:1px solid #e2e5ea !important;\n  border-left:3px solid #2f5bea !important;\n  border-radius:12px !important;\n  box-shadow:none !important;\n}\n.vf-agent-title{\n  color:#2f5bea !important;\n}\n.vf-agent-copy{\n  color:#4a515d !important;\n}\n\n/* Inputs */\ndiv[data-baseweb="select"] > div,\ninput,\ntextarea{\n  background:#fff !important;\n  border-color:#e1e4e8 !important;\n  box-shadow:none !important;\n  border-radius:10px !important;\n}\n\n/* Remove decorative noise */\n[data-testid="stAppViewContainer"]::before,\n.vf-hero::after{\n  display:none !important;\n}\n</style>\n', unsafe_allow_html=True)


st.markdown('\n<style>\n/* =========================================================\n   V24 — SOBER PREMIUM\n   80% neutral / 15% blue-violet / 5% discreet gold\n   ========================================================= */\n\n:root{\n  --vf-bg:#f6f7f9;\n  --vf-panel:#ffffff;\n  --vf-panel-soft:#fafbfc;\n  --vf-text:#151922;\n  --vf-muted:#6b7280;\n  --vf-border:#e3e7ee;\n  --vf-blue:#315ff4;\n  --vf-violet:#6f56d9;\n  --vf-gold:#b38b47;\n  --vf-green:#138a63;\n  --vf-red:#c84646;\n}\n\n/* Whole app */\nhtml, body, .stApp, [data-testid="stAppViewContainer"]{\n  background:#f6f7f9 !important;\n  color:var(--vf-text) !important;\n}\n\n[data-testid="stAppViewContainer"]::before{\n  display:none !important;\n}\n\n[data-testid="stMainBlockContainer"]{\n  max-width:1480px !important;\n  padding:1.1rem 1.4rem 4rem !important;\n}\n\n/* Sidebar */\nsection[data-testid="stSidebar"]{\n  background:#fbfbfc !important;\n  border-right:1px solid var(--vf-border) !important;\n  box-shadow:none !important;\n}\nsection[data-testid="stSidebar"]::after{\n  display:none !important;\n}\nsection[data-testid="stSidebar"] button[kind="secondary"]{\n  background:transparent !important;\n  border:1px solid transparent !important;\n  box-shadow:none !important;\n  color:#2f3746 !important;\n}\nsection[data-testid="stSidebar"] button[kind="secondary"]:hover{\n  background:#f2f4f7 !important;\n  border-color:#edf0f4 !important;\n}\nsection[data-testid="stSidebar"] button[kind="primary"]{\n  background:#eef3ff !important;\n  color:#2447b8 !important;\n  border:1px solid #d9e3ff !important;\n  box-shadow:none !important;\n}\n.vf-group-title{\n  color:#8a909b !important;\n  font-size:.70rem !important;\n  letter-spacing:.07em !important;\n}\n\n/* Main surfaces */\ndiv[data-testid="stVerticalBlockBorderWrapper"],\ndiv[data-testid="stMetric"],\ndiv[data-testid="stExpander"],\ndiv[data-testid="stDataFrame"],\ndiv[data-testid="stForm"]{\n  background:#ffffff !important;\n  border:1px solid var(--vf-border) !important;\n  box-shadow:0 2px 10px rgba(25,33,48,.028) !important;\n}\ndiv[data-testid="stVerticalBlockBorderWrapper"]{\n  border-radius:16px !important;\n}\ndiv[data-testid="stMetric"]{\n  border-radius:14px !important;\n}\ndiv[data-testid="stMetric"]:hover,\ndiv[data-testid="stVerticalBlockBorderWrapper"]:hover{\n  transform:none !important;\n  border-color:#d8dee8 !important;\n  box-shadow:0 3px 12px rgba(25,33,48,.035) !important;\n}\n\n/* Typography */\nh1,h2,h3,h4{\n  color:var(--vf-text) !important;\n  letter-spacing:-.02em !important;\n}\n.vf-name{\n  color:#151922 !important;\n  font-weight:800 !important;\n}\n.vf-isin,\n.vf-resolution-note,\n.vf-section-sub,\n.vf-command-note,\n.vf-hero-sub{\n  color:var(--vf-muted) !important;\n}\n\n/* Hero/header */\n.vf-page-shell{\n  background:transparent !important;\n  border:none !important;\n  box-shadow:none !important;\n  padding:0 !important;\n  margin-bottom:8px !important;\n}\n.vf-hero{\n  background:#ffffff !important;\n  border:1px solid var(--vf-border) !important;\n  box-shadow:none !important;\n  border-radius:18px !important;\n  min-height:92px !important;\n  padding:20px 22px !important;\n}\n.vf-hero::after{\n  display:none !important;\n}\n.vf-hero-title{\n  background:none !important;\n  -webkit-text-fill-color:initial !important;\n  color:#151922 !important;\n  font-size:1.55rem !important;\n}\n.vf-premium-divider{\n  height:1px !important;\n  background:#eceff3 !important;\n  opacity:1 !important;\n  margin:10px 0 16px !important;\n}\n\n/* Future strip becomes editorial, not decorative */\n.vf-future-strip{\n  background:#fbfbfc !important;\n  border:1px solid var(--vf-border) !important;\n  box-shadow:none !important;\n  border-radius:14px !important;\n  padding:13px 15px !important;\n}\n.vf-future-strip-title{\n  color:#7b8190 !important;\n  font-size:.70rem !important;\n  letter-spacing:.08em !important;\n}\n.vf-future-strip-text{\n  color:#2d3442 !important;\n  font-size:.92rem !important;\n  font-weight:650 !important;\n}\n\n/* Section title */\n.vf-section-title{\n  color:#202633 !important;\n  font-size:1.05rem !important;\n  margin-top:12px !important;\n}\n.vf-section-title::before{\n  width:3px !important;\n  height:14px !important;\n  background:#315ff4 !important;\n}\n\n/* Accent line = mostly blue, tiny gold */\n.vf-goldline{\n  width:48px !important;\n  height:2px !important;\n  background:linear-gradient(90deg,#315ff4 0 68%,#6f56d9 68% 88%,#b38b47 88% 100%) !important;\n  opacity:.9 !important;\n}\n\n/* Badges */\n.vf-badge,\n.vf-chip{\n  box-shadow:none !important;\n  border:1px solid transparent !important;\n}\n.vf-blue,.vf-chip-info{\n  background:#eef3ff !important;\n  color:#3155c6 !important;\n}\n.vf-violet{\n  background:#f3f0ff !important;\n  color:#654bc3 !important;\n}\n.vf-amber,.vf-chip-risk{\n  background:#fbf5e8 !important;\n  color:#8d6d34 !important;\n}\n.vf-green,.vf-chip-entry{\n  background:#edf8f3 !important;\n  color:#137654 !important;\n}\n.vf-red,.vf-chip-exit{\n  background:#fceeee !important;\n  color:#b64040 !important;\n}\n.vf-muted-badge{\n  background:#f1f3f6 !important;\n  color:#667085 !important;\n}\n\n/* Buttons */\nbutton[kind="secondary"]{\n  background:#ffffff !important;\n  border:1px solid var(--vf-border) !important;\n  box-shadow:none !important;\n  border-radius:11px !important;\n}\nbutton[kind="secondary"]:hover{\n  background:#f8f9fb !important;\n  border-color:#d8dee8 !important;\n}\nbutton[kind="primary"]{\n  background:#315ff4 !important;\n  color:#fff !important;\n  border:none !important;\n  box-shadow:none !important;\n  border-radius:11px !important;\n}\n\n/* Inputs */\ndiv[data-baseweb="select"] > div,\ninput,\ntextarea{\n  background:#ffffff !important;\n  border-color:var(--vf-border) !important;\n  box-shadow:none !important;\n}\ndiv[data-baseweb="select"] > div:focus-within,\ninput:focus,\ntextarea:focus{\n  border-color:#9fb4ff !important;\n  box-shadow:0 0 0 2px rgba(49,95,244,.07) !important;\n}\n\n/* Tabs */\ndiv[data-testid="stTabs"] [data-baseweb="tab-list"]{\n  background:#ffffff !important;\n  border:1px solid var(--vf-border) !important;\n  box-shadow:none !important;\n}\ndiv[data-testid="stTabs"] button[aria-selected="true"]{\n  background:#f1f4ff !important;\n  color:#3155c6 !important;\n}\n\n/* Logo shell */\n.vf-logo-shell{\n  background:#ffffff !important;\n  border:1px solid var(--vf-border) !important;\n  box-shadow:none !important;\n}\n.vf-logo-fallback{\n  background:#f0f3f8 !important;\n  color:#46546a !important;\n}\n\n/* Agent box: sober, visible */\n.vf-agent-callout{\n  background:#ffffff !important;\n  border:1px solid var(--vf-border) !important;\n  box-shadow:none !important;\n}\n.vf-agent-title{\n  color:#3155c6 !important;\n}\n.vf-agent-copy{\n  color:#414956 !important;\n}\n\n/* Alert / status boxes */\n[data-testid="stAlert"]{\n  border-radius:12px !important;\n  box-shadow:none !important;\n}\n\n/* Charts/table containers cleaner */\ndiv[data-testid="stDataFrame"]{\n  border-radius:14px !important;\n}\n\n/* Remove extra glow from command cards */\n.vf-command-card{\n  background:#ffffff !important;\n  border:1px solid var(--vf-border) !important;\n  box-shadow:none !important;\n}\n\n/* Editorial hierarchy words */\n.vf-eyebrow{\n  color:#3155c6 !important;\n  letter-spacing:.09em !important;\n  font-size:.68rem !important;\n}\n\n/* Footer */\nhr{\n  border-color:#e6e9ee !important;\n}\n</style>\n', unsafe_allow_html=True)


st.markdown('\n<style>\n/* V21 — stronger atmosphere across the full product */\n[data-testid="stAppViewContainer"]{\n  background:\n    radial-gradient(circle at 4% 3%, rgba(31,103,255,.23), transparent 24%),\n    radial-gradient(circle at 96% 4%, rgba(112,68,255,.20), transparent 28%),\n    radial-gradient(circle at 86% 96%, rgba(190,148,73,.12), transparent 23%),\n    linear-gradient(180deg,#f7f9ff 0%,#edf3fb 50%,#f7f3ff 100%) !important;\n}\nsection[data-testid="stSidebar"]{\n  background:\n    radial-gradient(circle at 10% 2%,rgba(31,103,255,.16),transparent 28%),\n    linear-gradient(180deg,#fbfcff 0%,#f1f6ff 50%,#f8f3ff 100%) !important;\n  box-shadow:12px 0 36px rgba(34,47,84,.045);\n}\ndiv[data-testid="stVerticalBlockBorderWrapper"],\ndiv[data-testid="stMetric"],\ndiv[data-testid="stExpander"]{\n  background:\n    linear-gradient(145deg,rgba(255,255,255,.98) 0%,rgba(244,248,255,.96) 67%,rgba(249,246,255,.94) 100%) !important;\n  border:1px solid rgba(66,96,169,.17) !important;\n}\ndiv[data-testid="stMetric"]{\n  box-shadow:\n    0 9px 24px rgba(39,58,103,.055),\n    inset 0 2px 0 rgba(53,107,255,.06) !important;\n}\ndiv[data-testid="stVerticalBlockBorderWrapper"]{\n  box-shadow:\n    0 12px 30px rgba(35,50,91,.05),\n    inset 0 1px 0 rgba(255,255,255,.85) !important;\n}\n.vf-page-shell{\n  background:\n    radial-gradient(circle at 90% 10%,rgba(112,68,255,.11),transparent 30%),\n    linear-gradient(135deg,rgba(255,255,255,.82),rgba(239,245,255,.79) 56%,rgba(248,244,255,.76)) !important;\n  border:1px solid rgba(59,91,171,.16) !important;\n}\n.vf-future-strip{\n  box-shadow:0 10px 28px rgba(39,58,103,.05);\n}\n.vf-logo-shell{\n  background:#ffffff !important;\n  border:1px solid rgba(64,94,166,.16) !important;\n  box-shadow:0 7px 17px rgba(33,48,87,.065) !important;\n}\n.vf-logo-shell img{\n  width:38px !important;\n  height:38px !important;\n  object-fit:contain !important;\n}\n.vf-name{\n  color:#111827 !important;\n  font-weight:900 !important;\n  letter-spacing:-.02em;\n}\n.vf-goldline{\n  width:66px !important;\n  height:2px !important;\n  background:linear-gradient(90deg,#2868ff,#7652ff,#b8904d) !important;\n}\n.vf-agent-callout{\n  background:\n    radial-gradient(circle at 100% 0%,rgba(112,68,255,.13),transparent 30%),\n    linear-gradient(120deg,#eef4ff,#f4efff 62%,#fbf5e8);\n  border:1px solid rgba(70,95,163,.16);\n  border-radius:17px;\n  padding:12px 14px;\n  margin:.35rem 0 .8rem;\n  box-shadow:0 8px 22px rgba(35,50,91,.045);\n}\n.vf-agent-title{font-size:.78rem;font-weight:900;letter-spacing:.08em;color:#5f6775;text-transform:uppercase;}\n.vf-agent-copy{font-size:.92rem;font-weight:760;color:#202a3d;margin-top:3px;}\n</style>\n', unsafe_allow_html=True)


st.markdown('\n<style>\n/* V20 — premium finance application, not just a themed Streamlit page */\n[data-testid="stAppViewContainer"]{\n  background:\n    radial-gradient(circle at 0% 0%,rgba(38,100,255,.20),transparent 26%),\n    radial-gradient(circle at 100% 0%,rgba(119,79,255,.18),transparent 31%),\n    radial-gradient(circle at 88% 100%,rgba(188,145,72,.10),transparent 25%),\n    linear-gradient(180deg,#f8faff 0%,#eef3fb 50%,#f7f5ff 100%)!important;\n}\n[data-testid="stMainBlockContainer"]{\n  max-width:1500px!important;\n  padding:1rem 1.35rem 4rem!important;\n}\nsection[data-testid="stSidebar"]{\n  background:\n    linear-gradient(180deg,rgba(249,251,255,.99),rgba(242,247,255,.99) 52%,rgba(247,243,255,.99))!important;\n}\nsection[data-testid="stSidebar"] button[kind="primary"]{\n  background:linear-gradient(90deg,#2a68ff,#7550f5)!important;\n  color:#fff!important;\n  box-shadow:0 7px 18px rgba(69,79,206,.18)!important;\n}\nsection[data-testid="stSidebar"] button[kind="secondary"]{\n  background:rgba(255,255,255,.70)!important;\n  border-color:transparent!important;\n  box-shadow:none!important;\n  text-align:left!important;\n}\nsection[data-testid="stSidebar"] button[kind="secondary"]:hover{\n  background:linear-gradient(90deg,rgba(42,104,255,.09),rgba(117,80,245,.08))!important;\n  border-color:rgba(42,104,255,.10)!important;\n}\n.vf-hero{\n  min-height:108px;\n  display:flex;\n  flex-direction:column;\n  justify-content:center;\n}\n.vf-hero-title{font-size:1.8rem!important;}\n.vf-hero-sub{font-size:.92rem!important;max-width:850px;}\n.vf-page-shell{\n  background:linear-gradient(135deg,rgba(255,255,255,.76),rgba(242,247,255,.68),rgba(248,245,255,.66))!important;\n  box-shadow:0 13px 38px rgba(28,43,78,.045)!important;\n}\ndiv[data-testid="stVerticalBlockBorderWrapper"]{\n  backdrop-filter:blur(12px);\n}\n.vf-command-card{\n  background:\n    radial-gradient(circle at 95% 0%,rgba(42,104,255,.08),transparent 35%),\n    linear-gradient(145deg,rgba(255,255,255,.97),rgba(247,250,255,.93))!important;\n}\n.vf-name{font-size:1.02rem!important;}\n.vf-logo-shell{background:#fff!important;}\n.vf-logo-shell img{width:38px!important;height:38px!important;}\n</style>\n', unsafe_allow_html=True)


st.markdown('\n<style>\n/* V19 — full-page premium identity */\n:root{\n  --vf-electric:#2868ff;\n  --vf-electric-2:#5b7cff;\n  --vf-violet:#7652ff;\n  --vf-gold:#b8904d;\n  --vf-ink:#111827;\n  --vf-ink-soft:#344054;\n  --vf-surface:rgba(255,255,255,.93);\n  --vf-surface-blue:rgba(244,248,255,.94);\n  --vf-surface-violet:rgba(248,245,255,.94);\n  --vf-hairline:rgba(83,105,160,.15);\n}\n[data-testid="stAppViewContainer"]{\n  background:\n    radial-gradient(circle at 7% 4%, rgba(40,104,255,.16), transparent 24%),\n    radial-gradient(circle at 93% 7%, rgba(118,82,255,.14), transparent 27%),\n    radial-gradient(circle at 88% 92%, rgba(184,144,77,.09), transparent 22%),\n    linear-gradient(180deg,#f9fbff 0%,#f3f6fb 47%,#f6f7ff 100%) !important;\n  background-attachment:fixed !important;\n}\n[data-testid="stMainBlockContainer"]{\n  padding-top:.7rem !important;\n}\nsection[data-testid="stSidebar"]{\n  background:\n    radial-gradient(circle at 15% 3%,rgba(40,104,255,.12),transparent 30%),\n    linear-gradient(180deg,#ffffff 0%,#f5f8ff 54%,#faf7ff 100%) !important;\n  border-right:1px solid rgba(84,105,160,.13)!important;\n}\nsection[data-testid="stSidebar"]::after{\n  content:"";\n  display:block;\n  height:2px;\n  margin:10px 20px;\n  border-radius:99px;\n  background:linear-gradient(90deg,var(--vf-electric),var(--vf-violet),var(--vf-gold));\n  opacity:.65;\n}\ndiv[data-testid="stVerticalBlockBorderWrapper"]{\n  background:\n    linear-gradient(145deg,rgba(255,255,255,.97),rgba(247,250,255,.95) 58%,rgba(250,247,255,.92))!important;\n  border:1px solid var(--vf-hairline)!important;\n  border-radius:20px!important;\n  box-shadow:0 9px 28px rgba(28,43,76,.045)!important;\n}\ndiv[data-testid="stMetric"]{\n  background:\n    linear-gradient(145deg,rgba(255,255,255,.97),rgba(246,249,255,.94))!important;\n  border:1px solid rgba(78,104,171,.14)!important;\n  border-radius:17px!important;\n  box-shadow:0 7px 20px rgba(31,47,85,.04)!important;\n}\ndiv[data-testid="stMetric"]:hover{\n  transform:translateY(-1px);\n  border-color:rgba(40,104,255,.25)!important;\n  box-shadow:0 11px 26px rgba(44,76,154,.07)!important;\n}\ndiv[data-testid="stExpander"]{\n  background:rgba(255,255,255,.90)!important;\n  border:1px solid rgba(78,104,171,.14)!important;\n  border-radius:17px!important;\n}\ndiv[data-testid="stDataFrame"]{\n  border:1px solid rgba(78,104,171,.13)!important;\n  border-radius:17px!important;\n  box-shadow:0 7px 22px rgba(31,47,85,.035)!important;\n}\n[data-testid="stAlert"]{\n  background:linear-gradient(110deg,rgba(244,248,255,.95),rgba(249,247,255,.93))!important;\n  border:1px solid rgba(77,102,166,.14)!important;\n  border-radius:15px!important;\n}\n.vf-page-shell{\n  background:\n    linear-gradient(135deg,rgba(255,255,255,.72),rgba(245,249,255,.68) 55%,rgba(250,247,255,.65));\n  border:1px solid rgba(91,113,169,.10);\n  border-radius:24px;\n  padding:12px 14px 4px;\n  margin-bottom:10px;\n  box-shadow:0 10px 34px rgba(34,51,91,.025);\n}\n.vf-premium-divider{\n  height:2px;width:100%;\n  background:linear-gradient(90deg,transparent,var(--vf-electric),var(--vf-violet),var(--vf-gold),transparent);\n  opacity:.24;border-radius:999px;margin:10px 0 14px;\n}\n.vf-instrument-identity{\n  display:flex;align-items:center;gap:12px;\n}\n.vf-logo-shell{\n  width:48px;height:48px;min-width:48px;\n  display:flex;align-items:center;justify-content:center;\n  border-radius:15px;\n  background:linear-gradient(145deg,#fff,#f2f5fb);\n  border:1px solid rgba(76,101,164,.14);\n  box-shadow:0 7px 18px rgba(30,48,88,.05);\n  overflow:hidden;\n}\n.vf-logo-shell img{\n  width:36px;height:36px;object-fit:contain;\n}\n.vf-logo-fallback{\n  width:34px;height:34px;border-radius:10px;\n  display:flex;align-items:center;justify-content:center;\n  font-size:.72rem;font-weight:900;letter-spacing:.02em;\n  color:#3659b8;\n  background:linear-gradient(135deg,#eaf1ff,#f3edff 70%,#faf2df);\n}\n.vf-resolution-note{\n  color:#7b8493;font-size:.74rem;margin-top:2px;\n}\n.vf-card-action{\n  border-top:1px solid rgba(84,105,160,.10);\n  padding-top:8px;margin-top:9px;\n}\n.vf-future-strip{\n  background:\n    radial-gradient(circle at 88% 20%,rgba(118,82,255,.10),transparent 28%),\n    linear-gradient(120deg,rgba(239,245,255,.94),rgba(247,243,255,.92) 58%,rgba(253,248,238,.90))!important;\n}\n.vf-section-title::before{\n  background:linear-gradient(180deg,var(--vf-electric),var(--vf-violet) 65%,var(--vf-gold))!important;\n}\n</style>\n', unsafe_allow_html=True)


st.markdown('\n<style>\n/* =========================================================\n   V18 — IMMERSIVE FUTURE DA\n   Electric blue + violet + discreet gold across the full app\n   ========================================================= */\nhtml, body, [data-testid="stAppViewContainer"], .stApp{\n  background:\n    radial-gradient(circle at 8% 4%, rgba(52,112,255,.18), transparent 25%),\n    radial-gradient(circle at 90% 8%, rgba(126,86,255,.16), transparent 28%),\n    radial-gradient(circle at 88% 88%, rgba(199,162,89,.10), transparent 23%),\n    linear-gradient(180deg,#f8faff 0%,#f4f7fc 48%,#f7f7ff 100%) !important;\n  background-attachment: fixed !important;\n}\n\n[data-testid="stAppViewContainer"]::before{\n  content:"";\n  position:fixed;\n  inset:0;\n  pointer-events:none;\n  z-index:0;\n  background-image:\n    linear-gradient(rgba(74,103,164,.025) 1px, transparent 1px),\n    linear-gradient(90deg, rgba(74,103,164,.025) 1px, transparent 1px);\n  background-size:34px 34px;\n  mask-image:linear-gradient(to bottom,rgba(0,0,0,.55),transparent 78%);\n}\n\n[data-testid="stMain"]{\n  position:relative;\n  z-index:1;\n}\n\n.block-container{\n  max-width:1540px !important;\n  padding-top:1rem !important;\n  padding-bottom:4rem !important;\n}\n\n/* Sidebar as part of the same visual universe */\nsection[data-testid="stSidebar"]{\n  background:\n    radial-gradient(circle at 0% 0%, rgba(63,124,255,.12), transparent 32%),\n    linear-gradient(180deg,rgba(255,255,255,.97) 0%,rgba(245,248,255,.98) 55%,rgba(248,245,255,.98) 100%) !important;\n  border-right:1px solid rgba(77,104,171,.14) !important;\n  box-shadow:10px 0 35px rgba(31,45,78,.025);\n}\n\n/* Global containers / cards */\ndiv[data-testid="stMetric"],\ndiv[data-testid="stExpander"],\ndiv[data-testid="stDataFrame"],\ndiv[data-testid="stForm"],\ndiv[data-testid="stVerticalBlockBorderWrapper"]{\n  background:linear-gradient(145deg,rgba(255,255,255,.96),rgba(249,251,255,.94)) !important;\n  border-color:rgba(97,119,175,.16) !important;\n  box-shadow:\n    0 8px 24px rgba(35,49,88,.045),\n    inset 0 1px 0 rgba(255,255,255,.75);\n}\n\n/* Cards get subtle future glow */\ndiv[data-testid="stMetric"]:hover,\ndiv[data-testid="stVerticalBlockBorderWrapper"]:hover{\n  border-color:rgba(63,124,255,.24) !important;\n  box-shadow:\n    0 10px 26px rgba(53,84,160,.07),\n    0 0 0 1px rgba(124,92,255,.035);\n  transition:.18s ease;\n}\n\n/* Inputs / select / text fields */\ndiv[data-baseweb="select"] > div,\ninput,\ntextarea{\n  background:rgba(255,255,255,.90) !important;\n  border-color:rgba(88,112,172,.18) !important;\n  border-radius:14px !important;\n}\ndiv[data-baseweb="select"] > div:focus-within,\ninput:focus,\ntextarea:focus{\n  border-color:rgba(63,124,255,.45) !important;\n  box-shadow:0 0 0 3px rgba(63,124,255,.08) !important;\n}\n\n/* Buttons */\nbutton[kind="secondary"]{\n  background:linear-gradient(180deg,#ffffff,#f7f9fd) !important;\n  border:1px solid rgba(89,113,171,.18) !important;\n  border-radius:13px !important;\n  box-shadow:0 4px 12px rgba(37,54,95,.035);\n}\nbutton[kind="secondary"]:hover{\n  border-color:rgba(63,124,255,.34) !important;\n  background:linear-gradient(90deg,rgba(238,244,255,.98),rgba(245,241,255,.98)) !important;\n}\nbutton[kind="primary"]{\n  background:linear-gradient(90deg,#3476ff,#7354f4) !important;\n  border:0 !important;\n  color:white !important;\n  border-radius:13px !important;\n  box-shadow:0 8px 20px rgba(76,84,214,.18);\n}\n\n/* Tabs */\ndiv[data-testid="stTabs"] [data-baseweb="tab-list"]{\n  gap:6px;\n  padding:5px;\n  border:1px solid rgba(93,116,171,.12);\n  border-radius:15px;\n  background:rgba(255,255,255,.60);\n  backdrop-filter:blur(8px);\n}\ndiv[data-testid="stTabs"] button[role="tab"]{\n  border-radius:11px !important;\n  padding:.45rem .75rem !important;\n}\ndiv[data-testid="stTabs"] button[aria-selected="true"]{\n  background:linear-gradient(90deg,rgba(63,124,255,.12),rgba(124,92,255,.12)) !important;\n}\n\n/* Tables */\ndiv[data-testid="stDataFrame"]{\n  overflow:hidden;\n  border-radius:17px !important;\n}\n\n/* Alerts */\ndiv[data-testid="stAlert"]{\n  border-radius:15px !important;\n  border:1px solid rgba(95,118,174,.14) !important;\n  box-shadow:0 6px 18px rgba(35,49,88,.035);\n}\n\n/* Hero / headers */\n.vf-hero{\n  position:relative;\n  overflow:hidden;\n  background:\n    radial-gradient(circle at 85% 18%, rgba(124,92,255,.13), transparent 28%),\n    radial-gradient(circle at 15% 15%, rgba(63,124,255,.13), transparent 30%),\n    linear-gradient(135deg,rgba(255,255,255,.98),rgba(241,246,255,.98) 52%,rgba(248,244,255,.98) 78%,rgba(253,248,237,.96)) !important;\n  border:1px solid rgba(88,112,172,.16) !important;\n}\n.vf-hero::after{\n  content:"";\n  position:absolute;\n  width:220px;height:220px;\n  right:-90px;top:-120px;\n  border-radius:50%;\n  background:radial-gradient(circle,rgba(199,162,89,.12),transparent 68%);\n}\n\n.vf-section-title{\n  letter-spacing:-.02em;\n}\n.vf-section-title::before{\n  content:"";\n  display:inline-block;\n  width:4px;height:16px;\n  border-radius:999px;\n  margin-right:8px;\n  vertical-align:-2px;\n  background:linear-gradient(180deg,#3476ff,#7c5cff 68%,#c7a259);\n}\n\n/* Full-width section ambiance */\n.vf-future-strip{\n  position:relative;\n  overflow:hidden;\n  background:\n    linear-gradient(120deg,rgba(238,244,255,.94),rgba(245,241,255,.92) 55%,rgba(252,247,236,.90));\n  border:1px solid rgba(95,118,174,.15);\n  border-radius:20px;\n  padding:16px 18px;\n  margin:6px 0 16px;\n  box-shadow:0 8px 24px rgba(35,49,88,.04);\n}\n.vf-future-strip-title{\n  font-size:.78rem;\n  text-transform:uppercase;\n  letter-spacing:.08em;\n  color:#6a7280;\n  font-weight:900;\n}\n.vf-future-strip-text{\n  margin-top:4px;\n  font-size:1rem;\n  font-weight:760;\n  color:#192235;\n}\n\n/* Instrument identity */\n.vf-instrument-identity{\n  display:flex;\n  align-items:center;\n  gap:12px;\n}\n.vf-logo-shell{\n  width:46px;height:46px;\n  min-width:46px;\n  border-radius:14px;\n  display:flex;\n  align-items:center;\n  justify-content:center;\n  background:linear-gradient(145deg,#fff,#f2f5fb);\n  border:1px solid rgba(91,114,171,.15);\n  box-shadow:0 5px 14px rgba(34,49,87,.05);\n  overflow:hidden;\n}\n.vf-logo-shell img{\n  width:32px;height:32px;object-fit:contain;border-radius:7px;\n}\n.vf-logo-fallback{\n  width:32px;height:32px;border-radius:9px;\n  display:flex;align-items:center;justify-content:center;\n  font-size:.70rem;font-weight:900;color:#355ab8;\n  background:linear-gradient(135deg,#eaf1ff,#f2edff);\n}\n\n/* Decorative gold micro accents */\n.vf-goldline{\n  height:2px;\n  width:56px;\n  margin:7px 0 0;\n  border-radius:999px;\n  background:linear-gradient(90deg,#3476ff,#7c5cff,#c7a259);\n}\n</style>\n', unsafe_allow_html=True)


st.markdown('\n<style>\nsection[data-testid="stSidebar"] div[data-baseweb="select"] > div{\n  border-radius:14px;\n  border-color:rgba(63,124,255,.22);\n  background:linear-gradient(90deg,rgba(238,244,255,.95),rgba(245,241,255,.95));\n}\nsection[data-testid="stSidebar"] [data-testid="stRadio"] label{\n  padding:.45rem .5rem;\n  border-radius:12px;\n  transition:background .15s ease,border-color .15s ease;\n}\nsection[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{\n  background:linear-gradient(90deg,rgba(63,124,255,.08),rgba(124,92,255,.08));\n}\n</style>\n', unsafe_allow_html=True)


st.markdown('\n<style>\n:root{\n  --vf-blue:#3f7cff;\n  --vf-blue-soft:#eef4ff;\n  --vf-violet:#7c5cff;\n  --vf-violet-soft:#f3efff;\n  --vf-gold:#c6a15b;\n  --vf-gold-soft:#fcf6e9;\n}\n.stApp{\n  background:\n    radial-gradient(circle at 0% 0%, rgba(63,124,255,.12), transparent 28%),\n    radial-gradient(circle at 100% 0%, rgba(124,92,255,.11), transparent 32%),\n    radial-gradient(circle at 100% 100%, rgba(198,161,91,.08), transparent 24%),\n    linear-gradient(180deg,#f7f9fd 0%,#f4f7fb 42%,#f6f9ff 100%);\n}\nsection[data-testid="stSidebar"]{\n  background:\n    linear-gradient(180deg, rgba(255,255,255,.94) 0%, rgba(247,250,255,.98) 40%, rgba(246,246,255,.98) 100%);\n  border-right:1px solid rgba(111,137,190,.12);\n}\n.vf-topbar{\n  display:flex;align-items:center;justify-content:space-between;gap:18px;\n  background:\n    linear-gradient(135deg, rgba(255,255,255,.96) 0%, rgba(238,244,255,.96) 38%, rgba(243,239,255,.96) 72%, rgba(252,246,233,.92) 100%);\n  border:1px solid rgba(111,137,190,.18);\n  border-radius:22px;\n  padding:18px 20px;\n  margin:0 0 16px 0;\n  box-shadow:0 10px 30px rgba(35,47,84,.06);\n}\n.vf-brand{font-weight:950;letter-spacing:-.04em;font-size:1.22rem;color:#111827;}\n.vf-brand-sub{color:#4b5565;font-size:.83rem;font-weight:650;margin-top:4px;}\n.vf-topbar-tag{color:#546071;font-size:.86rem;margin-top:7px;}\n.vf-topbar-right{display:flex;gap:8px;align-items:center;flex-wrap:wrap;justify-content:flex-end;}\n.vf-hero{\n  background:\n    linear-gradient(135deg, rgba(255,255,255,.98) 0%, rgba(239,245,255,.98) 44%, rgba(244,240,255,.98) 78%, rgba(252,246,233,.96) 100%);\n  border:1px solid rgba(111,137,190,.18);\n  box-shadow:0 12px 30px rgba(35,47,84,.05);\n}\n.vf-hero-title{\n  background:linear-gradient(90deg, #1f2937 0%, #245dff 44%, #6d47ff 80%, #987545 100%);\n  -webkit-background-clip:text;-webkit-text-fill-color:transparent;\n}\n.vf-group-title{\n  margin:.55rem 0 .2rem 0;\n  font-size:.74rem;\n  font-weight:900;\n  letter-spacing:.08em;\n  color:#6b7280;\n  text-transform:uppercase;\n}\n.vf-side-note{\n  color:#667085;\n  font-size:.75rem;\n}\ndiv[data-testid="stMetric"]{\n  background:rgba(255,255,255,.92);\n  border:1px solid rgba(111,137,190,.16);\n  border-radius:16px;\n  padding:.55rem .65rem;\n}\ndiv[data-testid="stMetric"] label{\n  font-weight:700;\n}\n</style>\n', unsafe_allow_html=True)


st.markdown('\n<style>\n.vf-terminal-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:10px 0 16px;}\n.vf-terminal-box{\n  background:#fff;border:1px solid var(--vf-border);border-radius:18px;\n  padding:14px 15px;box-shadow:0 5px 18px rgba(15,23,42,.03);\n}\n.vf-terminal-label{font-size:.72rem;color:var(--vf-muted);font-weight:800;text-transform:uppercase;letter-spacing:.06em;}\n.vf-terminal-value{font-size:1.2rem;font-weight:900;color:var(--vf-text);margin-top:4px;}\n.vf-terminal-note{font-size:.75rem;color:var(--vf-muted);margin-top:3px;}\n.vf-panel-title{font-size:1rem;font-weight:850;color:var(--vf-text);margin-bottom:3px;}\n.vf-panel-sub{font-size:.78rem;color:var(--vf-muted);}\n.vf-watch-row{\n  background:#fff;border:1px solid var(--vf-border);border-radius:16px;\n  padding:12px 14px;margin-bottom:8px;\n}\n</style>\n', unsafe_allow_html=True)


st.markdown('\n<style>\nsection[data-testid="stSidebar"]{\n  background:linear-gradient(180deg,#fbfcfe 0%,#f7f9fc 100%);\n}\nsection[data-testid="stSidebar"] [data-testid="stRadio"] > div{gap:.2rem;}\nsection[data-testid="stSidebar"] [data-testid="stRadio"] label{\n  padding:.46rem .55rem;border:1px solid transparent;border-radius:12px;\n}\nsection[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{\n  background:#eef4ff;border-color:#dce8fb;\n}\n.vf-topbar{\n  display:flex;align-items:center;justify-content:space-between;gap:16px;\n  background:#fff;border:1px solid var(--vf-border);border-radius:18px;\n  padding:12px 16px;margin-bottom:14px;box-shadow:0 5px 18px rgba(15,23,42,.025);\n}\n.vf-brand{font-weight:900;letter-spacing:-.035em;font-size:1.1rem;}\n.vf-brand-sub{color:var(--vf-muted);font-size:.76rem;}\n</style>\n', unsafe_allow_html=True)



def vf_page_header(title: str, subtitle: str = ""):
    sub = f'<div class="vf-hero-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        '<div class="vf-page-shell">'
        f'<div class="vf-hero"><div class="vf-hero-title">{title}</div>{sub}</div>'
        '<div class="vf-premium-divider"></div>'
        '</div>',
        unsafe_allow_html=True
    )


def vf_currency(v):
    try:
        return f"{float(v):,.2f} €"
    except Exception:
        return "—"


def vf_pie(df: pd.DataFrame, category: str, value: str, title: str):
    if df is None or df.empty or category not in df or value not in df:
        return
    d = df[[category, value]].copy()
    d[value] = pd.to_numeric(d[value], errors="coerce")
    d = d.dropna().query(f"`{value}` > 0")
    if d.empty:
        return
    chart = (
        alt.Chart(d)
        .mark_arc(innerRadius=55, outerRadius=105)
        .encode(
            theta=alt.Theta(f"{value}:Q"),
            color=alt.Color(f"{category}:N", legend=alt.Legend(title=None, orient="bottom")),
            tooltip=[alt.Tooltip(f"{category}:N"), alt.Tooltip(f"{value}:Q", format=",.2f")]
        )
        .properties(title=title, height=330)
    )
    st.altair_chart(chart, use_container_width=True)


def vf_bar(df: pd.DataFrame, category: str, value: str, title: str, horizontal=True):
    if df is None or df.empty or category not in df or value not in df:
        return
    d = df[[category, value]].copy()
    d[value] = pd.to_numeric(d[value], errors="coerce")
    d = d.dropna()
    if d.empty:
        return
    if horizontal:
        enc = dict(
            y=alt.Y(f"{category}:N", sort="-x", title=None),
            x=alt.X(f"{value}:Q", title=None),
        )
    else:
        enc = dict(
            x=alt.X(f"{category}:N", sort="-y", title=None),
            y=alt.Y(f"{value}:Q", title=None),
        )
    chart = alt.Chart(d).mark_bar(cornerRadiusEnd=5).encode(
        **enc,
        tooltip=[alt.Tooltip(f"{category}:N"), alt.Tooltip(f"{value}:Q", format=",.2f")]
    ).properties(title=title, height=max(260, min(520, 34*len(d))))
    st.altair_chart(chart, use_container_width=True)


def vf_signed_bar(df: pd.DataFrame, category: str, value: str, title: str):
    if df is None or df.empty or category not in df or value not in df:
        return
    d = df[[category, value]].copy()
    d[value] = pd.to_numeric(d[value], errors="coerce")
    d = d.dropna()
    if d.empty:
        return
    chart = alt.Chart(d).mark_bar(cornerRadiusEnd=4).encode(
        y=alt.Y(f"{category}:N", sort="-x", title=None),
        x=alt.X(f"{value}:Q", title=None),
        color=alt.condition(f"datum['{value}'] >= 0", alt.value("#059669"), alt.value("#dc2626")),
        tooltip=[alt.Tooltip(f"{category}:N"), alt.Tooltip(f"{value}:Q", format="+,.2f")]
    ).properties(title=title, height=max(260, min(520, 34*len(d))))
    st.altair_chart(chart, use_container_width=True)


def vf_line(df: pd.DataFrame, date_col: str, series_cols: list[str], title: str):
    if df is None or df.empty or date_col not in df:
        return
    cols = [c for c in series_cols if c in df.columns]
    if not cols:
        return
    d = df[[date_col] + cols].copy()
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    for c in cols:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=[date_col])
    long = d.melt(id_vars=[date_col], value_vars=cols, var_name="Série", value_name="Valeur").dropna()
    if long.empty:
        return
    chart = alt.Chart(long).mark_line(point=True).encode(
        x=alt.X(f"{date_col}:T", title=None),
        y=alt.Y("Valeur:Q", title=None),
        color=alt.Color("Série:N", legend=alt.Legend(title=None, orient="bottom")),
        tooltip=[alt.Tooltip(f"{date_col}:T"), "Série:N", alt.Tooltip("Valeur:Q", format=",.2f")]
    ).properties(title=title, height=330)
    st.altair_chart(chart, use_container_width=True)

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
             .select("ticker,isin,name,broker,quantity,pru,currency,purchase_date,last_price_imported,market_value_imported,instrument_key,source,source_import_hash")
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
            "Source": r.get("source") or "",
            "Instrument": r.get("instrument_key") or r.get("isin") or r.get("ticker") or r.get("name") or "",
        } for r in rows])
        if not out.empty:
            out["Date achat"] = pd.to_datetime(out["Date achat"], errors="coerce").dt.date
        return out
    except Exception as exc:
        st.error(f"Impossible de charger les positions Supabase : {exc}")
        return pd.DataFrame(columns=cols)


def _clean_text(value, upper: bool = False):
    """Return a clean optional string; pandas NaN/NA/None never become literal NAN."""
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    s = str(value).strip()
    if s.upper() in {"", "NAN", "NONE", "NULL", "<NA>", "NAT"}:
        return ""
    return s.upper() if upper else s


def save_positions(account: str, broker: str, df: pd.DataFrame, source: str = "document_import", source_import_hash: str | None = None):
    if SUPABASE is None:
        raise RuntimeError("Supabase n'est pas configuré.")

    SUPABASE.table("portfolio_positions").delete().eq("account", account).eq("broker", broker).execute()

    rows_by_key = {}
    for _, r in df.iterrows():
        ticker = _clean_text(r.get("ticker"), upper=True)
        isin = _clean_text(r.get("isin"), upper=True)
        name = _clean_text(r.get("name"))
        instrument_key = _clean_text(r.get("instrument_key"), upper=True) or isin or ticker or norm_token(name)
        if not instrument_key:
            continue

        purchase_date = r.get("purchase_date")
        if pd.notna(purchase_date):
            purchase_date = pd.Timestamp(purchase_date).date().isoformat()
        else:
            purchase_date = None

        qty = pd.to_numeric(r.get("quantity"), errors="coerce")
        qty = float(qty) if pd.notna(qty) else 0.0
        avg = pd.to_numeric(r.get("average_cost"), errors="coerce")
        avg = float(avg) if pd.notna(avg) else None
        mkt_price = pd.to_numeric(r.get("market_price"), errors="coerce")
        mkt_price = float(mkt_price) if pd.notna(mkt_price) else None
        mkt_value = pd.to_numeric(r.get("market_value"), errors="coerce")
        mkt_value = float(mkt_value) if pd.notna(mkt_value) else None

        payload = {
            "account": account,
            "broker": broker,
            "instrument_key": instrument_key,
            "ticker": ticker or None,
            "isin": isin or None,
            "name": name or None,
            "quantity": qty,
            "pru": avg,
            "currency": _clean_text(r.get("currency"), upper=True) or None,
            "last_price_imported": mkt_price,
            "market_value_imported": mkt_value,
            "purchase_date": purchase_date,
            "source": source,
            "source_import_hash": source_import_hash,
            "updated_at": datetime.utcnow().isoformat(),
        }

        if instrument_key in rows_by_key:
            old = rows_by_key[instrument_key]
            q_old = float(old.get("quantity") or 0)
            total_q = q_old + qty
            c_old = (old.get("pru") or 0) * q_old
            c_new = (avg or 0) * qty
            old["quantity"] = total_q
            old["pru"] = ((c_old + c_new) / total_q) if total_q else None
            if mkt_price is not None:
                old["last_price_imported"] = mkt_price
            if mkt_value is not None:
                old["market_value_imported"] = (old.get("market_value_imported") or 0) + mkt_value
            old["ticker"] = old.get("ticker") or payload["ticker"]
            old["isin"] = old.get("isin") or payload["isin"]
            old["name"] = old.get("name") or payload["name"]
        else:
            rows_by_key[instrument_key] = payload

    rows = list(rows_by_key.values())
    if rows:
        # Le snapshot compte+courtier a déjà été supprimé au début de save_positions.
        # INSERT évite de dépendre d'une contrainte UNIQUE/EXCLUSION PostgreSQL pour ON CONFLICT.
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
    isin = _clean_text(row.get("isin"), upper=True)
    symbol = _clean_text(row.get("symbol"), upper=True)
    name = _clean_text(row.get("name"))
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
            "ticker": _clean_text(r.get("symbol"), upper=True),
            "isin": _clean_text(r.get("isin"), upper=True),
            "name": _clean_text(r.get("name")),
            "currency": _clean_text(r.get("currency"), upper=True),
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
    """
    Supprime un import et, si demandé, les données qu'il a générées.
    V8.3 ajoute une réconciliation finale : si plus aucun import ne reste
    pour le couple compte + courtier, aucun snapshot/ledger orphelin ne subsiste.
    """
    if SUPABASE is None:
        raise RuntimeError("Supabase n'est pas configuré.")

    import_id = import_row.get("id")
    file_hash = _clean_text(import_row.get("file_hash"))
    account = _clean_text(import_row.get("account"))
    broker = _clean_text(import_row.get("broker"))
    doc_type = _clean_text(import_row.get("document_type"), upper=True)

    if not account:
        raise RuntimeError("Compte introuvable pour cet import.")

    if delete_generated_data:
        if doc_type == "POSITIONS":
            # V8+ : suppression ciblée par empreinte de fichier.
            linked_rows = []
            if file_hash:
                linked = (
                    SUPABASE.table("portfolio_positions")
                    .select("id")
                    .eq("account", account)
                    .eq("broker", broker)
                    .eq("source_import_hash", file_hash)
                    .execute()
                )
                linked_rows = _sb_data(linked)

            if linked_rows:
                (
                    SUPABASE.table("portfolio_positions")
                    .delete()
                    .eq("account", account)
                    .eq("broker", broker)
                    .eq("source_import_hash", file_hash)
                    .execute()
                )
            else:
                # Import legacy sans traçabilité : le snapshot courtier est indivisible.
                (
                    SUPABASE.table("portfolio_positions")
                    .delete()
                    .eq("account", account)
                    .eq("broker", broker)
                    .execute()
                )

        elif doc_type == "TRANSACTIONS":
            linked_rows = []
            if file_hash:
                linked = (
                    SUPABASE.table("transactions")
                    .select("id")
                    .eq("account", account)
                    .eq("broker", broker)
                    .eq("source_import_hash", file_hash)
                    .execute()
                )
                linked_rows = _sb_data(linked)

            if linked_rows:
                (
                    SUPABASE.table("transactions")
                    .delete()
                    .eq("account", account)
                    .eq("broker", broker)
                    .eq("source_import_hash", file_hash)
                    .execute()
                )
            else:
                # Import legacy : pas de lien fichier -> transaction fiable.
                (
                    SUPABASE.table("transactions")
                    .delete()
                    .eq("account", account)
                    .eq("broker", broker)
                    .execute()
                )

            # Reconstruit le snapshot à partir de ce qui reste.
            try:
                remaining_tx = (
                    SUPABASE.table("transactions")
                    .select("id")
                    .eq("account", account)
                    .eq("broker", broker)
                    .limit(1)
                    .execute()
                )
                if _sb_data(remaining_tx):
                    rebuild_positions_from_transactions(account, broker)
                else:
                    (
                        SUPABASE.table("portfolio_positions")
                        .delete()
                        .eq("account", account)
                        .eq("broker", broker)
                        .execute()
                    )
            except Exception:
                # En cas de doute, on évite de conserver un snapshot transactionnel orphelin.
                (
                    SUPABASE.table("portfolio_positions")
                    .delete()
                    .eq("account", account)
                    .eq("broker", broker)
                    .eq("source", "transaction_rebuild")
                    .execute()
                )

    # Supprime ensuite la ligne d'historique.
    if import_id is not None:
        SUPABASE.table("imports").delete().eq("id", import_id).execute()
    elif file_hash:
        (
            SUPABASE.table("imports")
            .delete()
            .eq("file_hash", file_hash)
            .eq("account", account)
            .execute()
        )

    # Réconciliation finale V8.3 :
    # s'il ne reste AUCUN import pour compte + courtier, on supprime les données orphelines.
    if delete_generated_data and broker:
        remaining_imports = (
            SUPABASE.table("imports")
            .select("id")
            .eq("account", account)
            .eq("broker", broker)
            .limit(1)
            .execute()
        )
        if not _sb_data(remaining_imports):
            (
                SUPABASE.table("portfolio_positions")
                .delete()
                .eq("account", account)
                .eq("broker", broker)
                .execute()
            )
            (
                SUPABASE.table("transactions")
                .delete()
                .eq("account", account)
                .eq("broker", broker)
                .execute()
            )

    st.cache_data.clear()


def reconcile_orphan_portfolio_data():
    """
    Réconciliation automatique et silencieuse :
    si un couple compte + courtier n'a plus aucun import, les positions/transactions
    héritées de ces imports sont supprimées automatiquement.
    """
    if SUPABASE is None:
        raise RuntimeError("Supabase n'est pas configuré.")

    imports_df = load_imports()
    valid_pairs = set()
    if not imports_df.empty:
        for _, r in imports_df.iterrows():
            a = _clean_text(r.get("account"))
            b = _clean_text(r.get("broker"))
            if a and b:
                valid_pairs.add((a, b))

    cleaned = 0
    positions = pd.DataFrame(_sb_data(
        SUPABASE.table("portfolio_positions")
        .select("account,broker")
        .execute()
    ))
    transactions = pd.DataFrame(_sb_data(
        SUPABASE.table("transactions")
        .select("account,broker")
        .execute()
    ))

    pairs = set()
    for df in (positions, transactions):
        if not df.empty:
            for _, r in df.iterrows():
                a = _clean_text(r.get("account"))
                b = _clean_text(r.get("broker"))
                if a and b:
                    pairs.add((a, b))

    for account, broker in pairs:
        if (account, broker) not in valid_pairs:
            (
                SUPABASE.table("portfolio_positions")
                .delete()
                .eq("account", account)
                .eq("broker", broker)
                .execute()
            )
            (
                SUPABASE.table("transactions")
                .delete()
                .eq("account", account)
                .eq("broker", broker)
                .execute()
            )
            cleaned += 1

    st.cache_data.clear()
    return cleaned


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
    """
    V8.6:
    - Broker position snapshot (document_import): imported market value is authoritative
      for total value and latent P/L reconciliation.
    - Transaction rebuild: live quote is preferred; otherwise last transaction price is fallback.
    - Live market estimate remains visible separately when available.
    """
    df = load_positions(account, broker=broker)
    rows = []

    for _, r in df.iterrows():
        ticker = _clean_text(r.get("Ticker"), upper=True)
        qty = float(r.get("Quantité") or 0)
        pru = float(r.get("PRU") or 0)
        source = _clean_text(r.get("Source"))

        imported_price = pd.to_numeric(pd.Series([r.get("Cours importé")]), errors="coerce").iloc[0]
        imported_value = pd.to_numeric(pd.Series([r.get("Valeur importée")]), errors="coerce").iloc[0]

        company = r.get("Nom") or r.get("ISIN") or ticker
        live_price = None
        live_value = np.nan

        if use_live and ticker:
            q = live_quote(ticker)
            if q.get("price") is not None:
                live_price = float(q["price"])
                company = q.get("name") or company
                live_value = qty * live_price

        cost = qty * pru if pru else np.nan

        # Exact broker snapshot: preserve the broker's own imported valuation.
        is_broker_snapshot = source in {"document_import", "positions_import", ""} and pd.notna(imported_value)

        if is_broker_snapshot:
            reference_value = float(imported_value)
            reference_price = float(imported_price) if pd.notna(imported_price) else (
                reference_value / qty if qty else np.nan
            )
            value_source = "Snapshot courtier"
        else:
            if pd.notna(live_value):
                reference_value = float(live_value)
                reference_price = live_price
                value_source = "Marché"
            elif pd.notna(imported_value):
                reference_value = float(imported_value)
                reference_price = float(imported_price) if pd.notna(imported_price) else (
                    reference_value / qty if qty else np.nan
                )
                value_source = "Dernière valeur connue"
            elif pd.notna(imported_price):
                reference_price = float(imported_price)
                reference_value = qty * reference_price
                value_source = "Dernier prix transaction"
            else:
                reference_price = np.nan
                reference_value = np.nan
                value_source = "Non valorisé"

        pnl = reference_value - cost if pd.notna(reference_value) and pd.notna(cost) else np.nan
        pct = pnl / cost * 100 if pd.notna(pnl) and cost else np.nan

        live_gap = (
            live_value - reference_value
            if pd.notna(live_value) and pd.notna(reference_value)
            else np.nan
        )

        rows.append({
            "Ticker": ticker,
            "ISIN": r.get("ISIN"),
            "Entreprise": company,
            "Courtier": r.get("Courtier"),
            "Qté": qty,
            "PRU": pru,
            "Cours référence": reference_price,
            "Source valorisation": value_source,
            "Valeur référence": reference_value,
            "Coût": cost,
            "P/L latent": pnl,
            "P/L %": pct,
            "Cours live": live_price,
            "Valeur live estimée": live_value,
            "Écart live / snapshot": live_gap,
        })

    detail = pd.DataFrame(rows)

    totals = {
        "value": float(detail["Valeur référence"].sum(skipna=True)) if not detail.empty else 0.0,
        "cost": float(detail["Coût"].sum(skipna=True)) if not detail.empty else 0.0,
        "unrealized": float(detail["P/L latent"].sum(skipna=True)) if not detail.empty else 0.0,
        "unpriced": int(detail["Valeur référence"].isna().sum()) if not detail.empty else 0,
        "live_value": float(detail["Valeur live estimée"].sum(skipna=True)) if not detail.empty else 0.0,
    }
    return totals, detail


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
    vf_page_header("📈 Performance", "Performance Board — évolution, flux, dividendes, P/L réalisé et latent.")
    account=st.selectbox("Compte analysé",["pea","cto_xtb","cto_trade_republic","cto_autre"],
        format_func=lambda x:{"pea":"PEA","cto_xtb":"CTO XTB","cto_trade_republic":"CTO Trade Republic","cto_autre":"CTO autre"}[x])
    m,pos,tx,realized,openlots=performance_metrics(account)
    save_performance_snapshot(account,m)

    c1,c2,c3,c4=st.columns(4)
    c1.metric("Actifs valorisés",f"{m['assets_value']:,.0f} €")
    c2.metric("P/L latent",f"{m['unrealized']:+,.0f} €")
    c3.metric("Dividendes",f"{m['dividends']:+,.0f} €")
    c4.metric("P/L réalisé FIFO",f"{m['realized_gross']:+,.0f} €")

    c5,c6,c7,c8=st.columns(4)
    c5.metric("Apports",f"{m['contributions']:,.0f} €")
    c6.metric("Retraits",f"{m['withdrawals']:,.0f} €")
    c7.metric("Frais + taxes",f"{m['fees']+m['taxes']:,.0f} €")
    c8.metric("Intérêts",f"{m['interest']:+,.0f} €")

    if m["equity_estimate"] is not None and m["net_contributions"]>0:
        vf_section("Rendement estimé", "Lecture consolidée basée sur l'historique actuellement disponible.")
        a,b,c=st.columns(3)
        a.metric("Cash reconstruit",f"{m['cash_estimate']:+,.0f} €")
        b.metric("Valeur totale estimée",f"{m['equity_estimate']:,.0f} €")
        c.metric("Rendement simple",f"{m['return_pct']:+.2f} %",delta=f"{m['pnl_estimate']:+,.0f} €")

    hist=load_performance_snapshots(account)
    if not hist.empty:
        vf_section("Évolution", "Valeur estimée, apports nets et actifs valorisés.")
        vf_line(hist, "snapshot_date", ["equity_estimate","net_contributions","assets_value"], "Évolution du portefeuille")

    if not pos.empty:
        pos = add_identity_columns(pos, "Ticker")
        vf_section("Répartition actuelle", "Allocation et P/L latent par position.")
        left,right=st.columns(2)
        with left:
            if "Valeur référence" in pos:
                vf_pie(pos, "Valeur", "Valeur référence", "Répartition")
        with right:
            if "P/L latent" in pos:
                vf_signed_bar(pos.sort_values("P/L latent").tail(15), "Valeur", "P/L latent", "P/L latent")

        with st.expander("📋 Positions valorisées"):
            st.dataframe(pos,use_container_width=True,hide_index=True)

    if not realized.empty:
        with st.expander("💰 P/L réalisé — FIFO"):
            st.dataframe(realized,use_container_width=True,hide_index=True)

    if m["corporate_actions"]:
        st.warning(f"{m['corporate_actions']} opération(s) sur titres détectée(s). Le snapshot courtier reste la référence pour les positions courantes.")
    if m["issues"]:
        with st.expander("⚠️ Contrôles du ledger"):
            for item in m["issues"][:50]:
                st.write("•",item)

def _norm_company_text(value):
    s = _clean_text(value).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    stop = {"sa","sas","se","plc","nv","ag","spa","oyj","inc","corp","corporation","ltd","limited","group","holding"}
    return " ".join(t for t in s.split() if t not in stop)


@st.cache_data(ttl=3600, show_spinner=False)
def resolve_ticker_from_identity(name="", isin=""):
    """
    Best-effort resolver:
    1) exact ISIN/name in our central directory
    2) Yahoo Search by ISIN
    3) Yahoo Search by company/fund name
    Returns (ticker, confidence, source). Never invents a ticker.
    """
    name = _clean_text(name)
    isin = _clean_text(isin, upper=True)

    try:
        d = load_instrument_directory()
        if not d.empty:
            if isin:
                hit = d[d["isin"].astype(str).str.upper() == isin]
                if not hit.empty:
                    return _clean_text(hit.iloc[0].get("symbol"), upper=True), 100, "Référentiel ISIN"
            if name:
                target = _norm_company_text(name)
                if target:
                    for _, rr in d.iterrows():
                        cand = _norm_company_text(rr.get("name"))
                        if cand and cand == target:
                            return _clean_text(rr.get("symbol"), upper=True), 96, "Référentiel nom"
    except Exception:
        pass

    queries = [q for q in [isin, name] if q]
    best = None
    target_tokens = set(_norm_company_text(name).split())
    for query in queries:
        try:
            search = yf.Search(query, max_results=10)
            quotes = getattr(search, "quotes", None) or []
        except Exception:
            quotes = []

        for q in quotes:
            symbol = _clean_text(q.get("symbol"), upper=True)
            if not symbol:
                continue
            qtype = _clean_text(q.get("quoteType"), upper=True)
            if qtype and qtype not in {"EQUITY","ETF","MUTUALFUND"}:
                continue

            qname = _clean_text(q.get("longname") or q.get("shortname") or q.get("name"))
            cand_tokens = set(_norm_company_text(qname).split())
            overlap = 0
            if target_tokens and cand_tokens:
                overlap = len(target_tokens & cand_tokens) / max(len(target_tokens), 1)

            score = int(round(overlap * 80))
            # FR ISIN generally makes a Paris-listed candidate more plausible.
            if isin.startswith("FR") and symbol.endswith(".PA"):
                score += 12
            if query == isin:
                score += 10
            score = min(score, 99)

            if best is None or score > best[1]:
                best = (symbol, score, "Yahoo Search")

    if best and best[1] >= 55:
        return best
    return "", 0, "Non résolu"


def open_instrument(symbol):
    symbol = _clean_text(symbol, upper=True)
    if not symbol:
        return
    st.session_state["instrument_symbol"] = symbol
    st.session_state.pop("instrument_unresolved", None)
    st.session_state["_pending_nav_mode"] = "📊 Instrument"
    st.session_state["_pending_nav_group"] = "Analyse"
    st.rerun()



def show_arbitrage_page():
    vf_page_header(
        "⚖️ Arbitrage portefeuille",
        "Poids du portefeuille, qualité technique et résolution automatique des instruments."
    )

    account=st.selectbox(
        "Compte",
        ["pea","cto_xtb","cto_trade_republic","cto_autre"],
        key="arb_account",
        format_func=lambda x:{"pea":"PEA","cto_xtb":"CTO XTB","cto_trade_republic":"CTO Trade Republic","cto_autre":"CTO autre"}[x]
    )

    _,pos=portfolio_valuation(account,use_live=True)
    if pos.empty:
        st.info("Aucune position à analyser.")
        return

    value_col = "Valeur référence" if "Valeur référence" in pos.columns else ("Valeur" if "Valeur" in pos.columns else None)
    if value_col is None:
        st.error("Impossible de calculer l'arbitrage : aucune colonne de valorisation n'est disponible.")
        return

    total = pd.to_numeric(pos[value_col], errors="coerce").sum(skipna=True)
    rows=[]
    bar=st.progress(0)

    for i,(_,r) in enumerate(pos.iterrows(),1):
        ticker=_clean_text(r.get("Ticker"), upper=True)
        name=_clean_text(r.get("Entreprise")) or _clean_text(r.get("Nom")) or ticker
        isin=_clean_text(r.get("ISIN"), upper=True)
        resolution_source="Import"
        resolution_confidence=100 if ticker else 0

        if not ticker:
            ticker, resolution_confidence, resolution_source = resolve_ticker_from_identity(name, isin)

        value=pd.to_numeric(pd.Series([r.get(value_col)]), errors="coerce").iloc[0]
        weight=(float(value)/total*100) if pd.notna(value) and total else np.nan

        if not ticker:
            rows.append({
                "Ticker":"",
                "Nom complet":name,
                "ISIN":isin,
                "Poids %":weight,
                "P/L %":r.get("P/L %"),
                "Score":np.nan,
                "Potentiel %":np.nan,
                "R/R":np.nan,
                "Résolution":"Non résolu",
                "Lecture":"Ticker à résoudre"
            })
            bar.progress(i/max(len(pos),1))
            continue

        setup=trade_setup(history(ticker,"6mo","1d"))
        if not setup:
            reading="Données insuffisantes"; score=up=rr=np.nan
        else:
            score,up,rr=setup["score"],setup["upside"],setup["rr"]
            if score>=85 and up>=5 and rr>=2:
                reading="🟢 Renforcer / conserver — signal technique fort"
            elif score<60 or up<2:
                reading="🟠 Examiner un allègement — signal faible"
            else:
                reading="🟡 Conserver / surveiller"

        resolution = resolution_source if resolution_confidence >= 90 else f"{resolution_source} ({resolution_confidence}%)"

        rows.append({
            "Ticker":ticker,
            "Nom complet":name,
            "ISIN":isin,
            "Poids %":weight,
            "P/L %":r.get("P/L %"),
            "Score":score,
            "Potentiel %":up,
            "R/R":rr,
            "Résolution":resolution,
            "Lecture":reading
        })
        bar.progress(i/max(len(pos),1))

    bar.empty()
    out=pd.DataFrame(rows)

    resolved = int(out["Ticker"].astype(bool).sum())
    unresolved = len(out) - resolved
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Positions", len(out))
    k2.metric("Résolues", resolved)
    k3.metric("À résoudre", unresolved)
    k4.metric("Valeur analysée", f"{total:,.0f} €")

    st.dataframe(
        out.sort_values("Score",ascending=False,na_position="last"),
        use_container_width=True,
        hide_index=True
    )

    cva,cvb=st.columns(2)
    with cva:
        chart_df=out.dropna(subset=["Poids %"]).copy()
        chart_df["Valeur"] = chart_df.apply(lambda x: f"{x['Ticker'] or '—'} • {x['Nom complet']}", axis=1)
        vf_bar(chart_df.nlargest(min(15,len(chart_df)), "Poids %"), "Valeur", "Poids %", "Poids des positions")
    with cvb:
        chart_df=out.dropna(subset=["Score"]).copy()
        if not chart_df.empty:
            chart_df["Valeur"] = chart_df.apply(lambda x: f"{x['Ticker']} • {x['Nom complet']}", axis=1)
            vf_bar(chart_df.nlargest(min(15,len(chart_df)), "Score"), "Valeur", "Score", "Score technique")

    resolved_rows = out[out["Ticker"].astype(bool)]
    if not resolved_rows.empty:
        st.markdown("#### Ouvrir une position")
        labels = {
            f"{rr['Ticker']} • {rr['Nom complet']}": rr["Ticker"]
            for _, rr in resolved_rows.iterrows()
        }
        a,b=st.columns([4,1])
        selected=a.selectbox("Position", list(labels.keys()), key="arb_open_symbol")
        if b.button("📊 Fiche instrument", use_container_width=True):
            _sym = labels[selected]
            _row = resolved_rows[resolved_rows["Ticker"] == _sym].iloc[0]
            open_instrument_identity(_sym, _row.get("Nom complet",""), _row.get("ISIN",""))

    if unresolved:
        st.warning(
            f"{unresolved} instrument(s) restent sans ticker fiable. "
            "VISION FUTURE ne leur attribue volontairement aucun score tant que la résolution n'est pas suffisamment sûre."
        )

    st.caption(
        "Lecture analytique croisant poids du portefeuille et setup technique. "
        "Les tickers résolus automatiquement sont identifiés dans la colonne Résolution."
    )


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
    "unrealized_pl": ["amountvariation","unrealizedpl","unrealizedpnl","latentpl","pllatent","plusvaluelatente","moinsvaluelatente"],
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
        unrealized_pl = parse_number(value_from(row, cmap, "unrealized_pl", np.nan))
        # In position snapshots, many brokers call the position value simply "amount".
        if not np.isfinite(market_value):
            amount_col = next((c for c in df.columns if norm_token(c) in {"amount","montant","value","valeur","valorisation"}), None)
            if amount_col is not None:
                market_value = parse_number(row.get(amount_col, np.nan))
        # Some broker exports round the displayed PRU heavily (e.g. penny stocks),
        # while market value and latent P/L are more precise. When both are present,
        # infer the effective cost basis so the app reconciles with the broker snapshot.
        if np.isfinite(qty) and abs(qty) > 1e-12 and np.isfinite(market_value) and np.isfinite(unrealized_pl):
            implied_cost = market_value - unrealized_pl
            implied_pru = implied_cost / qty
            if np.isfinite(implied_pru) and implied_pru >= 0:
                cost = implied_pru

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
    "USA": ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","AVGO","AMD","NFLX","ADBE","CRM","ORCL","QCOM","INTC","PLTR","JPM","V","MA","XOM","CVX","LLY","JNJ","UNH","COST","WMT","HD","CAT","GE","BA","NOW","PANW","CRWD","MU","AMAT","LRCX"],
    "Canada": ["SHOP.TO","RY.TO","TD.TO","BNS.TO","BMO.TO","ENB.TO","CNQ.TO","SU.TO","CP.TO","CNR.TO"],
    "France": ["MC.PA","OR.PA","AIR.PA","SAN.PA","SU.PA","TTE.PA","BNP.PA","AI.PA","SAF.PA","DG.PA","CS.PA","CAP.PA","ACA.PA","ENGI.PA","SGO.PA","VIE.PA","RMS.PA","KER.PA","DSY.PA","HO.PA"],
    "Germany": ["SAP.DE","SIE.DE","ALV.DE","DTE.DE","MBG.DE","BMW.DE","BAS.DE","IFX.DE","DBK.DE","RHM.DE","ADS.DE","VOW3.DE","HEN3.DE"],
    "Netherlands": ["ASML.AS","ADYEN.AS","INGA.AS","PRX.AS","PHIA.AS","UNA.AS","HEIA.AS"],
    "UK": ["SHEL.L","AZN.L","HSBA.L","ULVR.L","BP.L","GSK.L","RIO.L","BARC.L","LLOY.L","RR.L","LSEG.L"],
    "Spain": ["SAN.MC","BBVA.MC","IBE.MC","ITX.MC","REP.MC","TEF.MC","FER.MC"],
    "Italy": ["ENEL.MI","ENI.MI","ISP.MI","UCG.MI","STLAM.MI","RACE.MI","G.MI"],
    "Switzerland": ["NESN.SW","ROG.SW","NOVN.SW","UBSG.SW","ABBN.SW","CFR.SW"],
    "Nordics": ["NOVO-B.CO","MAERSK-B.CO","VOLV-B.ST","ERIC-B.ST","NDA-SE.ST","EQNR.OL"],
    "Japan": ["7203.T","6758.T","9984.T","8306.T","8035.T","6861.T"],
    "Hong Kong": ["0700.HK","9988.HK","3690.HK","1211.HK","1810.HK"],
    "Australia": ["BHP.AX","CBA.AX","CSL.AX","WBC.AX","NAB.AX","WES.AX"],
    "ETF globaux": ["SPY","QQQ","IWM","DIA","VGK","EWJ","EEM","GLD","SLV","TLT","HYG"],
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



YF_DISCOVERY_REGIONS = {
    "USA": "us",
    "Canada": "ca",
    "Royaume-Uni": "gb",
    "France": "fr",
    "Allemagne": "de",
    "Pays-Bas": "nl",
    "Espagne": "es",
    "Italie": "it",
    "Suisse": "ch",
    "Japon": "jp",
    "Australie": "au",
    "Suède": "se",
}


@st.cache_data(ttl=900, show_spinner=False)
def discover_yahoo_equities(region_labels, max_per_region=20):
    """
    Découverte dynamique via le screener Yahoo/yfinance.
    Important : ces instruments ne sont PAS considérés comme vérifiés chez XTB/TR.
    """
    rows = []
    for label in region_labels:
        region = YF_DISCOVERY_REGIONS.get(label)
        if not region:
            continue
        try:
            q = yf.EquityQuery("and", [
                yf.EquityQuery("eq", ["region", region]),
                yf.EquityQuery("gte", ["intradaymarketcap", 500_000_000]),
                yf.EquityQuery("gte", ["intradayprice", 2]),
                yf.EquityQuery("gte", ["avgdailyvol3m", 100_000]),
            ])
            resp = yf.screen(
                q,
                size=int(max_per_region),
                sortField="dayvolume",
                sortAsc=False,
            )
            quotes = (resp or {}).get("quotes", []) if isinstance(resp, dict) else []
            for x in quotes:
                sym = _clean_text(x.get("symbol"), upper=True)
                if not sym:
                    continue
                quote_type = _clean_text(x.get("quoteType"), upper=True)
                if quote_type and quote_type not in {"EQUITY", "ETF"}:
                    continue
                rows.append({
                    "symbol": sym,
                    "name": _clean_text(x.get("longName") or x.get("shortName")),
                    "isin": "",
                    "market": label,
                    "asset_type": quote_type or "EQUITY",
                    "broker": "À vérifier",
                    "enabled": True,
                    "source": "Découverte Yahoo",
                    "market_cap": x.get("marketCap") or x.get("intradaymarketcap"),
                    "volume": x.get("regularMarketVolume") or x.get("dayvolume"),
                })
        except Exception:
            continue

    if not rows:
        return pd.DataFrame(columns=[
            "symbol","name","isin","market","asset_type","broker","enabled",
            "source","market_cap","volume"
        ])
    df = pd.DataFrame(rows)
    return df.drop_duplicates(subset=["symbol"]).reset_index(drop=True)


def scanner_universe_frame(brokers, markets, include_discovery=False, discovery_regions=None, max_per_region=20):
    frames = []

    # Référentiel vérifié / géré par l'utilisateur.
    base = load_broker_universe(brokers=brokers, markets=markets)
    if not base.empty:
        base = base.copy()
        base["source"] = "Référentiel courtier"
        frames.append(base)

    # Découverte dynamique : volontairement séparée de la compatibilité courtier.
    if include_discovery and discovery_regions:
        disc = discover_yahoo_equities(discovery_regions, max_per_region=max_per_region)
        if not disc.empty:
            frames.append(disc)

    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True, sort=False)
    out["symbol"] = out["symbol"].map(lambda x: _clean_text(x, upper=True))
    out = out[out["symbol"].astype(bool)]
    # Si le même ticker existe dans le référentiel courtier et en découverte,
    # le référentiel courtier gagne.
    out["_priority"] = out["source"].map({"Référentiel courtier": 0, "Découverte Yahoo": 1}).fillna(2)
    out = out.sort_values("_priority").drop_duplicates("symbol").drop(columns="_priority")
    return out.reset_index(drop=True)



def _fallback_universe():
    rows = []
    for market, symbols in UNIVERSE.items():
        for symbol in symbols:
            rows.append({
                "symbol": symbol,
                "market": market,
                "broker": "fallback",
                "enabled": True,
                "asset_type": "ETF" if market == "ETF globaux" else "EQUITY",
            })
    return pd.DataFrame(rows)


@st.cache_data(ttl=300, show_spinner=False)
def load_broker_universe(brokers=None, markets=None):
    """
    Universe scanner:
    - Priorité à Supabase `broker_universe` si la table est renseignée.
    - Sinon fallback global intégré.
    La colonne broker permet de ne conserver que les instruments marqués
    compatibles avec XTB / Trade Republic / les deux.
    """
    if SUPABASE is not None:
        try:
            q = SUPABASE.table("broker_universe").select(
                "symbol,name,isin,market,asset_type,broker,enabled"
            ).eq("enabled", True)
            res = q.execute()
            data = _sb_data(res)
            if data:
                df = pd.DataFrame(data)
                if brokers:
                    wanted = {str(x).strip().lower() for x in brokers}
                    df = df[df["broker"].fillna("").str.lower().isin(wanted)]
                if markets:
                    df = df[df["market"].isin(markets)]
                if not df.empty:
                    return df.drop_duplicates(subset=["symbol","broker"])
        except Exception:
            pass

    df = _fallback_universe()
    if markets:
        df = df[df["market"].isin(markets)]
    return df


def compatible_scan_symbols(brokers, markets):
    df = load_broker_universe(brokers=brokers, markets=markets)
    return sorted({
        str(x).strip().upper()
        for x in df.get("symbol", pd.Series(dtype=str)).dropna().tolist()
        if str(x).strip()
    })


@st.cache_data(ttl=120, show_spinner=False)
def load_instrument_directory():
    """Référentiel central ticker -> nom complet + ISIN + marché/courtier."""
    rows = []
    if SUPABASE is None:
        return pd.DataFrame(columns=["symbol","name","isin","market","broker"])
    try:
        p = _sb_data(SUPABASE.table("portfolio_positions")
                     .select("ticker,name,isin,broker")
                     .execute())
        for r in p:
            sym = _clean_text(r.get("ticker"), upper=True)
            if sym:
                rows.append({"symbol":sym,"name":_clean_text(r.get("name")),"isin":_clean_text(r.get("isin"), upper=True),
                             "market":"","broker":_clean_text(r.get("broker"))})
    except Exception:
        pass
    try:
        u = _sb_data(SUPABASE.table("broker_universe")
                     .select("symbol,name,isin,market,broker")
                     .eq("enabled", True).execute())
        for r in u:
            sym = _clean_text(r.get("symbol"), upper=True)
            if sym:
                rows.append({"symbol":sym,"name":_clean_text(r.get("name")),"isin":_clean_text(r.get("isin"), upper=True),
                             "market":_clean_text(r.get("market")),"broker":_clean_text(r.get("broker"))})
    except Exception:
        pass
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["symbol","name","isin","market","broker"])
    # Prefer rows with most identity information.
    df["_quality"] = df[["name","isin"]].notna().sum(axis=1)
    df = df.sort_values("_quality", ascending=False).drop_duplicates("symbol").drop(columns="_quality")
    return df


def instrument_identity(symbol, row=None):
    """Always return (symbol, full_name, isin). Existing alert fields win, then central directory."""
    sym = _clean_text(symbol, upper=True)
    # Hotfix: pandas Series/DataFrame cannot be evaluated as True/False.
    if row is None:
        row = {}
    elif isinstance(row, pd.DataFrame):
        row = row.iloc[0].to_dict() if not row.empty else {}
    elif isinstance(row, pd.Series):
        row = row.to_dict()
    elif not isinstance(row, dict):
        try:
            row = dict(row)
        except Exception:
            row = {}
    name = _clean_text(row.get("name") if hasattr(row, "get") else None)
    isin = _clean_text(row.get("isin") if hasattr(row, "get") else None, upper=True)
    if sym and (not name or not isin):
        try:
            d = load_instrument_directory()
            hit = d[d["symbol"] == sym]
            if not hit.empty:
                rr = hit.iloc[0]
                name = name or _clean_text(rr.get("name"))
                isin = isin or _clean_text(rr.get("isin"), upper=True)
        except Exception:
            pass
    # Last-resort name only; never invent an ISIN.
    if sym and not name:
        try:
            name = _clean_text(live_quote(sym).get("name"))
        except Exception:
            pass
    return sym, name or "Nom non renseigné", isin or "ISIN non renseigné"


def add_identity_columns(df, symbol_col="Ticker"):
    """Adds a human-readable identity column to tabular views."""
    if df is None or df.empty or symbol_col not in df.columns:
        return df
    out = df.copy()
    directory = load_instrument_directory()
    lookup = directory.set_index("symbol") if not directory.empty else None
    labels=[]; names=[]; isins=[]
    for _, r in out.iterrows():
        sym=_clean_text(r.get(symbol_col), upper=True)
        name=_clean_text(r.get("Entreprise") or r.get("Nom") or r.get("name"))
        isin=_clean_text(r.get("ISIN") or r.get("isin"), upper=True)
        if lookup is not None and sym in lookup.index:
            rr=lookup.loc[sym]
            if isinstance(rr, pd.DataFrame): rr=rr.iloc[0]
            name=name or _clean_text(rr.get("name"))
            isin=isin or _clean_text(rr.get("isin"), upper=True)
        names.append(name or "Nom non renseigné")
        isins.append(isin or "ISIN non renseigné")
        labels.append(f"{sym} • {name or 'Nom non renseigné'} • {isin or 'ISIN non renseigné'}")
    out["Entreprise"] = names
    out["ISIN"] = isins
    out.insert(0, "Valeur", labels)
    return out


@st.cache_data(ttl=30, show_spinner=False)
def load_market_alerts(limit=100, status=None):
    if SUPABASE is None:
        return pd.DataFrame()
    try:
        q = SUPABASE.table("market_alerts").select("*").order("created_at", desc=True).limit(limit)
        if status:
            q = q.eq("status", status)
        df = pd.DataFrame(_sb_data(q.execute()))
        if not df.empty and "alert_type" in df.columns:
            actionable = {"ENTRY","EXIT","TAKE_PROFIT","PROTECT","RISK","NEWS_RISK","INVALIDATED"}
            df = df[df["alert_type"].isin(actionable)].copy()
        return df
    except Exception:
        return pd.DataFrame()


def acknowledge_alert(alert_id):
    if SUPABASE is None:
        return
    try:
        SUPABASE.table("market_alerts").update({
            "status": "ACKNOWLEDGED",
            "acknowledged_at": datetime.utcnow().isoformat()
        }).eq("id", alert_id).execute()
        st.cache_data.clear()
    except Exception:
        pass



@st.cache_data(ttl=30, show_spinner=False)
def load_agent_runs(limit=20):
    if SUPABASE is None:
        return pd.DataFrame()
    try:
        return pd.DataFrame(_sb_data(
            SUPABASE.table("agent_runs")
            .select("*")
            .order("ran_at", desc=True)
            .limit(limit)
            .execute()
        ))
    except Exception:
        return pd.DataFrame()


def parse_agent_details(text):
    out = {}
    raw = _clean_text(text)
    if not raw:
        return out
    for part in raw.split("|"):
        p = part.strip()
        if "=" in p:
            k, v = p.split("=", 1)
            out[k.strip().upper()] = v.strip()
    return out



def show_market_agent_page():
    vf_page_header(
        "🛰️ Agent marché",
        "Decision Board — alertes actionnables, régime de marché et suivi automatique des positions."
    )

    runs = load_agent_runs(10)
    latest = runs.iloc[0] if not runs.empty else None
    details = parse_agent_details(latest.get("details")) if latest is not None else {}

    regime_raw = details.get("REGIME","—")
    regime_state = regime_raw
    regime_score = None
    mm = re.match(r"^([A-Z_]+)\(([^)]+)\)$", str(regime_raw))
    if mm:
        regime_state, regime_score = mm.group(1), mm.group(2)

    h1,h2,h3,h4,h5 = st.columns(5)
    h1.metric("État agent", _clean_text(latest.get("status")) if latest is not None else "—")
    h2.metric("Régime", regime_state, regime_score)
    h3.metric("Univers ce cycle", details.get("UNIVERSE","—"))
    h4.metric("Candidats ce cycle", details.get("CONFIRMED","—"))
    h5.metric("Créées ce cycle", int(latest.get("created_alerts") or 0) if latest is not None else 0)
    if latest is not None:
        st.caption(f"Dernier cycle : {latest.get('ran_at','—')}")

    alerts = load_market_alerts(limit=250)
    if alerts.empty:
        st.info("Aucune alerte actionnable actuellement. L'agent continue de surveiller le marché.")
        return

    for c in ["score","upside","rr","entry","stop","tp1","tp2"]:
        if c in alerts.columns:
            alerts[c] = pd.to_numeric(alerts[c], errors="coerce")

    risk_types={"EXIT","TAKE_PROFIT","PROTECT","RISK","NEWS_RISK","INVALIDATED"}
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Alertes actionnables", len(alerts))
    c2.metric("Entrées", int((alerts["alert_type"]=="ENTRY").sum()) if "alert_type" in alerts else 0)
    c3.metric("Gestion / sorties", int(alerts["alert_type"].isin(risk_types).sum()) if "alert_type" in alerts else 0)
    c4.metric("Nouvelles", int((alerts["status"]=="NEW").sum()) if "status" in alerts else 0)

    entries = alerts[alerts["alert_type"]=="ENTRY"].copy() if "alert_type" in alerts else pd.DataFrame()
    if not entries.empty:
        vf_section("Opportunités d'entrée", "Les setups ENTRY classés par score et potentiel.")
        entries = entries.sort_values(["score","rr","upside"], ascending=False, na_position="last")
        for i in range(0, min(len(entries),6), 2):
            cols=st.columns(2)
            for j,col in enumerate(cols):
                idx=i+j
                if idx >= min(len(entries),6):
                    break
                with col:
                    row=entries.iloc[idx].to_dict()
                    row["Ticker"] = row.get("symbol")
                    row["Entreprise"] = row.get("name")
                    row["ISIN"] = row.get("isin")
                    row["Score combiné"] = row.get("score")
                    row["Potentiel %"] = row.get("upside")
                    row["R/R"] = row.get("rr")
                    row["Entrée"] = row.get("entry")
                    row["Stop"] = row.get("stop")
                    row["TP2"] = row.get("tp2")
                    vf_setup_card(row, key_prefix=f"agent_entry_{idx}")

        with st.expander("📋 Tableau des opportunités"):
            entries["Valeur"] = entries.apply(
                lambda r: f"{_clean_text(r.get('symbol'), upper=True)} • {_clean_text(r.get('name')) or 'Nom non renseigné'}",
                axis=1
            )
            cols = [c for c in ["Valeur","isin","market","broker","score","upside","rr","entry","stop","tp1","tp2","news_risk","created_at"] if c in entries.columns]
            st.dataframe(entries[cols], use_container_width=True, hide_index=True)

    vf_section("Flux de décisions", "Les derniers événements actionnables de l'agent.")
    for _, r in alerts.head(20).iterrows():
        typ=_clean_text(r.get("alert_type"),upper=True) or "ALERT"
        symbol,full_name,isin=instrument_identity(r.get("symbol"),r)
        score=r.get("score")

        with st.container(border=True):
            a,b=st.columns([5,1.2])
            with a:
                st.markdown(vf_identity_html(symbol, full_name, isin), unsafe_allow_html=True)
            with b:
                st.markdown(vf_alert_chip(typ), unsafe_allow_html=True)
                if pd.notna(score):
                    st.caption(f"Score {float(score):.0f}/100")

            vals=st.columns(4)
            specs=[
                ("Entrée",r.get("entry"),""),
                ("Stop",r.get("stop"),""),
                ("Potentiel",r.get("upside"),"%"),
                ("R/R",r.get("rr"),""),
            ]
            for col,(label,value,suffix) in zip(vals,specs):
                num=pd.to_numeric(pd.Series([value]),errors="coerce").iloc[0]
                col.metric(label,f"{float(num):.2f}{suffix}" if pd.notna(num) else "—")

            headline=_clean_text(r.get("headline"))
            analysis=_clean_text(r.get("analysis"))
            if headline:
                st.markdown(f"**📰 {headline}**")
            if analysis:
                st.caption(analysis[:420])

            footer=[]
            for item in [_clean_text(r.get("broker")),_clean_text(r.get("market")),f"news {_clean_text(r.get('news_risk'),upper=True)}" if _clean_text(r.get("news_risk")) else "",_clean_text(r.get("status"))]:
                if item:
                    footer.append(item)
            if footer:
                st.caption(" • ".join(footer))

            ba,bb = st.columns([1,1])
            with ba:
                if st.button("📊 Ouvrir la fiche", key=f"open_alert_{r.get('id','x')}_{vf_identity_key(symbol, full_name, isin)}", use_container_width=True):
                    open_instrument_identity(symbol, full_name, isin)
            with bb:
                if r.get("status")=="NEW" and r.get("id") is not None:
                    if st.button("🔖 Marquer comme lu",key=f"ack_{r.get('id')}", use_container_width=True):
                        acknowledge_alert(r.get("id"))
                        st.rerun()

    with st.expander("📊 Analyse agrégée des alertes"):
        left,right = st.columns(2)
        with left:
            if "alert_type" in alerts.columns:
                x=alerts["alert_type"].value_counts().rename_axis("Type").reset_index(name="Nombre")
                vf_bar(x,"Type","Nombre","Alertes par type",horizontal=False)
        with right:
            if "score" in alerts.columns:
                x=alerts.dropna(subset=["score"]).copy()
                if not x.empty:
                    x["Valeur"] = x.apply(lambda r: f"{_clean_text(r.get('symbol'), upper=True)} • {_clean_text(r.get('name'))}",axis=1)
                    vf_bar(x.nlargest(min(12,len(x)),"score"),"Valeur","score","Meilleurs scores")

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
    try:
        reconcile_orphan_portfolio_data()
    except Exception:
        pass

    st.header("📥 Imports & gestion des documents")
    st.caption(
        "Même espace pour importer, consulter et supprimer les documents. "
        "Les reconstructions de portefeuille restent automatiques."
    )

    tab_import, tab_manage = st.tabs(["➕ Importer", "📁 Gérer / supprimer"])

    with tab_import:
        st.subheader("Import intelligent")
        st.caption(
            "Dépose un export. VISION FUTURE détecte le format réel, le type de document "
            "et ses champs. L'extension du fichier n'impose pas le lecteur."
        )

        account = st.selectbox(
            "Compte cible",
            ["pea","cto_xtb","cto_trade_republic","cto_autre"],
            format_func=lambda x:{
                "pea":"PEA",
                "cto_xtb":"CTO XTB",
                "cto_trade_republic":"CTO Trade Republic",
                "cto_autre":"CTO / autre"
            }[x],
            key="import_account"
        )

        uploaded = st.file_uploader(
            "Document",
            type=None,
            accept_multiple_files=False,
            key="unified_import_uploader"
        )

        if uploaded is None:
            st.info(
                "Formats tabulaires pris en charge : CSV, CSV renommé .xls, TSV, TXT, XLSX et XLS. "
                "Les PDF seront ajoutés au moteur documentaire dans une étape dédiée."
            )
        else:
            try:
                result = interpret_document(uploaded)
            except Exception as exc:
                raw = uploaded.getvalue()
                st.error(f"Lecture impossible : {exc}")
                st.code(repr(raw[:240]))
                result = None

            if result is not None:
                meta=result["meta"]; doc=result["document_type"]; broker=result["broker"]
                c1,c2,c3,c4=st.columns(4)
                c1.metric("Type", doc)
                c2.metric("Confiance", f"{result['confidence']*100:.0f}%")
                c3.metric("Courtier probable", broker)
                c4.metric("Lignes", len(result["raw_df"]))
                st.caption(
                    f"Format réel : {meta['format']} • encodage : {meta['encoding']} • "
                    f"séparateur : {meta['separator']} • taille : {meta['size']} octets"
                )

                with st.expander("🔎 Champs reconnus", expanded=True):
                    if result["column_map"]:
                        mapping_df=pd.DataFrame([
                            {"Champ interne":k,"Colonne détectée":v}
                            for k,v in result["column_map"].items()
                        ])
                        st.dataframe(mapping_df,use_container_width=True,hide_index=True)
                    else:
                        st.warning("Aucun champ financier connu n'a été reconnu.")

                broker_override=st.text_input(
                    "Courtier / source",
                    value=broker,
                    key="unified_broker_override"
                )

                with st.expander("Aperçu normalisé", expanded=True):
                    st.dataframe(
                        result["normalized"].head(100),
                        use_container_width=True,
                        hide_index=True
                    )

                if not result["issues"].empty:
                    st.warning(f"{len(result['issues'])} ligne(s) nécessitent une vérification.")
                    st.dataframe(result["issues"],use_container_width=True,hide_index=True)

                duplicate = import_exists(meta["hash"], account)

                if duplicate:
                    st.success(
                        f"✅ Ce fichier a déjà été importé "
                        f"({duplicate.get('document_type','')}, {duplicate.get('imported_at','')})."
                    )
                elif doc == "UNKNOWN":
                    st.error(
                        "Document non reconnu avec assez de certitude. "
                        "Aucune donnée ne sera enregistrée."
                    )
                elif doc == "ACCOUNTING":
                    st.info(
                        "Document comptable reconnu. Il est volontairement exclu "
                        "du portefeuille et du ledger boursier."
                    )
                elif st.button(
                    "☁️ Valider et enregistrer dans Supabase",
                    type="primary",
                    key="unified_save_import"
                ):
                    try:
                        rebuild_stats = None

                        if doc == "POSITIONS":
                            count=save_positions(
                                account,
                                broker_override,
                                result["normalized"],
                                source_import_hash=meta["hash"]
                            )
                        else:
                            count=save_transactions(
                                account,
                                broker_override,
                                result["normalized"],
                                source_import_hash=meta["hash"]
                            )
                            rebuild_stats = rebuild_positions_from_transactions(
                                account,
                                broker_override
                            )

                        upsert_import_record({
                            "file_hash":meta["hash"],
                            "account":account,
                            "filename":uploaded.name,
                            "document_type":doc,
                            "broker":broker_override,
                            "row_count":int(count),
                            "status":"IMPORTED",
                            "imported_at":datetime.utcnow().isoformat(),
                            "metadata":json.dumps(
                                {k:v for k,v in meta.items() if k!="hash"},
                                ensure_ascii=False
                            ),
                        })

                        if rebuild_stats is not None:
                            st.success(
                                f"☁️ Import terminé : {count} transaction(s) synchronisée(s). "
                                f"Portefeuille reconstruit automatiquement : "
                                f"{rebuild_stats['positions']} position(s) ouverte(s)."
                            )
                            if rebuild_stats.get("corporate_actions"):
                                st.caption(
                                    f"{rebuild_stats['corporate_actions']} opération(s) "
                                    f"sur titres intégrée(s) automatiquement."
                                )
                            if rebuild_stats.get("issues"):
                                with st.expander("⚠️ Points à vérifier"):
                                    for msg in rebuild_stats["issues"][:20]:
                                        st.write("•", msg)
                        else:
                            st.success(
                                f"☁️ Import terminé : {count} position(s) enregistrée(s). "
                                "Elles seront rechargées automatiquement."
                            )

                        st.cache_data.clear()

                    except Exception as exc:
                        st.error(f"Échec d'enregistrement Supabase : {exc}")

    with tab_manage:
        st.subheader("Documents enregistrés")
        st.caption(
            "Filtre les imports par compte ou courtier puis supprime l'historique seul, "
            "ou le document avec les données qu'il a générées."
        )

        c1, c2 = st.columns(2)
        account_filter = c1.selectbox(
            "Compte",
            ["Tous","pea","cto_xtb","cto_trade_republic","cto_autre"],
            key="unified_docs_account"
        )
        broker_filter = c2.text_input(
            "Courtier (optionnel)",
            "",
            key="unified_docs_broker"
        ).strip()

        df = load_imports(
            None if account_filter == "Tous" else account_filter,
            broker_filter or None
        )

        if df.empty:
            st.info("Aucun document enregistré pour ce filtre.")
        else:
            show_cols = [
                c for c in
                ["id","filename","document_type","account","broker","row_count","status","imported_at"]
                if c in df.columns
            ]
            st.dataframe(
                df[show_cols],
                use_container_width=True,
                hide_index=True
            )

            options = {}
            for _, r in df.iterrows():
                label = (
                    f"#{r.get('id')} • {r.get('filename')} • "
                    f"{r.get('document_type')} • {r.get('account')} • {r.get('broker')}"
                )
                options[label] = r.to_dict()

            selected = st.selectbox(
                "Document à gérer",
                list(options),
                key="unified_doc_to_manage"
            )
            row = options[selected]

            st.caption(
                "La suppression retire le document et les données qu'il a générées. "
                "S'il reste d'autres transactions pour ce compte/courtier, le portefeuille "
                "est reconstruit automatiquement ; sinon les positions résiduelles disparaissent."
            )

            confirm = st.checkbox(
                "Je confirme la suppression de ce document et de ses données liées",
                key=f"unified_confirm_delete_{row.get('id')}"
            )

            if st.button(
                "🗑️ Supprimer",
                type="primary",
                use_container_width=True,
                disabled=not confirm,
                key="unified_delete_all"
            ):
                try:
                    delete_import_record(row, delete_generated_data=True)
                    reconcile_orphan_portfolio_data()
                    st.cache_data.clear()
                    st.success("Document supprimé et portefeuille actualisé automatiquement.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Suppression impossible : {exc}")




@st.cache_data(ttl=86400, show_spinner=False)
def vf_logo_dev_token():
    token = ""
    try:
        token = _clean_text(st.secrets.get("LOGO_DEV_TOKEN", ""))
    except Exception:
        token = ""
    if not token:
        token = _clean_text(os.getenv("LOGO_DEV_TOKEN", ""))
    return token


@st.cache_data(ttl=86400, show_spinner=False)
def vf_fetch_logo_data_uri(url):
    if not url:
        return ""
    try:
        from urllib.request import Request, urlopen
        req = Request(url, headers={"User-Agent": "VISION-FUTURE/22"})
        with urlopen(req, timeout=6) as resp:
            content_type = str(resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            data = resp.read(500_000)
        if not data or not content_type.startswith("image/"):
            return ""
        encoded = base64.b64encode(data).decode("ascii")
        return f"data:{content_type};base64,{encoded}"
    except Exception:
        return ""


@st.cache_data(ttl=86400, show_spinner=False)
def vf_logo_dev_search_company(name):
    """
    Name -> canonical domain/logo using Logo.dev Search API.
    This endpoint requires a secret key (sk_*). If the user configured only a
    publishable key, we simply skip this step and keep the other logo fallbacks.
    """
    name = _clean_text(name)
    token = vf_logo_dev_token()
    if not name or not token.startswith("sk_"):
        return {}

    try:
        from urllib.parse import quote
        from urllib.request import Request, urlopen

        url = f"https://api.logo.dev/search?q={quote(name)}&strategy=match"
        req = Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "VISION-FUTURE/22",
            },
        )
        with urlopen(req, timeout=6) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        if not isinstance(payload, list) or not payload:
            return {}

        # Pick first exact-ish result; Search API is ranked.
        first = payload[0] or {}
        return {
            "name": _clean_text(first.get("name")),
            "domain": _clean_text(first.get("domain")),
            "logo_url": _clean_text(first.get("logo_url")),
        }
    except Exception:
        return {}


@st.cache_data(ttl=86400, show_spinner=False)
def vf_company_brand_data(symbol, name="", isin=""):
    """
    Brand identity resolver.

    Priority:
      1. explicit logo URL from finance provider
      2. official website domain from finance provider
      3. Logo.dev company-name search -> canonical domain (secret key only)
      4. ticker lookup
      5. ISIN lookup
      6. clean monogram fallback
    """
    symbol = _clean_text(symbol, upper=True)
    name = _clean_text(name)
    isin = _clean_text(isin, upper=True)

    try:
        info = yf.Ticker(symbol).info or {} if symbol else {}
    except Exception:
        info = {}

    finance_name = _clean_text(info.get("longName") or info.get("shortName"))
    finance_logo = _clean_text(
        info.get("logo_url")
        or info.get("logoUrl")
        or info.get("companyLogoUrl")
    )
    website = _clean_text(info.get("website"))

    if finance_logo.startswith("http"):
        data_uri = vf_fetch_logo_data_uri(finance_logo)
        if data_uri:
            return {
                "url": data_uri,
                "source": "Source financière",
                "name": finance_name or name,
                "website": website,
            }

    domain = ""
    if website:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(website if "://" in website else "https://" + website)
            domain = (parsed.netloc or parsed.path).split(":")[0].lower().strip()
            if domain.startswith("www."):
                domain = domain[4:]
        except Exception:
            domain = ""

    token = vf_logo_dev_token()
    from urllib.parse import quote

    # 1) Domain from Yahoo / provider
    if token and domain:
        candidate = f"https://img.logo.dev/{quote(domain)}?token={quote(token)}&size=128&format=png&retina=true"
        data_uri = vf_fetch_logo_data_uri(candidate)
        if data_uri:
            return {
                "url": data_uri,
                "source": "Logo.dev • domaine",
                "name": finance_name or name,
                "website": domain,
            }

    # 2) Resolve by company name to canonical domain.
    searched = vf_logo_dev_search_company(finance_name or name)
    searched_domain = _clean_text(searched.get("domain"))
    searched_logo = _clean_text(searched.get("logo_url"))

    if searched_logo:
        # If search returns a ready-to-use image URL, fetch it server-side.
        data_uri = vf_fetch_logo_data_uri(searched_logo)
        if data_uri:
            return {
                "url": data_uri,
                "source": "Logo.dev • nom",
                "name": _clean_text(searched.get("name")) or finance_name or name,
                "website": searched_domain,
            }

    if token and searched_domain:
        candidate = f"https://img.logo.dev/{quote(searched_domain)}?token={quote(token)}&size=128&format=png&retina=true"
        data_uri = vf_fetch_logo_data_uri(candidate)
        if data_uri:
            return {
                "url": data_uri,
                "source": "Logo.dev • nom",
                "name": _clean_text(searched.get("name")) or finance_name or name,
                "website": searched_domain,
            }

    # 3) Ticker lookup.
    if token and symbol:
        candidates = [symbol]
        # For some European values, Logo.dev may know the base ticker better.
        if "." in symbol:
            candidates.append(symbol.split(".")[0])

        for ticker_candidate in candidates:
            candidate = f"https://img.logo.dev/ticker/{quote(ticker_candidate)}?token={quote(token)}&size=128&format=png"
            data_uri = vf_fetch_logo_data_uri(candidate)
            if data_uri:
                return {
                    "url": data_uri,
                    "source": "Logo.dev • ticker",
                    "name": finance_name or name,
                    "website": domain or searched_domain,
                }

    # 4) ISIN lookup.
    if token and isin:
        candidate = f"https://img.logo.dev/isin/{quote(isin)}?token={quote(token)}&size=128&format=png"
        data_uri = vf_fetch_logo_data_uri(candidate)
        if data_uri:
            return {
                "url": data_uri,
                "source": "Logo.dev • ISIN",
                "name": finance_name or name,
                "website": domain or searched_domain,
            }

    return {
        "url": "",
        "source": "",
        "name": finance_name or name,
        "website": domain or searched_domain,
    }


def vf_logo_html(symbol, name="", isin="", size=48):
    symbol = _clean_text(symbol, upper=True)
    name = _clean_text(name)
    isin = _clean_text(isin, upper=True)
    brand = vf_company_brand_data(symbol, name, isin)
    url = brand.get("url","")
    initials = "".join([p[:1] for p in (name or symbol or "?").split()[:2]]).upper() or "?"

    if url:
        return (
            f'<div class="vf-logo-shell" style="width:{size}px;height:{size}px;min-width:{size}px">'
            f'<img src="{url}" alt="{symbol or name} logo" />'
            '</div>'
        )

    return (
        f'<div class="vf-logo-shell" style="width:{size}px;height:{size}px;min-width:{size}px">'
        f'<div class="vf-logo-fallback">{initials[:3]}</div>'
        '</div>'
    )


@st.cache_data(ttl=21600, show_spinner=False)
def vf_resolve_identity(symbol="", name="", isin=""):
    symbol = _clean_text(symbol, upper=True)
    name = _clean_text(name)
    isin = _clean_text(isin, upper=True)

    if symbol and symbol not in {"NAN","NONE","NULL","<NA>"}:
        return {
            "symbol": symbol,
            "confidence": 100,
            "source": "Ticker",
            "name": name,
            "isin": isin,
        }

    resolved, confidence, source = resolve_ticker_from_identity(name, isin)
    return {
        "symbol": _clean_text(resolved, upper=True),
        "confidence": int(confidence or 0),
        "source": _clean_text(source),
        "name": name,
        "isin": isin,
    }


def vf_identity_html(symbol, name, isin="", resolve=False):
    symbol = _clean_text(symbol, upper=True)
    name = _clean_text(name)
    isin = _clean_text(isin, upper=True)

    identity = vf_resolve_identity(symbol, name, isin) if resolve else {
        "symbol":symbol,
        "confidence":100 if symbol else 0,
        "source":"Ticker" if symbol else "",
        "name":name,
        "isin":isin
    }

    shown_symbol = identity.get("symbol") or "À RÉSOUDRE"
    brand = vf_company_brand_data(identity.get("symbol"), name, isin)
    shown_name = name or brand.get("name") or shown_symbol
    subtitle = f"ISIN : {isin}" if isin else "ISIN non renseigné"

    resolution = ""
    if not symbol and identity.get("symbol"):
        resolution = (
            f'<div class="vf-resolution-note">Résolu : {identity.get("source")} • '
            f'confiance {identity.get("confidence")}%</div>'
        )
    elif not identity.get("symbol"):
        resolution = '<div class="vf-resolution-note">Instrument à résoudre — fiche assistée disponible.</div>'

    return (
        '<div class="vf-instrument-identity">'
        + vf_logo_html(identity.get("symbol"), shown_name, isin)
        + '<div>'
        + f'<div class="vf-name">{shown_symbol} • {shown_name}</div>'
        + f'<div class="vf-isin">{subtitle}</div>'
        + resolution
        + '<div class="vf-goldline"></div>'
        + '</div></div>'
    )


def open_instrument_identity(symbol="", name="", isin=""):
    symbol = _clean_text(symbol, upper=True)
    name = _clean_text(name)
    isin = _clean_text(isin, upper=True)

    identity = vf_resolve_identity(symbol, name, isin)
    resolved = identity.get("symbol","")

    if resolved:
        st.session_state["instrument_symbol"] = resolved
        st.session_state["instrument_identity_context"] = {
            "name": name,
            "isin": isin,
            "resolution_source": identity.get("source",""),
            "resolution_confidence": identity.get("confidence",0),
        }
        st.session_state.pop("instrument_unresolved", None)
    else:
        st.session_state["instrument_symbol"] = ""
        st.session_state["instrument_unresolved"] = {"name": name, "isin": isin}

    st.session_state["_pending_nav_mode"] = "📊 Instrument"
    st.rerun()


def vf_identity_key(symbol="", name="", isin=""):
    raw = "|".join([
        _clean_text(symbol, upper=True),
        _clean_text(name),
        _clean_text(isin, upper=True)
    ])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]



def vf_board_badge(text, kind="blue"):
    cls = {
        "blue":"vf-blue","green":"vf-green","red":"vf-red",
        "amber":"vf-amber","violet":"vf-violet","muted":"vf-muted-badge"
    }.get(kind,"vf-blue")
    return f'<span class="vf-badge {cls}">{_clean_text(text)}</span>'


def vf_position_card(row, key_prefix="pos"):
    symbol = _clean_text(row.get("Ticker"), upper=True)
    name = _clean_text(row.get("Entreprise") or row.get("Nom complet") or row.get("Nom")) or symbol
    isin = _clean_text(row.get("ISIN"), upper=True)
    value = _vf_num(row.get("Valeur référence"))
    pnl = _vf_num(row.get("P/L latent"))
    pnl_pct = _vf_num(row.get("P/L %"))
    weight = _vf_num(row.get("Poids %"))
    price = _vf_num(row.get("Cours live"))
    if pd.isna(price):
        price = _vf_num(row.get("Prix"))

    with st.container(border=True):
        a,b = st.columns([4.7,1.3])
        with a:
            st.markdown(vf_identity_html(symbol, name, isin), unsafe_allow_html=True)
        with b:
            if pd.notna(weight):
                st.metric("Poids", f"{weight:.1f}%")

        k1,k2,k3 = st.columns(3)
        k1.metric("Valeur", f"{value:,.0f} €" if pd.notna(value) else "—")
        if pd.notna(pnl):
            delta = f"{pnl_pct:+.1f}%" if pd.notna(pnl_pct) else None
            k2.metric("P/L latent", f"{pnl:+,.0f} €", delta=delta)
        else:
            k2.metric("P/L latent", "—")
        k3.metric("Cours", f"{price:.2f}" if pd.notna(price) else "—")

        identity_key = vf_identity_key(symbol, name, isin)
        if st.button("📊 Ouvrir la fiche", key=f"{key_prefix}_{identity_key}", use_container_width=True):
            open_instrument_identity(symbol, name, isin)


def vf_setup_card(row, key_prefix="setup", show_expand=False):
    if hasattr(row, "to_dict"):
        row = row.to_dict()
    symbol = _clean_text(row.get("Ticker") or row.get("symbol"), upper=True)
    name = _clean_text(row.get("Entreprise") or row.get("name")) or symbol
    isin = _clean_text(row.get("ISIN") or row.get("isin"), upper=True)
    score = _vf_num(row.get("Score combiné") if row.get("Score combiné") is not None else row.get("score"))
    upside = _vf_num(row.get("Potentiel %") if row.get("Potentiel %") is not None else row.get("upside"))
    rr = _vf_num(row.get("R/R") if row.get("R/R") is not None else row.get("rr"))
    entry = _vf_num(row.get("Entrée") if row.get("Entrée") is not None else row.get("entry"))
    stop = _vf_num(row.get("Stop") if row.get("Stop") is not None else row.get("stop"))
    tp2 = _vf_num(row.get("TP2") if row.get("TP2") is not None else row.get("tp2"))
    confirmed = _clean_text(row.get("Confirmé 1h") or row.get("confirmed_1h"))
    source = _clean_text(row.get("Source"))
    broker = _clean_text(row.get("Courtier") or row.get("broker"))
    market = _clean_text(row.get("Marché") or row.get("market"))

    with st.container(border=True):
        a,b = st.columns([4.7,1.3])
        with a:
            st.markdown(vf_identity_html(symbol, name, isin), unsafe_allow_html=True)
            badges=[]
            if source == "Découverte Yahoo":
                badges.append(vf_board_badge("Découverte","amber"))
                badges.append(vf_board_badge("Courtier à vérifier","violet"))
            elif source:
                badges.append(vf_board_badge(source,"green"))
            if broker and broker != "À vérifier":
                badges.append(vf_board_badge(broker,"blue"))
            if market:
                badges.append(vf_board_badge(market,"muted"))
            if badges:
                st.markdown("".join(badges), unsafe_allow_html=True)
        with b:
            if pd.notna(score):
                st.metric("Score", f"{score:.1f}/100")
            if confirmed:
                st.caption(f"Confirmation 1H {confirmed}")

        m1,m2,m3 = st.columns(3)
        m1.metric("Potentiel", f"{upside:.1f}%" if pd.notna(upside) else "—")
        m2.metric("R/R", f"{rr:.2f}" if pd.notna(rr) else "—")
        m3.metric("Entrée", f"{entry:.2f}" if pd.notna(entry) else "—")

        m4,m5 = st.columns(2)
        m4.metric("Stop", f"{stop:.2f}" if pd.notna(stop) else "—")
        m5.metric("TP2", f"{tp2:.2f}" if pd.notna(tp2) else "—")

        identity_key = vf_identity_key(symbol, name, isin)
        if st.button("📊 Fiche instrument", key=f"{key_prefix}_{identity_key}", use_container_width=True):
            open_instrument_identity(symbol, name, isin)

        if show_expand and symbol:
            with st.expander("Voir l'analyse détaillée"):
                vf_instrument_sheet(symbol, row)



def show_portfolio_page(account, title, broker: str | None = None):
    try:
        reconcile_orphan_portfolio_data()
    except Exception:
        pass

    vf_page_header(title, f"Portfolio Board — valorisation, allocation, P/L et accès direct aux positions • {broker or 'Tous courtiers'}")
    df=load_positions(account, broker=broker)
    if df.empty:
        try:
            rebuilt = ensure_transaction_positions(account)
            if rebuilt:
                df = load_positions(account, broker=broker)
        except Exception as exc:
            st.warning(f"Les transactions sont présentes mais la reconstruction automatique a échoué : {exc}")
    if df.empty:
        st.info("Aucune position enregistrée. Importe un export depuis « Imports & documents ».")
        return

    totals,m=portfolio_valuation(account,use_live=True, broker=broker)
    m = add_identity_columns(m, "Ticker")

    # KPIs
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Valeur suivie",f"{totals['value']:,.0f} €")
    c2.metric("Coût snapshot",f"{totals['cost']:,.0f} €")
    c3.metric("P/L latent",f"{totals['unrealized']:+,.0f} €")
    c4.metric("Positions",len(df))

    if totals.get("live_value", 0) > 0:
        st.caption(f"Estimation live : {totals['live_value']:,.0f} € — le snapshot courtier reste la référence.")

    vf_section("Vue portefeuille", "Allocation et gains/pertes en un coup d'œil.")
    c_left,c_right=st.columns(2)
    with c_left:
        if "Valeur référence" in m.columns:
            vf_pie(m, "Valeur", "Valeur référence", "Allocation")
    with c_right:
        if "P/L latent" in m.columns:
            vf_signed_bar(m.sort_values("P/L latent").tail(15), "Valeur", "P/L latent", "P/L latent")

    # Top positions as cards
    vf_section("Positions principales", "Lecture visuelle des lignes les plus importantes.")
    view=m.copy()
    if "Valeur référence" in view.columns:
        view["_weight"] = pd.to_numeric(view["Valeur référence"], errors="coerce") / max(float(pd.to_numeric(view["Valeur référence"], errors="coerce").sum()),1) * 100
        view["Poids %"] = view["_weight"]
        view = view.sort_values("Valeur référence", ascending=False, na_position="last")

    for i in range(0, min(len(view), 8), 2):
        cols=st.columns(2)
        for j,col in enumerate(cols):
            idx=i+j
            if idx >= min(len(view),8):
                break
            with col:
                vf_position_card(view.iloc[idx], key_prefix=f"portfolio_{account}_{idx}")

    with st.expander("📋 Toutes les positions"):
        st.dataframe(m,use_container_width=True,hide_index=True)

    st.caption("Le snapshot courtier reste la référence de valorisation ; les cours live sont une estimation séparée.")

def show_transactions_page():
    vf_page_header("💰 Transactions / Ledger", "Flux, frais, taxes et répartition des opérations.")
    account=st.selectbox("Compte", ["Tous","pea","cto_xtb","cto_trade_republic","cto_autre"])
    df=load_transactions(None if account=="Tous" else account)
    if df.empty:
        st.info("Aucune transaction enregistrée.")
        return

    c1,c2,c3=st.columns(3)
    amount=pd.to_numeric(df.get("amount"),errors="coerce") if "amount" in df else pd.Series(dtype=float)
    fees=pd.to_numeric(df.get("fee"),errors="coerce") if "fee" in df else pd.Series(dtype=float)
    taxes=pd.to_numeric(df.get("tax"),errors="coerce") if "tax" in df else pd.Series(dtype=float)
    c1.metric("Flux net importé", f"{amount.sum(skipna=True):+,.2f}")
    c2.metric("Frais", f"{fees.sum(skipna=True):+,.2f}")
    c3.metric("Taxes", f"{taxes.sum(skipna=True):+,.2f}")

    if "type" in df.columns:
        summary=df["type"].fillna("INCONNU").value_counts().rename_axis("Type").reset_index(name="Nombre")
        a,b=st.columns(2)
        with a:
            vf_bar(summary, "Type", "Nombre", "Nombre d'opérations par type")
        with b:
            vf_pie(summary, "Type", "Nombre", "Répartition des opérations")

    st.subheader("Journal détaillé")
    st.dataframe(df,use_container_width=True,hide_index=True)

# ==========================================================
# SIDEBAR / ROUTING — V20
# ==========================================================
_pending_nav = st.session_state.pop("_pending_nav_mode", None)
if _pending_nav:
    st.session_state["nav_mode"] = _pending_nav

if "nav_mode" not in st.session_state:
    st.session_state["nav_mode"] = "🏠 Dashboard"

with st.sidebar:
    st.markdown(
        '<div style="padding:.15rem 0 .65rem">'
        '<div style="font-size:1.28rem;font-weight:950;letter-spacing:-.04em">🔭 VISION FUTURE</div>'
        f'<div style="font-size:.78rem;color:#667085;margin-top:.2rem">{APP_TAGLINE}</div>'
        '</div>',
        unsafe_allow_html=True
    )

    def _nav_button(label, key):
        active = st.session_state.get("nav_mode") == label
        if st.button(
            ("● " if active else "") + label,
            key=key,
            use_container_width=True,
            type="primary" if active else "secondary"
        ):
            st.session_state["_pending_nav_mode"] = label
            st.rerun()

    st.markdown(
        '<div class="vf-agent-callout">'
        '<div class="vf-agent-title">Agent Intelligence</div>'
        '<div class="vf-agent-copy">Surveillance marché, scoring et alertes automatiques.</div>'
        '</div>',
        unsafe_allow_html=True
    )
    _nav_button("🛰️ Agent marché", "nav_agent_top")

    st.markdown('<div class="vf-group-title">Vue d’ensemble</div>', unsafe_allow_html=True)
    _nav_button("🏠 Dashboard", "nav_dashboard")
    _nav_button("⭐ Watchlist", "nav_watchlist")

    st.markdown('<div class="vf-group-title">Portefeuille</div>', unsafe_allow_html=True)
    _nav_button("🏦 PEA", "nav_pea")
    _nav_button("💼 CTO", "nav_cto")
    _nav_button("📈 Performance", "nav_perf")
    _nav_button("⚖️ Arbitrage", "nav_arb")
    _nav_button("💰 Transactions", "nav_tx")

    st.markdown('<div class="vf-group-title">Marché</div>', unsafe_allow_html=True)
    _nav_button("🔎 Scanner", "nav_scanner")
    _nav_button("🛰️ Agent marché", "nav_agent_market")

    st.markdown('<div class="vf-group-title">Analyse</div>', unsafe_allow_html=True)
    _nav_button("📊 Instrument", "nav_instrument")
    _nav_button("📊 Analyse", "nav_analysis")
    _nav_button("🧪 Simulation", "nav_sim")

    st.markdown('<div class="vf-group-title">Gestion</div>', unsafe_allow_html=True)
    _nav_button("📥 Imports & documents", "nav_import")

    st.markdown("---")
    st.markdown('<div class="vf-group-title">Accès rapide</div>', unsafe_allow_html=True)
    _quick_symbol = st.text_input(
        "Ticker rapide",
        placeholder="TSLA, MC.PA…",
        key="sidebar_quick_symbol"
    )
    if st.button("📊 Ouvrir l'instrument", key="sidebar_quick_open", use_container_width=True):
        if _clean_text(_quick_symbol, upper=True):
            open_instrument_identity(_quick_symbol)

    st.markdown("---")
    st.markdown('<div class="vf-group-title">Trading</div>', unsafe_allow_html=True)
    capital = st.number_input("Capital de référence (€)", 100.0, 1_000_000.0, 10_000.0, 100.0)
    risk_pct = st.number_input("Risque par trade (%)", 0.1, 3.0, 0.5, 0.05)
    refresh_min = st.select_slider("Actualisation scanner (min)", [1,2,5,10,15,30,60], value=5)
    auto_refresh = st.checkbox("Actualisation automatique", False)
    if auto_refresh:
        st_autorefresh(interval=refresh_min * 60 * 1000, key="auto_refresh")

    st.markdown("---")
    if SUPABASE is None:
        st.error("Supabase non connecté")
    else:
        st.success("Supabase connecté")

    if st.button("🔒 Déconnexion", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

mode = st.session_state.get("nav_mode", "🏠 Dashboard")

st.caption(f"{APP_SUBTITLE} — {APP_VERSION}")



def _vf_num(value):
    return pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]


def _vf_setup_from_row(row):
    """
    Single source of truth for scanner cards / premium sheet.
    Uses the already-computed scanner values first.
    """
    if row is None:
        return {}
    if hasattr(row, "to_dict"):
        row = row.to_dict()
    row = dict(row)

    mapping = {
        "price": ["Prix", "price"],
        "entry": ["Entrée", "entry"],
        "stop": ["Stop", "stop"],
        "tp1": ["TP1", "tp1"],
        "tp2": ["TP2", "tp2"],
        "upside": ["Potentiel %", "upside"],
        "rr": ["R/R", "rr"],
        "score": ["Score combiné", "Score", "score"],
        "vol_ratio": ["Volume relatif", "vol_ratio"],
        "hourly_score": ["Score 1h", "score_1h"],
        "confirmed_1h": ["Confirmé 1h"],
        "reasons": ["Raisons"],
    }

    out = {}
    for dest, keys in mapping.items():
        for key in keys:
            if key in row and row.get(key) is not None:
                out[dest] = row.get(key)
                break
    return out


def vf_trade_chart(symbol, setup=None, period="6mo", interval="1d"):
    df = history(symbol, period, interval)
    if df is None or df.empty:
        st.info("Historique indisponible.")
        return

    d = df.reset_index().copy()
    date_col = d.columns[0]
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna(subset=[date_col, "Close"])
    if d.empty:
        return

    base = alt.Chart(d).encode(x=alt.X(f"{date_col}:T", title=None))
    price = base.mark_line(strokeWidth=2).encode(
        y=alt.Y("Close:Q", title="Cours", scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip(f"{date_col}:T", title="Date"),
            alt.Tooltip("Close:Q", title="Cours", format=".2f"),
        ]
    )

    layers = [price]
    if setup:
        levels = []
        for label, key in [("Entrée","entry"),("Stop","stop"),("TP1","tp1"),("TP2","tp2")]:
            v = _vf_num(setup.get(key))
            if pd.notna(v):
                levels.append({"Niveau": label, "Prix": float(v)})

        if levels:
            ld = pd.DataFrame(levels)
            rules = alt.Chart(ld).mark_rule(strokeDash=[7,4], strokeWidth=1.5).encode(
                y=alt.Y("Prix:Q"),
                tooltip=[
                    alt.Tooltip("Niveau:N"),
                    alt.Tooltip("Prix:Q", format=".2f")
                ]
            )
            labels = alt.Chart(ld).mark_text(
                align="left", baseline="bottom", dx=8, dy=-2, fontSize=11
            ).encode(
                y="Prix:Q",
                text="Niveau:N"
            )
            layers.extend([rules, labels])

    st.altair_chart(
        alt.layer(*layers).properties(height=300).interactive(),
        use_container_width=True
    )


def vf_instrument_sheet(symbol, row=None):
    """
    Premium instrument sheet.
    IMPORTANT: when opened from the scanner, scanner calculations are authoritative.
    We do not recompute entry/stop/TP/score with a different engine.
    """
    symbol = _clean_text(symbol, upper=True)
    if not symbol:
        return

    if hasattr(row, "to_dict"):
        row = row.to_dict()
    if row is None:
        row = {}
    elif isinstance(row, pd.DataFrame):
        row = row.iloc[0].to_dict() if not row.empty else {}
    elif isinstance(row, pd.Series):
        row = row.to_dict()
    elif not isinstance(row, dict):
        try:
            row = dict(row)
        except Exception:
            row = {}

    q = live_quote(symbol)
    scan_setup = _vf_setup_from_row(row)

    name = _clean_text(row.get("Entreprise") or row.get("name")) or q.get("name", symbol)
    isin = _clean_text(row.get("ISIN") or row.get("isin"), upper=True)
    if not isin:
        _, _, resolved_isin = instrument_identity(symbol, row)
        isin = "" if "NON RENSEIGN" in _clean_text(resolved_isin, upper=True) else resolved_isin

    # Only enrich missing non-strategic metrics from live history.
    enrich = {}
    try:
        hist = history(symbol, "6mo", "1d")
        if hist is not None and not hist.empty:
            tmp = indicators(hist.copy())
            if tmp is not None and not tmp.empty:
                last = tmp.iloc[-1]
                enrich["rsi"] = last.get("RSI")
                enrich["macd"] = last.get("MACD")
                enrich["signal"] = last.get("MACD_SIGNAL")
                enrich["sma20"] = last.get("SMA20")
                enrich["sma50"] = last.get("SMA50")
                enrich["volume"] = last.get("Volume")
    except Exception:
        enrich = {}

    price = _vf_num(scan_setup.get("price"))
    if pd.isna(price):
        price = _vf_num(q.get("price"))

    score = _vf_num(scan_setup.get("score"))
    upside = _vf_num(scan_setup.get("upside"))
    rr = _vf_num(scan_setup.get("rr"))
    vol_ratio = _vf_num(scan_setup.get("vol_ratio"))

    # Premium identity header
    h1,h2 = st.columns([5,2])
    with h1:
        st.markdown(f"### {symbol} • {name}")
        if isin:
            st.caption(f"ISIN : {isin}")
        else:
            st.caption("ISIN non renseigné")
        badges = []
        source = _clean_text(row.get("Source"))
        broker = _clean_text(row.get("Courtier"))
        market = _clean_text(row.get("Marché"))
        if source == "Découverte Yahoo":
            badges.append("Découverte")
            badges.append("Courtier à vérifier")
        elif source:
            badges.append(source)
        if broker and broker != "À vérifier":
            badges.append(broker)
        if market:
            badges.append(market)
        if badges:
            st.caption(" • ".join(badges))
    with h2:
        if pd.notna(score):
            st.metric("Score combiné", f"{float(score):.1f}/100")
        confirmed = _clean_text(scan_setup.get("confirmed_1h"))
        if confirmed:
            st.metric("Confirmation 1H", confirmed)

    # Decision strip
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Cours", f"{float(price):.2f}" if pd.notna(price) else "—")
    c2.metric("Potentiel", f"{float(upside):.1f}%" if pd.notna(upside) else "—")
    c3.metric("R/R", f"{float(rr):.2f}" if pd.notna(rr) else "—")
    c4.metric("RSI", f"{float(enrich.get('rsi')):.0f}" if pd.notna(_vf_num(enrich.get("rsi"))) else "—")
    c5.metric("Volume relatif", f"{float(vol_ratio):.2f}x" if pd.notna(vol_ratio) else "—")

    # Verdict based on exact scanner setup
    st.markdown("#### Verdict VISION FUTURE")
    if pd.notna(score) and pd.notna(upside) and pd.notna(rr):
        if score >= 76 and upside >= 3 and rr >= 2:
            st.success("🟢 Setup techniquement éligible. Le scanner valide les critères principaux ; la confirmation 1H et le contexte actualités restent déterminants.")
        elif score >= 65:
            st.warning("🟠 Setup à surveiller : qualité correcte mais critères d'entrée incomplets.")
        else:
            st.info("⚪ Pas de setup prioritaire selon les règles actuelles.")
    else:
        st.info("Setup scanner incomplet pour cette valeur.")

    # Compact chart
    vf_trade_chart(symbol, scan_setup)

    # Trade plan – authoritative values from scanner
    st.markdown("#### Plan de trade")
    m = st.columns(4)
    for col, label, key in zip(m, ["Entrée","Stop","TP1","TP2"], ["entry","stop","tp1","tp2"]):
        v = _vf_num(scan_setup.get(key))
        col.metric(label, f"{float(v):.2f}" if pd.notna(v) else "—")

    reasons = _clean_text(scan_setup.get("reasons"))
    if reasons:
        st.caption(reasons)

    # Momentum / trend
    st.markdown("#### Momentum & tendance")
    t1,t2,t3 = st.columns(3)
    rsi = _vf_num(enrich.get("rsi"))
    macd = _vf_num(enrich.get("macd"))
    sig = _vf_num(enrich.get("signal"))
    sma20 = _vf_num(enrich.get("sma20"))
    sma50 = _vf_num(enrich.get("sma50"))

    if pd.notna(rsi):
        rsi_txt = "Suracheté" if rsi >= 70 else "Survendu" if rsi <= 30 else "Neutre"
        t1.metric("RSI", f"{rsi:.0f}", rsi_txt)
    else:
        t1.metric("RSI", "—")

    if pd.notna(macd) and pd.notna(sig):
        t2.metric("MACD", f"{macd:.3f}", "Haussier" if macd > sig else "Baissier")
    else:
        t2.metric("MACD", "—")

    if pd.notna(sma20) and pd.notna(sma50):
        t3.metric("Tendance", "Haussière" if sma20 > sma50 else "Baissière", f"SMA20 {sma20:.2f} / SMA50 {sma50:.2f}")
    else:
        t3.metric("Tendance", "—")

    # Free news
    st.markdown("#### Actualités récentes")
    try:
        news = yf.Ticker(symbol).news or []
    except Exception:
        news = []

    shown = 0
    for item in news[:5]:
        content = item.get("content", item) if isinstance(item, dict) else {}
        title = _clean_text(content.get("title"))
        if not title:
            continue
        provider = content.get("provider") or {}
        source = _clean_text(provider.get("displayName") if isinstance(provider, dict) else "")
        pub = _clean_text(content.get("pubDate"))
        st.markdown(f"**{title}**")
        st.caption(" • ".join(x for x in [source, pub] if x))
        shown += 1
    if shown == 0:
        st.caption("Aucune actualité Yahoo disponible actuellement.")




def vf_candlestick_chart(symbol, setup=None, period="6mo", interval="1d"):
    """Candles + volume + trade levels in the premium DA."""
    df = history(symbol, period, interval)
    if df is None or df.empty:
        st.info("Historique indisponible.")
        return

    d = df.reset_index().copy()
    date_col = d.columns[0]
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna(subset=[date_col, "Open", "High", "Low", "Close"])
    if d.empty:
        return

    d["Direction"] = (d["Close"] >= d["Open"]).map({True: "Hausse", False: "Baisse"})

    base = alt.Chart(d).encode(
        x=alt.X(f"{date_col}:T", title=None, axis=alt.Axis(labelAngle=0))
    )

    wick = base.mark_rule().encode(
        y=alt.Y("Low:Q", title="Cours", scale=alt.Scale(zero=False)),
        y2="High:Q",
        tooltip=[
            alt.Tooltip(f"{date_col}:T", title="Date"),
            alt.Tooltip("Open:Q", title="Ouverture", format=".2f"),
            alt.Tooltip("High:Q", title="Plus haut", format=".2f"),
            alt.Tooltip("Low:Q", title="Plus bas", format=".2f"),
            alt.Tooltip("Close:Q", title="Clôture", format=".2f"),
        ]
    )

    body = base.mark_bar(size=5).encode(
        y="Open:Q",
        y2="Close:Q",
        color=alt.Color(
            "Direction:N",
            scale=alt.Scale(domain=["Hausse","Baisse"]),
            legend=None
        )
    )

    layers = [wick, body]

    if setup:
        levels = []
        for label, key in [("Entrée","entry"),("Stop","stop"),("TP1","tp1"),("TP2","tp2")]:
            v = _vf_num(setup.get(key))
            if pd.notna(v):
                levels.append({"Niveau": label, "Prix": float(v)})
        if levels:
            ld = pd.DataFrame(levels)
            layers.append(
                alt.Chart(ld).mark_rule(strokeDash=[7,4], strokeWidth=1.6).encode(
                    y="Prix:Q",
                    tooltip=["Niveau:N", alt.Tooltip("Prix:Q", format=".2f")]
                )
            )
            layers.append(
                alt.Chart(ld).mark_text(
                    align="left", dx=8, dy=-4, fontWeight="bold", fontSize=11
                ).encode(y="Prix:Q", text="Niveau:N")
            )

    st.altair_chart(
        alt.layer(*layers).properties(height=390).interactive(),
        use_container_width=True
    )

    if "Volume" in d.columns:
        vol = alt.Chart(d).mark_bar().encode(
            x=alt.X(f"{date_col}:T", title=None),
            y=alt.Y("Volume:Q", title="Volume"),
            tooltip=[
                alt.Tooltip(f"{date_col}:T", title="Date"),
                alt.Tooltip("Volume:Q", title="Volume", format=",")
            ]
        ).properties(height=120)
        st.altair_chart(vol, use_container_width=True)


def vf_fundamentals(symbol):
    """Best-effort fundamentals from yfinance. Missing data stays missing."""
    try:
        info = yf.Ticker(symbol).info or {}
    except Exception:
        info = {}

    return {
        "market_cap": info.get("marketCap"),
        "pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "dividend_yield": info.get("dividendYield"),
        "beta": info.get("beta"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "country": info.get("country"),
        "currency": info.get("currency"),
        "target_mean": info.get("targetMeanPrice"),
        "recommendation": info.get("recommendationKey"),
        "profit_margin": info.get("profitMargins"),
        "revenue_growth": info.get("revenueGrowth"),
    }


def vf_fmt_large_number(v):
    n = _vf_num(v)
    if pd.isna(n):
        return "—"
    n = float(n)
    if abs(n) >= 1_000_000_000_000:
        return f"{n/1_000_000_000_000:.2f} T"
    if abs(n) >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f} Md"
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:.1f} M"
    return f"{n:,.0f}"


def vf_full_instrument_page(symbol, row=None):
    """Full-screen visual command center for one instrument."""
    symbol = _clean_text(symbol, upper=True)
    if not symbol:
        st.warning("Aucune valeur sélectionnée.")
        return

    if row is None:
        row = {}
    elif isinstance(row, pd.Series):
        row = row.to_dict()
    elif isinstance(row, pd.DataFrame):
        row = row.iloc[0].to_dict() if not row.empty else {}
    elif not isinstance(row, dict):
        try:
            row = dict(row)
        except Exception:
            row = {}

    scan_setup = _vf_setup_from_row(row)
    quote = live_quote(symbol)
    fundamentals = vf_fundamentals(symbol)

    # If the instrument page was opened from the universal selector,
    # the row usually contains identity metadata only and no scanner setup.
    # In that case, compute the SAME daily/hourly setup engine live.
    required_setup_keys = ["entry", "stop", "tp1", "tp2", "upside", "rr", "score"]
    missing_setup = any(pd.isna(_vf_num(scan_setup.get(k))) for k in required_setup_keys)

    if missing_setup:
        try:
            daily_setup = trade_setup(history(symbol, "6mo", "1d"))
        except Exception:
            daily_setup = None

        if daily_setup:
            live_setup = dict(daily_setup)

            # Same 1H confirmation logic as fast_scan()
            try:
                hourly_setup = trade_setup(history(symbol, "3mo", "1h"))
            except Exception:
                hourly_setup = None

            if hourly_setup:
                conf_score = hourly_setup.get("score")
                trend_ok = bool(
                    hourly_setup.get("score", 0) >= 65
                    and hourly_setup.get("rr", 0) >= 1.5
                )
                live_setup["hourly_score"] = conf_score
                live_setup["confirmed_1h"] = "✅" if trend_ok else "⚠️"
                live_setup["score"] = round(
                    0.65 * float(daily_setup.get("score", 0))
                    + 0.35 * float(conf_score),
                    1
                )
            else:
                live_setup["confirmed_1h"] = "⚠️"

            if isinstance(live_setup.get("reasons"), list):
                live_setup["reasons"] = " • ".join(live_setup["reasons"])

            # Existing scanner values remain authoritative if present.
            for k, v in live_setup.items():
                current = scan_setup.get(k)
                if k in {"confirmed_1h", "reasons"}:
                    if not current:
                        scan_setup[k] = v
                else:
                    if current is None or pd.isna(_vf_num(current)):
                        scan_setup[k] = v

    name = _clean_text(row.get("Entreprise") or row.get("name")) or quote.get("name", symbol)
    isin = _clean_text(row.get("ISIN") or row.get("isin"), upper=True)
    if not isin:
        _, _, resolved_isin = instrument_identity(symbol, row)
        isin = "" if "NON RENSEIGN" in _clean_text(resolved_isin, upper=True) else resolved_isin

    # Header
    left, right = st.columns([5,2])
    with left:
        st.markdown('<div class="vf-eyebrow">INSTRUMENT BOARD</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="vf-instrument-identity">'
            + vf_logo_html(symbol, name, isin, size=56)
            + '<div>'
            + f'<div style="font-size:1.9rem;font-weight:900;letter-spacing:-.04em;color:#111827">{symbol} • {name}</div>'
            + '<div class="vf-goldline"></div>'
            + '</div></div>',
            unsafe_allow_html=True
        )
        meta = []
        if isin:
            meta.append(f"ISIN {isin}")
        if fundamentals.get("sector"):
            meta.append(str(fundamentals.get("sector")))
        if fundamentals.get("country"):
            meta.append(str(fundamentals.get("country")))
        if fundamentals.get("currency"):
            meta.append(str(fundamentals.get("currency")))
        st.caption(" • ".join(meta) if meta else "Instrument")
        st.markdown(
            '<div class="vf-future-strip">'
            '<div class="vf-future-strip-title">Vision Future</div>'
            '<div class="vf-future-strip-text">Build the Future of Your Capital — lecture technique, risque et potentiel réunis dans une seule fiche.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        badge_parts=[]
        if _clean_text(row.get("Source")):
            badge_parts.append(vf_board_badge(_clean_text(row.get("Source")),"blue"))
        if _clean_text(row.get("Courtier")):
            badge_parts.append(vf_board_badge(_clean_text(row.get("Courtier")),"green"))
        if badge_parts:
            st.markdown("".join(badge_parts), unsafe_allow_html=True)
        vf_instrument_watch_controls(symbol)
    with right:
        score = _vf_num(scan_setup.get("score"))
        if pd.notna(score):
            st.metric("Score VISION FUTURE", f"{score:.1f}/100")
        confirm = _clean_text(scan_setup.get("confirmed_1h"))
        if confirm:
            st.metric("Confirmation 1H", confirm)

    # Main decision KPIs
    k = st.columns(6)
    price = _vf_num(scan_setup.get("price"))
    if pd.isna(price):
        price = _vf_num(quote.get("price"))
    values = [
        ("Cours", price, ""),
        ("Entrée", _vf_num(scan_setup.get("entry")), ""),
        ("Stop", _vf_num(scan_setup.get("stop")), ""),
        ("TP2", _vf_num(scan_setup.get("tp2")), ""),
        ("Potentiel", _vf_num(scan_setup.get("upside")), "%"),
        ("R/R", _vf_num(scan_setup.get("rr")), ""),
    ]
    for col,(label,val,suffix) in zip(k, values):
        col.metric(label, f"{float(val):.2f}{suffix}" if pd.notna(val) else "—")

    owned = vf_position_context(symbol)
    if owned:
        vf_section("Position détenue","Contexte portefeuille relié à cette valeur.")
        for pos_ctx in owned:
            pc1,pc2,pc3,pc4 = st.columns(4)
            pc1.metric("Compte",pos_ctx["account"])
            pc2.metric("Quantité",f"{pos_ctx['qty']:.4f}" if pd.notna(pos_ctx["qty"]) else "—")
            pc3.metric("Valeur",f"{pos_ctx['value']:,.0f} €" if pd.notna(pos_ctx["value"]) else "—")
            pc4.metric("P/L",f"{pos_ctx['pnl_pct']:+.1f}%" if pd.notna(pos_ctx["pnl_pct"]) else "—")

    # Verdict
    score = _vf_num(scan_setup.get("score"))
    upside = _vf_num(scan_setup.get("upside"))
    rr = _vf_num(scan_setup.get("rr"))
    if pd.notna(score) and pd.notna(upside) and pd.notna(rr):
        if score >= 76 and upside >= 3 and rr >= 2:
            st.success("🟢 SETUP ÉLIGIBLE — critères techniques principaux validés.")
        elif score >= 65:
            st.warning("🟠 WATCHLIST — setup intéressant mais incomplet.")
        else:
            st.info("⚪ PAS PRIORITAIRE — critères d'entrée insuffisants.")
    else:
        st.info("Analyse technique indisponible ou historique insuffisant pour cette valeur.")

    vf_section("Décision & risque","Lecture compacte du setup et dimensionnement théorique du risque.")
    dleft,dright = st.columns([1.1,1])
    with dleft:
        vf_compact_decision_panel(symbol, scan_setup)
    with dright:
        sizing = vf_trade_sizing(scan_setup, capital, risk_pct)
        with st.container(border=True):
            st.markdown("**Dimensionnement du risque**")
            if sizing:
                s1,s2 = st.columns(2)
                s1.metric("Risque max",f"{sizing['risk_amount']:.0f} €")
                s2.metric("Stop",f"{sizing['stop_pct']:.2f}%")
                s3,s4 = st.columns(2)
                s3.metric("Quantité théorique",f"{sizing['qty']}")
                s4.metric("Capital mobilisé",f"{sizing['capital_needed']:.0f} €")
                st.caption(f"Basé sur {risk_pct:.2f}% de risque pour un capital de référence de {capital:,.0f} €.")
            else:
                st.caption("Dimensionnement indisponible : niveaux entrée/stop insuffisants.")

    vf_section("Trade Terminal","Synthèse immédiate du setup.")
    tcols=st.columns(4)
    terminal_values=[
        ("Entrée",_vf_num(scan_setup.get("entry"))),
        ("Stop",_vf_num(scan_setup.get("stop"))),
        ("TP1",_vf_num(scan_setup.get("tp1"))),
        ("TP2",_vf_num(scan_setup.get("tp2"))),
    ]
    for c,(lab,val) in zip(tcols,terminal_values):
        c.metric(lab,f"{val:.2f}" if pd.notna(val) else "—")

    # Tabs in the same visual language
    tab_chart, tab_momentum, tab_funda, tab_news, tab_plan = st.tabs(
        ["📈 Graphique", "⚡ Momentum", "🏢 Fondamentaux", "📰 Actualités", "🎯 Plan de trade"]
    )

    with tab_chart:
        p1,p2,p3 = st.columns([1,1,4])
        period = p1.selectbox("Période", ["3mo","6mo","1y","2y"], index=1, key=f"period_{symbol}")
        interval = p2.selectbox("Unité", ["1d","1h"], index=0, key=f"interval_{symbol}")
        with p3:
            st.caption("Chandeliers, volumes et niveaux du setup.")
        vf_candlestick_chart(symbol, scan_setup, period=period, interval=interval)

    with tab_momentum:
        try:
            hist = history(symbol, "6mo", "1d")
            ind = indicators(hist.copy()) if hist is not None and not hist.empty else None
        except Exception:
            ind = None

        if ind is None or ind.empty:
            st.info("Indicateurs indisponibles.")
        else:
            last = ind.iloc[-1]
            rsi = _vf_num(last.get("RSI"))
            macd = _vf_num(last.get("MACD"))
            sig = _vf_num(last.get("MACD_SIGNAL"))
            sma20 = _vf_num(last.get("SMA20"))
            sma50 = _vf_num(last.get("SMA50"))

            m1,m2,m3,m4 = st.columns(4)
            m1.metric("RSI", f"{rsi:.0f}" if pd.notna(rsi) else "—")
            if pd.notna(macd) and pd.notna(sig):
                m2.metric("MACD", f"{macd:.3f}", "Haussier" if macd > sig else "Baissier")
            else:
                m2.metric("MACD", "—")
            m3.metric("SMA20", f"{sma20:.2f}" if pd.notna(sma20) else "—")
            m4.metric("SMA50", f"{sma50:.2f}" if pd.notna(sma50) else "—")

            if "RSI" in ind.columns:
                dd = ind.reset_index()
                xcol = dd.columns[0]
                rsi_chart = alt.Chart(dd.dropna(subset=["RSI"])).mark_line().encode(
                    x=alt.X(f"{xcol}:T", title=None),
                    y=alt.Y("RSI:Q", title="RSI", scale=alt.Scale(domain=[0,100])),
                    tooltip=[alt.Tooltip(f"{xcol}:T"), alt.Tooltip("RSI:Q", format=".1f")]
                ).properties(height=220)
                st.altair_chart(rsi_chart, use_container_width=True)

    with tab_funda:
        a,b,c,d = st.columns(4)
        a.metric("Capitalisation", vf_fmt_large_number(fundamentals.get("market_cap")))
        b.metric("PER", f"{_vf_num(fundamentals.get('pe')):.1f}" if pd.notna(_vf_num(fundamentals.get("pe"))) else "—")
        c.metric("PER forward", f"{_vf_num(fundamentals.get('forward_pe')):.1f}" if pd.notna(_vf_num(fundamentals.get("forward_pe"))) else "—")
        dy = _vf_num(fundamentals.get("dividend_yield"))
        d.metric("Rendement dividende", f"{dy*100:.2f}%" if pd.notna(dy) else "—")

        e,f,g,h = st.columns(4)
        beta = _vf_num(fundamentals.get("beta"))
        margin = _vf_num(fundamentals.get("profit_margin"))
        growth = _vf_num(fundamentals.get("revenue_growth"))
        target = _vf_num(fundamentals.get("target_mean"))
        e.metric("Beta", f"{beta:.2f}" if pd.notna(beta) else "—")
        f.metric("Marge nette", f"{margin*100:.1f}%" if pd.notna(margin) else "—")
        g.metric("Croissance CA", f"{growth*100:.1f}%" if pd.notna(growth) else "—")
        h.metric("Objectif analystes", f"{target:.2f}" if pd.notna(target) else "—")

        st.caption(
            "Données fondamentales best-effort via Yahoo Finance. "
            "Les champs absents restent volontairement vides."
        )

    with tab_news:
        try:
            news = yf.Ticker(symbol).news or []
        except Exception:
            news = []

        if not news:
            st.info("Aucune actualité Yahoo disponible actuellement.")
        else:
            for item in news[:8]:
                content = item.get("content", item) if isinstance(item, dict) else {}
                title = _clean_text(content.get("title"))
                if not title:
                    continue
                provider = content.get("provider") or {}
                source = _clean_text(provider.get("displayName") if isinstance(provider, dict) else "")
                pub = _clean_text(content.get("pubDate"))
                summary = _clean_text(content.get("summary") or content.get("description"))
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    if summary:
                        st.write(summary[:500])
                    st.caption(" • ".join(x for x in [source, pub] if x))

    with tab_plan:
        p = st.columns(4)
        for col,label,key in zip(p,["Entrée","Stop","TP1","TP2"],["entry","stop","tp1","tp2"]):
            v = _vf_num(scan_setup.get(key))
            col.metric(label, f"{v:.2f}" if pd.notna(v) else "—")

        reasons = _clean_text(scan_setup.get("reasons"))
        if reasons:
            st.markdown("**Lecture technique**")
            st.write(reasons)

        st.markdown("**Discipline de risque**")
        st.caption(
            "Le plan affiche des niveaux techniques issus du moteur. "
            "Il ne constitue pas une garantie de performance et doit rester compatible "
            "avec la taille de position et le risque accepté."
        )




def vf_section(title, subtitle=""):
    st.markdown(f'<div class="vf-section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="vf-section-sub">{subtitle}</div>', unsafe_allow_html=True)


def vf_nav_button(label, target, key):
    if st.button(label, key=key, use_container_width=True):
        st.session_state["_pending_nav_mode"] = target
        st.rerun()


def vf_alert_chip(alert_type):
    t = _clean_text(alert_type, upper=True)
    if t == "ENTRY":
        cls = "vf-chip-entry"
    elif t in {"EXIT", "TAKE_PROFIT"}:
        cls = "vf-chip-exit"
    elif t in {"RISK","PROTECT","INVALIDATED","NEWS_RISK"}:
        cls = "vf-chip-risk"
    else:
        cls = "vf-chip-info"
    return f'<span class="vf-chip {cls}">{t or "ALERTE"}</span>'



def vf_global_topbar():
    html = (
        '<div class="vf-topbar" style="padding:15px 18px">'
        '<div>'
        '<div class="vf-brand">VISION FUTURE</div>'
        '<div class="vf-brand-sub">DES IDÉES AU PATRIMOINE • CAPITAL INTELLIGENCE</div>'
        '</div>'
        '<div class="vf-topbar-right">'
        + vf_board_badge("VISION","blue")
        + vf_board_badge("MOMENTUM","violet")
        + vf_board_badge("CONVICTION","amber")
        + '</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def vf_watchlist_from_alerts(limit=6):
    alerts = load_market_alerts(limit=100)
    if alerts is None or alerts.empty:
        return pd.DataFrame()
    df = alerts.copy()
    for c in ["score","upside","rr"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "alert_type" in df.columns:
        df = df[df["alert_type"]=="ENTRY"]
    if df.empty:
        return df
    sort_cols=[c for c in ["score","upside","rr"] if c in df.columns]
    if sort_cols:
        df=df.sort_values(sort_cols, ascending=False, na_position="last")
    return df.drop_duplicates(subset=["symbol"]).head(limit)


def vf_portfolio_risk_board(limit=6):
    try:
        chunks=[]
        for acc in ["pea","cto_xtb","cto_trade_republic"]:
            _,m=portfolio_valuation(acc,use_live=False)
            if m is not None and not m.empty:
                mm=m.copy()
                mm["account"]=acc
                chunks.append(mm)
        if not chunks:
            return pd.DataFrame()
        df=pd.concat(chunks, ignore_index=True, sort=False)
        if "P/L %" in df.columns:
            df["P/L %"]=pd.to_numeric(df["P/L %"], errors="coerce")
            return df.sort_values("P/L %", ascending=True, na_position="last").head(limit)
        return df.head(limit)
    except Exception:
        return pd.DataFrame()




def vf_market_pulse():
    runs = load_agent_runs(5)
    if runs is None or runs.empty:
        return {"status":"—","regime":"—","regime_score":"—","universe":"—","confirmed":"—","created":"—"}
    latest = runs.iloc[0]
    details = parse_agent_details(latest.get("details"))
    raw = details.get("REGIME","—")
    regime = raw
    regime_score = "—"
    m = re.match(r"^([A-Z_]+)\(([^)]+)\)$", str(raw))
    if m:
        regime, regime_score = m.group(1), m.group(2)
    return {
        "status": _clean_text(latest.get("status")) or "—",
        "regime": regime,
        "regime_score": regime_score,
        "universe": details.get("UNIVERSE","—"),
        "confirmed": details.get("CONFIRMED","—"),
        "created": int(latest.get("created_alerts") or 0),
    }


def vf_trade_sizing(setup, capital_value, risk_pct_value):
    entry = _vf_num(setup.get("entry"))
    stop = _vf_num(setup.get("stop"))
    if pd.isna(entry) or pd.isna(stop) or entry <= 0 or entry <= stop:
        return {}
    risk_amount = float(capital_value) * float(risk_pct_value) / 100.0
    risk_per_share = float(entry - stop)
    qty = int(max(risk_amount // risk_per_share, 0))
    capital_needed = qty * float(entry)
    stop_pct = (risk_per_share / float(entry)) * 100
    return {
        "risk_amount": risk_amount,
        "risk_per_share": risk_per_share,
        "qty": qty,
        "capital_needed": capital_needed,
        "stop_pct": stop_pct,
    }


def vf_compact_decision_panel(symbol, setup):
    score = _vf_num(setup.get("score"))
    upside = _vf_num(setup.get("upside"))
    rr = _vf_num(setup.get("rr"))
    confirmed = _clean_text(setup.get("confirmed_1h"))

    if pd.notna(score) and pd.notna(upside) and pd.notna(rr):
        if score >= 76 and upside >= 3 and rr >= 2 and confirmed == "✅":
            kind, title, text = "green", "SETUP VALIDÉ", "Critères principaux + confirmation 1H validés."
        elif score >= 76 and upside >= 3 and rr >= 2:
            kind, title, text = "amber", "SETUP À CONFIRMER", "Critères journaliers valides, confirmation 1H insuffisante."
        elif score >= 65:
            kind, title, text = "amber", "WATCHLIST", "Configuration intéressante mais encore incomplète."
        else:
            kind, title, text = "muted", "PAS PRIORITAIRE", "Le setup ne passe pas les seuils actuels."
    else:
        kind, title, text = "muted", "DONNÉES INCOMPLÈTES", "Impossible de valider le setup avec les données disponibles."

    st.markdown(
        '<div class="vf-command-card">'
        f'<div class="vf-command-title">Décision VISION FUTURE</div>'
        f'<div class="vf-command-value">{title}</div>'
        f'<div class="vf-command-note">{text}</div>'
        f'<div style="margin-top:8px">{vf_board_badge(symbol, kind)}</div>'
        '</div>',
        unsafe_allow_html=True
    )




def vf_watchlist_get():
    return st.session_state.setdefault("vf_watchlist", [])


def vf_watchlist_add(symbol):
    symbol = _clean_text(symbol, upper=True)
    if not symbol:
        return
    wl = vf_watchlist_get()
    if symbol not in wl:
        wl.append(symbol)
        st.session_state["vf_watchlist"] = wl


def vf_watchlist_remove(symbol):
    symbol = _clean_text(symbol, upper=True)
    wl = [x for x in vf_watchlist_get() if x != symbol]
    st.session_state["vf_watchlist"] = wl


def vf_position_context(symbol):
    symbol = _clean_text(symbol, upper=True)
    found = []
    for acc,label in [("pea","PEA"),("cto_xtb","CTO XTB"),("cto_trade_republic","CTO Trade Republic"),("cto_autre","CTO autre")]:
        try:
            _,df = portfolio_valuation(acc,use_live=False)
        except Exception:
            df = pd.DataFrame()
        if df is None or df.empty:
            continue
        if "Ticker" not in df.columns:
            continue
        hit = df[df["Ticker"].astype(str).str.upper() == symbol]
        if hit.empty:
            continue
        for _,r in hit.iterrows():
            found.append({
                "account":label,
                "qty":_vf_num(r.get("Quantité") if r.get("Quantité") is not None else r.get("quantity")),
                "value":_vf_num(r.get("Valeur référence")),
                "pnl":_vf_num(r.get("P/L latent")),
                "pnl_pct":_vf_num(r.get("P/L %")),
                "pru":_vf_num(r.get("PRU") if r.get("PRU") is not None else r.get("pru")),
            })
    return found


def vf_instrument_watch_controls(symbol):
    wl = vf_watchlist_get()
    if symbol in wl:
        if st.button("★ Retirer de la watchlist", key=f"watch_remove_{symbol}", use_container_width=True):
            vf_watchlist_remove(symbol)
            st.rerun()
    else:
        if st.button("☆ Ajouter à la watchlist", key=f"watch_add_{symbol}", use_container_width=True):
            vf_watchlist_add(symbol)
            st.rerun()


def vf_watchlist_board():
    wl = vf_watchlist_get()
    if not wl:
        st.info("Watchlist vide. Ajoute une valeur depuis une fiche Instrument.")
        return
    for symbol in wl[:12]:
        try:
            q = live_quote(symbol)
            setup = trade_setup(history(symbol,"6mo","1d")) or {}
        except Exception:
            q,setup = {},{}
        name = _clean_text(q.get("name")) or symbol
        score = _vf_num(setup.get("score"))
        upside = _vf_num(setup.get("upside"))
        rr = _vf_num(setup.get("rr"))
        with st.container(border=True):
            a,b = st.columns([4,1.2])
            with a:
                st.markdown(vf_identity_html(symbol, name, ""), unsafe_allow_html=True)
                meta=[]
                if pd.notna(score): meta.append(f"Score {score:.0f}")
                if pd.notna(upside): meta.append(f"Potentiel {upside:.1f}%")
                if pd.notna(rr): meta.append(f"R/R {rr:.2f}")
                if meta: st.caption(" • ".join(meta))
            with b:
                if st.button("📊 Ouvrir", key=f"watch_open_{symbol}", use_container_width=True):
                    open_instrument_identity(symbol, name, "")
            if st.button("Retirer", key=f"watch_delete_{symbol}", use_container_width=True):
                vf_watchlist_remove(symbol)
                st.rerun()




def vf_editorial_level(index, title, copy):
    st.markdown(
        '<div class="vf-editorial-level">'
        '<div class="vf-editorial-level-head">'
        f'<div class="vf-editorial-index">{index}</div>'
        f'<div class="vf-editorial-title">{title}</div>'
        '</div>'
        f'<div class="vf-editorial-copy">{copy}</div>'
        '</div>',
        unsafe_allow_html=True
    )



def vf_dashboard_command_center():
    vf_page_header(
        "Build the Future of Your Capital",
        "Des insights d’aujourd’hui. Un patrimoine pour demain."
    )
    st.markdown(
        '<div class="vf-future-strip">'
        '<div class="vf-future-strip-title">VISION FUTURE</div>'
        '<div class="vf-future-strip-text">Plus loin que les marchés. Une vision.</div>'
        '<div class="vf-brand-line"></div>'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="vf-future-strip">'
        '<div class="vf-future-strip-title">Vision • Momentum • Growth</div>'
        '<div class="vf-future-strip-text">Build the Future of Your Capital — Vision, Conviction, Precision et Capital Intelligence au service de vos décisions.</div>'
        '</div>',
        unsafe_allow_html=True
    )

    accounts=[("pea","PEA"),("cto_xtb","CTO XTB"),("cto_trade_republic","CTO Trade Republic")]
    cards=[]
    total_value=0.0
    total_unrealized=0.0
    total_positions=0
    for acc,label in accounts:
        try:
            val,pos=portfolio_valuation(acc,use_live=False)
            value=float(val.get("value",0) or 0)
            unrealized=float(val.get("unrealized",0) or 0)
            pcount=len(pos) if pos is not None else 0
        except Exception:
            value=unrealized=0.0
            pcount=0
        total_value += value
        total_unrealized += unrealized
        total_positions += pcount
        cards.append({"Compte":label,"Valeur":value,"P/L latent":unrealized,"Positions":pcount})

    alerts=load_market_alerts(limit=100)
    entries=0
    risks=0
    if alerts is not None and not alerts.empty and "alert_type" in alerts.columns:
        entries=int((alerts["alert_type"]=="ENTRY").sum())
        risks=int(alerts["alert_type"].isin(["EXIT","RISK","PROTECT","INVALIDATED","NEWS_RISK"]).sum())

    pulse=vf_market_pulse()
    watch_count=len(vf_watchlist_get())

    st.markdown(
        '<div class="vf-cardline"><div class="vf-cardtitle">Build the Future of Your Capital</div>'
        '<div class="vf-cardnote">Une interface pensée pour la progression, la lisibilité et la prise de décision rapide : vision, opportunités, risque et croissance du capital.</div></div>',
        unsafe_allow_html=True
    )

    vf_editorial_level(
        "01",
        "Pilotage",
        "Une vision claire de votre situation, pour des décisions plus sereines."
    )

    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("Patrimoine suivi",f"{total_value:,.0f} €",f"{total_positions} position(s)")
    c2.metric("P/L latent",f"{total_unrealized:+,.0f} €")
    c3.metric("Opportunités",entries)
    c4.metric("Alertes risque",risks)
    c5.metric("Watchlist",watch_count)

    vf_section("Agent Intelligence","L'agent reste un module central et accessible directement depuis cette vue.")
    ai1,ai2 = st.columns([4,1])
    with ai1:
        st.caption("Scanner autonome • régime de marché • validation multi-timeframe • alertes ENTRY / PROTECT / EXIT.")
    with ai2:
        vf_nav_button("🛰️ Ouvrir l'Agent","🛰️ Agent marché","v20_open_agent")

    vf_section("Market Pulse","Dernier cycle de l'agent.")
    p1,p2,p3,p4,p5=st.columns(5)
    p1.metric("Agent",pulse["status"])
    p2.metric("Régime",pulse["regime"],pulse["regime_score"])
    p3.metric("Univers",pulse["universe"])
    p4.metric("Confirmés",pulse["confirmed"])
    p5.metric("Alertes créées",pulse["created"])

    vf_section("Accès rapide","Navigation opérationnelle.")
    q1,q2,q3,q4,q5=st.columns(5)
    with q1: vf_nav_button("⚡ Scanner","🔎 Scanner","v15_q_scan")
    with q2: vf_nav_button("🛰️ Agent","🛰️ Agent marché","v15_q_agent")
    with q3: vf_nav_button("📊 Instrument","📊 Instrument","v15_q_instr")
    with q4: vf_nav_button("⚖️ Arbitrage","⚖️ Arbitrage","v15_q_arb")
    with q5: vf_nav_button("📈 Performance","📈 Performance","v15_q_perf")

    vf_editorial_level(
        "02",
        "Opportunités",
        "Accéder aux meilleures idées d’investissement, au bon moment."
    )

    left,right=st.columns([1.25,1])

    with left:
        vf_section("Top opportunités","Les meilleurs ENTRY actuellement visibles.")
        watch=vf_watchlist_from_alerts(6)
        if watch is None or watch.empty:
            st.info("Aucune opportunité ENTRY active.")
        else:
            for i in range(0,len(watch),2):
                cols=st.columns(2)
                for j,col in enumerate(cols):
                    idx=i+j
                    if idx>=len(watch): break
                    with col:
                        r=watch.iloc[idx].to_dict()
                        r.update({
                            "Ticker":r.get("symbol"),
                            "Entreprise":r.get("name"),
                            "ISIN":r.get("isin"),
                            "Score combiné":r.get("score"),
                            "Potentiel %":r.get("upside"),
                            "R/R":r.get("rr"),
                            "Entrée":r.get("entry"),
                            "Stop":r.get("stop"),
                            "TP2":r.get("tp2"),
                        })
                        vf_setup_card(r,key_prefix=f"v15_dash_top_{idx}")

    with right:
        vf_section("Watchlist","Valeurs suivies manuellement.")
        vf_watchlist_board()

    vf_section("Risques portefeuille","Lignes les plus fragiles selon le P/L courant.")
    risk=vf_portfolio_risk_board(6)
    if risk is None or risk.empty:
        st.info("Aucune donnée de risque disponible.")
    else:
        cols=st.columns(3)
        for i,(_,r) in enumerate(risk.iterrows()):
            with cols[i % 3]:
                symbol=_clean_text(r.get("Ticker"),upper=True)
                name=_clean_text(r.get("Entreprise") or r.get("Nom")) or symbol
                pnl_pct=_vf_num(r.get("P/L %"))
                value=_vf_num(r.get("Valeur référence"))
                with st.container(border=True):
                    st.markdown(vf_identity_html(symbol, name, _clean_text(r.get("ISIN"), upper=True)), unsafe_allow_html=True)
                    st.metric("P/L",f"{pnl_pct:+.1f}%" if pd.notna(pnl_pct) else "—")
                    if pd.notna(value):
                        st.caption(f"Valeur : {value:,.0f} €")
                    if st.button("📊 Fiche",key=f"v19_risk_{vf_identity_key(symbol, name, _clean_text(r.get('ISIN'), upper=True))}",use_container_width=True):
                        open_instrument_identity(symbol, name, _clean_text(r.get("ISIN"), upper=True))

    vf_editorial_level(
        "03",
        "Croissance du capital",
        "Bâtir un patrimoine durable dans un monde en mouvement."
    )

    vf_section("Allocation","Répartition des comptes et contribution au P/L.")
    d=pd.DataFrame(cards)
    a,b=st.columns(2)
    with a: vf_pie(d,"Compte","Valeur","Allocation")
    with b: vf_signed_bar(d,"Compte","P/L latent","P/L latent")


@st.cache_data(ttl=900, show_spinner=False)
def vf_analysis_universe():
    rows = []

    for acc in ["pea","cto_xtb","cto_trade_republic","cto_autre"]:
        try:
            df = load_positions(acc)
        except Exception:
            df = pd.DataFrame()
        if df is None or df.empty:
            continue
        for _, r in df.iterrows():
            symbol = _clean_text(r.get("ticker") or r.get("Ticker"), upper=True)
            name = _clean_text(r.get("name") or r.get("Entreprise") or r.get("Nom"))
            isin = _clean_text(r.get("isin") or r.get("ISIN"), upper=True)
            if symbol:
                rows.append({"symbol":symbol,"name":name or symbol,"isin":isin,"source":"Portefeuille"})

    try:
        bu = load_broker_universe()
    except Exception:
        bu = pd.DataFrame()
    if bu is not None and not bu.empty:
        for _, r in bu.iterrows():
            symbol = _clean_text(r.get("symbol"), upper=True)
            if symbol:
                rows.append({
                    "symbol":symbol,
                    "name":_clean_text(r.get("name")) or symbol,
                    "isin":_clean_text(r.get("isin"), upper=True),
                    "source":"Référentiel"
                })

    try:
        disc = discover_yahoo_equities(list(YF_DISCOVERY_REGIONS.keys()), max_per_region=20)
    except Exception:
        disc = pd.DataFrame()
    if disc is not None and not disc.empty:
        for _, r in disc.iterrows():
            symbol = _clean_text(r.get("symbol"), upper=True)
            if symbol:
                rows.append({
                    "symbol":symbol,
                    "name":_clean_text(r.get("name")) or symbol,
                    "isin":_clean_text(r.get("isin"), upper=True),
                    "source":"Découverte"
                })

    if not rows:
        return pd.DataFrame(columns=["symbol","name","isin","source"])

    out = pd.DataFrame(rows)
    out["_prio"] = out["source"].map({"Portefeuille":0,"Référentiel":1,"Découverte":2}).fillna(3)
    out = out.sort_values("_prio").drop_duplicates("symbol").drop(columns="_prio")
    return out.reset_index(drop=True)


@st.cache_data(ttl=600, show_spinner=False)
def vf_yahoo_search_instruments(query, limit=12):
    query = _clean_text(query)
    if len(query) < 2:
        return pd.DataFrame(columns=["symbol","name","isin","source"])

    try:
        search = yf.Search(query, max_results=limit)
        quotes = getattr(search, "quotes", None) or []
    except Exception:
        quotes = []

    rows = []
    for q in quotes:
        symbol = _clean_text(q.get("symbol"), upper=True)
        qtype = _clean_text(q.get("quoteType"), upper=True)
        if not symbol or (qtype and qtype not in {"EQUITY","ETF","MUTUALFUND","INDEX"}):
            continue
        name = _clean_text(q.get("longname") or q.get("shortname") or q.get("name")) or symbol
        rows.append({"symbol":symbol,"name":name,"isin":"","source":"Recherche Yahoo"})

    return pd.DataFrame(rows).drop_duplicates("symbol").reset_index(drop=True) if rows else pd.DataFrame(
        columns=["symbol","name","isin","source"]
    )


def vf_analysis_option_label(row):
    symbol = _clean_text(row.get("symbol"), upper=True)
    name = _clean_text(row.get("name")) or symbol
    isin = _clean_text(row.get("isin"), upper=True)
    source = _clean_text(row.get("source"))
    extra = []
    if isin:
        extra.append(isin)
    if source:
        extra.append(source)
    suffix = " — " + " • ".join(extra) if extra else ""
    return f"{symbol} • {name}{suffix}"



vf_global_topbar()

if mode=="🏠 Dashboard":
    vf_dashboard_command_center()

elif mode=="⭐ Watchlist":
    vf_page_header("⭐ Watchlist","Board personnel des valeurs que tu souhaites suivre.")
    vf_watchlist_board()

elif mode=="📥 Imports & documents":
    show_import_page()

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
    vf_page_header(
        "⚡ Scanner mondial",
        "Discovery Board — découverte mondiale, scoring multi-timeframe, confirmation 1H et plan de risque."
    )

    # Top visual controls
    f1,f2,f3,f4 = st.columns(4)
    brokers = f1.multiselect(
        "Courtiers vérifiés",
        ["XTB","Trade Republic"],
        default=["XTB","Trade Republic"],
        help="Filtre uniquement le référentiel broker_universe."
    )
    available_markets = sorted(load_broker_universe()["market"].dropna().unique().tolist())
    default_markets = [x for x in ["USA","France","Germany","Netherlands","UK"] if x in available_markets]
    markets = f2.multiselect("Marchés du référentiel", available_markets, default=default_markets)
    min_upside = f3.number_input("Potentiel min. (%)", 1.0, 30.0, 3.0, .5)
    min_rr = f4.number_input("R/R min.", 1.0, 5.0, 2.0, .1)

    g1,g2,g3,g4 = st.columns(4)
    min_score = g1.slider("Score minimum", 50, 100, 72)
    top_n = g2.slider("Finalistes", 5, 50, 20)
    only_confirmed = g3.checkbox("Confirmés 1H seulement", False)
    include_discovery = g4.toggle("Découverte mondiale", value=True)

    discovery_regions = []
    max_per_region = 20
    if include_discovery:
        r1,r2 = st.columns([4,1])
        with r1:
            discovery_regions = st.multiselect(
                "Zones de découverte",
                list(YF_DISCOVERY_REGIONS.keys()),
                default=["USA","France","Allemagne","Royaume-Uni","Canada","Japon"],
            )
        with r2:
            max_per_region = st.selectbox("Titres / zone", [10,15,20,25,30], index=2)

    with st.spinner("Construction de l'univers mondial…"):
        universe_df = scanner_universe_frame(
            brokers=brokers,
            markets=markets,
            include_discovery=include_discovery,
            discovery_regions=discovery_regions,
            max_per_region=max_per_region,
        )

    if universe_df.empty:
        st.warning("Aucun instrument disponible pour les filtres sélectionnés.")
    else:
        verified_count = int((universe_df.get("source") == "Référentiel courtier").sum()) if "source" in universe_df else 0
        discovery_count = int((universe_df.get("source") == "Découverte Yahoo").sum()) if "source" in universe_df else 0
        symbols = universe_df["symbol"].dropna().astype(str).tolist()

        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Univers analysé", len(symbols))
        k2.metric("Courtier vérifié", verified_count)
        k3.metric("Découverte", discovery_count)
        k4.metric("Seuil setup", f"{min_upside:.1f}% / R-R {min_rr:.1f}")

        if discovery_count:
            st.info(
                "Les valeurs « Découverte Yahoo » élargissent la recherche mais leur disponibilité chez XTB "
                "ou Trade Republic n'est pas garantie. Elles sont donc affichées « courtier à vérifier »."
            )

        with st.spinner("Analyse technique groupée puis confirmation 1H…"):
            out = fast_scan(
                symbols,
                min_upside=min_upside,
                min_rr=min_rr,
                min_score=min_score,
                top_n=top_n
            )

        if out.empty:
            st.warning("Aucune configuration ne passe les filtres actuels.")
        else:
            meta = universe_df.set_index("symbol")
            names, isins, sources, broker_labels, market_labels = [], [], [], [], []
            for sym in out["Ticker"].tolist():
                if sym in meta.index:
                    rr = meta.loc[sym]
                    if isinstance(rr, pd.DataFrame):
                        rr = rr.iloc[0]
                    names.append(_clean_text(rr.get("name")) or live_quote(sym).get("name", sym))
                    isins.append(_clean_text(rr.get("isin"), upper=True))
                    sources.append(_clean_text(rr.get("source")))
                    broker_labels.append(_clean_text(rr.get("broker")))
                    market_labels.append(_clean_text(rr.get("market")))
                else:
                    names.append(live_quote(sym).get("name", sym))
                    isins.append("")
                    sources.append("")
                    broker_labels.append("")
                    market_labels.append("")

            out["Entreprise"] = names
            out["ISIN"] = isins
            out["Source"] = sources
            out["Courtier"] = broker_labels
            out["Marché"] = market_labels
            out = add_identity_columns(out, "Ticker")

            if only_confirmed:
                out = out[out["Confirmé 1h"]=="✅"]

            if out.empty:
                st.warning("Aucun finaliste n'est confirmé en 1H.")
            else:
                st.success(f"{len(out)} configuration(s) retenue(s).")

                # DA: charts before dense table
                ca,cb = st.columns(2)
                with ca:
                    vf_bar(
                        out.nlargest(min(12,len(out)), "Score combiné"),
                        "Valeur","Score combiné","Meilleurs scores"
                    )
                with cb:
                    vf_bar(
                        out.nlargest(min(12,len(out)), "Potentiel %"),
                        "Valeur","Potentiel %","Potentiel des finalistes"
                    )

                vf_section("Sélection prioritaire", "Les meilleurs setups du scanner présentés comme un board opérationnel.")
                top_cards = out.head(8).reset_index(drop=True)
                for i in range(0, len(top_cards), 2):
                    cols = st.columns(2)
                    for j,col in enumerate(cols):
                        idx=i+j
                        if idx >= len(top_cards):
                            break
                        with col:
                            vf_setup_card(top_cards.iloc[idx], key_prefix=f"scanner_card_{idx}", show_expand=True)

                with st.expander("📋 Voir le tableau complet"):
                    visible = [
                        "Valeur","Ticker","Entreprise","ISIN","Marché","Courtier","Source",
                        "Score combiné","Score","Confirmation 1h","Confirmé 1h",
                        "Prix","Entrée","Stop","TP1","TP2","Potentiel %","R/R","Qualité"
                    ]
                    st.dataframe(
                        out[[c for c in visible if c in out.columns]],
                        use_container_width=True,
                        hide_index=True
                    )


elif mode=="📊 Instrument":
    vf_page_header(
        "📊 Instrument",
        "Instrument Board — graphique, momentum, fondamentaux, actualités et plan de trade."
    )

    choices = []

    # 1) Positions réellement détenues
    try:
        pp = load_positions()
        if pp is not None and not pp.empty:
            for _, r in pp.iterrows():
                s = _clean_text(r.get("ticker"), upper=True)
                if not s:
                    continue
                name = _clean_text(r.get("name")) or s
                label = f"{s} • {name}  —  Portefeuille"
                row = r.to_dict()
                row["Source"] = "Portefeuille"
                choices.append((label, s, row, 0))
    except Exception:
        pass

    # 2) Référentiel courtier Supabase
    try:
        bu = load_broker_universe()
        if bu is not None and not bu.empty:
            for _, r in bu.iterrows():
                s = _clean_text(r.get("symbol"), upper=True)
                if not s:
                    continue
                name = _clean_text(r.get("name")) or s
                market = _clean_text(r.get("market"))
                broker = _clean_text(r.get("broker"))
                meta = " • ".join(x for x in [market, broker] if x)
                label = f"{s} • {name}" + (f"  —  {meta}" if meta else "")
                row = r.to_dict()
                row["Source"] = "Référentiel courtier"
                row["Entreprise"] = name
                row["Ticker"] = s
                row["Marché"] = market
                row["Courtier"] = broker
                choices.append((label, s, row, 1))
    except Exception:
        pass

    # 3) Découverte mondiale Yahoo / yfinance
    # Cached by discover_yahoo_equities(), so subsequent visits are much faster.
    try:
        discovery_regions = list(YF_DISCOVERY_REGIONS.keys())
        discovered = discover_yahoo_equities(
            discovery_regions,
            max_per_region=30
        )
        if discovered is not None and not discovered.empty:
            for _, r in discovered.iterrows():
                s = _clean_text(r.get("symbol"), upper=True)
                if not s:
                    continue
                name = _clean_text(r.get("name")) or s
                market = _clean_text(r.get("market"))
                label = f"{s} • {name}" + (f"  —  {market} • Découverte" if market else "  —  Découverte")
                row = r.to_dict()
                row["Source"] = "Découverte Yahoo"
                row["Entreprise"] = name
                row["Ticker"] = s
                row["Marché"] = market
                row["Courtier"] = "À vérifier"
                choices.append((label, s, row, 2))
    except Exception:
        pass

    # Déduplication : portefeuille > référentiel courtier > découverte.
    dedup = {}
    for label, s, row, priority in sorted(choices, key=lambda x: x[3]):
        if s not in dedup:
            dedup[s] = (label, s, row, priority)

    choices = sorted(
        dedup.values(),
        key=lambda x: (
            x[3],
            _clean_text(x[2].get("Entreprise") or x[2].get("name") or x[1]).lower()
        )
    )

    # KPIs universe
    n_portfolio = sum(1 for x in choices if x[3] == 0)
    n_broker = sum(1 for x in choices if x[3] == 1)
    n_discovery = sum(1 for x in choices if x[3] == 2)

    u1,u2,u3,u4 = st.columns(4)
    u1.metric("Valeurs disponibles", len(choices))
    u2.metric("Portefeuille", n_portfolio)
    u3.metric("Référentiel courtier", n_broker)
    u4.metric("Découverte mondiale", n_discovery)

    st.caption(
        "Tu peux taper directement dans le menu déroulant pour rechercher un ticker ou un nom d'entreprise. "
        "Les valeurs « Découverte » ne sont pas garanties disponibles chez XTB / Trade Republic."
    )

    c1,c2 = st.columns([5,1.5])

    labels = [x[0] for x in choices]
    selection = c1.selectbox(
        "Valeur",
        labels if labels else ["Aucune valeur disponible"],
        index=0,
        help="Tape un ticker ou le nom de l'entreprise pour filtrer la liste."
    )

    preset_symbol = _clean_text(st.session_state.pop("instrument_symbol", ""), upper=True)
    manual_symbol = c2.text_input(
        "Ticker libre",
        value=preset_symbol,
        placeholder="ex. TSLA, MC.PA",
        help="Permet d'analyser n'importe quel ticker Yahoo Finance même s'il n'est pas dans la liste."
    )

    selected_symbol = ""
    selected_row = {}

    if manual_symbol.strip():
        selected_symbol = _clean_text(manual_symbol, upper=True)
    elif choices:
        for label, s, row, _priority in choices:
            if label == selection:
                selected_symbol = s
                selected_row = row
                break

    unresolved_ctx = st.session_state.get("instrument_unresolved") or {}

    if selected_symbol:
        ctx = st.session_state.pop("instrument_identity_context", {}) or {}
        if ctx and not selected_row:
            selected_row = {
                "name": ctx.get("name",""),
                "isin": ctx.get("isin",""),
                "Source": ctx.get("resolution_source",""),
            }
        vf_full_instrument_page(selected_symbol, selected_row)

    elif unresolved_ctx:
        unresolved_name = _clean_text(unresolved_ctx.get("name"))
        unresolved_isin = _clean_text(unresolved_ctx.get("isin"), upper=True)

        vf_section("Instrument à résoudre", "La fiche existe, mais le ticker n'est pas encore suffisamment fiable.")
        st.markdown(
            vf_identity_html("", unresolved_name, unresolved_isin, resolve=False),
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="vf-future-strip">'
            '<div class="vf-future-strip-title">Résolution assistée</div>'
            '<div class="vf-future-strip-text">VISION FUTURE conserve la valeur et tente de relier son ISIN / nom à un ticker Yahoo sans inventer de correspondance.</div>'
            '</div>',
            unsafe_allow_html=True
        )

        r1,r2 = st.columns([3,1])
        retry_ticker = r1.text_input(
            "Ticker à confirmer",
            placeholder="ex. HRS.PA, ALHOP.PA…",
            key=f"unresolved_ticker_{vf_identity_key('', unresolved_name, unresolved_isin)}"
        )
        if r2.button("Valider", use_container_width=True):
            if _clean_text(retry_ticker, upper=True):
                st.session_state["instrument_symbol"] = _clean_text(retry_ticker, upper=True)
                st.session_state["instrument_identity_context"] = {
                    "name": unresolved_name,
                    "isin": unresolved_isin,
                    "resolution_source": "Validation manuelle",
                    "resolution_confidence": 100,
                }
                st.session_state.pop("instrument_unresolved", None)
                st.rerun()

        auto_sym, auto_conf, auto_source = resolve_ticker_from_identity(unresolved_name, unresolved_isin)
        if auto_sym:
            st.success(f"Correspondance proposée : {auto_sym} • {auto_source} • confiance {auto_conf}%")
            if st.button("📊 Ouvrir la correspondance proposée", use_container_width=True):
                st.session_state["instrument_symbol"] = auto_sym
                st.session_state["instrument_identity_context"] = {
                    "name": unresolved_name,
                    "isin": unresolved_isin,
                    "resolution_source": auto_source,
                    "resolution_confidence": auto_conf,
                }
                st.session_state.pop("instrument_unresolved", None)
                st.rerun()
        else:
            st.warning("Aucune correspondance suffisamment fiable pour l'instant. La valeur reste conservée comme instrument à résoudre.")

    else:
        st.info("Sélectionne une valeur ou saisis un ticker libre.")


elif mode=="🛰️ Agent marché":
    show_market_agent_page()

elif mode=="📊 Analyse":
    vf_page_header(
        "📊 Analyse détaillée",
        "Recherche par ticker ou nom d'entreprise, puis analyse technique multi-timeframe."
    )

    st.markdown(
        '<div class="vf-future-strip">'
        '<div class="vf-future-strip-title">Smart Search</div>'
        '<div class="vf-future-strip-text">Recherche une société par son nom ou son ticker. La liste combine portefeuille, référentiel, découverte mondiale et Yahoo.</div>'
        '</div>',
        unsafe_allow_html=True
    )

    base = vf_analysis_universe()

    q1,q2 = st.columns([2.2,1])
    search_query = q1.text_input(
        "Rechercher une valeur",
        placeholder="Ex. TotalEnergies, LVMH, Tesla, AAPL…",
        key="analysis_search_query"
    )

    yahoo_matches = vf_yahoo_search_instruments(search_query) if search_query.strip() else pd.DataFrame()

    frames = []
    if yahoo_matches is not None and not yahoo_matches.empty:
        frames.append(yahoo_matches)
    if base is not None and not base.empty:
        frames.append(base)

    if frames:
        candidates = pd.concat(frames, ignore_index=True, sort=False).drop_duplicates("symbol")
    else:
        candidates = pd.DataFrame(columns=["symbol","name","isin","source"])

    if search_query.strip() and not candidates.empty:
        query_norm = search_query.strip().lower()
        mask = (
            candidates["symbol"].fillna("").astype(str).str.lower().str.contains(query_norm, regex=False)
            | candidates["name"].fillna("").astype(str).str.lower().str.contains(query_norm, regex=False)
            | candidates["isin"].fillna("").astype(str).str.lower().str.contains(query_norm, regex=False)
            | candidates["source"].fillna("").eq("Recherche Yahoo")
        )
        filtered = candidates[mask].copy()
        if not filtered.empty:
            candidates = filtered

    labels = []
    label_to_row = {}
    for _, rr in candidates.head(500).iterrows():
        label = vf_analysis_option_label(rr)
        labels.append(label)
        label_to_row[label] = rr.to_dict()

    if labels:
        default_index = 0
        if not search_query.strip():
            for i, lab in enumerate(labels):
                if lab.startswith("AAPL •"):
                    default_index = i
                    break
        selected_label = q1.selectbox(
            "Valeur",
            labels,
            index=default_index,
            key="analysis_value_select",
            help="Le menu est recherchable : tape un ticker ou un nom pour filtrer."
        )
    else:
        selected_label = q1.selectbox(
            "Valeur",
            ["Aucun résultat"],
            index=0,
            key="analysis_value_select_empty"
        )

    manual_symbol = q2.text_input(
        "Ticker libre",
        placeholder="MC.PA",
        key="analysis_manual_ticker",
        help="Option de secours si la valeur n'apparaît pas dans la recherche."
    )

    selected_row = {}
    symbol = ""
    if manual_symbol.strip():
        symbol = _clean_text(manual_symbol, upper=True)
    elif selected_label in label_to_row:
        selected_row = label_to_row[selected_label]
        symbol = _clean_text(selected_row.get("symbol"), upper=True)

    if not symbol:
        st.warning("Sélectionne une valeur dans le menu ou saisis un ticker.")
    else:
        f1,f2 = st.columns(2)
        timeframe = f1.selectbox("Timeframe", list(TF), index=2, key="analysis_timeframe")
        period = f2.selectbox(
            "Historique",
            TF[timeframe]["periods"],
            index=min(1, len(TF[timeframe]["periods"])-1),
            key="analysis_period"
        )

        with st.spinner(f"Analyse de {symbol}…"):
            t = trade_setup(history(symbol, period, TF[timeframe]["interval"]))
            q = live_quote(symbol)

        selected_name = _clean_text(selected_row.get("name")) or _clean_text(q.get("name")) or symbol
        selected_isin = _clean_text(selected_row.get("isin"), upper=True)

        st.markdown(
            vf_identity_html(symbol, selected_name, selected_isin, resolve=True),
            unsafe_allow_html=True
        )

        if not t:
            st.warning("Données insuffisantes pour calculer le setup.")
        else:
            c = st.columns(7)
            c[0].metric("Cours", f"{t['price']:.2f}")
            c[1].metric("Entrée", f"{t['entry']:.2f}")
            c[2].metric("SL", f"{t['stop']:.2f}")
            c[3].metric("TP1", f"{t['tp1']:.2f}")
            c[4].metric("TP2", f"{t['tp2']:.2f}")
            c[5].metric("Potentiel", f"{t['upside']:.1f}%")
            c[6].metric("R/R", f"{t['rr']:.2f}")

            a,b = st.columns([3,1])
            with a:
                st.markdown(f"**Score {t['score']}/100 • {t['quality']}**")
                st.caption(" • ".join(t["reasons"]))
            with b:
                if st.button("📊 Ouvrir la fiche Instrument", key=f"analysis_open_{symbol}", use_container_width=True):
                    open_instrument_identity(symbol, selected_name, selected_isin)

            vf_trade_chart(symbol, t, period=period, interval=TF[timeframe]["interval"])


else:
    st.header("🧪 Simulation")
    symbol=st.text_input("Ticker","AAPL").upper().strip(); t=trade_setup(history(symbol,"6mo","1d"))
    if t:
        sym_i, name_i, isin_i = instrument_identity(symbol)
        st.markdown(f"**{sym_i} • {name_i}**")
        st.caption(f"ISIN : {isin_i}")
        entry=st.number_input("Entrée",value=float(t["entry"])); stop=st.number_input("Stop",value=float(t["stop"])); target=st.number_input("TP2",value=float(t["tp2"]))
        risk_e,qty,exposure,profit,rr=position_calc(capital,risk_pct,entry,stop,target)
        c=st.columns(5); c[0].metric("Risque max",f"{risk_e:.2f} €"); c[1].metric("Quantité",qty); c[2].metric("Exposition",f"{exposure:.2f} €"); c[3].metric("Gain cible",f"{profit:.2f} €"); c[4].metric("R/R",f"{rr:.2f}")
    else: st.warning("Setup indisponible.")

st.markdown("---")
st.caption(f"VISION FUTURE • {APP_VERSION} • Des idées au patrimoine • Build the Future of Your Capital")
