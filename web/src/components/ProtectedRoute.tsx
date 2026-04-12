import { useEffect, useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { supabase } from '../lib/supabase'

export function ProtectedRoute() {
  const [ready, setReady] = useState(false)
  const [signedIn, setSignedIn] = useState(false)

  useEffect(() => {
    if (!supabase) {
      setReady(true)
      setSignedIn(false)
      return
    }
    supabase.auth.getSession().then(({ data }) => {
      setSignedIn(!!data.session)
      setReady(true)
    })
    const { data: sub } = supabase.auth.onAuthStateChange((_e, session) => {
      setSignedIn(!!session)
    })
    return () => sub.subscription.unsubscribe()
  }, [])

  if (!ready) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-bg text-text-secondary">
        Cargando…
      </div>
    )
  }

  if (!supabase) {
    return (
      <div className="mx-auto flex min-h-dvh max-w-lg flex-col items-center justify-center p-8 text-center text-text-secondary">
        <p className="mb-2 text-text">Configura Supabase</p>
        <p className="text-sm">
          Copia <code className="text-accent">.env.example</code> a{' '}
          <code className="text-accent">.env</code> con tus claves y recarga.
        </p>
      </div>
    )
  }

  if (!signedIn) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
