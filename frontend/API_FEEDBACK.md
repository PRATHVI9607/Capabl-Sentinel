# API feedback

## Regulatory source document

The frontend brief requires every regulatory clause to show the source document. The documented `RegulatoryClause` response shape does not include a `source_document` field.

Current UI behavior: show the returned `regulation_name` and `section` as the source reference. The UI does not invent a document filename.

Suggested contract change:

```ts
interface RegulatoryClause {
  source_document: string
}
```

This should carry the corpus document identifier or filename used to retrieve `clause_text`.
