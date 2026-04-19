import { NavLink } from 'react-router-dom'
import clsx from 'clsx'

export type SubNavItem = { to: string; label: string }

export function SubNav({ items }: { items: SubNavItem[] }) {
  if (!items.length) return null
  return (
    <div className="sticky top-14 z-20 border-b border-border bg-bg/95 backdrop-blur">
      <div className="mx-auto flex w-full max-w-[1400px] gap-1 overflow-x-auto px-4 py-2 sm:px-6 md:px-8">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end
            className={({ isActive }) =>
              clsx(
                'whitespace-nowrap rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-accent text-white'
                  : 'text-text-secondary hover:bg-card hover:text-text',
              )
            }
          >
            {item.label}
          </NavLink>
        ))}
      </div>
    </div>
  )
}
