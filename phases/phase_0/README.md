# Phase 0 — Scope, Corpus, and Compliance Baseline

This phase implements the **project scope lock** and the **compliance baseline** described in `docs/architecture-phase-wise.md` (Phase 0).

## What exists in this phase

- `corpus/manifest.json`: Project scope (AMC + 5 schemes), anchor URLs, and corpus targets (15–25 URLs total).
- `corpus/schemes.json`: Canonical scheme table + aliases for query normalization.
- `corpus/whitelist.json`: Allowed hosts / patterns for ingestion and citation validation.
- `corpus/refusal-education-links.json`: Pre-approved educational links used in refusal responses.
- `policy/constraints.md`: Facts-only rules, refusal rules, response formatting constraints, and privacy constraints.
- `ui/disclaimer.md`: The disclaimer snippet: “Facts-only. No investment advice.”

## Phase outputs (consumed by later phases)

- **Corpus manifest + scheme scope** for ingestion (Phase 1).
- **Whitelist** for ingestion and citation enforcement (Phases 1, 3, 4).
- **Refusal link allowlist** for safe refusals (Phase 4).
- **Disclaimer snippet** for UI (Phase 5).

