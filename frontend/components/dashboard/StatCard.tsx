import type { Icon } from '@phosphor-icons/react'

import { NumberTicker } from '@/components/magicui/number-ticker'

interface StatCardProps {
  label: string
  value: number
  icon: Icon
  decimalPlaces?: number
}

export function StatCard({ label, value, icon: Icon, decimalPlaces = 0 }: StatCardProps) {
  return (
    <article className="print-surface relative overflow-hidden border-b border-border-subtle bg-bg-base p-5 last:border-b-0 sm:odd:border-r xl:border-b-0 xl:odd:border-r-0 md:p-6">
      <div aria-hidden="true" className="absolute bottom-0 left-0 h-px w-1/2 bg-accent/60" />
      <div className="relative flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.12em] text-text-muted">{label}</p>
          <NumberTicker value={value} decimalPlaces={decimalPlaces} className="mt-5 block font-display text-5xl font-bold tracking-[-0.055em]" />
        </div>
        <span className="grid h-10 w-10 place-items-center border border-accent/25 text-accent">
          <Icon aria-hidden="true" size={19} weight="light" />
        </span>
      </div>
    </article>
  )
}
