import { cn } from '@/lib/utils'

interface SpotlightProps {
  className?: string
}

export function Spotlight({ className }: SpotlightProps) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        'pointer-events-none absolute -left-32 -top-40 h-[420px] w-[420px] rounded-full bg-severity-critical/10 blur-[90px]',
        className,
      )}
    />
  )
}
