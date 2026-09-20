import { cn } from '@/lib/utils'

interface BackgroundBeamsProps {
  className?: string
}

export function BackgroundBeams({ className }: BackgroundBeamsProps) {
  return (
    <div aria-hidden="true" className={cn('pointer-events-none absolute inset-0 overflow-hidden', className)}>
      {Array.from({ length: 6 }, (_, index) => (
        <span
          key={index}
          className="absolute left-[-18%] top-[var(--beam-top)] h-px w-[136%] origin-center rotate-[var(--beam-angle)] animate-beam bg-gradient-to-r from-transparent via-accent/35 to-transparent opacity-0 motion-reduce:animate-none motion-reduce:opacity-20"
          style={
            {
              '--beam-top': `${12 + index * 15}%`,
              '--beam-angle': `${-7 + index * 2.5}deg`,
              animationDelay: `${index * 0.7}s`,
            } as React.CSSProperties
          }
        />
      ))}
    </div>
  )
}
