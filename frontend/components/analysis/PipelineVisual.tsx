'use client'

import { Bell, ChartBar, Check, Compass, FileText, Pulse, Scales, Tag, X } from '@phosphor-icons/react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'

import { AGENT_STAGES, SYNTHESIZER_STAGES } from '@/lib/constants'
import type { StreamUpdate } from '@/lib/types'
import { cn } from '@/lib/utils'

interface PipelineVisualProps { updates: StreamUpdate[]; activeMessage?: string | null }
type NodeState = 'idle' | 'active' | 'complete' | 'error'
const iconMap = { Compass, FileText, Tag, Activity: Pulse, Scale: Scales, BarChart2: ChartBar, Bell }

function updateMatches(stageId: string, update: StreamUpdate) {
  if (stageId === 'alert_synthesizer') return SYNTHESIZER_STAGES.includes(update.stage as (typeof SYNTHESIZER_STAGES)[number])
  return update.stage === stageId
}

function getNodeState(stageId: string, updates: StreamUpdate[]): NodeState {
  const update = [...updates].reverse().find((item) => updateMatches(stageId, item))
  if (!update) return 'idle'
  if (update.status === 'error') return 'error'
  if (update.status === 'completed') return 'complete'
  return 'active'
}

export function PipelineVisual({ updates, activeMessage }: PipelineVisualProps) {
  const reduce = useReducedMotion()
  return (
    <section aria-labelledby="pipeline-heading" aria-live="polite" className="instrument-panel rounded-b-[8px] border-x border-b border-border-default bg-[#090c12] px-5 py-5 md:px-7 md:py-6">
      <h2 id="pipeline-heading" className="sr-only">Evidence pipeline</h2>
      <div className="grid gap-3 md:grid-cols-7 md:gap-0">
        {AGENT_STAGES.map((stage,index) => {
          const state=getNodeState(stage.id,updates); const Icon=iconMap[stage.icon]
          return (
            <div key={stage.id} className="relative flex items-center gap-3 md:flex-col md:items-center md:gap-3 md:text-center">
              {index>0 ? <span aria-hidden="true" className={cn('absolute left-5 top-[-14px] h-4 w-px bg-border-default md:left-[-50%] md:top-5 md:h-px md:w-full',state==='complete'&&'bg-stage-complete/50')} /> : null}
              <motion.span animate={!reduce&&state==='active'?{opacity:[.62,1,.62]}:undefined} transition={!reduce&&state==='active'?{duration:1.6,repeat:Infinity,ease:[.22,1,.36,1]}:undefined} className={cn('relative z-10 grid h-10 w-10 shrink-0 place-items-center rounded-full border border-border-strong bg-bg-base text-text-muted',state==='active'&&'border-stage-active text-stage-active',state==='complete'&&'border-stage-complete/60 text-stage-complete',state==='error'&&'border-stage-error/60 text-stage-error')}>
                {state==='complete'?<Check size={17} weight="light" />:state==='error'?<X size={17} weight="light" />:<Icon size={17} weight="light" />}
              </motion.span>
              <div><p className="font-mono text-[9px] text-text-muted">0{index+1}</p><p className={cn('mt-1 text-[11px] font-semibold text-text-muted',state!=='idle'&&'text-text-primary')}>{stage.label}</p></div>
            </div>
          )
        })}
      </div>
      <AnimatePresence mode="wait" initial={false}>
        <motion.p key={activeMessage??'waiting'} initial={reduce?false:{opacity:0,y:4}} animate={{opacity:1,y:0}} exit={reduce?undefined:{opacity:0,y:-4}} transition={{duration:.22,ease:[.22,1,.36,1]}} className="mt-5 border-t border-border-subtle pt-4 font-mono text-[10px] uppercase tracking-[0.08em] text-text-secondary">
          {activeMessage ?? 'Preparing the analysis pipeline.'}
        </motion.p>
      </AnimatePresence>
    </section>
  )
}
