-- Segunda plataforma de listados: Mercado Libre (URL de listado web + PoW en backend).

do $migration$
begin
  if not exists (
    select 1
    from pg_enum e
    join pg_type t on t.oid = e.enumtypid
    join pg_namespace n on n.oid = t.typnamespace
    where n.nspname = 'public'
      and t.typname = 'listing_platform'
      and e.enumlabel = 'mercado_libre'
  ) then
    alter type listing_platform add value 'mercado_libre';
  end if;
end;
$migration$;

alter table public.scraping_sources
  add column if not exists list_url text;

comment on column public.scraping_sources.list_url is
  'URL de listado web ML (listado.mercadolibre.com.co/...). Solo para platform=mercado_libre.';
