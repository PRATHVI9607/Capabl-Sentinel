import { BorderBeam } from '@/components/magicui/border-beam'
import { Skeleton } from '@/components/ui/skeleton'
import { PipelineVisual } from '@/components/analysis/PipelineVisual'
import type { StreamUpdate } from '@/lib/types'

interface ProcessingStateProps {
  fileName: string
  updates: StreamUpdate[]
  message?: string | null
}

export function ProcessingState({ fileName, updates, message }: ProcessingStateProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.12em] text-text-muted">Processing report</p>
          <h1 className="mt-2 font-display text-3xl font-bold tracking-[-0.03em] md:text-4xl">Finding the warning signs</h1>
        </div>
        <span className="max-w-full truncate rounded-md border border-border-default bg-bg-card px-3 py-2 font-mono text-xs text-text-secondary">{fileName}</span>
      </div>

      <PipelineVisual updates={updates} activeMessage={message} />

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="relative overflow-hidden rounded-[12px] p-px">
          <BorderBeam />
          <div className="relative rounded-[11px] border border-border-subtle bg-bg-card p-6">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="mt-5 h-36 w-full" />
            <Skeleton className="mt-5 h-3 w-full" />
            <Skeleton className="mt-3 h-3 w-4/5" />
          </div>
        </div>
        {Array.from({ length: 3 }, (_, index) => (
          <div key={index} className="rounded-[12px] border border-border-subtle bg-bg-card p-6">
            <Skeleton className="h-5 w-36" />
            <Skeleton className="mt-6 h-4 w-full" />
            <Skeleton className="mt-3 h-4 w-5/6" />
            <Skeleton className="mt-8 h-16 w-full" />
          </div>
        ))}
      </div>
    </div>
  )
}
