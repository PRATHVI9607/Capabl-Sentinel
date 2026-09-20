import type { ButtonHTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

interface ShimmerButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {}

export function ShimmerButton({ className, children, ...props }: ShimmerButtonProps) {
  return (
    <button
      type="button"
      className={cn(
        'group relative inline-flex h-10 items-center justify-center overflow-hidden rounded-[9px] border border-border-default bg-bg-card px-4 text-sm font-semibold text-text-primary transition-colors hover:border-accent/50 hover:bg-bg-card-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent active:translate-y-px',
        className,
      )}
      {...props}
    >
      <span className="absolute inset-y-0 -left-16 w-12 skew-x-[-18deg] bg-accent/20 blur-sm transition-transform duration-700 group-hover:translate-x-[280px] motion-reduce:hidden" />
      <span className="relative">{children}</span>
    </button>
  )
}
