export const SEVERITY_CONFIG = {
  CRITICAL: { label: 'Critical', tone: 'text-severity-critical bg-severity-critical/10 border-severity-critical/25', gauge: '#FF3B30', pulse: true },
  HIGH:     { label: 'High',     tone: 'text-severity-high bg-severity-high/10 border-severity-high/25',             gauge: '#FF6B00', pulse: false },
  MEDIUM:   { label: 'Medium',   tone: 'text-severity-medium bg-severity-medium/10 border-severity-medium/25',       gauge: '#FFB800', pulse: false },
  LOW:      { label: 'Low',      tone: 'text-severity-low bg-severity-low/10 border-severity-low/25',                gauge: '#30D158', pulse: false },
  UNKNOWN:  { label: 'Unknown',  tone: 'text-text-muted bg-white/5 border-white/10',                                 gauge: '#5A5A7A', pulse: false },
} as const

// Order matters: this is the pipeline order the SSE stream follows.
export const AGENT_STAGES = [
  { id: 'document_router',    label: 'Router',    icon: 'Compass'   },
  { id: 'incident_parser',    label: 'Parser',    icon: 'FileText'  },
  { id: 'entity_extractor',   label: 'Entities',  icon: 'Tag'       },
  { id: 'pattern_detector',   label: 'Patterns',  icon: 'Activity'  },
  { id: 'regulatory_auditor', label: 'Auditor',   icon: 'Scale'     },
  { id: 'risk_scorer',        label: 'Scorer',    icon: 'BarChart2' },
  { id: 'alert_synthesizer',  label: 'Alerts',    icon: 'Bell'      },
] as const

// The backend runs exactly one of these; both map to the last pipeline node.
export const SYNTHESIZER_STAGES = ['alert_synthesizer', 'priority_alert_synthesizer'] as const

export const URGENCY_CONFIG = {
  IMMEDIATE:  { label: 'Immediate',  tone: 'text-severity-critical border-severity-critical/30' },
  SHORT_TERM: { label: 'Short term', tone: 'text-severity-medium border-severity-medium/30' },
  LONG_TERM:  { label: 'Long term',  tone: 'text-severity-low border-severity-low/30' },
} as const

export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024
