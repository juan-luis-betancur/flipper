import type { Property } from '../types/db'
import { formatCOP, formatCOPPerM2 } from './format'
import { mean, median, sum } from './stats'

/** Campos numéricos comparables en scatter y como métrica Y en barras. */
export const NUMERIC_AXIS_KEYS = [
  'price',
  'precio_por_m2',
  'area',
  'area_total',
  'habitaciones',
  'banos',
  'parqueaderos',
  'piso',
  'pisos_totales',
  'antiguedad',
  'antiguedad_max_anos',
  'estrato',
  'ano_construccion',
  'administracion',
  'predial',
] as const

export type NumericAxisKey = (typeof NUMERIC_AXIS_KEYS)[number]

export const NUMERIC_AXIS_LABELS: Record<NumericAxisKey, string> = {
  price: 'Precio',
  precio_por_m2: 'Precio / m²',
  area: 'Área (m²)',
  area_total: 'Área total (m²)',
  habitaciones: 'Habitaciones',
  banos: 'Baños',
  parqueaderos: 'Parqueaderos',
  piso: 'Piso',
  pisos_totales: 'Pisos del edificio',
  antiguedad: 'Antigüedad (años, legacy)',
  antiguedad_max_anos: 'Antigüedad máx. (años)',
  estrato: 'Estrato',
  ano_construccion: 'Año construcción',
  administracion: 'Administración (COP)',
  predial: 'Predial (COP)',
}

/** Dimensión categórica en eje X del gráfico de barras. Incluye `tiene_porteria_24h` (24h) y `tiene_porteria` (genérico FR). */
export const DIMENSION_KEYS = [
  'es_remodelado',
  'antiguedad_rango',
  'barrio',
  'zona',
  'ciudad',
  'tipo_anunciante',
  'tipo_cocina',
  'estrato',
  'tiene_ascensor',
  'tiene_porteria',
  'tiene_porteria_24h',
  'tiene_balcon',
  'tiene_parqueadero',
  'tiene_gimnasio',
  'tiene_piscina',
  'tiene_cuarto_util',
  'tiene_zona_ropas',
] as const

export type DimensionKey = (typeof DIMENSION_KEYS)[number]

export const DIMENSION_LABELS: Record<DimensionKey, string> = {
  es_remodelado: 'Remodelado',
  antiguedad_rango: 'Antigüedad (rango FR)',
  barrio: 'Barrio',
  zona: 'Zona',
  ciudad: 'Ciudad',
  tipo_anunciante: 'Tipo anunciante',
  tipo_cocina: 'Tipo cocina',
  estrato: 'Estrato',
  tiene_ascensor: 'Ascensor',
  tiene_porteria: 'Portería (genérico)',
  tiene_porteria_24h: 'Portería 24h',
  tiene_balcon: 'Balcón',
  tiene_parqueadero: 'Parqueadero',
  tiene_gimnasio: 'Gimnasio',
  tiene_piscina: 'Piscina',
  tiene_cuarto_util: 'Cuarto útil',
  tiene_zona_ropas: 'Zona ropas',
}

export type Aggregation = 'mean' | 'sum' | 'median'

export const AGGREGATION_LABELS: Record<Aggregation, string> = {
  mean: 'Promedio',
  sum: 'Suma',
  median: 'Mediana',
}

const intFmt = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 })

export function getNumericValue(p: Property, key: NumericAxisKey): number | null {
  const v = p[key]
  if (v == null) return null
  if (typeof v === 'boolean') return null
  const n = typeof v === 'number' ? v : Number(v)
  return Number.isFinite(n) ? n : null
}

function boolLabel(v: boolean | null | undefined): string {
  if (v === true) return 'Sí'
  if (v === false) return 'No'
  return 'Sin dato'
}

/** Etiqueta estable para agrupar por dimensión. */
export function getDimensionLabel(p: Property, key: DimensionKey): string {
  switch (key) {
    case 'es_remodelado':
      return boolLabel(p.es_remodelado)
    case 'tiene_ascensor':
    case 'tiene_porteria':
    case 'tiene_porteria_24h':
    case 'tiene_balcon':
    case 'tiene_parqueadero':
    case 'tiene_gimnasio':
    case 'tiene_piscina':
    case 'tiene_cuarto_util':
    case 'tiene_zona_ropas':
      return boolLabel(p[key] as boolean | null | undefined)
    case 'estrato': {
      const e = p.estrato
      return e != null ? `Estrato ${e}` : 'Sin dato'
    }
    default: {
      const s = p[key]
      if (s == null || String(s).trim() === '') return 'Sin dato'
      return String(s).trim()
    }
  }
}

export function formatNumericForChart(key: NumericAxisKey, n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return '—'
  if (key === 'price' || key === 'administracion' || key === 'predial') return formatCOP(n)
  if (key === 'precio_por_m2') return formatCOPPerM2(n)
  if (
    key === 'area' ||
    key === 'area_total' ||
    key === 'habitaciones' ||
    key === 'banos' ||
    key === 'parqueaderos' ||
    key === 'piso' ||
    key === 'pisos_totales' ||
    key === 'antiguedad' ||
    key === 'antiguedad_max_anos' ||
    key === 'estrato' ||
    key === 'ano_construccion'
  ) {
    return intFmt.format(Math.round(n))
  }
  return formatCOP(n)
}

export function axisUnitSuffix(key: NumericAxisKey): string {
  if (key === 'area' || key === 'area_total') return ' m²'
  if (key === 'antiguedad' || key === 'antiguedad_max_anos') return ' años'
  if (key === 'precio_por_m2') return ' /m²'
  if (key === 'price' || key === 'administracion' || key === 'predial') return ' COP'
  return ''
}

function aggregateValues(ys: number[], agg: Aggregation): number | null {
  if (agg === 'mean') return mean(ys)
  if (agg === 'sum') return sum(ys)
  return median(ys)
}

export type BarAggRow = { name: string; v: number; n: number }

/** Agrupa por dimensión, agrega métrica; si hay muchas categorías, colapsa el resto en «Otros». */
export function buildAggregatedBarRows(
  properties: Property[],
  dim: DimensionKey,
  metric: NumericAxisKey,
  agg: Aggregation,
  maxGroups = 15,
): BarAggRow[] {
  const groups = new Map<string, number[]>()
  for (const p of properties) {
    const lab = getDimensionLabel(p, dim)
    const y = getNumericValue(p, metric)
    if (y == null) continue
    if (!groups.has(lab)) groups.set(lab, [])
    groups.get(lab)!.push(y)
  }
  type Row = { name: string; ys: number[]; n: number; v: number }
  let rows: Row[] = [...groups.entries()].map(([name, ys]) => {
    const v = aggregateValues(ys, agg)
    return { name, ys, n: ys.length, v: v ?? 0 }
  })
  rows.sort((a, b) => b.n - a.n)
  if (rows.length <= maxGroups) {
    return rows.map(({ name, v, n }) => ({ name, v, n }))
  }
  const head = rows.slice(0, maxGroups)
  const tail = rows.slice(maxGroups)
  const pooled = tail.flatMap((r) => r.ys)
  const pooledV = aggregateValues(pooled, agg) ?? 0
  return [
    ...head.map(({ name, v, n }) => ({ name, v, n })),
    { name: 'Otros', v: pooledV, n: pooled.length },
  ]
}
