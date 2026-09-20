'use client'

import { AnalysisResults } from '@/components/analysis/AnalysisResults'
import { PipelineVisual } from '@/components/analysis/PipelineVisual'
import { ProcessingState } from '@/components/analysis/ProcessingState'
import { UploadZone } from '@/components/analysis/UploadZone'
import { SectionState } from '@/components/ui/SectionState'
import { useAnalysis } from '@/hooks/useAnalysis'
import { ThreatField } from '@/components/visuals/ThreatField'

export default function AnalyzePage() {
  const analysis = useAnalysis()
  const activeFileName = analysis.report?.file_name ?? analysis.fileName ?? 'Incident report'

  if (analysis.phase === 'streaming' || analysis.phase === 'uploading') {
    return (
      <ProcessingState
        fileName={activeFileName}
        updates={analysis.updates}
        message={analysis.lastUpdate?.message}
      />
    )
  }

  if (analysis.phase === 'complete' && analysis.report) {
    return (
      <AnalysisResults
        report={analysis.report}
        loadedFromCache={analysis.loadedFromCache}
        onReset={analysis.reset}
      />
    )
  }

  if (analysis.phase === 'error') {
    return (
      <div className="space-y-6">
        {analysis.updates.length ? (
          <PipelineVisual updates={analysis.updates} activeMessage={analysis.lastUpdate?.message} />
        ) : null}
        <SectionState
          kind="error"
          title="Analysis interrupted"
          description={analysis.error ?? 'The analysis could not be completed.'}
          onRetry={analysis.retry}
        />
      </div>
    )
  }

  return (
    <section className="min-h-[calc(100dvh-7rem)]" aria-labelledby="upload-heading">
      <div className="instrument-deck grid min-h-[640px] overflow-hidden rounded-t-[8px] border border-border-default bg-bg-base lg:grid-cols-[minmax(420px,0.92fr)_minmax(500px,1.08fr)]">
        <div className="relative z-10 flex flex-col justify-center border-b border-border-default p-6 sm:p-10 lg:border-b-0 lg:border-r lg:p-12 xl:p-16">
          <div className="max-w-[580px]">
            <p className="font-mono text-[10px] uppercase tracking-[0.28em] text-accent">Incident intelligence</p>
            <h1 id="upload-heading" className="mt-6 font-display text-[clamp(2.65rem,4vw,3.7rem)] font-bold leading-[0.98] tracking-[-0.055em]"><span className="block">Find the</span><span className="block">warnings that</span><span className="block">came before.</span></h1>
            <p className="mt-7 max-w-lg text-base leading-7 text-text-secondary md:text-lg">Upload an incident report. SENTINEL compares its hazards, causes and regulatory signals against historical cases.</p>
            <div className="mt-9"><UploadZone onAnalyze={(file) => void analysis.analyze(file)} initialError={analysis.error} /></div>
          </div>
        </div>
        <div className="panel-grid relative min-h-[460px] bg-[#080b11] lg:min-h-full"><ThreatField /></div>
      </div>
      <PipelineVisual updates={[]} activeMessage="Upload a report to begin the seven-stage evidence analysis." />
    </section>
  )
}
