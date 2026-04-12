/** Mensaje legible cuando fetch() falla antes de recibir respuesta (backend caído, CORS, etc.). */
export function apiErrorMessage(e: unknown): string {
  const raw = e instanceof Error ? e.message : 'Error'
  const isNetwork =
    raw === 'Failed to fetch' ||
    raw.includes('NetworkError') ||
    raw.includes('Load failed') ||
    raw.includes('Network request failed')
  if (isNetwork) {
    return 'Sin conexión con el API Python. En la carpeta backend ejecuta: uvicorn app.main:app --reload --host 127.0.0.1 --port 8000'
  }
  return raw
}
