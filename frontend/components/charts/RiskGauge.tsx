'use client'

import { motion, useMotionValue, useReducedMotion, useSpring, useTransform } from 'framer-motion'
import { useEffect } from 'react'

import { SEVERITY_CONFIG } from '@/lib/constants'
import type { SeverityTier } from '@/lib/types'

interface RiskGaugeProps {
  score: number
  tier: SeverityTier
}

const segments = [
  { start: 0, length: 30, stroke: 'var(--severity-low)' },
  { start: 30, length: 30, stroke: 'var(--severity-medium)' },
  { start: 60, length: 20, stroke: 'var(--severity-high)' },
  { start: 80, length: 20, stroke: 'var(--severity-critical)' },
]

export function RiskGauge({ score, tier }: RiskGaugeProps) {
  const reduce = useReducedMotion()
  const target = useMotionValue(0)
  const spring = useSpring(target, { stiffness: 60, damping: 15 })
  const rotation = useTransform(reduce ? target : spring, [0, 10], [-90, 90])
  const config = SEVERITY_CONFIG[tier]

  useEffect(() => {
    target.set(score)
  }, [score, target])

  return (
    <div className="relative mx-auto w-full max-w-[300px]" role="img" aria-label={`Risk score ${score.toFixed(1)} out of 10, ${config.label}`}>
      <svg viewBox="0 0 240 140" className="h-auto w-full overflow-visible">
        <path
          d="M20 120 A100 100 0 0 1 220 120"
          fill="none"
          stroke="var(--border-default)"
          strokeLinecap="round"
          strokeWidth="15"
          pathLength="100"
        />
        {segments.map((segment) => (
          <path
            key={segment.start}
            d="M20 120 A100 100 0 0 1 220 120"
            fill="none"
            stroke={segment.stroke}
            strokeDasharray={`${segment.length} ${100 - segment.length}`}
            strokeDashoffset={-segment.start}
            strokeLinecap="butt"
            strokeWidth="12"
            pathLength="100"
            opacity="0.82"
          />
        ))}
        <motion.g style={{ rotate: rotation, originX: '120px', originY: '120px' }}>
          <line x1="120" y1="120" x2="120" y2="42" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" />
        </motion.g>
        <circle cx="120" cy="120" r="6" fill={config.gauge} />
      </svg>
      <div className="absolute inset-x-0 bottom-0 text-center">
        <div className="font-display text-5xl font-extrabold tracking-[-0.05em]">{score.toFixed(1)}</div>
        <div className="mt-1 text-xs font-bold uppercase tracking-[0.12em]" style={{ color: config.gauge }}>
          {config.label}
        </div>
      </div>
    </div>
  )
}
