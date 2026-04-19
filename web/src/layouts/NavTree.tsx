import clsx from 'clsx'
import { useEffect, useRef } from 'react'
import { NavLink, useLocation } from 'react-router-dom'

export type NavTreeMode = 'wide' | 'rail' | 'drawer'

const propertiesChildren = [
  { to: '/properties/config', label: 'Configuración' },
  { to: '/properties/saved', label: 'Guardadas' },
  { to: '/properties/market', label: 'Análisis de Mercado' },
] as const

const sections = [
  {
    key: 'properties' as const,
    to: '/properties/config',
    label: 'Propiedades',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9.5 12 3l9 6.5V21a1 1 0 0 1-1 1h-5v-7h-6v7H4a1 1 0 0 1-1-1z" />
      </svg>
    ),
  },
  {
    key: 'contracts' as const,
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
    key: 'projects' as const,
    to: '/projects',
    label: 'Proyectos',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="4" width="18" height="16" rx="2" />
        <path d="M3 10h18M8 4v6M16 4v6" />
      </svg>
    ),
  },
]

export type NavTreeProps = {
  mode: NavTreeMode
  propertiesSubOpen: boolean
  onTogglePropertiesSub: () => void
  onItemClick?: () => void
  railFlyoutOpen?: boolean
  setRailFlyoutOpen?: (open: boolean) => void
}

export function NavTree({
  mode,
  propertiesSubOpen,
  onTogglePropertiesSub,
  onItemClick,
  railFlyoutOpen = false,
  setRailFlyoutOpen,
}: NavTreeProps) {
  const location = useLocation()
  const railWrapRef = useRef<HTMLDivElement>(null)

  const afterNav = () => {
    onItemClick?.()
  }

  const inProperties = location.pathname.startsWith('/properties')
  const showLabels = mode === 'wide' || mode === 'drawer'
  const isRail = mode === 'rail'

  useEffect(() => {
    if (!isRail || !railFlyoutOpen) return
    if (typeof setRailFlyoutOpen !== 'function') return
    const closeFlyout = setRailFlyoutOpen
    function onDocDown(e: MouseEvent) {
      if (railWrapRef.current?.contains(e.target as Node)) return
      closeFlyout(false)
    }
    document.addEventListener('mousedown', onDocDown)
    return () => document.removeEventListener('mousedown', onDocDown)
  }, [isRail, railFlyoutOpen, setRailFlyoutOpen])

  const linkChildClass = (isActive: boolean) =>
    clsx(
      'block rounded-md py-1.5 pl-3 pr-2 text-xs font-medium transition-colors',
      isActive ? 'bg-sidebar-active-bg/60 text-sidebar-text' : 'text-sidebar-muted hover:text-sidebar-text',
    )

  const propertiesFlyout = isRail && railFlyoutOpen && setRailFlyoutOpen && (
    <div
      className="absolute left-full top-0 z-[60] ml-1 w-52 rounded-lg border border-sidebar-border bg-sidebar py-1 elevated-shadow motion-safe:transition-opacity motion-safe:duration-150"
      role="menu"
    >
      {propertiesChildren.map((c) => (
        <NavLink
          key={c.to}
          to={c.to}
          end
          role="menuitem"
          onClick={() => {
            setRailFlyoutOpen(false)
            afterNav()
          }}
          className={({ isActive }) => clsx(linkChildClass(isActive), 'px-3')}
        >
          {c.label}
        </NavLink>
      ))}
    </div>
  )

  if (isRail) {
    return (
      <nav className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto overflow-x-visible px-1">
        <div ref={railWrapRef} className="relative flex justify-center">
          <button
            type="button"
            title="Propiedades"
            aria-haspopup="menu"
            aria-expanded={railFlyoutOpen}
            onClick={() => setRailFlyoutOpen?.(!railFlyoutOpen)}
            className={clsx(
              'flex h-11 w-11 items-center justify-center rounded-lg transition-colors',
              inProperties || railFlyoutOpen
                ? 'bg-sidebar-active-bg text-sidebar-text ring-1 ring-white/20'
                : 'text-sidebar-muted hover:bg-sidebar-hover hover:text-sidebar-text',
            )}
          >
            {sections[0]!.icon}
            <span className="sr-only">Propiedades</span>
          </button>
          {propertiesFlyout}
        </div>
        {sections.slice(1).map((s) => (
          <NavLink
            key={s.key}
            to={s.to}
            title={s.label}
            onClick={afterNav}
            className={({ isActive }) =>
              clsx(
                'flex h-11 w-11 items-center justify-center self-center rounded-lg transition-colors',
                isActive
                  ? 'bg-sidebar-active-bg text-sidebar-text ring-1 ring-white/20'
                  : 'text-sidebar-muted hover:bg-sidebar-hover hover:text-sidebar-text',
              )
            }
          >
            {s.icon}
            <span className="sr-only">{s.label}</span>
          </NavLink>
        ))}
      </nav>
    )
  }

  return (
    <nav className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto px-1">
      <div className="mb-1">
        <div
          className={clsx(
            'flex items-stretch gap-0.5 rounded-lg',
            inProperties && 'bg-sidebar-active-bg ring-1 ring-white/20',
          )}
        >
          <NavLink
            to="/properties/config"
            onClick={afterNav}
            className={clsx(
              'flex min-w-0 flex-1 items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
              inProperties ? 'text-sidebar-text' : 'text-sidebar-muted hover:bg-sidebar-hover hover:text-sidebar-text',
            )}
          >
            <span className="shrink-0 opacity-90">{sections[0]!.icon}</span>
            {showLabels && <span className="leading-tight">{sections[0]!.label}</span>}
          </NavLink>
          <button
            type="button"
            className="flex w-9 shrink-0 items-center justify-center rounded-r-lg text-sidebar-muted transition-colors hover:bg-sidebar-hover hover:text-sidebar-text"
            aria-expanded={propertiesSubOpen}
            aria-controls="flipper-properties-subnav"
            title={propertiesSubOpen ? 'Ocultar submenú' : 'Mostrar submenú'}
            onClick={(e) => {
              e.preventDefault()
              onTogglePropertiesSub()
            }}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className={clsx('transition-transform motion-safe:duration-200', propertiesSubOpen && 'rotate-180')}
              aria-hidden
            >
              <path d="m6 9 6 6 6-6" />
            </svg>
          </button>
        </div>
        {propertiesSubOpen && (
          <ul id="flipper-properties-subnav" className="mt-1 space-y-0.5 border-l border-white/10 pl-3 ml-[22px]">
            {propertiesChildren.map((c) => (
              <li key={c.to}>
                <NavLink
                  to={c.to}
                  end
                  onClick={afterNav}
                  className={({ isActive }) => linkChildClass(isActive)}
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
        )}
      </div>

      {sections.slice(1).map((s) => (
        <NavLink
          key={s.key}
          to={s.to}
          onClick={afterNav}
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
          {showLabels && s.label}
        </NavLink>
      ))}
    </nav>
  )
}
