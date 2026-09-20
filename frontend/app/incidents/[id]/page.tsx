'use client'

import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, CalendarBlank, Clock } from '@phosphor-icons/react'
import Link from 'next/link'

import { AnalysisResults } from '@/components/analysis/AnalysisResults'
import { SeverityBadge } from '@/components/ui/SeverityBadge'
import { SectionState } from '@/components/ui/SectionState'
import { Skeleton } from '@/components/ui/skeleton'
import { getAnalysis } from '@/lib/api'

interface IncidentDetailPageProps {
  params: { id: string }
}

export default function IncidentDetailPage({ params }: IncidentDetailPageProps) {
  const report = useQuery({
    queryKey: ['analysis', params.id],
    queryFn: () => getAnalysis(params.id),
  })

  if (report.isLoading) {
    return <div className="space-y-5"><Skeleton className="h-8 w-56" /><Skeleton className="h-[520px]" /></div>
  }
  if (report.isError || !report.data) {
    return <SectionState kind="error" title="Report unavailable" description={report.error instanceof Error ? report.error.message : 'This analysis could not be loaded.'} onRetry={() => void report.refetch()} />
  }

  const created = new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(report.data.created_at))
  return (
    <div className="space-y-6">
      <Link href="/incidents" className="no-print inline-flex items-center gap-2 rounded-[8px] px-1 py-2 text-sm font-semibold text-text-secondary hover:text-text-primary">
        <ArrowLeft aria-hidden="true" size={16} /> Back to incidents
      </Link>
      <header className="print-surface rounded-[12px] border border-border-subtle bg-bg-surface p-5 md:p-7">
        <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-3"><SeverityBadge severity={report.data.risk_score.tier} /><span className="font-mono text-xs text-text-muted">{report.data.analysis_id}</span></div>
            <h1 className="mt-4 break-words font-display text-3xl font-bold tracking-[-0.03em]">{report.data.file_name}</h1>
            <div className="mt-4 flex flex-wrap gap-4 text-sm text-text-secondary">
              <span className="flex items-center gap-2"><CalendarBlank aria-hidden="true" size={15} weight="light" />{created}</span>
              <span className="flex items-center gap-2"><Clock aria-hidden="true" size={15} weight="light" />{report.data.processing_time_seconds.toFixed(1)} seconds</span>
            </div>
          </div>
          <div className="font-display text-5xl font-extrabold tracking-[-0.05em]">{report.data.risk_score.total.toFixed(1)}</div>
        </div>
      </header>
      <AnalysisResults report={report.data} showHeading={false} />
    </div>
  )
}
