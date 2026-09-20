import type { HTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {}

export function Badge({ className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md border px-2 py-1 text-[11px] font-bold uppercase tracking-[0.08em]',
        className,
      )}
      {...props}
    />
  )
}
