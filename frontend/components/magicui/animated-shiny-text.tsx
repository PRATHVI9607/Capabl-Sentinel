import type { PropsWithChildren } from 'react'

import { cn } from '@/lib/utils'

interface AnimatedShinyTextProps extends PropsWithChildren {
  className?: string
}

export function AnimatedShinyText({ children, className }: AnimatedShinyTextProps) {
  return (
    <span
      className={cn(
        'animate-shine bg-[linear-gradient(100deg,var(--severity-critical)_0%,var(--severity-critical)_38%,var(--text-primary)_50%,var(--severity-critical)_62%,var(--severity-critical)_100%)] bg-[length:220%_100%] bg-clip-text text-transparent motion-reduce:animate-none',
        className,
      )}
    >
      {children}
    </span>
  )
}
