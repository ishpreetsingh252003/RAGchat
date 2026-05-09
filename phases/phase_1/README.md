# Phase 1 — Ingestion, Parsing, and Indexing

**Architecture reference:** `docs/architecture-phase-wise.md` (Phase 1).

This folder is reserved for Phase 1 implementation (fetch → parse → chunk → embed → index + audit log).

Planned inputs from Phase 0:

- `phases/phase-0/corpus/manifest.json`
- `phases/phase-0/corpus/whitelist.json`
- `phases/phase-0/corpus/schemes.json`

## Implemented subphases

- **1.1 — Corpus + whitelist validation**: `ingestion/subphase-1.1/` (run `validate_corpus.py`)

