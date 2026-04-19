import { useEffect, useRef, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { Logo } from './Logo'
import { MobileNavDrawer } from './MobileNavDrawer'
import { useTheme } from '../lib/theme'

/** Barra superior solo en móvil; en desktop la navegación está en SideNav. */
export function TopBar() {
  const { theme, toggleTheme } = useTheme()
  const [menuOpen, setMenuOpen] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)
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
    <header className="sticky top-0 z-30 border-b border-border bg-card/90 backdrop-blur-md md:hidden">
      <div className="flex h-14 w-full items-center gap-2 px-4">
        <button
          type="button"
          onClick={() => setDrawerOpen(true)}
          className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-border bg-card text-text-secondary transition-colors hover:border-border-strong hover:text-text"
          aria-label="Abrir menú de navegación"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <line x1="4" x2="20" y1="6" y2="6" />
            <line x1="4" x2="20" y1="12" y2="12" />
            <line x1="4" x2="20" y1="18" y2="18" />
          </svg>
        </button>

        <NavLink
          to="/properties/config"
          className="min-w-0 flex-1 outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg rounded-md"
          onClick={() => setDrawerOpen(false)}
        >
          <Logo size={30} withWordmark className="min-w-0" />
        </NavLink>

        <div className="ml-auto flex shrink-0 items-center gap-1">
          <button
            type="button"
            onClick={toggleTheme}
            className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-card text-text-secondary transition-colors hover:border-border-strong hover:text-text"
            aria-label={theme === 'dark' ? 'Activar tema claro' : 'Activar tema oscuro'}
          >
            {theme === 'dark' ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>

          <div className="relative" ref={menuRef}>
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
                  onClick={() => {
                    setMenuOpen(false)
                    void signOut()
                  }}
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
      </div>

      <MobileNavDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </header>
  )
}
