# Phase 2 — Retrieval Layer

**Architecture reference:** `docs/architecture-phase-wise.md` (Phase 2).

This phase implements **metadata-first + lexical (BM25) retrieval** suited to the current corpus (HTML-heavy flattened text) and current embedding approach.

## Implementation

- `retrieval/retriever.py`: scheme/topic detection → metadata filtering → BM25 scoring → top‑k chunks

## Run

```powershell
python phases/phase-2/retrieval/retriever.py "What is the exit load for HDFC Mid Cap Fund?"
```

