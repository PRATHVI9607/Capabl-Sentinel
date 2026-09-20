'use client'

import { useQueries, useQuery } from '@tanstack/react-query'
import { Factory, Gauge, Pulse, Warning } from '@phosphor-icons/react'
import { useEffect } from 'react'

import { SeverityChart } from '@/components/charts/SeverityChart'
import { IndustryHeatmap } from '@/components/dashboard/IndustryHeatmap'
import { RecentAlerts } from '@/components/dashboard/RecentAlerts'
import { StatCard } from '@/components/dashboard/StatCard'
import { SectionState } from '@/components/ui/SectionState'
import { Skeleton } from '@/components/ui/skeleton'
import { getAnalysis, getHistory, getStats } from '@/lib/api'
import { useSentinelStore } from '@/store/sentinel'

export default function DashboardPage() {
  const stats = useQuery({ queryKey: ['stats'], queryFn: getStats })
  const history = useQuery({
    queryKey: ['history', { limit: 100 }],
    queryFn: () => getHistory({ limit: 100 }),
  })
  const recentReports = useQueries({
    queries: (history.data?.items.slice(0, 8) ?? []).map((item) => ({
      queryKey: ['analysis', item.analysis_id],
      queryFn: () => getAnalysis(item.analysis_id),
      staleTime: 60_000,
    })),
  })
  const setHistory = useSentinelStore((state) => state.setAnalysisHistory)

  useEffect(() => {
    if (history.data) setHistory(history.data.items)
  }, [history.data, setHistory])

  if (stats.isError || history.isError) {
    const cause = stats.error ?? history.error
    return <SectionState kind="error" title="Dashboard unavailable" description={cause instanceof Error ? cause.message : 'The dashboard could not be loaded.'} onRetry={() => { void stats.refetch(); void history.refetch() }} />
  }

  if (stats.isLoading || history.isLoading || !stats.data || !history.data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }, (_, index) => <Skeleton key={index} className="h-36" />)}
        </div>
        <div className="grid gap-6 lg:grid-cols-[3fr_2fr]"><Skeleton className="h-96" /><Skeleton className="h-96" /></div>
      </div>
    )
  }

  const alerts = recentReports
    .flatMap((query) => query.data?.alerts ?? [])
    .sort((left, right) => Date.parse(right.created_at) - Date.parse(left.created_at))

  return (
    <div className="space-y-7">
      <header className="grid gap-6 border-b border-border-subtle pb-7 lg:grid-cols-[1fr_340px] lg:items-end">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-accent">Operational overview</p>
          <h1 className="mt-4 font-display text-4xl font-bold tracking-[-0.045em] md:text-5xl">Safety intelligence, in focus.</h1>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-text-secondary">Completed assessments, the current risk mix and findings that need review.</p>
        </div>
        <div className="border-l border-border-default pl-5 font-mono text-[10px] uppercase leading-6 tracking-[0.1em] text-text-muted">
          <p>Scope · most recent 100 analyses</p>
          <p>Order · newest findings first</p>
        </div>
      </header>

      <div className="instrument-panel grid overflow-hidden rounded-[8px] border border-border-default bg-bg-base sm:grid-cols-2 xl:grid-cols-4 xl:divide-x xl:divide-border-subtle">
        <StatCard label="Total analyses" value={stats.data.total_analyses} icon={Pulse} />
        <StatCard label="Critical alerts" value={stats.data.critical_alerts} icon={Warning} />
        <StatCard label="Average risk" value={stats.data.avg_risk_score} decimalPlaces={1} icon={Gauge} />
        <StatCard label="Industries covered" value={stats.data.industries_covered} icon={Factory} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.65fr)_minmax(340px,.75fr)]">
        <SeverityChart history={history.data.items} />
        <RecentAlerts alerts={alerts} />
      </div>
      <IndustryHeatmap history={history.data.items} />
    </div>
  )
}
