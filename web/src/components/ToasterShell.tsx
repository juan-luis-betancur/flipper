import { Toaster } from 'sonner'
import { useTheme } from '../lib/theme'

export function ToasterShell() {
  const { theme } = useTheme()
  return <Toaster richColors position="top-right" theme={theme} />
}
