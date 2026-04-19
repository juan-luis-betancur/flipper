import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { requireSupabase } from '../lib/supabase'
import { formatCOP, formatCOPPerM2, formatRelativeTime } from '../lib/format'
import { medianByGroup } from '../lib/stats'
import type { Property, SavedPropertyRow } from '../types/db'
import clsx from 'clsx'

type SortKey =
  | 'fecha_guardado'
  | 'precio_asc'
  | 'precio_desc'
  | 'm2_asc'
  | 'm2_desc'
  | 'oportunidad'

export function SavedPage() {
  const supabase = requireSupabase()
  const [rows, setRows] = useState<SavedPropertyRow[]>([])
  const [view, setView] = useState<'grid' | 'list'>('grid')
  const [sort, setSort] = useState<SortKey>('fecha_guardado')
  const [barrios, setBarrios] = useState<string[]>([])
  const [barrioFilter, setBarrioFilter] = useState<string[]>([])
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 20000000000])

  const load = useCallback(async () => {
    const { data: u } = await supabase.auth.getUser()
    const uid = u.user?.id
    if (!uid) return
    const { data, error } = await supabase
      .from('saved_properties')
      .select('*, property:properties(*)')
      .eq('user_id', uid)
      .order('fecha_guardado', { ascending: false })
    if (error) {
      toast.error(error.message)
      return
    }
    const list = (data ?? []) as SavedPropertyRow[]
    setRows(list)
    const bs = new Set<string>()
    for (const r of list) {
      const b = r.property?.barrio
      if (b) bs.add(b)
    }
    setBarrios([...bs])
    const prices = list.map((r) => r.property?.price).filter((p): p is number => p != null)
    if (prices.length) {
      setPriceRange([Math.min(...prices), Math.max(...prices)])
    }
  }, [supabase])

  useEffect(() => {
    load()
  }, [load])

  const medians = useMemo(() => {
    const props = rows.map((r) => r.property).filter(Boolean) as Property[]
    return medianByGroup(props, (p) => p.barrio, (p) => p.precio_por_m2)
  }, [rows])

  const filteredSorted = useMemo(() => {
    let list = [...rows]
    if (barrioFilter.length) {
      list = list.filter((r) => r.property?.barrio && barrioFilter.includes(r.property.barrio))
    }
    list = list.filter((r) => {
      const p = r.property?.price
      if (p == null) return true
      return p >= priceRange[0] && p <= priceRange[1]
    })
    const opp = (r: SavedPropertyRow) => {
      const p = r.property
      if (!p?.barrio || p.precio_por_m2 == null) return Infinity
      const m = medians[p.barrio]
      if (m == null || m <= 0) return Infinity
      return p.precio_por_m2 / m
    }
    list.sort((a, b) => {
      switch (sort) {
        case 'precio_asc':
          return (a.property?.price ?? 0) - (b.property?.price ?? 0)
        case 'precio_desc':
          return (b.property?.price ?? 0) - (a.property?.price ?? 0)
        case 'm2_asc':
          return (a.property?.precio_por_m2 ?? 0) - (b.property?.precio_por_m2 ?? 0)
        case 'm2_desc':
          return (b.property?.precio_por_m2 ?? 0) - (a.property?.precio_por_m2 ?? 0)
        case 'oportunidad':
          return opp(a) - opp(b)
        default:
          return new Date(b.fecha_guardado).getTime() - new Date(a.fecha_guardado).getTime()
      }
    })
    return list
  }, [rows, barrioFilter, priceRange, sort, medians])

  async function removeSaved(id: string) {
    const { error } = await supabase.from('saved_properties').delete().eq('id', id)
    if (error) toast.error(error.message)
    else {
      toast.success('Eliminada de guardados')
      load()
    }
  }

  if (!rows.length) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <p className="mb-2 max-w-md text-text-secondary">
          Aún no has guardado ninguna propiedad. Las propiedades que guardes desde Telegram aparecerán
          aquí automáticamente.
        </p>
        <Link
          to="/properties/config"
          className="mt-4 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90"
        >
          Ir a Configuración
        </Link>
      </div>
    )
  }

  return (
    <div>
      <header className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Propiedades Guardadas</h1>
          <p className="text-sm text-text-secondary">{filteredSorted.length} de {rows.length}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex rounded-md border border-border p-0.5">
            <button
              type="button"
              onClick={() => setView('grid')}
              className={clsx(
                'rounded px-3 py-1 text-sm',
                view === 'grid' ? 'bg-card text-text' : 'text-text-muted',
              )}
            >
              Grid
            </button>
            <button
              type="button"
              onClick={() => setView('list')}
              className={clsx(
                'rounded px-3 py-1 text-sm',
                view === 'list' ? 'bg-card text-text' : 'text-text-muted',
              )}
            >
              Lista
            </button>
          </div>
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as SortKey)}
            className="rounded-md border border-border bg-bg-secondary px-2 py-1.5 text-sm text-text"
          >
            <option value="fecha_guardado">Fecha guardado</option>
            <option value="precio_asc">Precio ↑</option>
            <option value="precio_desc">Precio ↓</option>
            <option value="m2_asc">Precio/m² ↑</option>
            <option value="m2_desc">Precio/m² ↓</option>
            <option value="oportunidad">Mejor oportunidad (m² vs barrio)</option>
          </select>
        </div>
      </header>

      <div className="mb-6 flex flex-wrap gap-4 rounded-lg border border-border bg-card p-4">
        <div>
          <p className="mb-1 text-xs text-text-muted">Barrios</p>
          <div className="flex flex-wrap gap-1">
            {barrios.map((b) => {
              const on = barrioFilter.includes(b)
              return (
                <button
                  key={b}
                  type="button"
                  onClick={() =>
                    setBarrioFilter((f) => (on ? f.filter((x) => x !== b) : [...f, b]))
                  }
                  className={clsx(
                    'rounded-full border px-2 py-0.5 text-xs',
                    on ? 'border-accent text-accent' : 'border-border text-text-secondary',
                  )}
                >
                  {b}
                </button>
              )
            })}
          </div>
        </div>
        <div className="min-w-[200px] flex-1">
          <p className="mb-1 text-xs text-text-muted">Rango precio (COP)</p>
          <div className="flex gap-2">
            <input
              type="number"
              className="w-full rounded border border-border bg-bg-secondary px-2 py-1 text-xs"
              value={priceRange[0]}
              onChange={(e) => setPriceRange([Number(e.target.value), priceRange[1]])}
            />
            <input
              type="number"
              className="w-full rounded border border-border bg-bg-secondary px-2 py-1 text-xs"
              value={priceRange[1]}
              onChange={(e) => setPriceRange([priceRange[0], Number(e.target.value)])}
            />
          </div>
        </div>
      </div>

      {view === 'grid' ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {filteredSorted.map((r) => (
            <PropertyCard
              key={r.id}
              row={r}
              medians={medians}
              onRemove={() => removeSaved(r.id)}
            />
          ))}
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-bg-secondary text-xs text-text-muted">
              <tr>
                <th className="p-2">Título</th>
                <th className="p-2 font-mono-nums">Precio</th>
                <th className="p-2 font-mono-nums">$/m²</th>
                <th className="p-2">Barrio</th>
                <th className="p-2" />
              </tr>
            </thead>
            <tbody>
              {filteredSorted.map((r) => (
                <tr key={r.id} className="border-b border-border/60 hover:bg-card-hover/50">
                  <td className="max-w-[200px] truncate p-2">{r.property?.title}</td>
                  <td className="p-2 font-mono-nums text-text">{formatCOP(r.property?.price ?? null)}</td>
                  <td className="p-2 font-mono-nums text-text-secondary">
                    {formatCOPPerM2(r.property?.precio_por_m2 ?? null)}
                  </td>
                  <td className="p-2 text-text-secondary">{r.property?.barrio}</td>
                  <td className="p-2">
                    <a
                      href={r.property?.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-accent hover:underline"
                    >
                      Ver
                    </a>
                    <button type="button" className="ml-2 text-danger" onClick={() => removeSaved(r.id)}>
                      Quitar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function PropertyCard({
  row,
  medians,
  onRemove,
}: {
  row: SavedPropertyRow
  medians: Record<string, number>
  onRemove: () => void
}) {
  const p = row.property
  if (!p) return null
  const med = p.barrio ? medians[p.barrio] : null
  const opportunity =
    med != null && p.precio_por_m2 != null && p.precio_por_m2 < med * 0.97

  const chips: { k: string; on: boolean | null | undefined }[] = [
    { k: 'Ascensor', on: p.tiene_ascensor },
    { k: 'Portería 24h', on: p.tiene_porteria_24h },
    { k: 'Balcón', on: p.tiene_balcon },
    { k: 'Gimnasio', on: p.tiene_gimnasio },
    { k: 'Piscina', on: p.tiene_piscina },
    { k: 'Remodelado', on: p.es_remodelado },
  ]

  return (
    <article
      className={clsx(
        'flex flex-col overflow-hidden rounded-lg border border-border bg-card transition-shadow',
        opportunity && 'ring-1 ring-opportunity/50 shadow-[0_0_20px_-5px_rgba(249,115,22,0.35)]',
      )}
    >
      <div className="aspect-video bg-bg-secondary">
        {p.fotos?.[0] ? (
          <img src={p.fotos[0]} alt="" className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-text-muted">Sin foto</div>
        )}
      </div>
      <div className="flex flex-1 flex-col p-4">
        <div className="flex items-start justify-between gap-2">
          <p className="font-mono-nums text-xl font-semibold text-text">{formatCOP(p.price)}</p>
          {opportunity && (
            <span className="shrink-0 rounded bg-opportunity/20 px-1.5 py-0.5 text-[10px] font-medium text-opportunity">
              Oportunidad
            </span>
          )}
        </div>
        <p className="font-mono-nums text-sm text-text-secondary">{formatCOPPerM2(p.precio_por_m2)}</p>
        <p className="mt-2 text-xs text-text-muted">
          {p.area ?? '—'} m² · {p.habitaciones ?? '—'} hab · {p.banos ?? '—'} baños · {p.parqueaderos ?? '—'}{' '}
          parq
        </p>
        <p className="mt-1 text-sm text-text-secondary">
          {p.barrio ?? '—'} · Estrato {p.estrato ?? '—'}
        </p>
        <p className="text-xs text-text-muted">
          {p.antiguedad_rango
            ? `${p.antiguedad_rango}${p.antiguedad_max_anos != null ? ` (≤${p.antiguedad_max_anos} años)` : ''}`
            : p.antiguedad_max_anos != null
              ? `≤${p.antiguedad_max_anos} años`
              : p.antiguedad != null
                ? `${p.antiguedad} años`
                : p.ano_construccion
                  ? `Año ${p.ano_construccion}`
                  : '—'}
        </p>
        <div className="mt-2 flex flex-wrap gap-1">
          {chips
            .filter((c) => c.on)
            .map((c) => (
              <span
                key={c.k}
                className="rounded border border-border bg-bg-secondary px-1.5 py-0.5 text-[10px] text-text-secondary"
              >
                {c.k}
              </span>
            ))}
        </div>
        {p.administracion != null && (
          <p className="mt-2 text-xs text-text-muted">Admón: {formatCOP(p.administracion)}/mes</p>
        )}
        <p className="mt-auto pt-3 text-[10px] text-text-muted">
          Guardada {formatRelativeTime(row.fecha_guardado)} vía {row.guardada_via}
        </p>
        <div className="mt-3 flex flex-wrap gap-2 border-t border-border pt-3">
          <a
            href={p.url}
            target="_blank"
            rel="noreferrer"
            className="text-xs text-accent hover:underline"
          >
            Ver en Finca Raíz
          </a>
          <button type="button" className="text-xs text-danger hover:underline" onClick={onRemove}>
            Eliminar
          </button>
          <span className="cursor-not-allowed text-xs text-text-muted" title="Próximamente">
            Convertir en proyecto
          </span>
        </div>
      </div>
    </article>
  )
}
