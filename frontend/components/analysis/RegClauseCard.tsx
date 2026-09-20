'use client'

import * as Collapsible from '@radix-ui/react-collapsible'
import { Books, CaretDown } from '@phosphor-icons/react'
import { useState } from 'react'

import { Badge } from '@/components/ui/badge'
import type { RegulatoryClause } from '@/lib/types'
import { cn } from '@/lib/utils'

interface RegClauseCardProps {
  clauses: RegulatoryClause[]
}

function confidenceTone(value: number) {
  if (value >= 0.8) return 'border-severity-low/30 bg-severity-low/10 text-severity-low'
  if (value >= 0.55) return 'border-severity-medium/30 bg-severity-medium/10 text-severity-medium'
  return 'border-border-default bg-bg-card text-text-secondary'
}

interface ClauseItemProps {
  clause: RegulatoryClause
}

function ClauseItem({ clause }: ClauseItemProps) {
  const [open, setOpen] = useState(false)
  return (
    <Collapsible.Root open={open} onOpenChange={setOpen} className="mechanical-card rounded-[8px] border border-border-subtle bg-bg-surface">
      <Collapsible.Trigger className="flex w-full items-center gap-3 rounded-[10px] p-4 text-left transition-colors hover:bg-bg-card-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent">
        <div className="min-w-0 flex-1">
          <div className="truncate font-mono text-sm text-accent">{clause.regulation_name}</div>
          <div className="mt-1 font-mono text-xs text-text-muted">Section {clause.section}</div>
        </div>
        <Badge className={cn('shrink-0', confidenceTone(clause.violation_confidence))}>{Math.round(clause.violation_confidence * 100)}%</Badge>
        <CaretDown aria-hidden="true" className={cn('shrink-0 text-text-muted transition-transform', open && 'rotate-180')} size={17} weight="light" />
      </Collapsible.Trigger>
      <Collapsible.Content forceMount className="data-[state=closed]:hidden" data-radix-collapsible-content>
        <div className="border-t border-border-subtle p-4">
          <blockquote className="rounded-[8px] bg-bg-card p-3 font-mono text-xs leading-6 text-text-secondary">{clause.clause_text}</blockquote>
          <dl className="mt-4 grid gap-3 text-sm">
            <div>
              <dt className="font-semibold text-text-primary">Source</dt>
              <dd className="mt-1 font-mono text-xs text-text-secondary">{clause.regulation_name}, section {clause.section}</dd>
            </div>
            <div>
              <dt className="font-semibold text-text-primary">Relevance</dt>
              <dd className="mt-1 leading-6 text-text-secondary">{clause.relevance_explanation}</dd>
            </div>
          </dl>
        </div>
      </Collapsible.Content>
    </Collapsible.Root>
  )
}

export function RegClauseCard({ clauses }: RegClauseCardProps) {
  return (
    <section aria-labelledby="regulation-heading" className="print-surface rounded-[12px] border border-border-subtle bg-bg-card p-5 md:p-6">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-[10px] border border-accent/20 bg-accent/10 text-accent">
          <Books aria-hidden="true" size={19} weight="light" />
        </span>
        <div>
          <h2 id="regulation-heading" className="font-display text-2xl font-bold">Regulatory clauses</h2>
          <p className="mt-1 text-sm leading-6 text-text-secondary">Every clause below was retrieved from the regulatory corpus. None was generated.</p>
        </div>
      </div>

      {clauses.length ? (
        <div className="mt-6 space-y-3">
          {clauses.map((clause) => <ClauseItem key={clause.clause_id} clause={clause} />)}
        </div>
      ) : (
        <div className="mt-6 rounded-[10px] border border-border-subtle bg-bg-surface p-5 text-center">
          <p className="text-sm font-semibold">No clauses were retrieved.</p>
          <p className="mt-1 text-sm leading-6 text-text-secondary">Check the corpus status or review the warnings attached to this report.</p>
        </div>
      )}
    </section>
  )
}
