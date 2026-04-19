import { useEffect, useRef, useState } from 'react'
import { NavLink } from 'react-router-dom'
import clsx from 'clsx'
import { supabase } from '../lib/supabase'
import { Logo } from './Logo'

const sections = [
  {
    to: '/properties',
    label: 'Propiedades',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9.5 12 3l9 6.5V21a1 1 0 0 1-1 1h-5v-7h-6v7H4a1 1 0 0 1-1-1z" />
      </svg>
    ),
  },
  {
    to: '/contracts',
    label: 'Contratos',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <path d="M14 2v6h6" />
        <path d="M8 13h8M8 17h5" />
      </svg>
    ),
  },
  {
    to: '/projects',
    label: 'Proyectos',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="4" width="18" height="16" rx="2" />
        <path d="M3 10h18M8 4v6M16 4v6" />
      </svg>
    ),
  },
]

export function TopBar() {
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
    <header className="sticky top-0 z-30 border-b border-border bg-card/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 w-full max-w-[1400px] items-center gap-6 px-4 sm:px-6 md:px-8">
        <Logo />

        <nav className="ml-2 hidden flex-1 items-center gap-1 md:flex">
          {sections.map((s) => (
            <NavLink
              key={s.to}
              to={s.to}
              className={({ isActive }) =>
                clsx(
                  'inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all',
                  isActive
                    ? 'bg-accent-soft text-accent'
                    : 'text-text-secondary hover:bg-card-hover hover:text-text',
                )
              }
            >
              {s.icon}
              {s.label}
            </NavLink>
          ))}
        </nav>

        <div className="relative ml-auto" ref={menuRef}>
          <button
            type="button"
            onClick={() => setMenuOpen((v) => !v)}
            className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-card text-text-secondary transition-colors hover:border-border-strong hover:text-text"
            aria-label="Menú de usuario"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </button>
          {menuOpen && (
            <div className="absolute right-0 top-11 z-40 w-48 overflow-hidden rounded-xl border border-border bg-card elevated-shadow">
              <button
                type="button"
                onClick={signOut}
                className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm text-text-secondary transition-colors hover:bg-card-hover hover:text-text"
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
    </header>
  )
}
