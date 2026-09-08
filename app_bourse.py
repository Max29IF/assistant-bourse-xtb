-- =========================================================
-- VISION FUTURE — V8 SMART PORTFOLIO & FAST SCANNER
-- A exécuter APRES V7/V7.1
-- =========================================================

-- Traçabilité fine des imports -> données générées
alter table public.portfolio_positions
    add column if not exists source_import_hash text;

alter table public.transactions
    add column if not exists source_import_hash text;

create index if not exists idx_positions_source_import_hash
    on public.portfolio_positions(source_import_hash);

create index if not exists idx_transactions_source_import_hash
    on public.transactions(source_import_hash);

-- Index utiles pour la séparation stricte compte + courtier
create index if not exists idx_positions_account_broker
    on public.portfolio_positions(account, broker);

create index if not exists idx_transactions_account_broker
    on public.transactions(account, broker);

create index if not exists idx_imports_account_broker
    on public.imports(account, broker, imported_at desc);

-- V8 utilise la clé serveur Supabase depuis les Secrets Streamlit.
-- Aucun accès anon public n'est requis.
alter table public.portfolio_positions enable row level security;
alter table public.transactions enable row level security;
alter table public.imports enable row level security;
