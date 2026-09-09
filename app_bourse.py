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
APP_VERSION = "V20 Premium Experience"
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
@st.cache_data(ttl=86400, show_spinner=False)
def vf_company_brand_data(symbol, name="", isin=""):
    """
    Premium brand identity resolution.
    Priority:
      1) explicit logo URL from finance provider
      2) Logo.dev by ticker / ISIN when LOGO_DEV_TOKEN is configured
      3) monogram fallback
    """
    symbol = _clean_text(symbol, upper=True)
    name = _clean_text(name)
    isin = _clean_text(isin, upper=True)

    try:
        info = yf.Ticker(symbol).info or {} if symbol else {}
    except Exception:
        info = {}

    finance_logo = _clean_text(
        info.get("logo_url")
        or info.get("logoUrl")
        or info.get("companyLogoUrl")
    )
    finance_name = _clean_text(info.get("longName") or info.get("shortName"))
    website = _clean_text(info.get("website"))

    if finance_logo.startswith("http"):
        return {
            "url": finance_logo,
            "source": "Source financière",
            "name": finance_name or name,
            "website": website,
        }

    token = ""
    try:
        token = _clean_text(st.secrets.get("LOGO_DEV_TOKEN", ""))
    except Exception:
        token = ""
    if not token:
        token = _clean_text(os.getenv("LOGO_DEV_TOKEN", ""))

    if token:
        from urllib.parse import quote
        if symbol:
            # Logo.dev supports ticker lookup. Exchange suffixes are kept when useful.
            return {
                "url": f"https://img.logo.dev/ticker/{quote(symbol)}?token={quote(token)}&size=128&format=png",
                "source": "Logo.dev",
                "name": finance_name or name,
                "website": website,
            }
        if isin:
            return {
                "url": f"https://img.logo.dev/isin/{quote(isin)}?token={quote(token)}&size=128&format=png",
                "source": "Logo.dev",
                "name": finance_name or name,
                "website": website,
            }

    return {
        "url": "",
        "source": "",
        "name": finance_name or name,
        "website": website,
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
            f'<div class="vf-resolution-note">Résolu automatiquement : '
            f'{identity.get("source")} • confiance {identity.get("confidence")}%</div>'
        )
    elif not identity.get("symbol"):
        resolution = '<div class="vf-resolution-note">Instrument à résoudre — fiche disponible avec résolution assistée.</div>'

    logo_source = brand.get("source","")
    logo_note = f'<div class="vf-resolution-note">Logo : {logo_source}</div>' if logo_source else ""

    return (
        '<div class="vf-instrument-identity">'
        + vf_logo_html(identity.get("symbol"), shown_name, isin)
        + '<div>'
        + f'<div class="vf-name">{shown_symbol} • {shown_name}</div>'
        + f'<div class="vf-isin">{subtitle}</div>'
        + resolution
        + logo_note
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
    _nav_button("🛰️ Agent marché", "nav_agent")

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

st.caption(f"{APP_SUBTITLE} — {APP_VERSION} • {APP_TAGLINE}")



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
        logo_meta = vf_company_brand_data(symbol, name, isin)
        if logo_meta.get("url"):
            st.caption("Logo fourni par la source financière")
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
        '<div class="vf-topbar">'
        '<div>'
        '<div class="vf-brand">🔭 VISION FUTURE</div>'
        f'<div class="vf-brand-sub">{APP_VERSION} • {APP_SUBTITLE}</div>'
        f'<div class="vf-topbar-tag">{APP_TAGLINE}</div>'
        '</div>'
        '<div class="vf-topbar-right">'
        + vf_board_badge("VISION", "blue")
        + vf_board_badge("STEP UP", "green")
        + vf_board_badge("GLOW UP", "amber")
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



def vf_dashboard_command_center():
    vf_page_header(
        "Command Center",
        "VISION FUTURE — portefeuille, marché, opportunités, risques et watchlist dans une lecture premium."
    )
    st.markdown(
        '<div class="vf-future-strip">'
        '<div class="vf-future-strip-title">Vision • Step Up • Glow Up</div>'
        '<div class="vf-future-strip-text">Build the Future of Your Capital — une lecture globale pour faire progresser ton capital avec méthode, discipline et visibilité.</div>'
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

    vf_section("Allocation","Répartition des comptes et contribution au P/L.")
    d=pd.DataFrame(cards)
    a,b=st.columns(2)
    with a: vf_pie(d,"Compte","Valeur","Allocation")
    with b: vf_signed_bar(d,"Compte","P/L latent","P/L latent")

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
    st.header("📊 Analyse détaillée")
    symbol=st.text_input("Ticker","AAPL").upper().strip(); timeframe=st.selectbox("Timeframe",list(TF),index=2); period=st.selectbox("Historique",TF[timeframe]["periods"],index=min(1,len(TF[timeframe]["periods"])-1))
    t=trade_setup(history(symbol,period,TF[timeframe]["interval"])); q=live_quote(symbol)
    if not t: st.warning("Données insuffisantes pour calculer le setup.")
    else:
        c=st.columns(7); c[0].metric("Cours",f"{t['price']:.2f}"); c[1].metric("Entrée",f"{t['entry']:.2f}"); c[2].metric("SL",f"{t['stop']:.2f}"); c[3].metric("TP1",f"{t['tp1']:.2f}"); c[4].metric("TP2",f"{t['tp2']:.2f}"); c[5].metric("Potentiel",f"{t['upside']:.1f}%"); c[6].metric("R/R",f"{t['rr']:.2f}")
        sym_i, name_i, isin_i = instrument_identity(symbol, {"name": q.get("name", "")})
        st.write(f"**{sym_i} • {name_i}**")
        st.caption(f"ISIN : {isin_i}")
        st.write(f"Score {t['score']}/100 • {t['quality']}")
        st.write(" • ".join(t["reasons"]))

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
st.caption(f"VISION FUTURE • {APP_VERSION} • {APP_TAGLINE} • Les scénarios analytiques ne constituent pas des garanties de performance.")
