'use client'

import { useQueries, useQuery } from '@tanstack/react-query'
import * as Tabs from '@radix-ui/react-tabs'
import { ArrowSquareOut } from '@phosphor-icons/react'
import Link from 'next/link'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useEffect } from 'react'

import { SeverityBadge } from '@/components/ui/SeverityBadge'
import { SectionState } from '@/components/ui/SectionState'
import { Skeleton } from '@/components/ui/skeleton'
import { getAllHistory, getAnalysis } from '@/lib/api'
import type { Alert, SeverityTier } from '@/lib/types'
import { titleCase } from '@/lib/utils'
import { useSentinelStore } from '@/store/sentinel'

const filters = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const
type AlertFilter = (typeof filters)[number]

interface AlertWithReport {
  alert: Alert
  analysisId: string
  fileName: string
}

function isAlertFilter(value: string | null): value is AlertFilter {
  return value !== null && filters.includes(value as AlertFilter)
}

function AlertsContent() {
  const router = useRouter()
  const pathname = usePathname()
  const params = useSearchParams()
  const filter = isAlertFilter(params.get('severity')) ? params.get('severity') as AlertFilter : 'ALL'
  const history = useQuery({ queryKey: ['history', 'all'], queryFn: getAllHistory })
  const reports = useQueries({
    queries: (history.data ?? []).map((item) => ({
      queryKey: ['analysis', item.analysis_id],
      queryFn: () => getAnalysis(item.analysis_id),
      staleTime: 60_000,
    })),
  })
  const setGlobalAlerts = useSentinelStore((state) => state.setGlobalAlerts)

  const alerts: AlertWithReport[] = reports
    .flatMap((query) =>
      (query.data?.alerts ?? []).map((alert) => ({
        alert,
        analysisId: query.data?.analysis_id ?? '',
        fileName: query.data?.file_name ?? '',
      })),
    )
    .sort((left, right) => Date.parse(right.alert.created_at) - Date.parse(left.alert.created_at))

  useEffect(() => {
    setGlobalAlerts(alerts.map((item) => item.alert))
  }, [alerts, setGlobalAlerts])

  const setFilter = (value: AlertFilter) => {
    router.replace(value === 'ALL' ? pathname : `${pathname}?severity=${value}`)
  }
  const visible = filter === 'ALL' ? alerts : alerts.filter((item) => item.alert.severity === filter as SeverityTier)
  const loading = history.isLoading || reports.some((query) => query.isLoading)
  const failed = history.isError || reports.some((query) => query.isError)

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs font-bold uppercase tracking-[0.12em] text-accent">Alert register</p>
        <h1 className="mt-2 font-display text-3xl font-bold tracking-[-0.03em] md:text-4xl">Findings that need attention</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary">Alerts from every completed analysis, ordered newest first.</p>
      </header>

      <Tabs.Root value={filter} onValueChange={(value) => setFilter(value as AlertFilter)} className="rounded-[12px] border border-border-subtle bg-bg-surface p-3">
        <Tabs.List aria-label="Filter alerts by severity" className="grid max-w-2xl grid-cols-5 gap-1">
          {filters.map((item) => (
            <Tabs.Trigger key={item} value={item} className="rounded-[8px] px-3 py-2 text-xs font-semibold text-text-muted transition-colors hover:text-text-primary data-[state=active]:bg-bg-card data-[state=active]:text-text-primary data-[state=active]:shadow-[inset_0_0_0_1px_var(--border-default)]">
              {item === 'ALL' ? 'All' : titleCase(item)}
            </Tabs.Trigger>
          ))}
        </Tabs.List>
      </Tabs.Root>

      {failed && !loading ? (
        <SectionState kind="error" title="Some alerts could not be loaded" description="One or more analysis reports were unavailable. Retry to rebuild the full register." onRetry={() => { void history.refetch(); reports.forEach((query) => void query.refetch()) }} />
      ) : loading ? (
        <div className="grid gap-4 lg:grid-cols-2">{Array.from({ length: 6 }, (_, index) => <Skeleton key={index} className="h-56" />)}</div>
      ) : visible.length ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {visible.map(({ alert, analysisId, fileName }) => (
            <article key={`${analysisId}-${alert.id}`} className="mechanical-card print-surface rounded-[9px] border border-border-subtle bg-bg-card p-5 md:p-6">
              <div className="flex items-start justify-between gap-4">
                <SeverityBadge severity={alert.severity} />
                <time className="font-mono text-[11px] text-text-muted" dateTime={alert.created_at}>{new Intl.DateTimeFormat('en', { dateStyle: 'medium' }).format(new Date(alert.created_at))}</time>
              </div>
              <h2 className="mt-5 font-display text-lg font-semibold leading-6">{alert.title}</h2>
              <p className="mt-2 text-sm leading-6 text-text-secondary">{alert.description}</p>
              {(alert.regulatory_violations.length || alert.precursor_patterns.length) ? (
                <div className="mt-5 grid gap-4 border-t border-border-subtle pt-4 sm:grid-cols-2">
                  <div><h3 className="text-[11px] font-bold uppercase tracking-[0.1em] text-text-muted">Regulatory</h3><p className="mt-2 line-clamp-3 font-mono text-xs leading-5 text-text-secondary">{alert.regulatory_violations.join(', ') || 'None cited'}</p></div>
                  <div><h3 className="text-[11px] font-bold uppercase tracking-[0.1em] text-text-muted">Precursors</h3><p className="mt-2 line-clamp-3 text-xs leading-5 text-text-secondary">{alert.precursor_patterns.join(', ') || 'None cited'}</p></div>
                </div>
              ) : null}
              <Link href={`/incidents/${analysisId}`} className="mt-5 inline-flex items-center gap-2 rounded-[8px] text-sm font-semibold text-accent hover:text-accent-hover">
                {fileName}<ArrowSquareOut aria-hidden="true" size={14} weight="light" />
              </Link>
            </article>
          ))}
        </div>
      ) : (
        <SectionState kind="empty" title="No matching alerts" description="Alerts with this severity will appear after a completed incident analysis." actionHref="/analyze" actionLabel="Analyze a report" />
      )}
    </div>
  )
}

export default function AlertsPage() {
  return (
    <Suspense fallback={<Skeleton className="h-[480px]" />}>
      <AlertsContent />
    </Suspense>
  )
}
