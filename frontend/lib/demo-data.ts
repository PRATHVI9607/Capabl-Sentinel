import type { AnalysisReport, AnalysisSummary, DashboardStats } from '@/lib/types'

const reports: AnalysisReport[] = [
  {
    analysis_id: 'demo-press-guard-01',
    file_name: 'hydraulic-press-near-miss.pdf',
    incident: {
      incident_date: '2026-08-14',
      location: 'Assembly hall 2',
      industry: 'manufacturing',
      equipment_involved: ['Hydraulic press', 'Light curtain'],
      sequence_of_events: 'A press cycle began while an operator was clearing a misaligned workpiece.',
      immediate_causes: ['Guard bypassed', 'Unexpected equipment cycle'],
      root_causes: ['Repeated sensor faults', 'Maintenance work deferred'],
      injury_count: 0,
      fatality_count: 0,
      severity_indicator: 'CRITICAL',
      raw_text_length: 6842,
      extraction_confidence: 0.94,
    },
    entities: [
      { text: 'hydraulic press', entity_type: 'EQUIPMENT', confidence: 0.9, source: 'spacy' },
      { text: 'guard bypass', entity_type: 'UNSAFE_ACT', confidence: 0.75, source: 'llm' },
    ],
    similar_incidents: [
      {
        doc_id: 'osha-2019-447',
        title: 'Press activation during jam clearing',
        industry: 'Metal fabrication',
        severity: 'Fatal',
        similarity_score: 0.89,
        chunk_excerpt: 'The presence-sensing device had generated intermittent faults for several shifts before the event.',
        source_document: 'OSHA Fatality Inspection 1427712',
        incident_date: '2019-05-22',
        hazard_tags: ['machine_guarding', 'unexpected_startup'],
      },
    ],
    regulatory_clauses: [
      {
        clause_id: '1910.212-a-1',
        regulation_name: 'OSHA 29 CFR',
        section: '1910.212(a)(1)',
        clause_text: 'One or more methods of machine guarding shall be provided to protect the operator and other employees in the machine area.',
        violation_confidence: 0.91,
        relevance_explanation: 'The report describes operation with a bypassed presence-sensing guard.',
      },
      {
        clause_id: '1910.147-c-4',
        regulation_name: 'OSHA 29 CFR',
        section: '1910.147(c)(4)',
        clause_text: 'Procedures shall be developed, documented and utilized for the control of potentially hazardous energy.',
        violation_confidence: 0.84,
        relevance_explanation: 'Jam clearing exposed the operator to unexpected energization without a documented isolation step.',
      },
    ],
    precursor_patterns: [
      {
        pattern_name: 'Recurring safeguard faults',
        description: 'Intermittent light-curtain faults were documented across three maintenance shifts before the near miss.',
        confidence: 0.93,
        evidence_count: 9,
        hazard_types: ['machine_guarding', 'maintenance_delay'],
      },
      {
        pattern_name: 'Temporary bypass became routine',
        description: 'A short-term production workaround remained in use after the original fault condition returned.',
        confidence: 0.87,
        evidence_count: 6,
        hazard_types: ['unsafe_act', 'procedural_drift'],
      },
      {
        pattern_name: 'Jam clearing under stored energy',
        description: 'The task exposed personnel to motion before energy isolation was verified.',
        confidence: 0.81,
        evidence_count: 4,
        hazard_types: ['unexpected_startup'],
      },
    ],
    causal_chain: [
      { order: 1, label: 'Light curtain faults recur', node_type: 'CONDITION', relation: 'normalizes' },
      { order: 2, label: 'Safeguard bypass remains active', node_type: 'UNSAFE_ACT', relation: 'permits' },
      { order: 3, label: 'Operator reaches into press envelope', node_type: 'EXPOSURE', relation: 'precedes' },
      { order: 4, label: 'Unexpected press cycle begins', node_type: 'EVENT', relation: 'creates near miss' },
    ],
    risk_score: {
      total: 8.24,
      tier: 'CRITICAL',
      components: [
        { name: 'Severity', score: 9.5, weight: 0.3, explanation: 'Potential outcome classified as critical from the reported press motion.' },
        { name: 'Frequency', score: 10, weight: 0.25, explanation: 'Nine indexed incidents contain the same safeguard-fault pattern.' },
        { name: 'Regulatory', score: 6, weight: 0.25, explanation: 'Machine guarding and hazardous energy clauses are implicated.' },
        { name: 'Precursor Density', score: 4.45, weight: 0.2, explanation: 'Three corroborated precursors occur in a short operational window.' },
      ],
      explanation: 'The combination of a disabled safeguard, recurring faults, and exposure during an energized task produces a critical risk classification.',
    },
    alerts: [
      {
        id: 'alert-demo-01',
        severity: 'CRITICAL',
        title: 'Press safeguard bypassed during operation',
        description: 'Stop press operation until the presence-sensing safeguard is restored and validated.',
        regulatory_violations: ['29 CFR 1910.212(a)(1)'],
        precursor_patterns: ['Recurring safeguard faults', 'Temporary bypass became routine'],
        created_at: '2026-08-14T10:42:00Z',
      },
      {
        id: 'alert-demo-02',
        severity: 'HIGH',
        title: 'Energy isolation absent for jam clearing',
        description: 'The current jam-clearing sequence does not verify isolation before entry into the press envelope.',
        regulatory_violations: ['29 CFR 1910.147(c)(4)'],
        precursor_patterns: ['Jam clearing under stored energy'],
        created_at: '2026-08-14T10:41:00Z',
      },
    ],
    corrective_actions: [
      { urgency: 'IMMEDIATE', action: 'Stop the affected press and remove the safeguard bypass.', rationale: 'The current condition permits unexpected motion while personnel are inside the hazard envelope.', regulation_reference: '29 CFR 1910.212(a)(1)' },
      { urgency: 'SHORT_TERM', action: 'Revalidate jam-clearing and energy-isolation procedures with every shift.', rationale: 'The task sequence must require a verified zero-energy state before access.', regulation_reference: '29 CFR 1910.147(c)(4)' },
      { urgency: 'LONG_TERM', action: 'Add recurring safety-device faults to the maintenance escalation threshold.', rationale: 'Repeated protective-device faults are a leading signal and should not remain in a normal queue.', regulation_reference: null },
    ],
    warnings: ['Preview data is shown because local demo mode is enabled.'],
    processing_time_seconds: 18.4,
    created_at: '2026-08-14T10:42:00Z',
  },
]

const variants = [
  { id: 'demo-confined-space-02', file: 'tank-entry-observation.pdf', severity: 'HIGH' as const, risk: 7.3, industry: 'chemicals', date: '2026-08-11T08:20:00Z' },
  { id: 'demo-conveyor-03', file: 'conveyor-entanglement.pdf', severity: 'HIGH' as const, risk: 6.8, industry: 'logistics', date: '2026-08-07T16:12:00Z' },
  { id: 'demo-forklift-04', file: 'forklift-pedestrian-near-miss.pdf', severity: 'MEDIUM' as const, risk: 5.4, industry: 'warehousing', date: '2026-08-02T11:03:00Z' },
  { id: 'demo-solvent-05', file: 'solvent-transfer-review.pdf', severity: 'MEDIUM' as const, risk: 4.7, industry: 'chemicals', date: '2026-07-29T14:46:00Z' },
  { id: 'demo-crane-06', file: 'overhead-crane-inspection.pdf', severity: 'LOW' as const, risk: 2.6, industry: 'manufacturing', date: '2026-07-24T09:15:00Z' },
]

for (const variant of variants) {
  const source = reports[0]
  reports.push({
    ...source,
    analysis_id: variant.id,
    file_name: variant.file,
    created_at: variant.date,
    incident: { ...source.incident, industry: variant.industry, severity_indicator: variant.severity },
    risk_score: { ...source.risk_score, total: variant.risk, tier: variant.severity },
    alerts: source.alerts.slice(0, 1).map((alert) => ({
      ...alert,
      id: `alert-${variant.id}`,
      severity: variant.severity,
      created_at: variant.date,
    })),
  })
}

export const DEMO_REPORTS = reports

export const DEMO_HISTORY: AnalysisSummary[] = reports.map((report) => ({
  analysis_id: report.analysis_id,
  file_name: report.file_name,
  status: 'complete',
  severity: report.risk_score.tier,
  risk_total: report.risk_score.total,
  industry: report.incident.industry,
  created_at: report.created_at,
}))

export const DEMO_STATS: DashboardStats = {
  total_analyses: DEMO_HISTORY.length,
  critical_alerts: reports.flatMap((report) => report.alerts).filter((alert) => alert.severity === 'CRITICAL').length,
  avg_risk_score: DEMO_HISTORY.reduce((sum, report) => sum + report.risk_total, 0) / DEMO_HISTORY.length,
  industries_covered: new Set(DEMO_HISTORY.map((report) => report.industry).filter(Boolean)).size,
}
