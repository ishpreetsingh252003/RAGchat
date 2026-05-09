# Phase 1.2 — Fetching + snapshotting

**Architecture reference:** `docs/architecture-phase-wise.md` → Phase 1 → Subphase **1.2**.

## Goal

Fetch all validated URLs and store **raw snapshots** (HTML/PDF) plus a per-URL log (HTTP status, timestamps, content hash).

## Planned inputs

- Output of Subphase 1.1: `../subphase-1.1/output/validated_urls.json`
- Phase 0 whitelist: `phases/phase-0/corpus/whitelist.json`

## Planned outputs (to `output/`)

- `fetch_log.jsonl` (one line per URL attempt)
- `snapshots/` (raw files; naming based on stable url hash)
- `snapshot_index.json` (url → snapshot path, content hash, fetched_at)

## Run

From the repo root:

```powershell
python phases/phase-1/ingestion/subphase-1.2/fetch_snapshots.py
```

