-- Propiedades: tracking de "pendientes de notificar" para el digest diario Telegram.
-- Quedan NULL al ser insertadas; el cron de digest las marca con now() tras enviarlas.
alter table public.properties
  add column if not exists notificada_at timestamptz null;

-- Índice parcial: la consulta del digest filtra siempre por notificada_at IS NULL
-- y por user_id; este índice es pequeño (solo propiedades pendientes).
create index if not exists properties_pending_notify_idx
  on public.properties (user_id, fecha_scrapeo desc)
  where notificada_at is null;
