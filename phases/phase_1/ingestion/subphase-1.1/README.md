# Phase 1.1 — Corpus + whitelist validation

**Architecture reference:** `docs/architecture-phase-wise.md` → Phase 1 → Subphase **1.1**.

This subphase validates and normalizes the Phase 0 URL inventory before any fetching happens.

## Inputs

- `phases/phase-0/corpus/manifest.json`
- `phases/phase-0/corpus/schemes.json`
- `phases/phase-0/corpus/whitelist.json`

## What it does

- Collects candidate URLs from:
  - `manifest.corpus.anchor_urls`
  - `schemes[].groww_url`
  - `manifest.corpus.backlog_official_urls_to_add[].url` (when present)
- Normalizes URLs (lowercases host, drops fragments, strips common tracking params, trims trailing slashes)
- Enforces:
  - HTTPS only
  - host must be in whitelist
  - URL must match one of the allowed prefixes
- Produces:
  - deduped validated URL list
  - rejected URL report with reasons
  - scope sanity check: anchors vs schemes should typically match 1:1 in Phase 0

## Run

From the repo root:

```powershell
python phases/phase-1/ingestion/subphase-1.1/validate_corpus.py
```

## Outputs

Written to `phases/phase-1/ingestion/subphase-1.1/output/`:

- `validated_urls.json`
- `rejected_urls.json`

