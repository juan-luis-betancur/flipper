import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { toast } from 'sonner'
import { supabase } from '../lib/supabase'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionOk, setSessionOk] = useState<boolean | null>(null)

  useEffect(() => {
    if (!supabase) return
    supabase.auth.getSession().then(({ data }) => setSessionOk(!!data.session))
    const { data: sub } = supabase.auth.onAuthStateChange((_e, session) => {
      setSessionOk(!!session)
    })
    return () => sub.subscription.unsubscribe()
  }, [])

  if (!supabase) {
    return (
      <div className="flex min-h-dvh flex-col items-center justify-center bg-bg px-4 text-text-secondary">
        <p className="text-text">Falta configuración de Supabase (.env)</p>
      </div>
    )
  }

  if (sessionOk) {
    return <Navigate to="/config" replace />
  }

  if (sessionOk === null) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-bg text-text-secondary">
        Cargando…
      </div>
    )
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!supabase) return
    setLoading(true)
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    setLoading(false)
    if (error) {
      toast.error(error.message)
      return
    }
    toast.success('Sesión iniciada')
    setSessionOk(true)
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-bg px-4">
      <div className="w-full max-w-md rounded-lg border border-border bg-card p-8 shadow-xl">
        <h1 className="mb-1 text-xl font-semibold text-text">Flipper</h1>
        <p className="mb-6 text-sm text-text-secondary">Ingresa con tu cuenta</p>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <label className="block text-sm text-text-secondary">
            Email
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-3 py-2 text-text outline-none focus:border-accent"
            />
          </label>
          <label className="block text-sm text-text-secondary">
            Contraseña
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-md border border-border bg-bg-secondary px-3 py-2 text-text outline-none focus:border-accent"
            />
          </label>
          <button
            type="submit"
            disabled={loading}
            className="rounded-md bg-accent px-4 py-2.5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {loading ? 'Entrando…' : 'Entrar'}
          </button>
        </form>
        <p className="mt-4 text-center text-xs text-text-muted">
          Crea el usuario en Supabase Auth (Dashboard) si aún no existe.
        </p>
      </div>
    </div>
  )
}
