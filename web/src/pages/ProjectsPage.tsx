export function ProjectsPage() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-8 text-center shadow-sm">
        <div className="mx-auto mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-bg-secondary text-accent">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="16" rx="2" />
            <path d="M3 10h18M8 4v6M16 4v6" />
          </svg>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-text">Proyectos</h1>
        <p className="mt-1 text-sm font-medium text-accent">Próximamente</p>
        <p className="mt-4 text-sm text-text-secondary">
          Aquí vas a poder organizar tus proyectos de inversión: flujos de caja,
          estado de obra, avances por hito y comparativos de rentabilidad.
        </p>
      </div>
    </div>
  )
}
