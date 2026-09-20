import { Database, MagnifyingGlass } from '@phosphor-icons/react'

import type { PrecursorPattern } from '@/lib/types'

interface PrecursorListProps {
  patterns: PrecursorPattern[]
}

export function PrecursorList({ patterns }: PrecursorListProps) {
  return (
    <section aria-labelledby="precursor-heading" className="print-surface rounded-[12px] border border-border-subtle bg-bg-card p-5 md:p-6">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-[10px] border border-accent/20 bg-accent/10 text-accent">
          <MagnifyingGlass aria-hidden="true" size={19} weight="light" />
        </span>
        <div>
          <h2 id="precursor-heading" className="font-display text-2xl font-bold">Precursor patterns</h2>
          <p className="mt-1 text-sm leading-6 text-text-secondary">Warning signs matched against prior incidents.</p>
        </div>
      </div>

      {patterns.length ? (
        <div className="mt-6 space-y-4">
          {patterns.map((pattern) => (
            <article key={pattern.pattern_name} className="rounded-[10px] border border-border-subtle bg-bg-surface p-4">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <h3 className="font-display text-base font-semibold">{pattern.pattern_name}</h3>
                <span className="shrink-0 font-mono text-xs text-text-secondary">{Math.round(pattern.confidence * 100)}% confidence</span>
              </div>
              <p className="mt-2 text-sm leading-6 text-text-secondary">{pattern.description}</p>
              <div className="mt-4 h-1.5 overflow-hidden rounded-sm bg-border-default" aria-hidden="true">
                <div className="h-full bg-accent" style={{ width: `${Math.min(100, Math.max(0, pattern.confidence * 100))}%` }} />
              </div>
              <p className={pattern.evidence_count ? 'mt-3 text-sm font-semibold text-text-primary' : 'mt-3 text-sm text-text-muted'}>
                {pattern.evidence_count
                  ? `Seen in ${pattern.evidence_count} historical incident${pattern.evidence_count === 1 ? '' : 's'}.`
                  : 'Not corroborated in the corpus.'}
              </p>
            </article>
          ))}
        </div>
      ) : (
        <div className="mt-6 rounded-[10px] border border-border-subtle bg-bg-surface p-5 text-center">
          <Database aria-hidden="true" className="mx-auto text-text-muted" size={23} />
          <p className="mt-3 text-sm font-semibold">No precursor patterns were identified.</p>
          <p className="mt-1 text-sm text-text-secondary">The report may be too thin, or the configured corpus may not contain a match.</p>
        </div>
      )}
    </section>
  )
}
