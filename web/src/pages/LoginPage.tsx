import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { toast } from 'sonner'
import { supabase } from '../lib/supabase'
import { Logo } from '../layouts/Logo'

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
    return <Navigate to="/properties/config" replace />
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
    <div className="relative flex min-h-dvh items-center justify-center overflow-hidden bg-bg px-4 py-10">
      <div
        aria-hidden
        className="pointer-events-none absolute -top-40 left-1/2 h-[520px] w-[720px] -translate-x-1/2 rounded-full opacity-30 blur-3xl"
        style={{ background: 'radial-gradient(circle, #a855f7 0%, transparent 70%)' }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -bottom-32 left-1/4 h-96 w-96 rounded-full opacity-20 blur-3xl"
        style={{ background: 'radial-gradient(circle, #6366f1 0%, transparent 70%)' }}
      />

      <div className="relative w-full max-w-md">
        <div className="mb-8 flex flex-col items-center text-center">
          <Logo size={56} withWordmark={false} />
          <h1 className="mt-4 text-3xl font-bold tracking-tight text-text">
            Bienvenido a <span className="brand-gradient-text">Flipper</span>
          </h1>
          <p className="mt-2 max-w-sm text-sm text-text-secondary">
            Tu plataforma para detectar y capitalizar oportunidades inmobiliarias.
          </p>
        </div>

        <div className="rounded-2xl border border-border bg-card p-7 elevated-shadow">
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <label className="block text-sm font-medium text-text">
              Email
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="tu@correo.com"
                className="mt-1.5 w-full rounded-lg border border-border bg-card px-3.5 py-2.5 text-text placeholder:text-text-muted outline-none transition-colors focus:border-accent focus:ring-2 focus:ring-accent/15"
              />
            </label>
            <label className="block text-sm font-medium text-text">
              Contraseña
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="mt-1.5 w-full rounded-lg border border-border bg-card px-3.5 py-2.5 text-text placeholder:text-text-muted outline-none transition-colors focus:border-accent focus:ring-2 focus:ring-accent/15"
              />
            </label>
            <button
              type="submit"
              disabled={loading}
              className="mt-2 inline-flex items-center justify-center rounded-lg brand-gradient px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-transform hover:-translate-y-px disabled:opacity-60"
            >
              {loading ? 'Entrando…' : 'Entrar'}
            </button>
          </form>
          <p className="mt-5 text-center text-xs text-text-muted">
            ¿Sin cuenta? Créala en Supabase Auth (Dashboard).
          </p>
        </div>
      </div>
    </div>
  )
}
