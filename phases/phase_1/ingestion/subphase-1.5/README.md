# Phase 1.5 — Chunking + metadata enrichment

**Architecture reference:** `docs/architecture-phase-wise.md` → Phase 1 → Subphase **1.5**.

## Goal

Split normalized documents into retrievable chunks and attach metadata required for citation and filtering.

## Planned inputs

- Subphase 1.4 outputs: `../subphase-1.4/output/normalized/`
- Phase 0 scheme scope: `phases/phase-0/corpus/schemes.json`
- Phase 0 manifest: `phases/phase-0/corpus/manifest.json`

## Planned outputs (to `output/`)

- `chunks.jsonl` (one chunk per line with metadata)
- `chunk_index.json` (chunk_id → source url, offsets, scheme_id, doc_type)

## Run

From the repo root (after running Subphase 1.4):

```powershell
python phases/phase-1/ingestion/subphase-1.5/chunk_documents.py
```

