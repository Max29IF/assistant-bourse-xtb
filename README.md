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

## Installation V37.2

1. Exécuter `v37_2_crypto_monitoring.sql` dans le projet Supabase.
2. Déployer `app_bourse.py` et `market_agent.py`.
3. Conserver les secrets existants `SUPABASE_URL`, `SUPABASE_ANON_KEY` et `SUPABASE_SERVICE_KEY` dans leurs environnements respectifs.
4. Lancer manuellement le workflow **Market Agent** une première fois pour vérifier les diagnostics.

La clé publique/anonyme est utilisée par l'interface connectée. La clé `service_role` reste exclusivement dans les secrets GitHub Actions et n'est jamais envoyée au navigateur.
