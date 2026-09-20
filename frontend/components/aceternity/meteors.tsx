import { cn } from '@/lib/utils'

interface MeteorsProps {
  count?: number
  className?: string
}

export function Meteors({ count = 12, className }: MeteorsProps) {
  return (
    <div aria-hidden="true" className={cn('pointer-events-none absolute inset-0 overflow-hidden opacity-30', className)}>
      {Array.from({ length: count }, (_, index) => (
        <span
          key={index}
          className="absolute h-px w-20 rotate-[135deg] animate-meteor bg-gradient-to-r from-accent/60 to-transparent opacity-0 motion-reduce:animate-none motion-reduce:opacity-10"
          style={
            {
              left: `${8 + ((index * 19) % 92)}%`,
              top: `${-12 + ((index * 13) % 34)}%`,
              animationDelay: `${index * 1.4}s`,
              animationDuration: `${10 + (index % 4) * 2}s`,
            } as React.CSSProperties
          }
        />
      ))}
    </div>
  )
}
