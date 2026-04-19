import { useEffect, useRef, useState } from 'react'
import { NavLink } from 'react-router-dom'
import clsx from 'clsx'
import { supabase } from '../lib/supabase'

const sections = [
  { to: '/properties', label: 'Propiedades' },
  { to: '/contracts', label: 'Contratos' },
  { to: '/projects', label: 'Proyectos' },
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
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b border-border bg-bg-secondary/90 px-4 backdrop-blur sm:px-6">
      <div className="flex items-center gap-2">
        <span className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-accent text-sm font-semibold text-white">
          F
        </span>
        <span className="text-base font-semibold tracking-tight text-text">Flipper</span>
      </div>

      <nav className="ml-2 hidden flex-1 items-center gap-1 md:flex">
        {sections.map((s) => (
          <NavLink
            key={s.to}
            to={s.to}
            className={({ isActive }) =>
              clsx(
                'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-card text-text'
                  : 'text-text-secondary hover:bg-card-hover hover:text-text',
              )
            }
          >
            {s.label}
          </NavLink>
        ))}
      </nav>

      <div className="ml-auto" ref={menuRef}>
        <button
          type="button"
          onClick={() => setMenuOpen((v) => !v)}
          className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-card text-sm text-text-secondary hover:text-text"
          aria-label="Menú de usuario"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        </button>
        {menuOpen && (
          <div className="absolute right-4 top-12 z-40 w-44 overflow-hidden rounded-lg border border-border bg-card shadow-lg sm:right-6">
            <button
              type="button"
              onClick={signOut}
              className="block w-full px-4 py-2.5 text-left text-sm text-text-secondary hover:bg-card-hover hover:text-text"
            >
              Cerrar sesión
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
