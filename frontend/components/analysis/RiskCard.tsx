'use client'

import { motion, useReducedMotion } from 'framer-motion'

import { BackgroundGradient } from '@/components/aceternity/background-gradient'
import { Spotlight } from '@/components/aceternity/spotlight'
import { RiskGauge } from '@/components/charts/RiskGauge'
import { AnimatedShinyText } from '@/components/magicui/animated-shiny-text'
import { SeverityBadge } from '@/components/ui/SeverityBadge'
import type { RiskScore } from '@/lib/types'

interface RiskCardProps {
  risk: RiskScore
}

export function RiskCard({ risk }: RiskCardProps) {
  const reduce = useReducedMotion()
  const critical = risk.tier === 'CRITICAL'

  return (
    <motion.section
      aria-labelledby="risk-heading"
      animate={
        critical && !reduce
          ? {
              boxShadow: [
                '0 0 0 0 rgba(255,59,48,0)',
                '0 0 0 10px rgba(255,59,48,.18)',
                '0 0 0 0 rgba(255,59,48,0)',
              ],
            }
          : undefined
      }
      transition={critical && !reduce ? { duration: 2.2, repeat: Infinity, ease: 'easeInOut' } : undefined}
      className="rounded-[13px]"
    >
      <BackgroundGradient critical={critical}>
        <div className="print-surface relative overflow-hidden rounded-[12px] bg-bg-card p-5 md:p-7">
          {critical ? <Spotlight /> : null}
          <div className="relative grid gap-8 xl:grid-cols-[320px_minmax(0,1fr)] xl:items-center">
            <div>
              <div className="mb-5 flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.12em] text-text-muted">Risk assessment</p>
                  <h2 id="risk-heading" className="mt-1 font-display text-2xl font-bold">Explainable score</h2>
                </div>
                <SeverityBadge severity={risk.tier}>
                  {critical ? <AnimatedShinyText>Critical</AnimatedShinyText> : undefined}
                </SeverityBadge>
              </div>
              <RiskGauge score={risk.total} tier={risk.tier} />
              <p className="mt-6 text-sm leading-6 text-text-secondary">{risk.explanation}</p>
            </div>

            <div className="min-w-0 overflow-x-auto">
              <table className="w-full min-w-[720px] border-separate border-spacing-0 text-left">
                <thead>
                  <tr className="text-[11px] uppercase tracking-[0.1em] text-text-muted">
                    <th className="pb-3 font-semibold">Component</th>
                    <th className="w-20 px-3 pb-3 text-right font-semibold">Score</th>
                    <th className="w-24 px-3 pb-3 text-center font-semibold">Weight</th>
                    <th className="w-32 px-3 pb-3 text-right font-semibold">Contribution</th>
                    <th className="pb-3 pl-6 font-semibold">Basis</th>
                  </tr>
                </thead>
                <tbody>
                  {risk.components.map((component) => (
                    <tr key={component.name} className="border-t border-border-subtle align-top">
                      <th className="border-t border-border-subtle py-4 pr-4 font-display text-sm font-semibold">{component.name}</th>
                      <td className="border-t border-border-subtle px-3 py-4 text-right font-mono text-sm">{component.score.toFixed(1)}</td>
                      <td className="border-t border-border-subtle px-3 py-4 text-center font-mono text-sm text-text-secondary">× {component.weight.toFixed(2)}</td>
                      <td className="border-t border-border-subtle px-3 py-4 text-right font-mono text-sm font-semibold text-accent">= {(component.score * component.weight).toFixed(2)}</td>
                      <td className="border-t border-border-subtle py-4 pl-6 text-sm leading-5 text-text-secondary">{component.explanation}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <th colSpan={3} className="border-t border-border-strong pt-4 text-right font-display text-sm font-bold">Reported total</th>
                    <td className="border-t border-border-strong pt-4 text-right font-mono text-base font-bold text-text-primary">{risk.total.toFixed(2)}</td>
                    <td className="border-t border-border-strong pt-4" />
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      </BackgroundGradient>
    </motion.section>
  )
}
