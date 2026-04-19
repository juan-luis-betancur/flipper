import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import { NavSidebarFooter } from './NavSidebarFooter'
import { NavTree } from './NavTree'
import { useShellNav } from './ShellNavContext'

type Props = {
  open: boolean
  onClose: () => void
}

export function MobileNavDrawer({ open, onClose }: Props) {
  const { propertiesSubOpen, togglePropertiesSub } = useShellNav()

  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  useEffect(() => {
    if (open) document.body.style.overflow = 'hidden'
    else document.body.style.overflow = ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [open])

  if (!open) return null

  const node = (
    <div
      className="fixed inset-0 z-[100] md:hidden"
      role="dialog"
      aria-modal="true"
      aria-label="Menú de navegación"
    >
      <button
        type="button"
        className="absolute inset-0 bg-black/50 motion-safe:transition-opacity"
        aria-label="Cerrar menú"
        onClick={onClose}
      />
      <aside className="absolute left-0 top-0 flex h-full w-[min(300px,88vw)] max-w-[320px] flex-col border-r border-sidebar-border bg-sidebar elevated-shadow motion-safe:transition-transform motion-safe:duration-200">
        <div className="flex items-center justify-between border-b border-sidebar-border px-3 py-3">
          <span className="text-sm font-semibold text-sidebar-text">Menú</span>
          <button
            type="button"
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-sidebar-muted transition-colors hover:bg-sidebar-hover hover:text-sidebar-text"
            aria-label="Cerrar menú"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden px-2 pb-3 pt-2">
          <div className="min-h-0 flex-1 overflow-y-auto">
            <NavTree
              mode="drawer"
              propertiesSubOpen={propertiesSubOpen}
              onTogglePropertiesSub={togglePropertiesSub}
              onItemClick={onClose}
            />
          </div>
          <NavSidebarFooter />
        </div>
      </aside>
    </div>
  )

  return typeof document !== 'undefined' ? createPortal(node, document.body) : null
}
