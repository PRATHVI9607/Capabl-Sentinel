---
tags: [codegraph, layer]
---

# Orchestration

16 modules. Layer 4 of 6; imports may point down this list, never up.

| Module | In | Out | Symbols | Purpose |
|---|---|---|---|---|
| [[app.agents]] | 0 | 0 | 0 | LangGraph agent: typed state, nodes, and the compiled graph. |
| [[app.agents.graph]] | 1 | 10 | 4 | The SENTINEL state machine. |
| [[app.agents.nodes]] | 0 | 9 | 0 | The nine nodes of the SENTINEL graph. |
| [[app.agents.nodes.alert_synthesizer]] | 2 | 3 | 1 | Standard synthesis path, taken when the risk score is below 8.0. |
| [[app.agents.nodes.base]] | 8 | 3 | 5 | Shared node plumbing: streaming, error capture, and the iteration guard. |
| [[app.agents.nodes.document_router]] | 2 | 4 | 1 | Decide what was uploaded and flag documents the pipeline cannot do much with. |
| [[app.agents.nodes.entity_extractor]] | 2 | 6 | 1 | Pull hazard entities out of the text and settle on a hazard family. |
| [[app.agents.nodes.error_handler]] | 2 | 6 | 2 | Terminal node for a failed run: emit what was produced before the failure. |
| [[app.agents.nodes.incident_parser]] | 2 | 4 | 1 | Extract the structured incident from the report text. |
| [[app.agents.nodes.pattern_detector]] | 2 | 6 | 2 | Find historical matches, then the precursor patterns they corroborate. |
| [[app.agents.nodes.priority_alert_synthesizer]] | 2 | 3 | 1 | Priority synthesis path, taken when the risk score reaches 8.0 or above. |
| [[app.agents.nodes.regulatory_auditor]] | 2 | 5 | 1 | Retrieve the regulatory clauses that apply to this incident. |
| [[app.agents.nodes.risk_scorer]] | 2 | 7 | 1 | Compute the risk score. Pure Python -- the LLM never touches this number. |
| [[app.agents.nodes.synthesis]] | 2 | 6 | 4 | Shared assembly for both alert-synthesis paths. |
| [[app.agents.state]] | 13 | 0 | 2 | The typed state every LangGraph node reads from and writes to. |
| [[app.pipeline]] | 1 | 11 | 4 | One analysis, end to end: PDF in, persisted AnalysisReport out. |
