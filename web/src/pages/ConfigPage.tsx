import { useCallback, useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { requireSupabase } from '../lib/supabase'
import { buildFincaRaizListadoUrl } from '../lib/fincaRaizUrl'
import { PRESET_NEIGHBORHOODS } from '../constants/neighborhoods'
import type { AlertFilter, ListingPlatform, PublicationFilter, ScrapingSource, TelegramSettings } from '../types/db'
import { ScrapeFab } from '../components/ScrapeFab'
import { CurrencyTextInput } from '../components/CurrencyTextInput'
import { AreaM2TextInput } from '../components/AreaM2TextInput'
import { apiFetch } from '../lib/api'
import { apiErrorMessage } from '../lib/apiErrors'

const PLATFORM_OPTIONS: { value: ListingPlatform; label: string }[] = [
  { value: 'finca_raiz', label: 'Finca Raíz' },
  { value: 'mercado_libre', label: 'Mercado Libre (listado web)' },
]

const PUBLICATION_OPTIONS: { value: PublicationFilter; label: string }[] = [
  { value: 'today', label: 'Hoy' },
  { value: 'yesterday', label: 'Ayer' },
  { value: 'this_week', label: 'Última semana (7 días)' },
  { value: 'last_15_days', label: 'Últimos 15 días' },
  { value: 'last_30_days', label: 'Últimos 30 días' },
  { value: 'last_40_days', label: 'Últimos 40 días' },
  { value: 'none', label: 'Sin filtro' },
]

function emptySourceForm() {
  return {
    name: '',
    platform: 'finca_raiz' as ListingPlatform,
    list_url: '',
    neighborhoods: [] as string[],
    customBarrio: '',
    publication_filter: 'today' as PublicationFilter,
  }
}

export function ConfigPage() {
  const supabase = requireSupabase()
  const [userId, setUserId] = useState<string | null>(null)
  const [sources, setSources] = useState<ScrapingSource[]>([])
  const [filterRow, setFilterRow] = useState<AlertFilter | null>(null)
  const [telegram, setTelegram] = useState<TelegramSettings | null>(null)
  const [telegramOpen, setTelegramOpen] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState(emptySourceForm)
  const [runsBySource, setRunsBySource] = useState<Record<string, { log_resumen: string | null; estado: string }>>({})

  const load = useCallback(async () => {
    const { data: s } = await supabase.auth.getUser()
    const uid = s.user?.id
    if (!uid) return
    setUserId(uid)

    const { data: src } = await supabase
      .from('scraping_sources')
      .select('*')
      .eq('user_id', uid)
      .order('created_at', { ascending: false })
    setSources((src ?? []) as ScrapingSource[])

    const { data: flt } = await supabase.from('alert_filters').select('*').eq('user_id', uid).limit(1).maybeSingle()
    setFilterRow((flt as AlertFilter) ?? null)

    const { data: tg } = await supabase.from('telegram_settings').select('*').eq('user_id', uid).maybeSingle()
    setTelegram((tg as TelegramSettings) ?? null)

    const { data: runs } = await supabase
      .from('scraper_runs')
      .select('source_id, log_resumen, estado, fecha_inicio')
      .eq('user_id', uid)
      .order('fecha_inicio', { ascending: false })
      .limit(200)

    const map: Record<string, { log_resumen: string | null; estado: string }> = {}
    for (const r of runs ?? []) {
      if (r.source_id && !map[r.source_id]) {
        map[r.source_id] = { log_resumen: r.log_resumen, estado: r.estado }
      }
    }
    setRunsBySource(map)
  }, [supabase])

  useEffect(() => {
    load()
  }, [load])

  const previewUrl = useMemo(() => {
    if (form.platform === 'mercado_libre') {
      const u = form.list_url.trim()
      return u || 'https://listado.mercadolibre.com.co/… (pega la URL del listado)'
    }
    return buildFincaRaizListadoUrl(form.neighborhoods, form.publication_filter)
  }, [form.platform, form.list_url, form.neighborhoods, form.publication_filter])

  const globalError = useMemo(() => sources.find((s) => s.last_run_error)?.last_run_error, [sources])

  async function saveSource(e: React.FormEvent) {
    e.preventDefault()
    if (!userId || !form.name.trim()) {
      toast.error('Nombre requerido')
      return
    }
    if (form.platform === 'mercado_libre') {
      const u = form.list_url.trim()
      if (!u.startsWith('https://listado.mercadolibre.com.co')) {
        toast.error('La URL debe ser de listado.mercadolibre.com.co (https)')
        return
      }
    }
    const row = {
      user_id: userId,
      name: form.name.trim(),
      platform: form.platform,
      list_url: form.platform === 'mercado_libre' ? form.list_url.trim() : null,
      neighborhoods: form.platform === 'mercado_libre' ? [] : form.neighborhoods,
      publication_filter:
        form.platform === 'mercado_libre' ? ('none' as PublicationFilter) : form.publication_filter,
      is_active: true,
    }
    if (editingId) {
      const { error } = await supabase.from('scraping_sources').update(row).eq('id', editingId)
      if (error) {
        toast.error(error.message)
        return
      }
      toast.success('Fuente actualizada')
    } else {
      const { error } = await supabase.from('scraping_sources').insert(row)
      if (error) {
        toast.error(error.message)
        return
      }
      toast.success('Fuente guardada')
    }
    setModalOpen(false)
    setEditingId(null)
    setForm(emptySourceForm())
    load()
  }

  function openEdit(s: ScrapingSource) {
    setEditingId(s.id)
    setForm({
      name: s.name,
      platform: s.platform,
      list_url: s.list_url ?? '',
      neighborhoods: [...(s.neighborhoods ?? [])],
      customBarrio: '',
      publication_filter: s.publication_filter,
    })
    setModalOpen(true)
  }

  async function toggleSource(s: ScrapingSource) {
    const { error } = await supabase
      .from('scraping_sources')
      .update({ is_active: !s.is_active })
      .eq('id', s.id)
    if (error) toast.error(error.message)
    else load()
  }

  async function deleteSource(id: string) {
    if (!confirm('¿Eliminar esta fuente?')) return
    const { error } = await supabase.from('scraping_sources').delete().eq('id', id)
    if (error) toast.error(error.message)
    else {
      toast.success('Eliminada')
      load()
    }
  }

  async function saveFilters(e: React.FormEvent) {
    e.preventDefault()
    if (!userId) return
    const f = filterRow ?? defaultFilter(userId)
    const payload = {
      user_id: userId,
      name: f.name || 'Default',
      price_min: num(f.price_min),
      price_max: num(f.price_max),
      price_m2_min: num(f.price_m2_min),
      price_m2_max: num(f.price_m2_max),
      area_min: num(f.area_min),
      area_max: num(f.area_max),
      rooms_min: int(f.rooms_min),
      baths_min: int(f.baths_min),
      max_age_years: int(f.max_age_years),
      neighborhoods: f.neighborhoods ?? [],
      required_features: f.required_features ?? [],
      send_telegram: f.send_telegram,
      is_active: f.is_active,
    }
    if (f.id) {
      const { error } = await supabase.from('alert_filters').update(payload).eq('id', f.id)
      if (error) toast.error(error.message)
      else toast.success('Filtros guardados')
    } else {
      const { error } = await supabase.from('alert_filters').insert(payload)
      if (error) toast.error(error.message)
      else toast.success('Filtros guardados')
    }
    load()
  }

  async function saveTelegram(e: React.FormEvent) {
    e.preventDefault()
    if (!userId) return
    const rawChat = telegram?.chat_id
    const chatTrimmed =
      typeof rawChat === 'string' ? rawChat.trim() || null : rawChat ?? null
    const payload = {
      user_id: userId,
      chat_id: chatTrimmed,
      bot_token: telegram?.bot_token ?? null,
      is_active: !!(chatTrimmed && telegram?.bot_token),
    }
    const { error } = await supabase.from('telegram_settings').upsert(payload)
    if (error) toast.error(error.message)
    else toast.success('Configuración de Telegram guardada')
    load()
  }

  async function testTelegram() {
    try {
      const res = await apiFetch('/api/telegram/test', { method: 'POST' })
      if (!res.ok) throw new Error(await res.text())
      toast.success('Mensaje de prueba enviado')
    } catch (e) {
      toast.error(apiErrorMessage(e))
    }
  }

  function setFilter<K extends keyof AlertFilter>(k: K, v: AlertFilter[K]) {
    setFilterRow((prev) => ({ ...(prev ?? defaultFilter(userId!)), [k]: v }))
  }

  return (
    <div className="relative pb-24">
      {globalError && (
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-text">
          <span>Scraper falló: {globalError}</span>
          <button
            type="button"
            className="rounded-md border border-border bg-card px-3 py-1 text-xs text-text-secondary hover:bg-card-hover"
            onClick={() => load()}
          >
            Reintentar lectura
          </button>
        </div>
      )}

      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">Configuración</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Fuentes, filtros de alerta y Telegram
        </p>
      </header>

      <div className="grid gap-10 lg:grid-cols-12">
        <section className="lg:col-span-7">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-medium">Fuentes de scraping</h2>
            <button
              type="button"
              onClick={() => {
                setEditingId(null)
                setForm(emptySourceForm())
                setModalOpen(true)
              }}
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90"
            >
              + Agregar fuente
            </button>
          </div>

          {sources.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border bg-bg-secondary p-8 text-center text-text-secondary">
              <p className="mb-2 text-text">Agrega tu primera fuente de scraping</p>
              <p className="text-sm">para empezar a recibir propiedades</p>
            </div>
          ) : (
            <ul className="flex flex-col gap-3">
              {sources.map((s) => (
                <li
                  key={s.id}
                  className="rounded-lg border border-border bg-card p-4 transition-colors hover:border-border/80"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h3 className="font-medium text-text">{s.name}</h3>
                      <p className="mt-1 text-xs text-text-secondary">
                        {PLATFORM_OPTIONS.find((o) => o.value === s.platform)?.label ?? s.platform}
                      </p>
                      {s.platform === 'mercado_libre' && s.list_url ? (
                        <p className="mt-2 break-all font-mono text-[11px] text-text-muted">{s.list_url}</p>
                      ) : (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {(s.neighborhoods ?? []).map((b) => (
                            <span
                              key={b}
                              className="rounded-full border border-border bg-bg-secondary px-2 py-0.5 text-xs text-text-secondary"
                            >
                              {b}
                            </span>
                          ))}
                        </div>
                      )}
                      <p className="mt-2 text-xs text-text-muted">
                        Publicación:{' '}
                        {PUBLICATION_OPTIONS.find((o) => o.value === s.publication_filter)?.label}
                      </p>
                    </div>
                    <label className="flex items-center gap-2 text-sm text-text-secondary">
                      <input
                        type="checkbox"
                        checked={s.is_active}
                        onChange={() => toggleSource(s)}
                      />
                      Activa
                    </label>
                  </div>
                  <p className="mt-2 text-xs text-text-muted">
                    Última ejecución:{' '}
                    {s.last_run_at
                      ? new Date(s.last_run_at).toLocaleString('es-CO')
                      : '—'}{' '}
                    · Encontradas: {s.last_run_properties_count ?? '—'}
                  </p>
                  {runsBySource[s.id]?.log_resumen && (
                    <pre className="mt-2 max-h-24 overflow-auto rounded border border-border bg-bg p-2 text-[10px] text-text-muted">
                      {runsBySource[s.id].log_resumen}
                    </pre>
                  )}
                  <div className="mt-3 flex gap-2">
                    <button
                      type="button"
                      onClick={() => openEdit(s)}
                      className="text-sm text-accent hover:underline"
                    >
                      Editar
                    </button>
                    <button
                      type="button"
                      onClick={() => deleteSource(s.id)}
                      className="text-sm text-danger hover:underline"
                    >
                      Eliminar
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="lg:col-span-5">
          <h2 className="mb-4 text-lg font-medium">Filtros de alerta</h2>
          {userId && (
            <form onSubmit={saveFilters} className="space-y-4 rounded-lg border border-border bg-card p-4">
              <FilterFormBody filter={filterRow ?? defaultFilter(userId)} setFilter={setFilter} />
              <button type="submit" className="w-full rounded-md bg-accent py-2 text-sm font-medium text-white">
                Guardar filtros
              </button>
            </form>
          )}
        </section>
      </div>

      <section className="mt-10">
        <button
          type="button"
          onClick={() => setTelegramOpen((o) => !o)}
          className="flex w-full items-center justify-between rounded-lg border border-border bg-bg-secondary px-4 py-3 text-left text-sm font-medium text-text"
        >
          Configuración de Telegram
          <span className="text-text-muted">{telegramOpen ? '▲' : '▼'}</span>
        </button>
        {telegramOpen && (
          <form onSubmit={saveTelegram} className="mt-3 rounded-lg border border-border bg-card p-4 space-y-4">
            <p className={`text-sm ${telegram?.bot_token && telegram?.chat_id ? 'text-success' : 'text-warning'}`}>
              {telegram?.bot_token && telegram?.chat_id ? 'Bot conectado' : 'No configurado'}
            </p>
            <ol className="list-decimal space-y-1 pl-4 text-xs text-text-muted">
              <li>Busca @BotFather en Telegram</li>
              <li>Crea un bot con /newbot y copia el token</li>
              <li>Envía un mensaje a tu bot, luego pega tu chat ID</li>
            </ol>
            <label className="block text-sm text-text-secondary">
              Bot token
              <input
                type="password"
                value={telegram?.bot_token ?? ''}
                onChange={(e) =>
                  setTelegram((t) => ({ ...(t ?? { user_id: userId!, is_active: false, updated_at: '', chat_id: null, bot_token: null }), bot_token: e.target.value }))
                }
                className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-3 py-2 font-mono text-xs text-text"
              />
            </label>
            <label className="block text-sm text-text-secondary">
              Chat ID
              <input
                type="text"
                value={telegram?.chat_id ?? ''}
                onChange={(e) =>
                  setTelegram((t) => ({ ...(t ?? { user_id: userId!, is_active: false, updated_at: '', chat_id: null, bot_token: null }), chat_id: e.target.value }))
                }
                className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-3 py-2 font-mono text-xs text-text"
              />
            </label>
            <div className="flex flex-wrap gap-2">
              <button type="submit" className="rounded-md bg-card-hover px-4 py-2 text-sm text-text">
                Guardar
              </button>
              <button
                type="button"
                onClick={testTelegram}
                className="rounded-md border border-accent px-4 py-2 text-sm text-accent"
              >
                Enviar mensaje de prueba
              </button>
            </div>
          </form>
        )}
      </section>

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg border border-border bg-card p-6 shadow-xl">
            <h3 className="mb-4 text-lg font-medium">{editingId ? 'Editar fuente' : 'Nueva fuente'}</h3>
            <form onSubmit={saveSource} className="space-y-4">
              <label className="block text-sm text-text-secondary">
                Nombre
                <input
                  required
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-3 py-2 text-text"
                />
              </label>
              <label className="block text-sm text-text-secondary">
                Plataforma
                <select
                  value={form.platform}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      platform: e.target.value as ListingPlatform,
                    }))
                  }
                  disabled={!!editingId}
                  className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-3 py-2 text-text"
                >
                  {PLATFORM_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
                {editingId && (
                  <p className="mt-1 text-xs text-text-muted">La plataforma no se puede cambiar al editar.</p>
                )}
              </label>
              {form.platform === 'mercado_libre' ? (
                <label className="block text-sm text-text-secondary">
                  URL del listado (listado.mercadolibre.com.co)
                  <textarea
                    required
                    rows={3}
                    value={form.list_url}
                    onChange={(e) => setForm((f) => ({ ...f, list_url: e.target.value }))}
                    placeholder="https://listado.mercadolibre.com.co/inmuebles/..."
                    className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-3 py-2 font-mono text-xs text-text"
                  />
                </label>
              ) : (
                <>
                  <div>
                    <p className="text-sm text-text-secondary">Barrios</p>
                    <div className="mt-2 flex max-h-32 flex-wrap gap-1 overflow-y-auto">
                      {PRESET_NEIGHBORHOODS.map((b) => {
                        const on = form.neighborhoods.includes(b)
                        return (
                          <button
                            key={b}
                            type="button"
                            onClick={() =>
                              setForm((f) => ({
                                ...f,
                                neighborhoods: on
                                  ? f.neighborhoods.filter((x) => x !== b)
                                  : [...f.neighborhoods, b],
                              }))
                            }
                            className={`rounded-full border px-2 py-0.5 text-xs ${
                              on ? 'border-accent bg-accent/20 text-accent' : 'border-border text-text-secondary'
                            }`}
                          >
                            {b}
                          </button>
                        )
                      })}
                    </div>
                    <div className="mt-2 flex gap-2">
                      <input
                        placeholder="Barrio personalizado"
                        value={form.customBarrio}
                        onChange={(e) => setForm((f) => ({ ...f, customBarrio: e.target.value }))}
                        className="flex-1 rounded-md border border-border bg-bg-secondary px-2 py-1 text-sm text-text"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          const v = form.customBarrio.trim()
                          if (!v || form.neighborhoods.includes(v)) return
                          setForm((f) => ({ ...f, neighborhoods: [...f.neighborhoods, v], customBarrio: '' }))
                        }}
                        className="rounded-md border border-border px-2 text-sm text-text-secondary"
                      >
                        Añadir
                      </button>
                    </div>
                  </div>
                  <label className="block text-sm text-text-secondary">
                    Filtro de publicación
                    <select
                      value={form.publication_filter}
                      onChange={(e) =>
                        setForm((f) => ({ ...f, publication_filter: e.target.value as PublicationFilter }))
                      }
                      className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-3 py-2 text-text"
                    >
                      {PUBLICATION_OPTIONS.map((o) => (
                        <option key={o.value} value={o.value}>
                          {o.label}
                        </option>
                      ))}
                    </select>
                  </label>
                </>
              )}
              <div>
                <p className="text-sm text-text-secondary">Vista previa URL</p>
                <pre className="mt-1 overflow-x-auto rounded-md border border-border bg-bg p-2 text-[10px] text-text-muted">
                  {previewUrl}
                </pre>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setModalOpen(false)
                    setEditingId(null)
                  }}
                  className="rounded-md px-4 py-2 text-sm text-text-secondary"
                >
                  Cancelar
                </button>
                <button type="submit" className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white">
                  Guardar fuente
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <ScrapeFab onComplete={load} />
    </div>
  )
}

function defaultFilter(userId: string): AlertFilter {
  return {
    id: '',
    user_id: userId,
    name: 'Default',
    price_min: null,
    price_max: null,
    price_m2_min: null,
    price_m2_max: null,
    area_min: null,
    area_max: null,
    rooms_min: null,
    baths_min: null,
    max_age_years: null,
    neighborhoods: [],
    required_features: [],
    send_telegram: true,
    is_active: true,
    created_at: '',
    updated_at: '',
  }
}

function num(v: unknown): number | null {
  if (v === '' || v == null) return null
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

function int(v: unknown): number | null {
  const n = num(v)
  return n == null ? null : Math.round(n)
}

function FilterFormBody({
  filter,
  setFilter,
}: {
  filter: AlertFilter
  setFilter: <K extends keyof AlertFilter>(k: K, v: AlertFilter[K]) => void
}) {
  return (
    <>
      <div className="grid grid-cols-2 gap-3">
        <label className="text-sm text-text-secondary">
          Precio min (COP)
          <CurrencyTextInput
            value={filter.price_min}
            onChange={(n) => setFilter('price_min', n)}
            className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-2 py-1 font-mono-nums text-sm text-text"
          />
        </label>
        <label className="text-sm text-text-secondary">
          Precio max (COP)
          <CurrencyTextInput
            value={filter.price_max}
            onChange={(n) => setFilter('price_max', n)}
            className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-2 py-1 font-mono-nums text-sm text-text"
          />
        </label>
        <label className="text-sm text-text-secondary">
          Precio/m² min (COP)
          <CurrencyTextInput
            value={filter.price_m2_min}
            onChange={(n) => setFilter('price_m2_min', n)}
            className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-2 py-1 font-mono-nums text-sm text-text"
          />
        </label>
        <label className="text-sm text-text-secondary">
          Precio/m² max (COP)
          <CurrencyTextInput
            value={filter.price_m2_max}
            onChange={(n) => setFilter('price_m2_max', n)}
            className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-2 py-1 font-mono-nums text-sm text-text"
          />
        </label>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <label className="text-sm text-text-secondary">
          Área mínima (m²)
          <AreaM2TextInput
            value={filter.area_min}
            onChange={(n) => setFilter('area_min', n)}
            className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-2 py-1 font-mono-nums text-sm text-text"
          />
        </label>
        <label className="text-sm text-text-secondary">
          Área máxima (m²)
          <AreaM2TextInput
            value={filter.area_max}
            onChange={(n) => setFilter('area_max', n)}
            className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-2 py-1 font-mono-nums text-sm text-text"
          />
        </label>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <label className="text-sm text-text-secondary">
          Hab. mín
          <select
            value={filter.rooms_min ?? ''}
            onChange={(e) =>
              setFilter('rooms_min', e.target.value === '' ? null : Number(e.target.value))
            }
            className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-2 py-1 text-sm text-text"
          >
            <option value="">—</option>
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
            <option value={6}>5+</option>
          </select>
        </label>
        <label className="text-sm text-text-secondary">
          Baños mín
          <select
            value={filter.baths_min ?? ''}
            onChange={(e) =>
              setFilter('baths_min', e.target.value === '' ? null : Number(e.target.value))
            }
            className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-2 py-1 text-sm text-text"
          >
            <option value="">—</option>
            {[1, 2, 3, 4].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
            <option value={5}>4+</option>
          </select>
        </label>
      </div>
      <label className="block text-sm text-text-secondary">
        Antigüedad máx (años)
        <input
          type="number"
          value={filter.max_age_years ?? ''}
          onChange={(e) =>
            setFilter('max_age_years', e.target.value === '' ? null : Number(e.target.value))
          }
          className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-2 py-1 text-sm text-text"
        />
      </label>
      <div>
        <p className="text-sm text-text-secondary">Características requeridas</p>
        <div className="mt-2 flex flex-wrap gap-3 text-sm text-text-secondary">
          {[
            ['tiene_ascensor', 'Ascensor'],
            ['tiene_porteria', 'Portería 24h'],
            ['tiene_balcon', 'Balcón'],
            ['tiene_parqueadero', 'Parqueadero'],
          ].map(([key, label]) => (
            <label key={key} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={(filter.required_features ?? []).includes(key)}
                onChange={(e) => {
                  const cur = new Set(filter.required_features ?? [])
                  if (e.target.checked) cur.add(key)
                  else cur.delete(key)
                  setFilter('required_features', [...cur])
                }}
              />
              {label}
            </label>
          ))}
        </div>
      </div>
      <label className="flex items-center gap-2 text-sm text-text-secondary">
        <input
          type="checkbox"
          checked={filter.send_telegram}
          onChange={(e) => setFilter('send_telegram', e.target.checked)}
        />
        Enviar a Telegram
      </label>
    </>
  )
}
