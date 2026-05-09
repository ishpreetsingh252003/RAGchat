# Phase 1.7 — Index upsert + build manifest

**Architecture reference:** `docs/architecture-phase-wise.md` → Phase 1 → Subphase **1.7**.

## Goal

Upsert vectors + metadata into the vector index and write an **index build manifest** used by later phases (including the “Last updated from sources” footer).

## Planned inputs

- Subphase 1.6 outputs: `../subphase-1.6/output/embeddings/` + `embed_manifest.json`
- Subphase 1.5 outputs: `../subphase-1.5/output/chunk_index.json`

## Planned outputs (to `output/`)

- `index_v{n}/` (vector index artifacts)
- `index_build_manifest.json` (index version, build time, source urls, fetched_at max, embedder info)

## Run

From the repo root (after running Subphase 1.6):

```powershell
python phases/phase-1/ingestion/subphase-1.7/upsert_index.py
```

