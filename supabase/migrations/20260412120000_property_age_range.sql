-- Antigüedad según rangos Finca Raíz: etiqueta + límite superior numérico para filtros.

alter table public.properties add column antiguedad_rango text;
alter table public.properties add column antiguedad_max_anos smallint;

comment on column public.properties.antiguedad_rango is
  'Etiqueta de antigüedad tipo Finca Raíz (ej. De 9 a 15 años).';

comment on column public.properties.antiguedad_max_anos is
  'Límite superior en años para el rango (1, 8, 15, 30, 45 según UI FR).';
