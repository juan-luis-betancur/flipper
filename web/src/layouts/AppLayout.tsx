import { Outlet, useLocation } from 'react-router-dom'
import { TopBar } from './TopBar'
import { SubNav, type SubNavItem } from './SubNav'
import { BottomNav } from './BottomNav'

const propertiesSubNav: SubNavItem[] = [
  { to: '/properties/config', label: 'Configuración' },
  { to: '/properties/saved', label: 'Guardadas' },
  { to: '/properties/market', label: 'Análisis de Mercado' },
]

export function AppLayout() {
  const location = useLocation()
  const subNav = location.pathname.startsWith('/properties') ? propertiesSubNav : []

  return (
    <div className="flex min-h-dvh flex-col bg-bg text-text">
      <TopBar />
      <SubNav items={subNav} />
      <main className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 pb-24 sm:px-6 md:px-8 md:pb-6">
        <Outlet />
      </main>
      <BottomNav />
    </div>
  )
}
