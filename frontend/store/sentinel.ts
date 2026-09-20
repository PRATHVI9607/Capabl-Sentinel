import { create } from 'zustand'

import type { Alert, AnalysisReport, AnalysisSummary } from '@/lib/types'

interface SentinelState {
  currentAnalysis: AnalysisReport | null
  analysisHistory: AnalysisSummary[]
  globalAlerts: Alert[]
  setCurrentAnalysis: (report: AnalysisReport | null) => void
  setAnalysisHistory: (history: AnalysisSummary[]) => void
  setGlobalAlerts: (alerts: Alert[]) => void
}

export const useSentinelStore = create<SentinelState>((set) => ({
  currentAnalysis: null,
  analysisHistory: [],
  globalAlerts: [],
  setCurrentAnalysis: (currentAnalysis) => set({ currentAnalysis }),
  setAnalysisHistory: (analysisHistory) => set({ analysisHistory }),
  setGlobalAlerts: (globalAlerts) => set({ globalAlerts }),
}))
