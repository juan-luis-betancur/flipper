import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import clsx from 'clsx'
import { supabase } from '../lib/supabase'

const nav = [
  { to: '/config', label: 'Configuración', short: 'Cfg' },
  { to: '/saved', label: 'Guardadas', short: '★' },
  { to: '/market', label: 'Análisis de Mercado', short: 'ACM' },
]

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  async function signOut() {
    await supabase?.auth.signOut()
  }

  return (
    <div className="flex min-h-dvh bg-bg text-text">
      <aside
        className={clsx(
          'fixed left-0 top-0 z-40 flex h-full flex-col border-r border-border bg-bg-secondary transition-[width] duration-200 md:static',
          collapsed ? 'w-16' : 'w-60',
          mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
        )}
      >
        <div
          className={clsx(
            'flex h-14 items-center border-b border-border px-3',
            collapsed && 'justify-center',
          )}
        >
          <span className="font-semibold tracking-tight text-text">
            {collapsed ? 'F' : 'Flipper'}
          </span>
        </div>
        <nav className="flex flex-1 flex-col gap-0.5 p-2">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                clsx(
                  'rounded-md px-3 py-2 text-sm font-medium transition-colors duration-150',
                  isActive
                    ? 'bg-card text-accent'
                    : 'text-text-secondary hover:bg-card-hover hover:text-text',
                  collapsed && 'px-2 text-center',
                )
              }
              title={item.label}
            >
              {collapsed ? item.short : item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-border p-2">
          <button
            type="button"
            onClick={() => setCollapsed((c) => !c)}
            className="mb-1 hidden w-full rounded-md px-2 py-1.5 text-xs text-text-muted hover:bg-card-hover hover:text-text-secondary md:block"
          >
            {collapsed ? '→' : '← Colapsar'}
          </button>
          <button
            type="button"
            onClick={signOut}
            className="w-full rounded-md px-2 py-2 text-left text-sm text-text-secondary hover:bg-card-hover"
          >
            Salir
          </button>
        </div>
      </aside>

      {mobileOpen && (
        <button
          type="button"
          aria-label="Cerrar menú"
          className="fixed inset-0 z-30 bg-black/60 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <div className="flex min-h-dvh flex-1 flex-col md:pl-0">
        <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-border bg-bg/95 px-4 backdrop-blur md:hidden">
          <button
            type="button"
            className="rounded-md border border-border px-2 py-1 text-sm text-text-secondary"
            onClick={() => setMobileOpen(true)}
          >
            Menú
          </button>
          <span className="font-semibold">Flipper</span>
        </header>
        <main className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 sm:px-6 md:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
