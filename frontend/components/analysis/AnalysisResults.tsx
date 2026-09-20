'use client'

import { ArrowCounterClockwise, DownloadSimple, FileMagnifyingGlass } from '@phosphor-icons/react'
import { motion, useReducedMotion } from 'framer-motion'
import Link from 'next/link'

import { ActionList } from '@/components/analysis/ActionList'
import { CausalChainView } from '@/components/analysis/CausalChainView'
import { PrecursorList } from '@/components/analysis/PrecursorList'
import { RegClauseCard } from '@/components/analysis/RegClauseCard'
import { RiskCard } from '@/components/analysis/RiskCard'
import { WarningsBanner } from '@/components/analysis/WarningsBanner'
import { TextGenerateEffect } from '@/components/aceternity/text-generate-effect'
import { ShimmerButton } from '@/components/magicui/shimmer-button'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { AnalysisReport } from '@/lib/types'

interface AnalysisResultsProps {
  report: AnalysisReport
  loadedFromCache?: boolean
  onReset?: () => void
  showHeading?: boolean
}

export function AnalysisResults({
  report,
  loadedFromCache = false,
  onReset,
  showHeading = true,
}: AnalysisResultsProps) {
  const reduce = useReducedMotion()
  const child = {
    hidden: { opacity: 0, y: 12 },
    visible: { opacity: 1, y: 0 },
  }

  return (
    <div className="space-y-6">
      {showHeading ? (
        <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <TextGenerateEffect text="Analysis complete" className="font-display text-3xl font-bold tracking-[-0.03em] md:text-4xl" />
              {loadedFromCache ? <Badge className="border-accent/25 bg-accent/10 text-accent">Loaded from cache</Badge> : null}
            </div>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-text-secondary">{report.file_name} was evaluated against the configured incident and regulatory corpora.</p>
          </div>
          {onReset ? (
            <Button type="button" variant="secondary" onClick={onReset} className="no-print self-start md:self-auto">
              <ArrowCounterClockwise aria-hidden="true" size={16} weight="light" />
              Analyze another
            </Button>
          ) : null}
        </div>
      ) : null}

      <WarningsBanner warnings={report.warnings} />

      <motion.div
        initial={reduce ? false : 'hidden'}
        animate="visible"
        variants={{ visible: { transition: { staggerChildren: reduce ? 0 : 0.08 } } }}
        className="space-y-6"
      >
        <motion.div variants={child} transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}>
          <RiskCard risk={report.risk_score} />
        </motion.div>
        <div className="grid gap-6 xl:grid-cols-2">
          <motion.div variants={child} transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}>
            <PrecursorList patterns={report.precursor_patterns} />
          </motion.div>
          <motion.div variants={child} transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}>
            <RegClauseCard clauses={report.regulatory_clauses} />
          </motion.div>
        </div>
        <motion.div variants={child} transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}>
          <CausalChainView events={report.causal_chain} />
        </motion.div>
        <motion.div variants={child} transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}>
          <ActionList actions={report.corrective_actions} />
        </motion.div>
      </motion.div>

      <div className="no-print flex flex-col gap-3 rounded-[12px] border border-border-subtle bg-bg-surface p-4 sm:flex-row sm:items-center sm:justify-end">
        <ShimmerButton className="h-11" onClick={() => window.print()}>
          <span className="flex items-center gap-2"><DownloadSimple aria-hidden="true" size={16} weight="light" />Download summary</span>
        </ShimmerButton>
        <Button asChild variant="secondary">
          <Link href={`/incidents/${report.analysis_id}`}>
            <FileMagnifyingGlass aria-hidden="true" size={16} weight="light" />
            View in incidents
          </Link>
        </Button>
      </div>
    </div>
  )
}
