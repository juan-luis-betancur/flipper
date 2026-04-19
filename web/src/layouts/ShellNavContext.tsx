import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

const KEY_SIDEBAR = 'flipper-sidebar-collapsed'
const KEY_PROPERTIES_SUB = 'flipper-properties-subnav-open'

function readStoredBool(key: string, defaultValue: boolean): boolean {
  try {
    const v = localStorage.getItem(key)
    if (v === '1' || v === 'true') return true
    if (v === '0' || v === 'false') return false
  } catch {
    /* ignore */
  }
  return defaultValue
}

type ShellNavContextValue = {
  sidebarCollapsed: boolean
  setSidebarCollapsed: (v: boolean) => void
  toggleSidebarCollapsed: () => void
  propertiesSubOpen: boolean
  setPropertiesSubOpen: (v: boolean) => void
  togglePropertiesSub: () => void
}

const ShellNavContext = createContext<ShellNavContextValue | null>(null)

export function ShellNavProvider({ children }: { children: ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() =>
    readStoredBool(KEY_SIDEBAR, false),
  )
  const [propertiesSubOpen, setPropertiesSubOpen] = useState(() =>
    readStoredBool(KEY_PROPERTIES_SUB, true),
  )

  useEffect(() => {
    try {
      localStorage.setItem(KEY_SIDEBAR, sidebarCollapsed ? '1' : '0')
    } catch {
      /* ignore */
    }
  }, [sidebarCollapsed])

  useEffect(() => {
    try {
      localStorage.setItem(KEY_PROPERTIES_SUB, propertiesSubOpen ? '1' : '0')
    } catch {
      /* ignore */
    }
  }, [propertiesSubOpen])

  const toggleSidebarCollapsed = useCallback(() => {
    setSidebarCollapsed((c) => !c)
  }, [])

  const togglePropertiesSub = useCallback(() => {
    setPropertiesSubOpen((v) => !v)
  }, [])

  const value = useMemo(
    () => ({
      sidebarCollapsed,
      setSidebarCollapsed,
      toggleSidebarCollapsed,
      propertiesSubOpen,
      setPropertiesSubOpen,
      togglePropertiesSub,
    }),
    [sidebarCollapsed, propertiesSubOpen, toggleSidebarCollapsed, togglePropertiesSub],
  )

  return <ShellNavContext.Provider value={value}>{children}</ShellNavContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components -- hook compartido
export function useShellNav() {
  const ctx = useContext(ShellNavContext)
  if (!ctx) throw new Error('useShellNav must be used within ShellNavProvider')
  return ctx
}
