import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AppLayout } from './layouts/AppLayout'
import { LoginPage } from './pages/LoginPage'
import { ConfigPage } from './pages/ConfigPage'
import { SavedPage } from './pages/SavedPage'
import { MarketAnalysisPage } from './pages/MarketAnalysisPage'
import { ContractsPage } from './pages/ContractsPage'
import { ProjectsPage } from './pages/ProjectsPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/properties/config" replace />} />
          <Route path="/properties" element={<Navigate to="/properties/config" replace />} />
          <Route path="/properties/config" element={<ConfigPage />} />
          <Route path="/properties/saved" element={<SavedPage />} />
          <Route path="/properties/market" element={<MarketAnalysisPage />} />
          <Route path="/contracts" element={<ContractsPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/config" element={<Navigate to="/properties/config" replace />} />
          <Route path="/saved" element={<Navigate to="/properties/saved" replace />} />
          <Route path="/market" element={<Navigate to="/properties/market" replace />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/properties/config" replace />} />
    </Routes>
  )
}
