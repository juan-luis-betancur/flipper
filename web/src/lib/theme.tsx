import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'

export type FlipperTheme = 'light' | 'dark'

const STORAGE_KEY = 'flipper-theme'

function readStoredTheme(): FlipperTheme | null {
  try {
    const v = localStorage.getItem(STORAGE_KEY)
    if (v === 'dark' || v === 'light') return v
  } catch {
    /* ignore */
  }
  return null
}

function getInitialTheme(): FlipperTheme {
  const stored = readStoredTheme()
  if (stored) return stored
  if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }
  return 'light'
}

function applyDomTheme(theme: FlipperTheme) {
  const root = document.documentElement
  if (theme === 'dark') root.classList.add('dark')
  else root.classList.remove('dark')
  root.style.colorScheme = theme === 'dark' ? 'dark' : 'light'
}

type ThemeContextValue = {
  theme: FlipperTheme
  setTheme: (t: FlipperTheme) => void
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<FlipperTheme>(getInitialTheme)

  const setTheme = useCallback((t: FlipperTheme) => {
    setThemeState(t)
    try {
      localStorage.setItem(STORAGE_KEY, t)
    } catch {
      /* ignore */
    }
  }, [])

  useEffect(() => {
    applyDomTheme(theme)
  }, [theme])

  const toggleTheme = useCallback(() => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }, [theme, setTheme])

  const value = useMemo(
    () => ({ theme, setTheme, toggleTheme }),
    [theme, setTheme, toggleTheme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

/** Hook consumido por muchos componentes; excepción al-only-components de react-refresh. */
// eslint-disable-next-line react-refresh/only-export-components -- hook compartido
export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
