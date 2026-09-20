'use client'

import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import * as Tabs from '@radix-ui/react-tabs'
import { Funnel } from '@phosphor-icons/react'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { Suspense } from 'react'

import { IncidentCard } from '@/components/incidents/IncidentCard'
import { Button } from '@/components/ui/button'
import { SectionState } from '@/components/ui/SectionState'
import { Skeleton } from '@/components/ui/skeleton'
import { getHistory } from '@/lib/api'
import type { SeverityTier } from '@/lib/types'
import { titleCase } from '@/lib/utils'

const severities = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const
type SeverityFilter = (typeof severities)[number]

function isSeverityFilter(value: string | null): value is SeverityFilter {
  return value !== null && severities.includes(value as SeverityFilter)
}

function IncidentsContent() {
  const router = useRouter()
  const pathname = usePathname()
  const params = useSearchParams()
  const severity = isSeverityFilter(params.get('severity')) ? params.get('severity') as SeverityFilter : 'ALL'
  const industry = params.get('industry') ?? ''

  const allHistory = useQuery({
    queryKey: ['history', 'industries'],
    queryFn: () => getHistory({ limit: 100 }),
  })
  const incidents = useInfiniteQuery({
    queryKey: ['incidents', severity, industry],
    initialPageParam: 1,
    queryFn: ({ pageParam }) =>
      getHistory({
        page: pageParam,
        limit: 12,
        severity: severity === 'ALL' ? undefined : severity,
        industry: industry || undefined,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.page * lastPage.limit < lastPage.total ? lastPage.page + 1 : undefined,
  })

  const updateFilters = (nextSeverity: SeverityFilter, nextIndustry: string) => {
    const query = new URLSearchParams()
    if (nextSeverity !== 'ALL') query.set('severity', nextSeverity)
    if (nextIndustry) query.set('industry', nextIndustry)
    router.replace(query.size ? `${pathname}?${query.toString()}` : pathname)
  }

  const items = incidents.data?.pages.flatMap((page) => page.items) ?? []
  const industries = Array.from(
    new Set((allHistory.data?.items ?? []).map((item) => item.industry).filter((value): value is string => Boolean(value))),
  ).sort()

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs font-bold uppercase tracking-[0.12em] text-accent">Incident archive</p>
        <h1 className="mt-2 font-display text-3xl font-bold tracking-[-0.03em] md:text-4xl">Past analyses</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary">Review completed reports by severity and industry.</p>
      </header>

      <div className="flex flex-col gap-4 rounded-[12px] border border-border-subtle bg-bg-surface p-3 lg:flex-row lg:items-center lg:justify-between">
        <Tabs.Root value={severity} onValueChange={(value) => updateFilters(value as SeverityFilter, industry)}>
          <Tabs.List aria-label="Filter incidents by severity" className="grid grid-cols-5 gap-1">
            {severities.map((item) => (
              <Tabs.Trigger
                key={item}
                value={item}
                className="rounded-[8px] px-3 py-2 text-xs font-semibold text-text-muted transition-colors hover:text-text-primary data-[state=active]:bg-bg-card data-[state=active]:text-text-primary data-[state=active]:shadow-[inset_0_0_0_1px_var(--border-default)]"
              >
                {item === 'ALL' ? 'All' : titleCase(item)}
              </Tabs.Trigger>
            ))}
          </Tabs.List>
        </Tabs.Root>

        <label className="flex items-center gap-2 rounded-[9px] border border-border-default bg-bg-card px-3 text-sm text-text-secondary focus-within:ring-2 focus-within:ring-accent">
          <Funnel aria-hidden="true" size={15} weight="light" />
          <span className="sr-only">Filter by industry</span>
          <select
            value={industry}
            onChange={(event) => updateFilters(severity, event.target.value)}
            className="h-10 min-w-52 bg-transparent text-sm text-text-primary outline-none"
          >
            <option value="">All industries</option>
            {industries.map((item) => <option key={item} value={item}>{titleCase(item)}</option>)}
          </select>
        </label>
      </div>

      {incidents.isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }, (_, index) => <Skeleton key={index} className="h-64" />)}
        </div>
      ) : incidents.isError ? (
        <SectionState kind="error" title="Incidents unavailable" description={incidents.error instanceof Error ? incidents.error.message : 'The archive could not be loaded.'} onRetry={() => void incidents.refetch()} />
      ) : items.length ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {items.map((incident) => <IncidentCard key={incident.analysis_id} incident={incident} />)}
          </div>
          {incidents.hasNextPage ? (
            <div className="flex justify-center pt-2">
              <Button type="button" variant="secondary" disabled={incidents.isFetchingNextPage} onClick={() => void incidents.fetchNextPage()}>
                {incidents.isFetchingNextPage ? 'Loading reports' : 'Load more'}
              </Button>
            </div>
          ) : null}
        </>
      ) : (
        <SectionState kind="empty" title="No matching incidents" description="Completed analyses that match these filters will appear here." actionHref="/analyze" actionLabel="Analyze a report" />
      )}
    </div>
  )
}

export default function IncidentsPage() {
  return (
    <Suspense fallback={<Skeleton className="h-[480px]" />}>
      <IncidentsContent />
    </Suspense>
  )
}
