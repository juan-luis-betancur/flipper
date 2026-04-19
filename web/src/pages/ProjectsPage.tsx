import { ComingSoon } from '../components/ComingSoon'

export function ProjectsPage() {
  return (
    <ComingSoon
      title="Proyectos"
      tagline="Organiza tus proyectos de inversión: presupuesto, avance de obra, flujos de caja y rentabilidad por hito."
      heroIcon={
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="4" width="18" height="16" rx="2" />
          <path d="M3 10h18M8 4v6M16 4v6" />
        </svg>
      }
      features={[
        {
          icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2 2 7l10 5 10-5-10-5z" />
              <path d="m2 17 10 5 10-5M2 12l10 5 10-5" />
            </svg>
          ),
          title: 'Presupuesto por rubro',
          description: 'Plantillas de remodelación con costos por m² y proveedores recurrentes.',
        },
        {
          icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
          ),
          title: 'Flujo de caja',
          description: 'Aportes, desembolsos y proyecciones de retorno mes a mes.',
        },
        {
          icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
              <polyline points="17 6 23 6 23 12" />
            </svg>
          ),
          title: 'Rentabilidad real',
          description: 'ROI y TIR calculados con datos reales vs. presupuesto inicial.',
        },
      ]}
    />
  )
}
