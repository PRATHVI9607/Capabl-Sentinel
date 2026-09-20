import { GitBranch } from '@phosphor-icons/react'

import type { CausalEvent } from '@/lib/types'
import { titleCase } from '@/lib/utils'

interface CausalChainViewProps {
  events: CausalEvent[]
}

export function CausalChainView({ events }: CausalChainViewProps) {
  const ordered = [...events].sort((left, right) => left.order - right.order)
  return (
    <section aria-labelledby="causal-heading" className="print-surface rounded-[12px] border border-border-subtle bg-bg-card p-5 md:p-7">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-[10px] border border-accent/20 bg-accent/10 text-accent">
          <GitBranch aria-hidden="true" size={19} weight="light" />
        </span>
        <div>
          <h2 id="causal-heading" className="font-display text-2xl font-bold">Causal chain</h2>
          <p className="mt-1 text-sm leading-6 text-text-secondary">The incident sequence reconstructed from the submitted report.</p>
        </div>
      </div>

      {ordered.length ? (
        <ol className="mt-7 grid gap-0 md:grid-cols-[repeat(auto-fit,minmax(180px,1fr))]">
          {ordered.map((event, index) => (
            <li key={`${event.order}-${event.label}`} className="relative flex gap-4 pb-7 last:pb-0 md:block md:pb-0 md:pr-6">
              <span className="relative z-10 mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-full border border-accent/35 bg-accent/10 font-mono text-xs font-bold text-accent">{event.order}</span>
              {index < ordered.length - 1 ? <span aria-hidden="true" className="absolute bottom-0 left-[15px] top-9 w-px bg-border-default md:bottom-auto md:left-9 md:right-0 md:top-4 md:h-px md:w-auto" /> : null}
              <div className="min-w-0 md:mt-4">
                <span className="rounded-md border border-border-default bg-bg-surface px-2 py-1 text-[10px] font-bold uppercase tracking-[0.08em] text-text-muted">{titleCase(event.node_type)}</span>
                <h3 className="mt-3 font-display text-base font-semibold leading-6">{event.label}</h3>
                {index < ordered.length - 1 ? <p className="mt-2 font-mono text-[11px] text-text-muted">{titleCase(event.relation)}</p> : null}
              </div>
            </li>
          ))}
        </ol>
      ) : (
        <p className="mt-6 rounded-[10px] border border-border-subtle bg-bg-surface p-5 text-sm text-text-secondary">No causal chain could be extracted from this report.</p>
      )}
    </section>
  )
}
