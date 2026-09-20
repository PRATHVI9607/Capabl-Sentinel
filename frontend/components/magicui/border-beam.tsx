import { cn } from '@/lib/utils'

interface BorderBeamProps {
  critical?: boolean
  className?: string
}

export function BorderBeam({ critical = false, className }: BorderBeamProps) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        'pointer-events-none absolute inset-[-70%] animate-border-orbit bg-[conic-gradient(from_0deg,transparent_0_84%,var(--accent)_92%,transparent_100%)] motion-reduce:animate-none',
        critical && 'bg-[conic-gradient(from_0deg,transparent_0_82%,var(--severity-critical)_92%,transparent_100%)] [animation-duration:4s]',
        className,
      )}
    />
  )
}
