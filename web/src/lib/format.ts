const cop = new Intl.NumberFormat('es-CO', {
  style: 'currency',
  currency: 'COP',
  maximumFractionDigits: 0,
})

const intEs = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 })

export function formatCOP(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—'
  return cop.format(value)
}

export function formatCOPPerM2(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—'
  return `${cop.format(value)}/m²`
}

/** Interpreta texto con $, espacios y separadores de miles (.) como en es-CO. */
export function parseLooseCOPInput(s: string): number | null {
  const t = s.trim()
  if (!t) return null
  let x = t.replace(/\$/g, '').replace(/\s/g, '').replace(/COP/gi, '')
  if (/,\d{1,2}$/.test(x)) {
    x = x.replace(/\./g, '').replace(',', '.')
  } else {
    x = x.replace(/\./g, '').replace(/,/g, '')
  }
  const n = Number(x)
  return Number.isFinite(n) ? Math.round(n) : null
}

export function formatAreaM2(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return ''
  return `${intEs.format(Math.round(value))} m²`
}

export function parseLooseIntegerInput(s: string): number | null {
  const t = s.trim()
  if (!t) return null
  const x = t.replace(/\./g, '').replace(/\s/g, '').replace(/m²/gi, '').replace(/,/g, '.')
  const n = Number(x)
  return Number.isFinite(n) ? Math.round(n) : null
}

export function formatRelativeTime(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  const diff = Date.now() - d.getTime()
  const days = Math.floor(diff / 86400000)
  if (days <= 0) return 'hoy'
  if (days === 1) return 'hace 1 día'
  if (days < 7) return `hace ${days} días`
  const weeks = Math.floor(days / 7)
  if (weeks < 5) return `hace ${weeks} semana${weeks > 1 ? 's' : ''}`
  return d.toLocaleDateString('es-CO')
}
