import { CircleNotch, FileMagnifyingGlass, Warning } from '@phosphor-icons/react'
import Link from 'next/link'

import { Button } from '@/components/ui/button'

interface SectionStateProps {
  kind: 'loading' | 'empty' | 'error'
  title: string
  description: string
  actionHref?: string
  actionLabel?: string
  onRetry?: () => void
}

export function SectionState({
  kind,
  title,
  description,
  actionHref,
  actionLabel,
  onRetry,
}: SectionStateProps) {
  const Icon = kind === 'loading' ? CircleNotch : kind === 'error' ? Warning : FileMagnifyingGlass
  return (
    <div className="print-surface flex min-h-64 flex-col items-center justify-center rounded-[12px] border border-border-subtle bg-bg-surface p-8 text-center">
      <Icon
        aria-hidden="true"
        className={kind === 'error' ? 'text-severity-critical' : 'text-text-muted'}
        size={28}
        weight="light"
      />
      <h2 className="mt-4 font-display text-xl font-bold">{title}</h2>
      <p className="mt-2 max-w-md text-sm leading-6 text-text-secondary">{description}</p>
      {actionHref && actionLabel ? (
        <Button asChild className="mt-5">
          <Link href={actionHref}>{actionLabel}</Link>
        </Button>
      ) : null}
      {onRetry ? (
        <Button type="button" variant="secondary" className="mt-5" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  )
}
