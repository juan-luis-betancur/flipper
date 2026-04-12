-- Portería / vigilancia / recepción las 24 horas (heurística scraper).

alter table public.properties add column tiene_porteria_24h boolean default false;

comment on column public.properties.tiene_porteria_24h is
  'True si comodidades o descripción indican portería/vigilancia/recepción 24h (24/7, 24 horas, etc.).';
