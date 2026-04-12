import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { requireSupabase } from '../lib/supabase'
import { apiBase, apiFetch } from '../lib/api'
import { apiErrorMessage } from '../lib/apiErrors'

type Props = {
  onComplete?: () => void
}

export function ScrapeFab({ onComplete }: Props) {
  const [busy, setBusy] = useState(false)
  const [phase, setPhase] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPoll = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  const run = useCallback(async () => {
    if (import.meta.env.PROD && !apiBase()) {
      toast.error('Configura VITE_API_URL con la URL pública del backend Python')
      return
    }
    setBusy(true)
    setPhase('Iniciando…')
    try {
      const res = await apiFetch('/api/scrape/run', { method: 'POST' })
      if (!res.ok) {
        const t = await res.text()
        throw new Error(t || res.statusText)
      }
      const data = (await res.json()) as { run_id: string }
      const supabase = requireSupabase()
      pollRef.current = setInterval(async () => {
        const { data: row } = await supabase
          .from('scraper_runs')
          .select('*')
          .eq('id', data.run_id)
          .maybeSingle()
        if (!row) return
        setPhase(row.etapa ?? row.estado ?? '…')
        if (row.estado === 'success' || row.estado === 'failed') {
          stopPoll()
          setBusy(false)
          setPhase(null)
          if (row.estado === 'failed') {
            toast.error(row.mensaje_error ?? 'Error en scraping')
          } else {
            toast.success(
              `Se encontraron ${row.total_encontradas ?? 0} propiedades. ${row.nuevas ?? 0} nuevas. ${row.enviadas_a_telegram ?? 0} enviadas a Telegram.`,
            )
          }
          onComplete?.()
        }
      }, 2000)
    } catch (e) {
      stopPoll()
      setBusy(false)
      setPhase(null)
      toast.error(apiErrorMessage(e))
    }
  }, [onComplete])

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2">
      {phase && (
        <div className="max-w-xs rounded-lg border border-border bg-card px-3 py-2 text-xs text-text-secondary shadow-lg">
          {phase}
        </div>
      )}
      <button
        type="button"
        disabled={busy}
        onClick={run}
        className="rounded-lg bg-accent px-5 py-3 text-sm font-semibold text-white shadow-lg transition-opacity hover:opacity-90 disabled:opacity-50"
      >
        {busy ? 'Scraping…' : 'Ejecutar scraping ahora'}
      </button>
    </div>
  )
}
