export type SeverityTier = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN'
export type EntityType = 'HAZARD' | 'EQUIPMENT' | 'CHEMICAL' | 'CONDITION' | 'UNSAFE_ACT'
export type Urgency = 'IMMEDIATE' | 'SHORT_TERM' | 'LONG_TERM'
export type StreamStatus = 'started' | 'completed' | 'error' | 'alive'

export interface IncidentReport {
  incident_date: string | null
  location: string | null
  industry: string | null
  equipment_involved: string[]
  sequence_of_events: string
  immediate_causes: string[]
  root_causes: string[]
  injury_count: number
  fatality_count: number
  severity_indicator: SeverityTier
  raw_text_length: number
  extraction_confidence: number
}

export interface HazardEntity {
  text: string
  entity_type: EntityType
  confidence: number
  source: string
}

export interface SimilarIncident {
  doc_id: string
  title: string
  industry: string
  severity: string
  similarity_score: number
  chunk_excerpt: string
  source_document: string
  incident_date: string | null
  hazard_tags: string[]
}

export interface RegulatoryClause {
  clause_id: string
  regulation_name: string
  section: string
  clause_text: string
  violation_confidence: number
  relevance_explanation: string
}

export interface PrecursorPattern {
  pattern_name: string
  description: string
  confidence: number
  evidence_count: number
  hazard_types: string[]
}

export interface CausalEvent {
  order: number
  label: string
  node_type: string
  relation: string
}

export interface RiskComponent {
  name: string
  score: number
  weight: number
  explanation: string
}

export interface RiskScore {
  total: number
  tier: SeverityTier
  components: RiskComponent[]
  explanation: string
}

export interface Alert {
  id: string
  severity: SeverityTier
  title: string
  description: string
  regulatory_violations: string[]
  precursor_patterns: string[]
  created_at: string
}

export interface CorrAction {
  urgency: Urgency
  action: string
  rationale: string
  regulation_reference: string | null
}

export interface AnalysisReport {
  analysis_id: string
  file_name: string
  incident: IncidentReport
  entities: HazardEntity[]
  similar_incidents: SimilarIncident[]
  regulatory_clauses: RegulatoryClause[]
  precursor_patterns: PrecursorPattern[]
  causal_chain: CausalEvent[]
  risk_score: RiskScore
  alerts: Alert[]
  corrective_actions: CorrAction[]
  warnings: string[]
  processing_time_seconds: number
  created_at: string
}

export interface AnalysisSummary {
  analysis_id: string
  file_name: string
  status: string
  severity: SeverityTier
  risk_total: number
  industry: string | null
  created_at: string
}

export interface HistoryPage {
  items: AnalysisSummary[]
  total: number
  page: number
  limit: number
}

export interface DashboardStats {
  total_analyses: number
  critical_alerts: number
  avg_risk_score: number
  industries_covered: number
}

export interface StreamUpdate {
  stage: string
  status: StreamStatus
  message: string
  data: Record<string, unknown> | null
  timestamp: string
}

export interface StartAnalysisResponse {
  analysis_id: string
  status: 'processing' | 'cached'
}
