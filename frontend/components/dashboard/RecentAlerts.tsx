import { Bell, Warning } from '@phosphor-icons/react'
import Link from 'next/link'

import { SeverityBadge } from '@/components/ui/SeverityBadge'
import type { Alert } from '@/lib/types'

interface RecentAlertsProps {
  alerts: Alert[]
}

export function RecentAlerts({ alerts }: RecentAlertsProps) {
  return (
    <section aria-labelledby="recent-alerts-heading" className="instrument-panel print-surface min-h-[440px] rounded-[8px] border border-border-default bg-bg-base p-5 md:p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 id="recent-alerts-heading" className="font-display text-2xl font-bold">Recent alerts</h2>
          <p className="mt-1 text-sm text-text-secondary">Newest findings that need attention.</p>
        </div>
        <Bell aria-hidden="true" className="text-text-muted" size={21} weight="light" />
      </div>

      {alerts.length ? (
        <div className="mt-5 divide-y divide-border-subtle border-y border-border-subtle">
          {alerts.slice(0, 5).map((alert) => (
            <article key={alert.id} className="py-4">
              <div className="flex items-start justify-between gap-3">
                <h3 className="font-display text-sm font-semibold leading-5">{alert.title}</h3>
                <SeverityBadge severity={alert.severity} />
              </div>
              <p className="mt-2 line-clamp-2 text-xs leading-5 text-text-secondary">{alert.description}</p>
            </article>
          ))}
          <Link href="/alerts" className="mt-3 inline-flex px-1 py-2 text-sm font-semibold text-accent hover:text-accent-hover">View all alerts</Link>
        </div>
      ) : (
        <div className="mt-8 flex min-h-56 flex-col items-center justify-center text-center">
          <Warning aria-hidden="true" className="text-text-muted" size={25} weight="light" />
          <p className="mt-3 text-sm font-semibold">No alerts yet</p>
          <p className="mt-1 max-w-xs text-sm leading-6 text-text-secondary">Alerts appear after an incident report has completed analysis.</p>
        </div>
      )}
    </section>
  )
}
