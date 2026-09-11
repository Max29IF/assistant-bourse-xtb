# VISION FUTURE

Application Streamlit de suivi de portefeuille et de surveillance des marchés, avec authentification Supabase et isolation multi-profil par RLS.

## V37.2 — Surveillance crypto

Le menu **₿ Crypto** ajoute :

- le suivi 24/7 de BTC, ETH, SOL, BNB, XRP et ADA ;
- une watchlist crypto persistante et privée par utilisateur ;
- des seuils personnels de prix haut et bas ;
- la saisie et la valorisation de positions détenues sur plusieurs plateformes ;
- les indicateurs 24 h, 7 jours, score technique, RSI, potentiel et ratio rendement/risque ;
- des alertes automatiques par le worker GitHub Actions exécuté toutes les 15 minutes.

Les signaux généraux de marché sont partagés avec les utilisateurs autorisés. Les alertes issues d'un seuil ou d'une position sont liées au `user_id` et restent privées.

## V37.3 — Scanner de trades crypto

Le premier onglet du menu **₿ Crypto** fonctionne désormais comme le scanner actions :

- classement des setups avec analyse quotidienne et confirmation 1H ;
- filtre potentiel estimé ≥ 5 %, R/R ≥ 2 et score ≥ 76 ;
- indication `zone d'entrée`, `attendre un retest`, `surveiller le rebond` ou `attendre confirmation 1H` ;
- niveaux indicatifs Entrée, Stop, TP1 et TP2 ;
- quantité fractionnaire calculée avec un risque plafonné entre 0,1 et 1,5 % ;
- horizon tactique filtré à 1–20 jours ;
- quota crypto dédié dans le worker pour éviter que les actions écartent les setups crypto.

Les indications sont une aide à la décision et non une garantie de rendement. Elles excluent les frais, le slippage, la fiscalité et l'exécution réelle.

## Installation V37.2 / V37.3

1. Exécuter `v37_2_crypto_monitoring.sql` dans le projet Supabase.
2. Déployer `app_bourse.py` et `market_agent.py`.
3. Conserver les secrets existants `SUPABASE_URL`, `SUPABASE_ANON_KEY` et `SUPABASE_SERVICE_KEY` dans leurs environnements respectifs.
4. Lancer manuellement le workflow **Market Agent** une première fois pour vérifier les diagnostics.

La clé publique/anonyme est utilisée par l'interface connectée. La clé `service_role` reste exclusivement dans les secrets GitHub Actions et n'est jamais envoyée au navigateur.
