import { supabase } from './supabase'

/** Base del API: en desarrollo, rutas relativas /api… (proxy Vite → FastAPI). En build, VITE_API_URL. */
export function apiBase(): string {
  if (import.meta.env.DEV) {
    return ''
  }
  return import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? ''
}

export async function apiFetch(path: string, init: RequestInit = {}) {
  const base = apiBase()
  const client = supabase
  const session = client ? (await client.auth.getSession()).data.session : null
  const headers = new Headers(init.headers)
  if (session?.access_token) {
    headers.set('Authorization', `Bearer ${session.access_token}`)
  }
  if (!headers.has('Content-Type') && init.body && !(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  const res = await fetch(`${base}${path}`, { ...init, headers })
  return res
}
