---
tags: [codegraph, layer]
---

# Tools

7 modules. Layer 3 of 6; imports may point down this list, never up.

| Module | In | Out | Symbols | Purpose |
|---|---|---|---|---|
| [[app.tools]] | 9 | 6 | 2 | The ten SENTINEL tools. |
| [[app.tools.actions]] | 2 | 3 | 6 | Corrective action generation. |
| [[app.tools.parsing]] | 3 | 5 | 13 | Turn raw report text into an IncidentReport and a list of hazard entities. |
| [[app.tools.patterns]] | 4 | 5 | 7 | Precursor detection and causal chain traversal. |
| [[app.tools.retrieval]] | 4 | 4 | 8 | Retrieval tools: historical incidents and applicable regulatory clauses. |
| [[app.tools.scoring]] | 3 | 3 | 7 | Severity classification and the risk score. |
| [[app.tools.streaming]] | 3 | 3 | 1 | Publish a pipeline update to whichever SSE clients are watching this analysis. |
