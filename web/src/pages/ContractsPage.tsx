export function ContractsPage() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-8 text-center shadow-sm">
        <div className="mx-auto mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-bg-secondary text-accent">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <path d="M14 2v6h6" />
            <path d="M8 13h8M8 17h5" />
          </svg>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-text">Contratos</h1>
        <p className="mt-1 text-sm font-medium text-accent">Próximamente</p>
        <p className="mt-4 text-sm text-text-secondary">
          Aquí vas a poder gestionar tus contratos de compraventa y arrendamiento:
          carga de documentos, seguimiento de firmas, vencimientos y alertas.
        </p>
      </div>
    </div>
  )
}
