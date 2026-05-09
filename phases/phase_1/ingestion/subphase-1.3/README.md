# Phase 1.3 — Parsing (PDF/HTML → text)

**Architecture reference:** `docs/architecture-phase-wise.md` → Phase 1 → Subphase **1.3**.

## Goal

Convert raw snapshots into extracted text suitable for normalization and chunking.

## Planned inputs

- Subphase 1.2 outputs:
  - `../subphase-1.2/output/snapshot_index.json`
  - `../subphase-1.2/output/snapshots/`

## Planned outputs (to `output/`)

- `parsed/` (one file per URL snapshot, extracted text)
- `parse_report.json` (empty-text flags, OCR-needed flags, failures)

## Run

From the repo root (after running Subphase 1.2):

```powershell
python phases/phase-1/ingestion/subphase-1.3/parse_snapshots.py
```

