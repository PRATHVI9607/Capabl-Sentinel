import type { PropsWithChildren } from 'react'

import { Navigation } from '@/components/layout/Navigation'
import { IS_DEMO_MODE } from '@/lib/api'

export function AppShell({ children }: PropsWithChildren) {
  return (
    <div className="min-h-[100dvh] bg-bg-base text-text-primary md:grid md:grid-cols-[216px_minmax(0,1fr)]">
      <Navigation />
      <main className="min-w-0 px-3 pb-6 pt-3 md:px-3 md:py-3">
        <div className="app-frame min-h-[calc(100dvh-1.5rem)] overflow-hidden rounded-[14px] border border-border-subtle bg-bg-surface">
          {IS_DEMO_MODE ? <div className="no-print flex min-h-8 items-center justify-center border-b border-border-subtle bg-accent/[0.06] px-4 text-center font-mono text-[10px] uppercase tracking-[0.14em] text-accent">Local preview data · connect the API to inspect production records</div> : null}
          <div className="mx-auto w-full max-w-[1680px] p-4 md:p-7 lg:p-9">{children}</div>
        </div>
      </main>
    </div>
  )
}
