import { ComingSoon } from '../components/ComingSoon'

export function ContractsPage() {
  return (
    <ComingSoon
      title="Contratos"
      tagline="Gestiona tus promesas de compraventa y contratos de arrendamiento en un solo lugar. Firmas, vencimientos y alertas automáticas."
      heroIcon={
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <path d="M14 2v6h6" />
          <path d="M8 13h8M8 17h5" />
        </svg>
      }
      features={[
        {
          icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.59 13.41 13.42 20.58a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z" />
              <line x1="7" y1="7" x2="7.01" y2="7" />
            </svg>
          ),
          title: 'Carga y OCR',
          description: 'Sube PDFs y extrae automáticamente partes, fechas clave y montos.',
        },
        {
          icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
            </svg>
          ),
          title: 'Firmas y estados',
          description: 'Tracking de cada parte, firmado vs pendiente, con timeline visual.',
        },
        {
          icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M6 2v6a6 6 0 0 0 12 0V2" />
              <path d="M6 22v-6a6 6 0 0 1 12 0v6" />
              <line x1="4" y1="2" x2="20" y2="2" />
              <line x1="4" y1="22" x2="20" y2="22" />
            </svg>
          ),
          title: 'Vencimientos',
          description: 'Alertas por Telegram cuando se acerca una fecha crítica del contrato.',
        },
      ]}
    />
  )
}
