export_positions_comptables_06_09_2026_20_43_05-1788720218719.csv(1)(1).xls
Feuille de calcul
export_positions_comptables_06_09_2026_20_43_05-1788720218719.csv(2).xls
Feuille de calcul

comptabilite 23 02 2026 page 1(1)
Impossible d’afficher la visualisation
voici le deuxieme fichier

export_positions_comptables_06_09_2026_20_43_05-1788720218719.csv(1)(2).xls
Feuille de calcul

Reçu. J’ai contrôlé le fichier réel : c’est encore l’export de positions, pas l’export de transactions.

Il contient bien :

name;isin;quantity;buyingPrice;lastPrice;intradayVariation;amount;amountVariation;variation;lastMovementDate;compensation

avec par exemple 2CRSI, Air Liquide, AXA, ETF S&P 500, Crédit Agricole, etc. Il fait 1 793 octets, est en UTF-8 BOM et utilise ; comme séparateur.

On a donc actuellement deux formats réels pour construire V7 : POSITIONS et COMPTABILITÉ. Le fichier qui nous manque est celui dont l’en-tête commence par datetime,date,account_type,category,type,asset_class,name,symbol,shares,price,amount,fee,tax,currency....

Dès que tu m’envoies ce fichier de transactions, je pourrai attaquer le nouveau app_bourse.py VISION FUTURE V7 sur une base propre, avec détection automatique des documents, prévisualisation, normalisation et stockage Supabase permanent.

Exportation de transactions
datetime	date	account_type
2024-11-06T12:50:55.585724Z	2024-11-06	DEFAULT
2024-11-13T08:58:22.257Z	2024-11-13	DEFAULT
2024-11-15T14:19:42.268Z	2024-11-15	DEFAULT
2024-12-01T18:07:35.750717Z	2024-12-01	DEFAULT

Parfait. Cette fois j’ai bien le vrai fichier de transactions et je l’ai lu directement. On a maintenant les trois formats nécessaires pour repartir proprement.

Ton fichier Exportation de transactions.csv est un CSV standard UTF-8, séparateur virgule, avec 42 opérations et 23 colonnes. Il contient notamment datetime, category, type, asset_class, name, symbol, shares, price, amount, fee, tax, currency, description et transaction_id.

Surtout, ses opérations réelles sont suffisamment variées pour construire correctement le moteur V7 : 17 BUY, 3 SELL, 8 DIVIDEND, 4 INTEREST_PAYMENT, 3 BONUS_ISSUE, 2 SPLIT, 2 CUSTOMER_INBOUND, 2 TRANSFER_INSTANT_INBOUND et 1 BONUS_ISSUE_CANCELLED. Il contient aussi des actions et des cryptos. Par exemple, Tesla est identifié par US88160R1014 dans symbol : cela montre qu'on ne doit pas supposer que la colonne symbol contient toujours un ticker. Cardano, lui, utilise ADA.
Je fixe donc la nouvelle architecture

On abandonne l'ancien importeur et on construit VISION FUTURE V7 autour de trois niveaux :

                 📥 DOCUMENT
                      │
              ┌───────▼────────┐
              │ DOCUMENT ENGINE │
              └───────┬────────┘
                      │
        encodage / séparateur / structure
                      │
              ┌───────▼────────┐
              │ CLASSIFICATION │
              └───────┬────────┘
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
   POSITIONS      TRANSACTIONS   COMPTABILITÉ
       │              │              │
       ▼              ▼              ▼
 Portfolio Engine   Ledger       Information
       │              │
       └──────┬───────┘
              ▼
          NORMALISATION
              │
              ▼
           SUPABASE
              │
       ┌──────┴────────┐
       ▼               ▼
    PEA/CTO        Transactions
       │               │
       └───────┬───────┘
               ▼
        PERFORMANCE RÉELLE

Le Document Engine ne regardera jamais l'extension en premier. Il inspectera les octets, détectera UTF-8/UTF-16/etc., le séparateur et les colonnes. Ainsi ton .csv.xls sera correctement reconnu comme CSV ;, tandis que ce fichier de transactions sera reconnu comme CSV ,.

Ensuite seulement, le Financial Parser déterminera la signification. Et il ne dépendra pas d'un nom de colonne exact : quantity, shares, qty, unités, quantité pourront tous devenir notre champ interne quantity.

Il y a aussi une amélioration importante : positions et transactions ne seront plus mélangées. Ton export BoursoBank de positions servira à photographier l'état actuel du portefeuille ; ton export de transactions servira au ledger historique. On pourra alors calculer beaucoup plus proprement achats, ventes, dividendes, frais, intérêts, apports et opérations sur titres.
Ce que je vais conserver de l'application actuelle

On ne jette pas le travail utile : authentification, Supabase, scanner, analyse technique, multi-timeframe, score, prix d'entrée, Stop Loss, TP1, TP2, R/R, actualités, PEA, CTO, TradingView et journal restent dans V7.

Ce qu'on remplace entièrement, c'est la couche Import → Interprétation → Stockage.

Et le nom devient définitivement :
VISION FUTURE
Trading & Portfolio Intelligence

Je peux maintenant construire le nouveau app_bourse.py V7 complet + le nouveau schéma Supabase, parce que nous avons enfin de vrais échantillons des trois structures nécessaires.

go

C’est prêt. J’ai reconstruit une V7 Core propre, basée sur les trois vrais fichiers que tu m’as fournis, avec un moteur d’interprétation qui inspecte le contenu du document avant son extension.

Télécharger app_bourse.py — VISION FUTURE V7

Télécharger supabase_v7.sql

Télécharger requirements.txt

J’ai testé le moteur directement sur tes documents : ton export .csv.xls est maintenant détecté comme POSITIONS / BoursoBank / 20 lignes, ton fichier Exportation de transactions.csv comme TRANSACTIONS / Trade Republic / 42 opérations, et ton relevé DATE / LABEL / DEBIT / CREDIT comme ACCOUNTING / 12 lignes. Le script passe aussi la vérification Python sans erreur de syntaxe.
Ce que V7 change réellement

L’ancienne logique faisait essentiellement :

CSV → chercher buyingPrice → importer ou erreur

La nouvelle fait :

DOCUMENT
   ↓
lecture des octets
   ↓
CSV texte ou vrai Excel ?
   ↓
détection encodage
   ↓
détection séparateur
   ↓
analyse des colonnes
   ↓
classification
   ├── POSITIONS
   ├── TRANSACTIONS
   ├── COMPTABILITÉ
   └── INCONNU
   ↓
normalisation des champs
   ↓
prévisualisation
   ↓
validation
   ↓
SUPABASE

Par exemple ton fichier bizarrement nommé .csv.xls est correctement reconnu comme :

Format réel : delimited_text
Encodage : utf-8-sig
Séparateur : ;
Type : POSITIONS
Courtier probable : BoursoBank
20 positions

Et le fichier Trade Republic :

Format réel : delimited_text
Séparateur : ,
Type : TRANSACTIONS
Courtier probable : Trade Republic
42 opérations

Le moteur sait aussi qu’un symbol peut en réalité contenir un ISIN. Par exemple US88160R1014 n’est donc plus naïvement pris pour un ticker.
Actions à mener maintenant

    Dans Supabase → SQL Editor, ouvre
    supabase_v7.sql, colle tout et clique sur Run. Ce script est prévu pour migrer depuis les versions précédentes : il conserve portfolio_positions mais ajoute les colonnes V7, puis crée transactions et imports.

    Dans GitHub, remplace entièrement ton ancien app_bourse.py par
    celui-ci, puis remplace également ton requirements.txt par
    celui-ci. J’ai ajouté openpyxl et xlrd pour que le moteur puisse également lire de vrais fichiers Excel.

    Dans Streamlit → Settings → Secrets, garde ton mot de passe et ton URL Supabase. Pour cette nouvelle base, je te recommande d’utiliser :

APP_PASSWORD = "ton_mot_de_passe"

SUPABASE_URL = "https://xxxxx.supabase.co"

SUPABASE_SERVICE_KEY = "ta_service_role_key"

La SUPABASE_SERVICE_KEY doit rester uniquement dans les Secrets Streamlit, jamais dans GitHub. La V7 accepte encore SUPABASE_KEY en secours, mais la nouvelle architecture SQL est volontairement pensée sans politique publique anon.

    Fais Commit changes, puis Reboot app dans Streamlit.

    Dans l’application, ouvre désormais :

📥 Import documents

Tu choisis d’abord le compte cible, par exemple PEA, puis tu déposes ton export BoursoBank. L’app doit afficher le diagnostic avant toute sauvegarde.

Tu devrais obtenir approximativement :

Type             POSITIONS
Confiance        85 %
Courtier         BoursoBank
Lignes           20

Format réel      delimited_text
Encodage         utf-8-sig
Séparateur       ;

Puis un tableau avec les correspondances détectées :

name              → name
isin              → isin
quantity          → quantity
buyingPrice       → average_cost
lastPrice         → market_price
amount            → market_value
lastMovementDate  → purchase_date

Et la prévisualisation doit notamment donner correctement :

AIR LIQUIDE
ISIN : FR0000120073
Quantité : 15
PRU : 159,56
Cours importé : 170,44
Valeur : 2 556,60
Date : 11/06/2026

Il n’y a plus la mauvaise conversion en centimes que nous avions auparavant.

Ensuite tu cliques une seule fois sur :

☁️ Valider et enregistrer dans Supabase

À partir de là, les positions seront chargées automatiquement aux connexions suivantes.

Pour le fichier Trade Republic, même fonctionnement, mais il sera envoyé dans la table transactions. Grâce au transaction_id, le même historique réimporté ne créera pas 42 doublons.

Le fichier comptable, lui, sera correctement identifié mais pas injecté dans ton portefeuille. C’est volontaire : on conserve la capacité de le comprendre sans contaminer les données boursières.

Le nouveau titre de l’application est maintenant :
VISION FUTURE

Trading & Portfolio Intelligence

Et les pages principales deviennent Dashboard, Import documents, PEA, CTO, Transactions, Scanner, Analyse et Simulation. Les indications Entrée / Stop Loss / TP1 / TP2 / potentiel / R/R / score sont toujours présentes dans le scanner et l’analyse.

La prochaine vraie couche, une fois cette V7 installée et l’import validé, sera la V7.1 Performance Engine : reconstruire automatiquement le portefeuille depuis BUY / SELL / DIVIDEND / FEE / TAX / dépôts, calculer P&L réalisé/non réalisé, dividendes, frais, apports et performance réelle par compte.
app_bourse.pyCode
supabase_v7.sqlCode
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
APP_VERSION = "V7 Core"

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
