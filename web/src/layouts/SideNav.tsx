import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import clsx from 'clsx'
import { Logo } from './Logo'
import { NavSidebarFooter } from './NavSidebarFooter'
import { NavTree } from './NavTree'
import { useShellNav } from './ShellNavContext'

export function SideNav() {
  const { sidebarCollapsed, toggleSidebarCollapsed, propertiesSubOpen, togglePropertiesSub } = useShellNav()
  const [railFlyoutOpen, setRailFlyoutOpen] = useState(false)

  useEffect(() => {
    if (!sidebarCollapsed) setRailFlyoutOpen(false)
  }, [sidebarCollapsed])

  return (
    <aside
      className={clsx(
        'relative hidden min-h-dvh shrink-0 flex-col border-r border-sidebar-border bg-sidebar motion-safe:transition-[width] motion-safe:duration-200 motion-safe:ease-out md:flex',
        sidebarCollapsed ? 'w-[72px]' : 'w-[220px]',
      )}
    >
      <div className="flex h-full min-h-0 flex-1 flex-col px-2 pb-4 pt-4">
        <div
          className={clsx(
            'mb-3 flex shrink-0 items-center gap-1',
            sidebarCollapsed ? 'flex-col' : 'flex-row',
          )}
        >
          <NavLink
            to="/properties/config"
            className={clsx(
              'flex min-w-0 items-center rounded-lg px-1 py-1 outline-none transition-opacity hover:opacity-95 focus-visible:ring-2 focus-visible:ring-accent/50',
              sidebarCollapsed ? 'justify-center' : 'min-w-0 flex-1',
            )}
          >
            <Logo
              size={sidebarCollapsed ? 32 : 36}
              withWordmark={!sidebarCollapsed}
              variant="onDark"
              className="min-w-0"
            />
          </NavLink>
          <button
            type="button"
            onClick={toggleSidebarCollapsed}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-sidebar-muted transition-colors hover:bg-sidebar-hover hover:text-sidebar-text"
            aria-expanded={!sidebarCollapsed}
            aria-label={sidebarCollapsed ? 'Expandir menú lateral' : 'Contraer menú lateral'}
          >
            {sidebarCollapsed ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <path d="M9 18V6l6 6-6 6Z" />
                <path d="M15 6h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <path d="M15 18V6l-6 6 6 6Z" />
                <path d="M9 6H7a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" />
              </svg>
            )}
          </button>
        </div>

        <NavTree
          mode={sidebarCollapsed ? 'rail' : 'wide'}
          propertiesSubOpen={propertiesSubOpen}
          onTogglePropertiesSub={togglePropertiesSub}
          railFlyoutOpen={railFlyoutOpen}
          setRailFlyoutOpen={setRailFlyoutOpen}
        />

        <NavSidebarFooter compact={sidebarCollapsed} />
      </div>
    </aside>
  )
}
