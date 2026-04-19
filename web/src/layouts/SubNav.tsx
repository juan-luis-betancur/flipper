import { NavLink } from 'react-router-dom'
import clsx from 'clsx'

export type SubNavItem = { to: string; label: string; icon?: React.ReactNode }

export function SubNav({ items }: { items: SubNavItem[] }) {
  if (!items.length) return null
  return (
    <div className="sticky top-16 z-20 border-b border-border bg-bg/85 backdrop-blur-md">
      <div className="mx-auto flex w-full max-w-[1400px] gap-1 overflow-x-auto px-4 py-2.5 sm:px-6 md:px-8">
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
    </div>
  )
}
