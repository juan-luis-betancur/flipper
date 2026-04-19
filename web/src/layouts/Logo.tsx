import clsx from 'clsx'

type Props = {
  size?: number
  withWordmark?: boolean
  className?: string
}

export function Logo({ size = 32, withWordmark = true, className }: Props) {
  return (
    <div className={clsx('flex items-center gap-2', className)}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-label="Flipper"
      >
        <defs>
          <linearGradient id="flipper-logo-grad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#6366f1" />
            <stop offset="60%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#d946ef" />
          </linearGradient>
          <linearGradient id="flipper-logo-accent" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#fbbf24" />
            <stop offset="100%" stopColor="#f59e0b" />
          </linearGradient>
        </defs>
        <rect width="40" height="40" rx="10" fill="url(#flipper-logo-grad)" />
        <path
          d="M9 21.5 20 11l11 10.5V30a1 1 0 0 1-1 1h-6v-7h-8v7h-6a1 1 0 0 1-1-1z"
          fill="#ffffff"
          fillOpacity="0.98"
        />
        <path
          d="M15 22.5 20 17l5 5.5"
          stroke="url(#flipper-logo-accent)"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
        <path
          d="M23.2 17.2 25 17l-.2 1.8"
          stroke="url(#flipper-logo-accent)"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
      </svg>
      {withWordmark && (
        <span className="text-[17px] font-semibold tracking-tight text-text">
          Flipper
        </span>
      )}
    </div>
  )
}
