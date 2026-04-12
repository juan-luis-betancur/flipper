-- Flipper MVP: core schema, generated precio_por_m2, RLS

-- Extensions
create extension if not exists "pgcrypto";

-- Enums
create type publication_filter as enum ('today', 'yesterday', 'this_week', 'none');
create type listing_platform as enum ('finca_raiz');
create type scraper_run_status as enum ('pending', 'running', 'success', 'failed');
create type saved_via as enum ('web', 'telegram');

-- Profiles (extends auth.users)
create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  full_name text,
  created_at timestamptz not null default now()
);

-- Scraping sources (Finca Raíz URLs built from neighborhoods + filter)
create table public.scraping_sources (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  name text not null,
  platform listing_platform not null default 'finca_raiz',
  neighborhoods text[] not null default '{}',
  publication_filter publication_filter not null default 'today',
  is_active boolean not null default true,
  last_run_at timestamptz,
  last_run_properties_count integer,
  last_run_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index scraping_sources_user_id_idx on public.scraping_sources (user_id);

-- Alert filters (backend applies; one row per user MVP — allow multiple with name)
create table public.alert_filters (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  name text not null default 'Default',
  price_min numeric,
  price_max numeric,
  price_m2_min numeric,
  price_m2_max numeric,
  area_min numeric,
  area_max numeric,
  rooms_min smallint,
  baths_min smallint,
  max_age_years smallint,
  neighborhoods text[] default '{}',
  required_features text[] default '{}',
  send_telegram boolean not null default true,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index alert_filters_user_id_idx on public.alert_filters (user_id);

-- Properties (scraped)
create table public.properties (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  external_id text not null,
  platform listing_platform not null default 'finca_raiz',
  url text not null,
  title text,
  price numeric,
  precio_por_m2 numeric generated always as (
    case
      when area is not null and area > 0 and price is not null then round(price / area, 2)
      else null
    end
  ) stored,
  administracion numeric,
  predial numeric,
  area numeric,
  area_total numeric,
  habitaciones smallint,
  banos smallint,
  parqueaderos smallint,
  piso smallint,
  pisos_totales smallint,
  antiguedad smallint,
  estrato smallint,
  ano_construccion smallint,
  barrio text,
  zona text,
  ciudad text,
  direccion text,
  latitud double precision,
  longitud double precision,
  tiene_ascensor boolean default false,
  tiene_porteria boolean default false,
  tiene_balcon boolean default false,
  tiene_parqueadero boolean default false,
  tiene_gimnasio boolean default false,
  tiene_piscina boolean default false,
  tiene_cuarto_util boolean default false,
  tiene_zona_ropas boolean default false,
  es_remodelado boolean default false,
  tipo_cocina text,
  descripcion text,
  fotos text[] default '{}',
  nombre_anunciante text,
  tipo_anunciante text,
  fecha_publicacion timestamptz,
  fecha_scrapeo timestamptz not null default now(),
  datos_crudos jsonb default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (platform, external_id, user_id)
);

create index properties_user_scrape_idx on public.properties (user_id, fecha_scrapeo desc);
create index properties_user_barrio_idx on public.properties (user_id, barrio);
create index properties_user_pub_idx on public.properties (user_id, fecha_publicacion desc);

-- Saved / favorites
create table public.saved_properties (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  property_id uuid not null references public.properties (id) on delete cascade,
  notes text,
  guardada_via saved_via not null default 'web',
  fecha_guardado timestamptz not null default now(),
  unique (user_id, property_id)
);

create index saved_properties_user_idx on public.saved_properties (user_id, fecha_guardado desc);

-- Scraper execution logs
create table public.scraper_runs (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references public.scraping_sources (id) on delete set null,
  user_id uuid not null references public.profiles (id) on delete cascade,
  fecha_inicio timestamptz not null default now(),
  fecha_fin timestamptz,
  estado scraper_run_status not null default 'pending',
  total_encontradas integer default 0,
  nuevas integer default 0,
  enviadas_a_telegram integer default 0,
  mensaje_error text,
  log_resumen text,
  etapa text
);

create index scraper_runs_source_idx on public.scraper_runs (source_id, fecha_inicio desc);
create index scraper_runs_user_idx on public.scraper_runs (user_id, fecha_inicio desc);

-- Telegram settings (one row per user for MVP)
create table public.telegram_settings (
  user_id uuid primary key references public.profiles (id) on delete cascade,
  chat_id text,
  bot_token text,
  is_active boolean not null default false,
  updated_at timestamptz not null default now()
);

-- Auto-create profile on signup
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, full_name)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)));
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- updated_at helper
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger set_scraping_sources_updated
  before update on public.scraping_sources
  for each row execute function public.set_updated_at();

create trigger set_alert_filters_updated
  before update on public.alert_filters
  for each row execute function public.set_updated_at();

create trigger set_properties_updated
  before update on public.properties
  for each row execute function public.set_updated_at();

create trigger set_telegram_settings_updated
  before update on public.telegram_settings
  for each row execute function public.set_updated_at();

-- RLS
alter table public.profiles enable row level security;
alter table public.scraping_sources enable row level security;
alter table public.alert_filters enable row level security;
alter table public.properties enable row level security;
alter table public.saved_properties enable row level security;
alter table public.scraper_runs enable row level security;
alter table public.telegram_settings enable row level security;

-- Profiles
create policy "profiles_select_own" on public.profiles for select using (id = auth.uid());
create policy "profiles_update_own" on public.profiles for update using (id = auth.uid());

-- Scraping sources
create policy "scraping_sources_all_own" on public.scraping_sources
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

-- Alert filters
create policy "alert_filters_all_own" on public.alert_filters
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

-- Properties
create policy "properties_select_own" on public.properties for select using (user_id = auth.uid());
create policy "properties_insert_own" on public.properties for insert with check (user_id = auth.uid());
create policy "properties_update_own" on public.properties for update using (user_id = auth.uid());
create policy "properties_delete_own" on public.properties for delete using (user_id = auth.uid());

-- Saved
create policy "saved_all_own" on public.saved_properties
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

-- Scraper runs (read own; insert/update typically service role)
create policy "scraper_runs_select_own" on public.scraper_runs for select using (user_id = auth.uid());
create policy "scraper_runs_insert_own" on public.scraper_runs for insert with check (user_id = auth.uid());
create policy "scraper_runs_update_own" on public.scraper_runs for update using (user_id = auth.uid());

-- Telegram
create policy "telegram_all_own" on public.telegram_settings
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

-- Enable Realtime for properties in Supabase Dashboard: Database > Replication > properties
