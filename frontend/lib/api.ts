import type {
  AnalysisReport,
  DashboardStats,
  HistoryPage,
  SeverityTier,
  StartAnalysisResponse,
} from '@/lib/types'
import { DEMO_HISTORY, DEMO_REPORTS, DEMO_STATS } from '@/lib/demo-data'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
export const IS_DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === 'true'

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function readError(response: Response) {
  try {
    const payload = (await response.json()) as unknown
    if (
      typeof payload === 'object' &&
      payload !== null &&
      'detail' in payload &&
      typeof payload.detail === 'string'
    ) {
      return payload.detail
    }
  } catch {
    return response.statusText || 'The request could not be completed.'
  }
  return response.statusText || 'The request could not be completed.'
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init)
  if (!response.ok) throw new ApiError(await readError(response), response.status)
  return response.json() as Promise<T>
}

export async function startAnalysis(file: File): Promise<StartAnalysisResponse> {
  if (IS_DEMO_MODE) {
    await new Promise((resolve) => window.setTimeout(resolve, 420))
    return { analysis_id: DEMO_REPORTS[0].analysis_id, status: 'cached' }
  }
  const body = new FormData()
  body.append('file', file)
  return request<StartAnalysisResponse>('/analyze', { method: 'POST', body })
}

export function getAnalysis(id: string): Promise<AnalysisReport> {
  if (IS_DEMO_MODE) {
    const report = DEMO_REPORTS.find((item) => item.analysis_id === id) ?? DEMO_REPORTS[0]
    return Promise.resolve(report)
  }
  return request<AnalysisReport>(`/analyze/${encodeURIComponent(id)}`)
}

interface HistoryParams {
  page?: number
  limit?: number
  severity?: SeverityTier
  industry?: string
}

export function getHistory(params: HistoryParams = {}): Promise<HistoryPage> {
  if (IS_DEMO_MODE) {
    const filtered = DEMO_HISTORY.filter((item) => {
      const matchesSeverity = !params.severity || item.severity === params.severity
      const matchesIndustry = !params.industry || item.industry === params.industry
      return matchesSeverity && matchesIndustry
    })
    const page = params.page ?? 1
    const limit = params.limit ?? 20
    const start = (page - 1) * limit
    return Promise.resolve({ items: filtered.slice(start, start + limit), total: filtered.length, page, limit })
  }
  const query = new URLSearchParams()
  if (params.page) query.set('page', String(params.page))
  if (params.limit) query.set('limit', String(params.limit))
  if (params.severity) query.set('severity', params.severity)
  if (params.industry) query.set('industry', params.industry)
  const suffix = query.size ? `?${query.toString()}` : ''
  return request<HistoryPage>(`/history${suffix}`)
}

export async function getAllHistory(): Promise<HistoryPage['items']> {
  const first = await getHistory({ page: 1, limit: 100 })
  const pageCount = Math.ceil(first.total / first.limit)
  if (pageCount <= 1) return first.items

  const remaining = await Promise.all(
    Array.from({ length: pageCount - 1 }, (_, index) =>
      getHistory({ page: index + 2, limit: 100 }),
    ),
  )
  return [first, ...remaining].flatMap((page) => page.items)
}

export function getStats(): Promise<DashboardStats> {
  if (IS_DEMO_MODE) return Promise.resolve(DEMO_STATS)
  return request<DashboardStats>('/history/stats')
}

export function getHealth(): Promise<{
  status: string
  llm_configured: boolean
  vector_store_ready: boolean
}> {
  if (IS_DEMO_MODE) return Promise.resolve({ status: 'preview', llm_configured: true, vector_store_ready: true })
  return request('/health')
}

export function streamUrl(id: string) {
  return `${API_URL}/analyze/${encodeURIComponent(id)}/stream`
}

export async function getSampleReport(): Promise<File> {
  const response = await fetch('/sample-report.pdf')
  if (!response.ok) throw new ApiError('The sample report is unavailable.', response.status)
  const blob = await response.blob()
  return new File([blob], 'sample-incident-report.pdf', { type: 'application/pdf' })
}
