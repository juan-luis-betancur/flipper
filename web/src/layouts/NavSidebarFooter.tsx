import { useEffect, useRef, useState } from 'react'
import { supabase } from '../lib/supabase'
import { useTheme } from '../lib/theme'
import clsx from 'clsx'

type Props = {
  /** Solo iconos (rail colapsado) */
  compact?: boolean
}

export function NavSidebarFooter({ compact }: Props) {
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

  const btnBase =
    'flex w-full items-center gap-2 rounded-lg text-sidebar-muted transition-colors hover:bg-sidebar-hover hover:text-sidebar-text'

  return (
    <div className="mt-auto shrink-0 space-y-2 border-t border-sidebar-border pt-4">
      <button
        type="button"
        onClick={toggleTheme}
        className={clsx(btnBase, compact ? 'justify-center px-2 py-2' : 'px-3 py-2 text-left text-xs font-medium')}
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
        {!compact && <span>{theme === 'dark' ? 'Tema claro' : 'Tema oscuro'}</span>}
        {compact && <span className="sr-only">{theme === 'dark' ? 'Tema claro' : 'Tema oscuro'}</span>}
      </button>

      <div className="relative" ref={menuRef}>
        <button
          type="button"
          onClick={() => setMenuOpen((v) => !v)}
          className={clsx(btnBase, compact ? 'justify-center px-2 py-2' : 'px-3 py-2 text-left text-xs font-medium')}
          aria-expanded={menuOpen}
          aria-haspopup="menu"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          {!compact && <span>Cuenta</span>}
          {compact && <span className="sr-only">Cuenta</span>}
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
  )
}
