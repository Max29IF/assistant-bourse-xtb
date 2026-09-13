-- ============================================================
-- VISION FUTURE V38.7 — IMPORT IMMOBILIER / GESTION LOCATIVE
-- Traçabilité + déduplication des relevés comptables
-- Compatible avec le RLS immobilier existant
-- ============================================================

begin;

alter table public.real_estate_cashflows
    add column if not exists source_import_hash text,
    add column if not exists source_row_key text,
    add column if not exists source_provider text,
    add column if not exists source_filename text;

-- Une même écriture comptable importée dans deux relevés qui se chevauchent
-- ne doit pas être comptée deux fois.
create unique index if not exists real_estate_cashflows_source_row_uniq
on public.real_estate_cashflows(user_id, property_id, source_row_key);

create index if not exists real_estate_cashflows_import_hash_idx
on public.real_estate_cashflows(user_id, source_import_hash);

commit;

-- Vérification
select
    column_name,
    data_type
from information_schema.columns
where table_schema = 'public'
  and table_name = 'real_estate_cashflows'
  and column_name in (
      'source_import_hash',
      'source_row_key',
      'source_provider',
      'source_filename'
  )
order by column_name;
