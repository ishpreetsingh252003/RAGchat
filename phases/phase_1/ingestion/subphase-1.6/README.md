# Phase 1.6 — Embedding

**Architecture reference:** `docs/architecture-phase-wise.md` → Phase 1 → Subphase **1.6**.

## Goal

Generate embeddings for chunks and record embedder version so indexes are reproducible.

## Planned inputs

- Subphase 1.5 output: `../subphase-1.5/output/chunks.jsonl`

## Planned outputs (to `output/`)

- `embeddings/` (vectors serialized, format TBD)
- `embed_manifest.json` (model name/version, dimensions, date, chunk count)

## Run

From the repo root (after running Subphase 1.5):

```powershell
python phases/phase-1/ingestion/subphase-1.6/embed_chunks.py
```

