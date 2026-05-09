# Phase 3 — Generation, Formatting, and Citations

**Architecture reference:** `docs/architecture-phase-wise.md` (Phase 3).

## Implementation

- `generation/answer.py` — Retrieval (Phase 2) → grounded answer (**max 3 sentences**).
  - **Grounded**: one `Source:` URL + `Last updated from sources:` footer when confident.
  - **Unknown / low confidence**: no URL, no footer (no fabricated citations).
  - **PII in query**: refusal-style message **without any URL**.

## Run

```powershell
python phases/phase-3/generation/answer.py "What is the exit load for HDFC Mid Cap Fund?"
```

