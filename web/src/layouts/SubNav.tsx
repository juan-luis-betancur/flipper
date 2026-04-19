import { NavLink } from 'react-router-dom'
import clsx from 'clsx'
import { useShellNav } from './ShellNavContext'

export type SubNavItem = { to: string; label: string; icon?: React.ReactNode }

export function SubNav({ items, className }: { items: SubNavItem[]; className?: string }) {
  const { propertiesSubOpen, togglePropertiesSub } = useShellNav()

  if (!items.length) return null

  return (
    <div
      className={clsx(
        'sticky top-14 z-20 border-b border-border bg-bg/85 backdrop-blur-md md:hidden',
        className,
      )}
    >
      <div className="mx-auto flex w-full max-w-[1400px] flex-col gap-2 px-4 py-2.5 sm:px-6 md:px-8">
        <button
          type="button"
          className="flex w-full items-center justify-between rounded-lg border border-border/70 bg-card/60 px-3 py-2 text-left text-sm font-medium text-text transition-colors hover:bg-card"
          onClick={togglePropertiesSub}
          aria-expanded={propertiesSubOpen}
          aria-controls="flipper-mobile-subnav-pills"
        >
          <span>Propiedades</span>
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={clsx('shrink-0 text-text-muted motion-safe:transition-transform motion-safe:duration-200', propertiesSubOpen && 'rotate-180')}
            aria-hidden
          >
            <path d="m6 9 6 6 6-6" />
          </svg>
        </button>
        {propertiesSubOpen && (
          <div id="flipper-mobile-subnav-pills" className="flex gap-1 overflow-x-auto pb-0.5">
            {items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end
                className={({ isActive }) =>
                  clsx(
                    'inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium transition-all',
                    isActive
                      ? 'bg-text text-bg shadow-sm'
                      : 'text-text-secondary hover:bg-card hover:text-text',
                  )
                }
              >
                {item.icon}
                {item.label}
              </NavLink>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
