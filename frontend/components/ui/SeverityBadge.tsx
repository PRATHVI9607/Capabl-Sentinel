import { Badge } from '@/components/ui/badge'
import { SEVERITY_CONFIG } from '@/lib/constants'
import type { SeverityTier } from '@/lib/types'
import { cn } from '@/lib/utils'

interface SeverityBadgeProps {
  severity: SeverityTier
  className?: string
  children?: React.ReactNode
}

export function SeverityBadge({ severity, className, children }: SeverityBadgeProps) {
  const config = SEVERITY_CONFIG[severity]
  return (
    <Badge role="status" className={cn(config.tone, className)}>
      {children ?? config.label}
    </Badge>
  )
}
