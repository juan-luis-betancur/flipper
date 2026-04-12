import type { PublicationFilter } from '../types/db'

const PREFIX = 'https://www.fincaraiz.com.co/venta/apartamentos/antioquia'

/** Map UI barrio names to URL-friendly tokens (alineado a rutas tipo Finca Raíz). */
export function slugBarrio(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/\p{M}/gu, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

/** Une varios barrios como en el sitio: `el-poblado-y-en-san-lucas`. */
function locationPathSegment(neighborhoods: string[]): string {
  const slugs = neighborhoods.map(slugBarrio).filter(Boolean)
  if (slugs.length === 0) return ''
  if (slugs.length === 1) return slugs[0]!
  return slugs.join('-y-en-')
}

/**
 * Sufijo de publicación en el path (ej. `publicado-ayer`, `publicado-ultimos-7-dias`).
 * Alineado a Finca Raíz; mantener en sync con backend `finca_raiz.PUBLICATION_PATH`.
 */
function publicationPathSegment(filter: PublicationFilter): string {
  const map: Record<PublicationFilter, string> = {
    today: 'publicado-hoy',
    yesterday: 'publicado-ayer',
    this_week: 'publicado-ultimos-7-dias',
    last_15_days: 'publicado-ultimos-15-dias',
    last_30_days: 'publicado-ultimos-30-dias',
    last_40_days: 'publicado-ultimos-40-dias',
    none: '',
  }
  return map[filter] ?? ''
}

/**
 * URL de listado como en el sitio real, p. ej.:
 * `https://www.fincaraiz.com.co/venta/apartamentos/antioquia/el-poblado-y-en-san-lucas/publicado-ayer`
 */
export function buildFincaRaizListadoUrl(
  neighborhoods: string[],
  publicationFilter: PublicationFilter,
): string {
  const loc = locationPathSegment(neighborhoods)
  const pub = publicationPathSegment(publicationFilter)

  if (!loc && !pub) return PREFIX
  if (!loc) return `${PREFIX}/${pub}`
  if (!pub) return `${PREFIX}/${loc}`
  return `${PREFIX}/${loc}/${pub}`
}

export function slugifyForLog(name: string): string {
  return slugBarrio(name)
}
