import { Factory } from '@phosphor-icons/react'

import type { AnalysisSummary } from '@/lib/types'
import { titleCase } from '@/lib/utils'

interface IndustryHeatmapProps {
  history: AnalysisSummary[]
}

export function IndustryHeatmap({ history }: IndustryHeatmapProps) {
  const counts = history.reduce<Record<string, number>>((result, item) => {
    const industry = item.industry ?? 'Unspecified'
    result[industry] = (result[industry] ?? 0) + 1
    return result
  }, {})
  const entries = Object.entries(counts).sort((left, right) => right[1] - left[1])
  const maximum = Math.max(...entries.map(([, count]) => count), 1)

  return (
    <section aria-labelledby="industry-heading" className="instrument-panel print-surface rounded-[8px] border border-border-default bg-bg-base p-5 md:p-7">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center border border-accent/25 text-accent">
          <Factory aria-hidden="true" size={19} weight="light" />
        </span>
        <div>
          <h2 id="industry-heading" className="font-display text-2xl font-bold">Industry coverage</h2>
          <p className="mt-1 text-sm text-text-secondary">Completed analyses grouped by reported industry.</p>
        </div>
      </div>

      {entries.length ? (
        <div className="mt-7 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {entries.map(([industry, count]) => (
            <article key={industry} className="relative overflow-hidden border-l border-border-default bg-bg-surface p-4">
              <div aria-hidden="true" className="absolute inset-y-0 left-0 bg-accent/10" style={{ width: `${Math.max(8, (count / maximum) * 100)}%` }} />
              <div className="relative flex items-baseline justify-between gap-4">
                <h3 className="truncate font-display text-sm font-semibold">{titleCase(industry)}</h3>
                <span className="font-mono text-sm font-bold text-accent">{count}</span>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="mt-6 rounded-[10px] border border-border-subtle bg-bg-surface p-5 text-sm text-text-secondary">Industry coverage will appear after the first completed analysis.</p>
      )}
    </section>
  )
}
