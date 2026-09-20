'use client'

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { SEVERITY_CONFIG } from '@/lib/constants'
import type { AnalysisSummary, SeverityTier } from '@/lib/types'

interface SeverityChartProps {
  history: AnalysisSummary[]
}

interface ChartTooltipProps {
  active?: boolean
  payload?: Array<{ value: number; payload: { label: string } }>
}

function ChartTooltip({ active, payload }: ChartTooltipProps) {
  if (!active || !payload?.length) return null
  return (
    <div className="border border-border-default bg-bg-surface px-3 py-2 text-xs shadow-card">
      <span className="font-semibold text-text-primary">{payload[0].payload.label}</span>
      <span className="ml-2 font-mono text-text-secondary">{payload[0].value}</span>
    </div>
  )
}

export function SeverityChart({ history }: SeverityChartProps) {
  const tiers: SeverityTier[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']
  const data = tiers.map((tier) => ({
    tier,
    label: SEVERITY_CONFIG[tier].label,
    count: history.filter((item) => item.severity === tier).length,
    fill: SEVERITY_CONFIG[tier].gauge,
  }))

  return (
    <section aria-labelledby="severity-chart-heading" className="instrument-panel print-surface min-h-[440px] rounded-[8px] border border-border-default bg-bg-base p-5 md:p-7">
      <div className="flex items-start justify-between gap-5 border-b border-border-subtle pb-5"><div><p className="font-mono text-[9px] uppercase tracking-[.18em] text-accent">Risk landscape</p><h2 id="severity-chart-heading" className="mt-2 font-display text-2xl font-bold">Severity distribution</h2></div><p className="max-w-48 text-right text-xs leading-5 text-text-muted">Most recent 100 completed analyses</p></div>
      <div className="mt-6 h-[310px] w-full" aria-label="Bar chart of analyses by severity">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 4, left: -22, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--border-subtle)" />
            <XAxis dataKey="label" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis allowDecimals={false} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={<ChartTooltip />} cursor={{ fill: 'var(--accent-glow)' }} />
            <Bar dataKey="count" radius={0} maxBarSize={52}>
              {data.map((entry) => <Cell key={entry.tier} fill={entry.fill} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
