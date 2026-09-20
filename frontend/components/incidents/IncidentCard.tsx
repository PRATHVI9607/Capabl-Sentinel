import { ArrowUpRight, CalendarBlank, Factory } from '@phosphor-icons/react'
import Link from 'next/link'

import { SeverityBadge } from '@/components/ui/SeverityBadge'
import type { AnalysisSummary } from '@/lib/types'
import { titleCase } from '@/lib/utils'

interface IncidentCardProps {
  incident: AnalysisSummary
}

export function IncidentCard({ incident }: IncidentCardProps) {
  const date = new Intl.DateTimeFormat('en', { dateStyle: 'medium' }).format(new Date(incident.created_at))
  return (
    <article className="mechanical-card print-surface group flex min-h-64 flex-col rounded-[9px] border border-border-subtle bg-bg-card p-5 hover:bg-bg-card-hover">
      <div className="flex items-start justify-between gap-4">
        <SeverityBadge severity={incident.severity} />
        <span className="font-display text-3xl font-bold tracking-[-0.04em]">{incident.risk_total.toFixed(1)}</span>
      </div>
      <h2 className="mt-6 line-clamp-2 font-display text-lg font-semibold leading-6">{incident.file_name}</h2>
      <div className="mt-4 space-y-2 text-sm text-text-secondary">
        <div className="flex items-center gap-2"><Factory aria-hidden="true" size={15} /><span>{incident.industry ? titleCase(incident.industry) : 'Industry not identified'}</span></div>
        <div className="flex items-center gap-2"><CalendarBlank aria-hidden="true" size={15} weight="light" /><time dateTime={incident.created_at}>{date}</time></div>
      </div>
      <Link href={`/incidents/${incident.analysis_id}`} className="mt-auto inline-flex items-center gap-2 rounded-[8px] pt-6 text-sm font-semibold text-accent transition-colors hover:text-accent-hover">
        View report <ArrowUpRight aria-hidden="true" size={15} />
      </Link>
    </article>
  )
}
