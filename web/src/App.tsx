import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AppLayout } from './layouts/AppLayout'
import { LoginPage } from './pages/LoginPage'
import { ConfigPage } from './pages/ConfigPage'
import { SavedPage } from './pages/SavedPage'
import { MarketAnalysisPage } from './pages/MarketAnalysisPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/config" replace />} />
          <Route path="/config" element={<ConfigPage />} />
          <Route path="/saved" element={<SavedPage />} />
          <Route path="/market" element={<MarketAnalysisPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/config" replace />} />
    </Routes>
  )
}
