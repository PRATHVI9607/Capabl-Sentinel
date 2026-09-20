import { Warning } from '@phosphor-icons/react'

interface WarningsBannerProps {
  warnings: string[]
}

export function WarningsBanner({ warnings }: WarningsBannerProps) {
  if (!warnings.length) return null
  return (
    <aside role="alert" className="rounded-[12px] border border-severity-medium/35 bg-severity-medium/10 p-4 text-severity-medium md:p-5">
      <div className="flex gap-3">
        <Warning aria-hidden="true" className="mt-0.5 shrink-0" size={20} weight="light" />
        <div>
          <h2 className="font-display text-base font-bold">Review with caution</h2>
          <ul className="mt-2 space-y-1 text-sm leading-6">
            {warnings.map((warning) => <li key={warning}>{warning}</li>)}
          </ul>
        </div>
      </div>
    </aside>
  )
}
