import type { PropsWithChildren } from 'react'

import { cn } from '@/lib/utils'

interface BackgroundGradientProps extends PropsWithChildren {
  className?: string
  critical?: boolean
}

export function BackgroundGradient({ children, className, critical = false }: BackgroundGradientProps) {
  return (
    <div
      className={cn(
        'rounded-[13px] border border-border-default bg-bg-card p-px shadow-card',
        critical && 'border-severity-critical/30 shadow-[0_18px_70px_rgba(255,59,48,0.08)]',
        className,
      )}
    >
      {children}
    </div>
  )
}
