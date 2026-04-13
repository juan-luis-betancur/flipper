export type PublicationFilter =
  | 'today'
  | 'yesterday'
  | 'this_week'
  | 'last_15_days'
  | 'last_30_days'
  | 'last_40_days'
  | 'none'
export type ListingPlatform = 'finca_raiz' | 'mercado_libre'
export type ScraperRunStatus = 'pending' | 'running' | 'success' | 'failed'
export type SavedVia = 'web' | 'telegram'

export interface ScrapingSource {
  id: string
  user_id: string
  name: string
  platform: ListingPlatform
  /** URL de listado web ML; solo ``mercado_libre``. */
  list_url: string | null
  neighborhoods: string[]
  publication_filter: PublicationFilter
  is_active: boolean
  last_run_at: string | null
  last_run_properties_count: number | null
  last_run_error: string | null
  created_at: string
  updated_at: string
}

export interface AlertFilter {
  id: string
  user_id: string
  name: string
  price_min: number | null
  price_max: number | null
  price_m2_min: number | null
  price_m2_max: number | null
  area_min: number | null
  area_max: number | null
  rooms_min: number | null
  baths_min: number | null
  max_age_years: number | null
  neighborhoods: string[] | null
  required_features: string[] | null
  send_telegram: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Property {
  id: string
  user_id: string
  external_id: string
  platform: ListingPlatform
  url: string
  title: string | null
  price: number | null
  precio_por_m2: number | null
  administracion: number | null
  predial: number | null
  area: number | null
  area_total: number | null
  habitaciones: number | null
  banos: number | null
  parqueaderos: number | null
  piso: number | null
  pisos_totales: number | null
  antiguedad: number | null
  /** Etiqueta de rango tipo Finca Raíz (ej. De 9 a 15 años). */
  antiguedad_rango: string | null
  /** Límite superior del rango en años (1, 8, 15, 30, 45). */
  antiguedad_max_anos: number | null
  estrato: number | null
  ano_construccion: number | null
  barrio: string | null
  zona: string | null
  ciudad: string | null
  direccion: string | null
  latitud: number | null
  longitud: number | null
  tiene_ascensor: boolean | null
  tiene_porteria: boolean | null
  /** Portería / vigilancia / recepción 24h (comodidades o descripción). */
  tiene_porteria_24h: boolean | null
  tiene_balcon: boolean | null
  tiene_parqueadero: boolean | null
  tiene_gimnasio: boolean | null
  tiene_piscina: boolean | null
  tiene_cuarto_util: boolean | null
  tiene_zona_ropas: boolean | null
  es_remodelado: boolean | null
  tipo_cocina: string | null
  descripcion: string | null
  fotos: string[] | null
  nombre_anunciante: string | null
  tipo_anunciante: string | null
  fecha_publicacion: string | null
  fecha_scrapeo: string
  datos_crudos: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface SavedPropertyRow {
  id: string
  user_id: string
  property_id: string
  notes: string | null
  guardada_via: SavedVia
  fecha_guardado: string
  property?: Property
}

export interface ScraperRun {
  id: string
  source_id: string | null
  user_id: string
  fecha_inicio: string
  fecha_fin: string | null
  estado: ScraperRunStatus
  total_encontradas: number | null
  nuevas: number | null
  enviadas_a_telegram: number | null
  mensaje_error: string | null
  log_resumen: string | null
  etapa: string | null
}

export interface TelegramSettings {
  user_id: string
  chat_id: string | null
  bot_token: string | null
  is_active: boolean
  updated_at: string
}
