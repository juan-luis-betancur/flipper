type Feature = {
  icon: React.ReactNode
  title: string
  description: string
}

type Props = {
  title: string
  tagline: string
  heroIcon: React.ReactNode
  features: Feature[]
}

export function ComingSoon({ title, tagline, heroIcon, features }: Props) {
  return (
    <div className="mx-auto max-w-3xl py-6 sm:py-10">
      <div className="relative overflow-hidden rounded-3xl border border-border bg-card p-8 text-center card-shadow sm:p-14">
        <div
          aria-hidden
          className="pointer-events-none absolute -left-16 -top-16 h-56 w-56 rounded-full opacity-30 blur-3xl"
          style={{ background: 'radial-gradient(circle, #a855f7 0%, transparent 70%)' }}
        />
        <div
          aria-hidden
          className="pointer-events-none absolute -right-20 -top-10 h-64 w-64 rounded-full opacity-25 blur-3xl"
          style={{ background: 'radial-gradient(circle, #6366f1 0%, transparent 70%)' }}
        />

        <div className="relative">
          <div className="mx-auto mb-5 inline-flex h-16 w-16 items-center justify-center rounded-2xl brand-gradient text-white elevated-shadow">
            {heroIcon}
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-accent-soft px-3 py-1 text-xs font-semibold uppercase tracking-wide text-accent">
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
            Próximamente
          </span>
          <h1 className="mt-4 text-3xl font-bold tracking-tight text-text sm:text-4xl">
            {title}
          </h1>
          <p className="mx-auto mt-3 max-w-lg text-base text-text-secondary">
            {tagline}
          </p>
        </div>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        {features.map((f) => (
          <div
            key={f.title}
            className="rounded-2xl border border-border bg-card p-5 card-shadow transition-all hover:-translate-y-0.5 hover:border-border-strong"
          >
            <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-accent">
              {f.icon}
            </div>
            <h3 className="text-sm font-semibold text-text">{f.title}</h3>
            <p className="mt-1 text-xs leading-relaxed text-text-secondary">
              {f.description}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
