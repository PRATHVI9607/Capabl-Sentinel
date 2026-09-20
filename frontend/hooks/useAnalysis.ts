'use client'

import { useMutation } from '@tanstack/react-query'
import { useCallback, useEffect, useState } from 'react'

import { ApiError, getAnalysis, startAnalysis, streamUrl } from '@/lib/api'
import type { AnalysisReport } from '@/lib/types'
import { useSentinelStore } from '@/store/sentinel'
import { useSSE } from '@/hooks/useSSE'

export type AnalysisPhase = 'idle' | 'uploading' | 'streaming' | 'complete' | 'error'

function isAnalysisReport(value: unknown): value is AnalysisReport {
  if (typeof value !== 'object' || value === null) return false
  const record = value as Record<string, unknown>
  return (
    typeof record.analysis_id === 'string' &&
    typeof record.file_name === 'string' &&
    typeof record.risk_score === 'object' &&
    record.risk_score !== null &&
    Array.isArray(record.precursor_patterns) &&
    Array.isArray(record.regulatory_clauses)
  )
}

export function useAnalysis() {
  const [phase, setPhase] = useState<AnalysisPhase>('idle')
  const [analysisId, setAnalysisId] = useState<string | null>(null)
  const [activeStreamUrl, setActiveStreamUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loadedFromCache, setLoadedFromCache] = useState(false)
  const [lastFile, setLastFile] = useState<File | null>(null)
  const report = useSentinelStore((state) => state.currentAnalysis)
  const setReport = useSentinelStore((state) => state.setCurrentAnalysis)

  const mutation = useMutation({ mutationFn: startAnalysis })
  const stream = useSSE(activeStreamUrl)

  const analyze = useCallback(
    async (file: File) => {
      setLastFile(file)
      setError(null)
      setReport(null)
      setLoadedFromCache(false)
      setActiveStreamUrl(null)
      setPhase('uploading')

      try {
        const response = await mutation.mutateAsync(file)
        setAnalysisId(response.analysis_id)
        if (response.status === 'cached') {
          const cached = await getAnalysis(response.analysis_id)
          setReport(cached)
          setLoadedFromCache(true)
          setPhase('complete')
          return
        }

        setActiveStreamUrl(streamUrl(response.analysis_id))
        setPhase('streaming')
      } catch (cause) {
        setError(cause instanceof ApiError ? cause.message : 'The analysis could not be started.')
        setPhase('error')
      }
    },
    [mutation, setReport],
  )

  useEffect(() => {
    const update = stream.lastUpdate
    if (!update) return
    if (update.stage === 'complete') {
      if (!isAnalysisReport(update.data)) {
        setError('The completed report did not match the documented response shape.')
        setPhase('error')
        return
      }
      setReport(update.data)
      setActiveStreamUrl(null)
      setPhase('complete')
      return
    }
    if (update.stage === 'error') {
      setError(update.message)
      setActiveStreamUrl(null)
      setPhase('error')
    }
  }, [setReport, stream.lastUpdate])

  useEffect(() => {
    if (!stream.error || phase !== 'streaming') return
    setError(stream.error)
    setPhase('error')
  }, [phase, stream.error])

  const retry = useCallback(() => {
    if (lastFile) void analyze(lastFile)
  }, [analyze, lastFile])

  const reset = useCallback(() => {
    setPhase('idle')
    setAnalysisId(null)
    setActiveStreamUrl(null)
    setError(null)
    setLoadedFromCache(false)
    setReport(null)
  }, [setReport])

  return {
    phase,
    analysisId,
    report,
    error,
    loadedFromCache,
    updates: stream.updates,
    lastUpdate: stream.lastUpdate,
    isConnected: stream.isConnected,
    fileName: lastFile?.name ?? null,
    analyze,
    retry,
    reset,
  }
}
