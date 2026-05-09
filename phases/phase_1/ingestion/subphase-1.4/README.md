# Phase 1.4 — Normalization + cleaning

**Architecture reference:** `docs/architecture-phase-wise.md` → Phase 1 → Subphase **1.4**.

## Goal

Normalize extracted text (encoding fixes, whitespace cleanup), preserve headings/sections, and produce consistent text blocks for chunking.

## Planned inputs

- Subphase 1.3 outputs: `../subphase-1.3/output/parsed/` + `parse_report.json`

## Planned outputs (to `output/`)

- `normalized/` (cleaned text per document)
- `normalization_report.json` (what transformations were applied)

## Run

From the repo root (after running Subphase 1.3):

```powershell
python phases/phase-1/ingestion/subphase-1.4/normalize_text.py
```

