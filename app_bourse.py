export_positions_comptables_06_09_2026_20_43_05-1788720218719.csv(1)(1).xls
Feuille de calcul
export_positions_comptables_06_09_2026_20_43_05-1788720218719.csv(2).xls
Feuille de calcul

comptabilite 23 02 2026 page 1(1)
Impossible d’afficher la visualisation
voici le deuxieme fichier

export_positions_comptables_06_09_2026_20_43_05-1788720218719.csv(1)(2).xls
Feuille de calcul

Exportation de transactions
datetime	date	account_type
2024-11-06T12:50:55.585724Z	2024-11-06	DEFAULT
2024-11-13T08:58:22.257Z	2024-11-13	DEFAULT
2024-11-15T14:19:42.268Z	2024-11-15	DEFAULT
2024-12-01T18:07:35.750717Z	2024-12-01	DEFAULT

0834c535-987b-4b68-acaa-166af25e7193.png
GUIDE MOI

55dfabaa-1ee0-483a-9fab-af54da7feccf.png
122cb8aa-5f1a-4b39-8b86-9670d40c9dde.png

Oui. Cette erreur est maintenant très précise, et elle vient du schéma historique de ta table Supabase, pas de l’importeur.

Ton ETF BNPP EASY S&P 500 ETF EUR C a bien été compris grâce à son ISIN FR0011550185, mais aucun ticker n’a été trouvé avec certitude. La V7 est justement conçue pour accepter ça : elle utilise instrument_key = ISIN quand le ticker manque. Le problème est que ta vieille table portfolio_positions impose encore ticker NOT NULL.

Il faut donc retirer cette contrainte ancienne. Va dans Supabase → SQL Editor et exécute ceci :

-- VISION FUTURE V7 - correction schéma positions

alter table public.portfolio_positions
alter column ticker drop not null;

-- On s'assure que les colonnes V7 existent
alter table public.portfolio_positions
add column if not exists instrument_key text;

alter table public.portfolio_positions
add column if not exists isin text;

alter table public.portfolio_positions
add column if not exists name text;

alter table public.portfolio_positions
add column if not exists broker text default 'Inconnu / générique';

alter table public.portfolio_positions
add column if not exists currency text;

alter table public.portfolio_positions
add column if not exists last_price_imported numeric;

alter table public.portfolio_positions
add column if not exists market_value_imported numeric;

alter table public.portfolio_positions
add column if not exists source text default 'document_import';

alter table public.portfolio_positions
add column if not exists updated_at timestamptz default now();

-- Reconstitue une clé d'instrument pour les anciennes lignes
update public.portfolio_positions
set instrument_key = coalesce(
    nullif(isin, ''),
    nullif(ticker, ''),
    nullif(name, '')
)
where instrument_key is null;

-- Index utilisé par V7
create unique index if not exists uq_positions_account_broker_instrument
on public.portfolio_positions(account, broker, instrument_key)
where instrument_key is not null;

Ensuite retourne dans VISION FUTURE et réimporte exactement le même fichier.

Cette fois cette ligne pourra être enregistrée ainsi :

Compte          PEA
Courtier        BoursoBank
Ticker          NULL
ISIN            FR0011550185
Nom             BNPP EASY S&P 500 ETF EUR C
Quantité        59
PRU             24,94 €
Cours importé   33,60 €
Valeur          1 982,65 €
Instrument key  FR0011550185

Et c’est mieux que de forcer un ticker possiblement faux.

Le principe de V7 doit être :

Ticker connu
    ↓
on l'utilise

Sinon ISIN connu
    ↓
on utilise l'ISIN comme identifiant fiable

Sinon nom connu
    ↓
identification provisoire

Sinon
    ↓
ligne à vérifier

Donc ne modifie pas app_bourse.py pour cette erreur. Le code actuel se comporte correctement : c’est simplement la contrainte NOT NULL de ton ancienne base qui bloque le nouveau fonctionnement.

Après avoir exécuté le SQL, retente l’import. Si une nouvelle erreur apparaît, envoie-la-moi exactement : on est maintenant en train de nettoyer les dernières incompatibilités du vieux schéma V6 avec le Core V7.

c'est bon 

Parfait. La chaîne document → interprétation → Supabase est donc opérationnelle.

La prochaine étape logique est la V7.1 Performance Engine : exploiter les positions et les transactions enregistrées pour calculer proprement valorisation, P&L latent/réalisé, dividendes, frais/taxes, apports/retraits et performance PEA/CTO, puis alimenter le dashboard et l’arbitrage.

Je garderais le scanner actuel avec Entrée / SL / TP1 / TP2 / R/R, mais en le reliant désormais au portefeuille réel pour distinguer automatiquement Renforcer / Conserver / Surveiller / Alléger.

On peut attaquer cette V7.1 maintenant.

go

C’est prêt. J’ai construit la V7.1 Performance Engine sur la V7 qui fonctionne maintenant avec Supabase.

Télécharger app_bourse.py — V7.1
Télécharger la migration Supabase V7.1
Télécharger requirements.txt

J’ai aussi vérifié le script avec py_compile : aucune erreur de syntaxe.
Ce que V7.1 apporte

Tu as maintenant deux nouvelles pages :

📈 Performance calcule automatiquement, à partir de Supabase, la valorisation actuelle, le P/L latent, les dividendes, les intérêts, les frais, les taxes, les apports, les retraits et le P/L réalisé FIFO sur les ventes.

Pour ton export Trade Republic, par exemple, le moteur distingue désormais automatiquement les opérations du type :

BUY
SELL
DIVIDEND
INTEREST_PAYMENT
CUSTOMER_INBOUND
TRANSFER_INSTANT_INBOUND
SPLIT
BONUS_ISSUE
BONUS_ISSUE_CANCELLED

Je n’ai volontairement pas inventé de traitement automatique des splits et bonus complexes : lorsqu’ils sont présents, VISION FUTURE les signale. C’est plus fiable que de modifier artificiellement un PRU ou une quantité.

La page ⚖️ Arbitrage croise maintenant les positions enregistrées avec le moteur technique :

Position actuelle
      +
Poids portefeuille
      +
P/L
      +
Score technique
      +
Potentiel
      +
R/R
      ↓
Lecture analytique

et conserve les niveaux :

Entrée
Stop Loss
TP1
TP2
Potentiel
R/R
Score

La valorisation est aussi plus robuste

Si un titre possède un ticker reconnu :

Ticker → cours marché

Sinon :

ISIN connu
   ↓
cours du dernier export courtier

Et à défaut :

valorisation du dernier export

Donc ton ETF BNP avec ISIN mais sans ticker ne disparaît plus de la valorisation.
Historique de performance

J’ai également ajouté une nouvelle table Supabase :

performance_snapshots

VISION FUTURE enregistre un snapshot quotidien :

Date
Valeur des actifs
Cash estimé
Valeur totale estimée
Apports nets
P/L estimé
Rendement %

La courbe va donc se construire automatiquement dans le temps.

Attention : pour l’instant le rendement global affiché est un rendement simple estimé, pas encore un vrai TWR/XIRR institutionnel. Il devient fiable si l’historique des transactions couvre bien le compte depuis son origine.
Maintenant fais ces actions

    Va dans Supabase → SQL Editor, ouvre
    supabase_v7_1.sql, colle tout et fais Run.

    Remplace entièrement ton app_bourse.py GitHub par
    ce nouveau fichier.

    Vérifie que ton requirements.txt est
    celui-ci.

    Fais Commit changes → Streamlit → Reboot app.

    Ouvre 📈 Performance puis sélectionne PEA ou CTO Trade Republic.

    Ouvre ensuite ⚖️ Arbitrage pour tester le croisement portefeuille/scanner.

Tu n’as pas besoin de réimporter tes positions PEA : elles sont déjà dans Supabase. Pour Trade Republic, si tes 42 transactions sont déjà enregistrées, elles sont également récupérées automatiquement.

Une fois cette V7.1 validée, je passerais à la V7.2 Dashboard Intelligence : un écran d’accueil beaucoup plus visuel avec patrimoine PEA/CTO consolidé, allocation, meilleurs/pires titres, dividendes, cash, performance, alertes et opportunités du scanner.
app_bourse.pyCode
supabase_v7_1.sqlCode
requirements.txtDocument


Bibliothèque/
app_bourse.py
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
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
APP_VERSION = "V7.1 Performance Engine"

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
