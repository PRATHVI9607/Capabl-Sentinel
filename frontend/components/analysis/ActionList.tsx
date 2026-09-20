import { ClipboardText } from '@phosphor-icons/react'

import { Badge } from '@/components/ui/badge'
import { URGENCY_CONFIG } from '@/lib/constants'
import type { CorrAction, Urgency } from '@/lib/types'
import { cn } from '@/lib/utils'

interface ActionListProps {
  actions: CorrAction[]
}

export function ActionList({ actions }: ActionListProps) {
  let previousUrgency: Urgency | null = null

  return (
    <section aria-labelledby="action-heading" className="print-surface rounded-[12px] border border-border-subtle bg-bg-card p-5 md:p-7">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-[10px] border border-accent/20 bg-accent/10 text-accent">
          <ClipboardText aria-hidden="true" size={19} weight="light" />
        </span>
        <div>
          <h2 id="action-heading" className="font-display text-2xl font-bold">Corrective actions</h2>
          <p className="mt-1 text-sm leading-6 text-text-secondary">Prioritized controls based on the identified hazards and retrieved clauses.</p>
        </div>
      </div>

      {actions.length ? (
        <div className="mt-7 space-y-4">
          {actions.map((item, index) => {
            const config = URGENCY_CONFIG[item.urgency]
            const showHeading = previousUrgency !== item.urgency
            previousUrgency = item.urgency
            return (
              <div key={`${item.urgency}-${index}`}>
                {showHeading ? <h3 className={cn('mb-3 font-display text-sm font-bold', config.tone.split(' ')[0])}>{config.label}</h3> : null}
                <article className={cn('rounded-[10px] border bg-bg-surface p-4 md:p-5', item.urgency === 'IMMEDIATE' ? 'border-severity-critical/30' : 'border-border-subtle')}>
                  <p className="font-display text-base font-semibold leading-6">{item.action}</p>
                  <p className="mt-2 text-sm leading-6 text-text-secondary">{item.rationale}</p>
                  {item.regulation_reference ? <Badge className={cn('mt-4 font-mono normal-case tracking-normal', config.tone)}>{item.regulation_reference}</Badge> : null}
                </article>
              </div>
            )
          })}
        </div>
      ) : (
        <p className="mt-6 rounded-[10px] border border-border-subtle bg-bg-surface p-5 text-sm text-text-secondary">No corrective actions were produced for this report.</p>
      )}
    </section>
  )
}
