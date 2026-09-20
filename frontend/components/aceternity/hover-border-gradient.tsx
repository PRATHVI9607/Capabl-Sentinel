import type { ButtonHTMLAttributes } from 'react'

import { CircleNotch } from '@phosphor-icons/react'

import { cn } from '@/lib/utils'

interface HoverBorderGradientProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean
}

export function HoverBorderGradient({
  children,
  className,
  loading = false,
  disabled,
  ...props
}: HoverBorderGradientProps) {
  return (
    <button
      type="button"
      className={cn(
        'group relative flex h-12 w-full items-center justify-center overflow-hidden rounded-[10px] p-px font-semibold text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:pointer-events-none disabled:opacity-50 active:translate-y-px',
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      <span className="absolute inset-[-80%] bg-[conic-gradient(from_90deg,transparent_0_72%,var(--accent)_82%,var(--accent-hover)_90%,transparent_100%)] transition-transform duration-[3000ms] group-hover:rotate-[360deg] motion-reduce:transition-none" />
      <span className="relative flex h-full w-full items-center justify-center gap-2 rounded-[9px] bg-bg-surface px-5 transition-colors group-hover:bg-bg-card">
        {loading ? <CircleNotch aria-hidden="true" className="animate-spin" size={17} weight="light" /> : null}
        {children}
      </span>
    </button>
  )
}
