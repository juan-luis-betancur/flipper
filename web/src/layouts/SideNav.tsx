import { useEffect, useRef, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import clsx from 'clsx'
import { supabase } from '../lib/supabase'
import { Logo } from './Logo'
import { useTheme } from '../lib/theme'

const propertiesChildren = [
  { to: '/properties/config', label: 'Configuración' },
  { to: '/properties/saved', label: 'Guardadas' },
  { to: '/properties/market', label: 'Análisis de Mercado' },
] as const

const sections = [
  {
    key: 'properties',
    to: '/properties/config',
    label: 'Propiedades',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9.5 12 3l9 6.5V21a1 1 0 0 1-1 1h-5v-7h-6v7H4a1 1 0 0 1-1-1z" />
      </svg>
    ),
  },
  {
    key: 'contracts',
    to: '/contracts',
    label: 'Contratos',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <path d="M14 2v6h6" />
        <path d="M8 13h8M8 17h5" />
      </svg>
    ),
  },
  {
    key: 'projects',
    to: '/projects',
    label: 'Proyectos',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="4" width="18" height="16" rx="2" />
        <path d="M3 10h18M8 4v6M16 4v6" />
      </svg>
    ),
  },
] as const

export function SideNav() {
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  async function signOut() {
    await supabase?.auth.signOut()
  }

  return (
    <aside className="relative hidden min-h-dvh w-[220px] shrink-0 flex-col border-r border-sidebar-border bg-sidebar md:flex">
      <div className="flex h-full min-h-0 flex-1 flex-col px-3 pb-4 pt-5">
        <NavLink
          to="/properties/config"
          className="mb-6 flex shrink-0 items-center gap-2 rounded-lg px-1 py-1 outline-none transition-opacity hover:opacity-95 focus-visible:ring-2 focus-visible:ring-accent/50"
        >
          <Logo size={36} withWordmark variant="onDark" className="min-w-0" />
        </NavLink>

        <nav className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto">
          {sections.map((s) => {
            if (s.key === 'properties') {
              const inProperties = location.pathname.startsWith('/properties')
              return (
                <div key={s.key} className="mb-1">
                  <NavLink
                    to={s.to}
                    className={clsx(
                      'flex items-start gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                      inProperties
                        ? 'bg-sidebar-active-bg text-sidebar-text ring-1 ring-white/20'
                        : 'text-sidebar-muted hover:bg-sidebar-hover hover:text-sidebar-text',
                    )}
                  >
                    <span className="mt-0.5 shrink-0 opacity-90">{s.icon}</span>
                    <span className="leading-tight">{s.label}</span>
                  </NavLink>
                  <ul className="mt-1 space-y-0.5 border-l border-white/10 pl-3 ml-[22px]">
                    {propertiesChildren.map((c) => (
                      <li key={c.to}>
                        <NavLink
                          to={c.to}
                          end
                          className={({ isActive }) =>
                            clsx(
                              'block rounded-md py-1.5 pl-3 pr-2 text-xs font-medium transition-colors',
                              isActive
                                ? 'text-sidebar-text bg-sidebar-active-bg/60'
                                : 'text-sidebar-muted hover:text-sidebar-text',
                            )
                          }
                        >
                          <span className="flex items-center gap-2">
                            <span
                              className={clsx(
                                'h-1.5 w-1.5 shrink-0 rounded-full',
                                location.pathname === c.to ? 'bg-accent' : 'bg-sidebar-muted',
                              )}
                            />
                            {c.label}
                          </span>
                        </NavLink>
                      </li>
                    ))}
                  </ul>
                </div>
              )
            }

            return (
              <NavLink
                key={s.key}
                to={s.to}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-sidebar-active-bg text-sidebar-text ring-1 ring-white/20'
                      : 'text-sidebar-muted hover:bg-sidebar-hover hover:text-sidebar-text',
                  )
                }
              >
                <span className="shrink-0 opacity-90">{s.icon}</span>
                {s.label}
              </NavLink>
            )
          })}
        </nav>

        <div className="mt-auto shrink-0 space-y-2 border-t border-sidebar-border pt-4">
          <button
            type="button"
            onClick={toggleTheme}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs font-medium text-sidebar-muted transition-colors hover:bg-sidebar-hover hover:text-sidebar-text"
            aria-label={theme === 'dark' ? 'Activar tema claro' : 'Activar tema oscuro'}
          >
            {theme === 'dark' ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="4" />
                  <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
                </svg>
                Tema claro
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
                Tema oscuro
              </>
            )}
          </button>

          <div className="relative" ref={menuRef}>
            <button
              type="button"
              onClick={() => setMenuOpen((v) => !v)}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs font-medium text-sidebar-muted transition-colors hover:bg-sidebar-hover hover:text-sidebar-text"
              aria-expanded={menuOpen}
              aria-haspopup="menu"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
              Cuenta
            </button>
            {menuOpen && (
              <div className="absolute bottom-full left-0 right-0 z-50 mb-1 overflow-hidden rounded-xl border border-sidebar-border bg-card py-1 elevated-shadow">
                <button
                  type="button"
                  onClick={() => {
                    setMenuOpen(false)
                    void signOut()
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-text-secondary transition-colors hover:bg-card-hover hover:text-text"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                    <polyline points="16 17 21 12 16 7" />
                    <line x1="21" y1="12" x2="9" y2="12" />
                  </svg>
                  Cerrar sesión
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </aside>
  )
}
