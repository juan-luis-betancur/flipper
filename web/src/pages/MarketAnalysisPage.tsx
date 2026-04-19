import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  Cell,
} from 'recharts'
import { requireSupabase } from '../lib/supabase'
import type { Property } from '../types/db'
import { formatCOP, formatCOPPerM2 } from '../lib/format'
import { mean, median } from '../lib/stats'
import { MarketMap } from '../components/MarketMap'
import {
  AGGREGATION_LABELS,
  DIMENSION_KEYS,
  DIMENSION_LABELS,
  NUMERIC_AXIS_KEYS,
  NUMERIC_AXIS_LABELS,
  type Aggregation,
  type DimensionKey,
  type NumericAxisKey,
  axisUnitSuffix,
  buildAggregatedBarRows,
  formatNumericForChart,
  getNumericValue,
} from '../lib/marketChartConfig'

type Period = '7d' | '30d' | 'all'

const BAR_COLORS = [
  '#6366f1',
  '#8b5cf6',
  '#a855f7',
  '#22c55e',
  '#06b6d4',
  '#f59e0b',
  '#f97316',
  '#ec4899',
]

function cutoff(period: Period): string | null {
  if (period === 'all') return null
  const d = new Date()
  d.setDate(d.getDate() - (period === '7d' ? 7 : 30))
  return d.toISOString()
}

type BarrioRow = {
  barrio: string
  count: number
  precio_avg: number | null
  m2_avg: number | null
  m2_median: number | null
  area_avg: number | null
  age_avg: number | null
  pct_remodel: number | null
}

export function MarketAnalysisPage() {
  const supabase = requireSupabase()
  const [period, setPeriod] = useState<Period>('30d')
  const [barriosSel, setBarriosSel] = useState<string[]>([])
  const [props, setProps] = useState<Property[]>([])
  const [sort, setSort] = useState<{ key: keyof BarrioRow; dir: 'asc' | 'desc' }>({
    key: 'count',
    dir: 'desc',
  })
  const [scatterX, setScatterX] = useState<NumericAxisKey>('area')
  const [scatterY, setScatterY] = useState<NumericAxisKey>('price')
  const [barDim, setBarDim] = useState<DimensionKey>('es_remodelado')
  const [barMetric, setBarMetric] = useState<NumericAxisKey>('precio_por_m2')
  const [barAgg, setBarAgg] = useState<Aggregation>('mean')

  const load = useCallback(async () => {
    const { data: u } = await supabase.auth.getUser()
    const uid = u.user?.id
    if (!uid) return
    let q = supabase.from('properties').select('*').eq('user_id', uid)
    const c = cutoff(period)
    if (c) q = q.gte('fecha_scrapeo', c)
    const { data, error } = await q
    if (error) {
      console.error(error)
      return
    }
    setProps((data ?? []) as Property[])
  }, [supabase, period])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    const ch = supabase
      .channel('properties-changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'properties' },
        () => {
          void load()
        },
      )
    void ch.subscribe((status) => {
      if (status === 'CHANNEL_ERROR') {
        console.warn('Realtime no disponible; activa replicación en Supabase para `properties`.')
      }
    })
    return () => {
      void supabase.removeChannel(ch)
    }
  }, [supabase, load])

  const barriosAll = useMemo(() => {
    const s = new Set<string>()
    for (const p of props) {
      if (p.barrio) s.add(p.barrio)
    }
    return [...s].sort()
  }, [props])

  const filtered = useMemo(() => {
    if (!barriosSel.length) return props
    return props.filter((p) => p.barrio && barriosSel.includes(p.barrio))
  }, [props, barriosSel])

  const daysLabel = period === '7d' ? 7 : period === '30d' ? 30 : 'todos los'

  const barrioColor = useMemo(() => {
    const m: Record<string, string> = {}
    barriosAll.forEach((b, i) => {
      m[b] = BAR_COLORS[i % BAR_COLORS.length]!
    })
    return m
  }, [barriosAll])

  const scatterData = useMemo(() => {
    const out: {
      x: number
      y: number
      name: string | null
      barrio: string | null
      price: number | null
      fill: string
    }[] = []
    for (const p of filtered) {
      const x = getNumericValue(p, scatterX)
      const y = getNumericValue(p, scatterY)
      if (x == null || y == null || !Number.isFinite(x) || !Number.isFinite(y)) continue
      out.push({
        x,
        y,
        name: p.title,
        barrio: p.barrio,
        price: p.price,
        fill: p.barrio ? (barrioColor[p.barrio] ?? '#6366f1') : '#6366f1',
      })
    }
    return out
  }, [filtered, scatterX, scatterY, barrioColor])

  const barRows = useMemo(
    () => buildAggregatedBarRows(filtered, barDim, barMetric, barAgg),
    [filtered, barDim, barMetric, barAgg],
  )

  const barFootnote = useMemo(() => {
    if (!barRows.length) {
      return 'Elige otra dimensión o métrica: no hay valores numéricos en el filtro actual.'
    }
    const totalN = barRows.reduce((s, r) => s + r.n, 0)
    const dimLabel = DIMENSION_LABELS[barDim]
    const metricLabel = NUMERIC_AXIS_LABELS[barMetric]
    const aggLabel = AGGREGATION_LABELS[barAgg]
    let extra = ''
    if (barRows.length === 2) {
      const a = barRows[0]
      const b = barRows[1]
      if (a && b && a.v > 0 && b.v > 0) {
        const hi = a.v >= b.v ? a : b
        const lo = a.v >= b.v ? b : a
        const pct = Math.round(((hi.v - lo.v) / lo.v) * 100)
        extra = ` «${hi.name}» lleva un ${aggLabel.toLowerCase()} de ${metricLabel} ~${pct}% ${pct >= 0 ? 'por encima' : 'por debajo'} de «${lo.name}».`
      }
    }
    return `${aggLabel} de ${metricLabel} por ${dimLabel}. ${totalN} propiedades con valor en esta vista.${extra}`
  }, [barRows, barDim, barMetric, barAgg])

  const tableRows: BarrioRow[] = useMemo(() => {
    const by = new Map<string, Property[]>()
    for (const p of filtered) {
      const b = p.barrio ?? 'Sin barrio'
      if (!by.has(b)) by.set(b, [])
      by.get(b)!.push(p)
    }
    const rows: BarrioRow[] = []
    for (const [barrio, list] of by) {
      const prices = list.map((p) => p.price).filter((x): x is number => x != null)
      const m2s = list.map((p) => p.precio_por_m2).filter((x): x is number => x != null)
      const areas = list.map((p) => p.area).filter((x): x is number => x != null)
      const ages = list
        .map((p) => p.antiguedad_max_anos ?? p.antiguedad)
        .filter((x): x is number => x != null)
      const rem = list.filter((p) => p.es_remodelado).length
      rows.push({
        barrio,
        count: list.length,
        precio_avg: mean(prices),
        m2_avg: mean(m2s),
        m2_median: median(m2s),
        area_avg: mean(areas),
        age_avg: mean(ages),
        pct_remodel: list.length ? Math.round((rem / list.length) * 100) : null,
      })
    }
    const mul = sort.dir === 'asc' ? 1 : -1
    rows.sort((a, b) => {
      const va = a[sort.key]
      const vb = b[sort.key]
      if (va == null && vb == null) return 0
      if (va == null) return 1
      if (vb == null) return -1
      if (typeof va === 'string' && typeof vb === 'string') return va.localeCompare(vb) * mul
      return (Number(va) - Number(vb)) * mul
    })
    return rows
  }, [filtered, sort])

  const toggleSort = (key: keyof BarrioRow) => {
    setSort((s) =>
      s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'desc' },
    )
  }

  if (filtered.length < 10) {
    return (
      <div className="rounded-lg border border-border bg-card p-10 text-center text-text-secondary">
        <h1 className="mb-2 text-xl font-semibold text-text">Análisis Comparativo de Mercado</h1>
        <p>
          Necesitas al menos 10 propiedades scrapeadas para ver análisis significativos. Configura una
          fuente y ejecuta el scraper.
        </p>
        <p className="mt-2 text-sm text-text-muted">Actualmente: {filtered.length}</p>
      </div>
    )
  }

  return (
    <div className="space-y-10">
      <header className="grid gap-4 border-b border-border pb-6 lg:grid-cols-12 lg:items-end">
        <div className="lg:col-span-6">
          <h1 className="text-2xl font-semibold tracking-tight">Análisis Comparativo de Mercado</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Basado en {filtered.length} propiedades scrapeadas en los últimos {daysLabel}{' '}
            {period !== 'all' ? 'días' : 'tiempo'}
          </p>
        </div>
        <div className="flex flex-wrap gap-3 lg:col-span-6 lg:justify-end">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as Period)}
            className="rounded-md border border-border bg-bg-secondary px-3 py-2 text-sm text-text"
          >
            <option value="7d">Últimos 7 días</option>
            <option value="30d">Último mes</option>
            <option value="all">Todo</option>
          </select>
        </div>
        <div className="lg:col-span-12">
          <p className="mb-2 text-xs text-text-muted">Zonas (barrios)</p>
          <div className="flex flex-wrap gap-1">
            {barriosAll.map((b) => {
              const on = barriosSel.includes(b)
              return (
                <button
                  key={b}
                  type="button"
                  onClick={() =>
                    setBarriosSel((f) => (on ? f.filter((x) => x !== b) : [...f, b]))
                  }
                  className={`rounded-full border px-2 py-0.5 text-xs ${
                    on ? 'border-accent text-accent' : 'border-border text-text-secondary'
                  }`}
                >
                  {b}
                </button>
              )
            })}
            {barriosSel.length > 0 && (
              <button
                type="button"
                className="text-xs text-text-muted underline"
                onClick={() => setBarriosSel([])}
              >
                Limpiar
              </button>
            )}
          </div>
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-4">
          <h2 className="mb-2 text-sm font-medium text-text-secondary">
            {NUMERIC_AXIS_LABELS[scatterY]} vs {NUMERIC_AXIS_LABELS[scatterX]}
          </h2>
          <div className="mb-3 flex flex-wrap gap-2">
            <label className="flex items-center gap-2 text-xs text-text-secondary">
              Eje X
              <select
                value={scatterX}
                onChange={(e) => setScatterX(e.target.value as NumericAxisKey)}
                className="rounded-md border border-border bg-bg-secondary px-2 py-1 text-text"
              >
                {NUMERIC_AXIS_KEYS.map((k) => (
                  <option key={k} value={k}>
                    {NUMERIC_AXIS_LABELS[k]}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 text-xs text-text-secondary">
              Eje Y
              <select
                value={scatterY}
                onChange={(e) => setScatterY(e.target.value as NumericAxisKey)}
                className="rounded-md border border-border bg-bg-secondary px-2 py-1 text-text"
              >
                {NUMERIC_AXIS_KEYS.map((k) => (
                  <option key={k} value={k}>
                    {NUMERIC_AXIS_LABELS[k]}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
                <CartesianGrid stroke="#e7e5de" strokeDasharray="3 3" />
                <XAxis
                  type="number"
                  dataKey="x"
                  name={NUMERIC_AXIS_LABELS[scatterX]}
                  unit={axisUnitSuffix(scatterX)}
                  stroke="#98a0b3"
                  tick={{ fill: '#52607a', fontSize: 11 }}
                />
                <YAxis
                  type="number"
                  dataKey="y"
                  name={NUMERIC_AXIS_LABELS[scatterY]}
                  unit={axisUnitSuffix(scatterY)}
                  stroke="#98a0b3"
                  tick={{ fill: '#52607a', fontSize: 11 }}
                />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  content={({ active, payload }) => {
                    if (!active || !payload?.[0]) return null
                    const p = payload[0].payload as {
                      name?: string | null
                      price?: number | null
                      x: number
                      y: number
                      barrio?: string | null
                    }
                    return (
                      <div className="rounded border border-border bg-card px-3 py-2 text-xs text-text shadow-lg">
                        <div className="font-medium">{p.name ?? '—'}</div>
                        <div>{formatCOP(p.price ?? null)}</div>
                        <div>
                          {NUMERIC_AXIS_LABELS[scatterX]}: {formatNumericForChart(scatterX, p.x)}
                        </div>
                        <div>
                          {NUMERIC_AXIS_LABELS[scatterY]}: {formatNumericForChart(scatterY, p.y)}
                        </div>
                        {p.barrio ? <div>{p.barrio}</div> : null}
                      </div>
                    )
                  }}
                />
                <Scatter name="Props" data={scatterData} shape="circle">
                  {scatterData.map((_, i) => (
                    <Cell key={i} fill={scatterData[i]!.fill} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-2 flex flex-wrap gap-2 text-[10px] text-text-muted">
            {barriosAll.slice(0, 8).map((b) => (
              <span key={b} className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full" style={{ background: barrioColor[b] }} />
                {b}
              </span>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-4">
          <h2 className="mb-3 text-sm font-medium text-text-secondary">Mapa por precio / m²</h2>
          <MarketMap properties={filtered} />
        </div>
      </section>

      <section className="rounded-lg border border-border bg-card p-4">
        <h2 className="mb-2 text-sm font-medium text-text-secondary">Barras por dimensión</h2>
        <div className="mb-3 flex flex-wrap gap-2">
          <label className="flex items-center gap-2 text-xs text-text-secondary">
            Eje X (dimensión)
            <select
              value={barDim}
              onChange={(e) => setBarDim(e.target.value as DimensionKey)}
              className="max-w-[200px] rounded-md border border-border bg-bg-secondary px-2 py-1 text-text"
            >
              {DIMENSION_KEYS.map((k) => (
                <option key={k} value={k}>
                  {DIMENSION_LABELS[k]}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2 text-xs text-text-secondary">
            Eje Y (métrica)
            <select
              value={barMetric}
              onChange={(e) => setBarMetric(e.target.value as NumericAxisKey)}
              className="max-w-[200px] rounded-md border border-border bg-bg-secondary px-2 py-1 text-text"
            >
              {NUMERIC_AXIS_KEYS.map((k) => (
                <option key={k} value={k}>
                  {NUMERIC_AXIS_LABELS[k]}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2 text-xs text-text-secondary">
            Agregación
            <select
              value={barAgg}
              onChange={(e) => setBarAgg(e.target.value as Aggregation)}
              className="rounded-md border border-border bg-bg-secondary px-2 py-1 text-text"
            >
              {(Object.keys(AGGREGATION_LABELS) as Aggregation[]).map((k) => (
                <option key={k} value={k}>
                  {AGGREGATION_LABELS[k]}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="h-[280px]">
          {barRows.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barRows} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                <CartesianGrid stroke="#e7e5de" strokeDasharray="3 3" />
                <XAxis
                  dataKey="name"
                  stroke="#98a0b3"
                  tick={{ fill: '#52607a', fontSize: 10 }}
                  interval={0}
                  angle={barRows.length > 6 ? -22 : 0}
                  textAnchor={barRows.length > 6 ? 'end' : 'middle'}
                  height={barRows.length > 6 ? 72 : 36}
                />
                <YAxis stroke="#98a0b3" tick={{ fill: '#52607a', fontSize: 11 }} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.[0]) return null
                    const row = payload[0].payload as { name: string; v: number; n: number }
                    return (
                      <div
                        className="rounded border border-border px-3 py-2 text-xs text-text shadow-lg"
                        style={{ background: '#ffffff', borderColor: '#e7e5de' }}
                      >
                        <div className="font-medium">{row.name}</div>
                        <div>{formatNumericForChart(barMetric, row.v)}</div>
                        <div className="text-text-muted">n = {row.n}</div>
                      </div>
                    )
                  }}
                />
                <Bar dataKey="v" name={NUMERIC_AXIS_LABELS[barMetric]}>
                  {barRows.map((_, i) => (
                    <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]!} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="flex h-full items-center justify-center text-sm text-text-muted">
              No hay datos para esta combinación de dimensión y métrica.
            </p>
          )}
        </div>
        <p className="mt-3 text-center text-sm text-text-secondary">{barFootnote}</p>
      </section>

      <section className="rounded-lg border border-border bg-card p-4">
        <h2 className="mb-3 text-sm font-medium text-text-secondary">Resumen por barrio</h2>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[800px] text-left text-sm">
            <thead>
              <tr className="border-b border-border text-xs text-text-muted">
                {(
                  [
                    ['barrio', 'Barrio'],
                    ['count', 'Total'],
                    ['precio_avg', 'Precio prom.'],
                    ['m2_avg', '$/m² prom.'],
                    ['m2_median', '$/m² mediana'],
                    ['area_avg', 'Área prom.'],
                    ['age_avg', 'Antig. prom.'],
                    ['pct_remodel', '% remodel.'],
                  ] as const
                ).map(([key, label]) => (
                  <th key={key} className="cursor-pointer p-2 hover:text-text" onClick={() => toggleSort(key)}>
                    {label}
                    {sort.key === key ? (sort.dir === 'asc' ? ' ↑' : ' ↓') : ''}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableRows.map((r) => (
                <tr key={r.barrio} className="border-b border-border/50 hover:bg-card-hover/40">
                  <td className="p-2 font-medium">{r.barrio}</td>
                  <td className="p-2 font-mono-nums">{r.count}</td>
                  <td className="p-2 font-mono-nums">{formatCOP(r.precio_avg)}</td>
                  <td className="p-2 font-mono-nums">{formatCOPPerM2(r.m2_avg)}</td>
                  <td className="p-2 font-mono-nums">{formatCOPPerM2(r.m2_median)}</td>
                  <td className="p-2 font-mono-nums">{r.area_avg != null ? `${r.area_avg.toFixed(0)} m²` : '—'}</td>
                  <td className="p-2 font-mono-nums">{r.age_avg != null ? `${r.age_avg.toFixed(0)} años` : '—'}</td>
                  <td className="p-2 font-mono-nums">{r.pct_remodel ?? '—'}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
