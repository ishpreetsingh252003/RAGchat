# Edge Cases — Phase 3 (Generation, Formatting, and Citations)

**Related architecture:** [architecture-phase-wise.md §6](architecture-phase-wise.md) (Phase 3).

Covers the **answer synthesizer**, **three-sentence cap**, **single citation**, **performance-query handling**, and **footer date** when the model or post-processors misbehave.

| Edge case | What goes wrong | Suggested handling | If ignored |
|-----------|-----------------|--------------------|------------|
| **Fourth sentence sneaks in** | Model adds “In summary…” | **Hard post-check** (sentence count); trim or regenerate with stricter prompt; fallback template. | Violates problem statement §2. |
| **Zero or multiple URLs** | Model forgets link or adds three sources “for transparency.” | **Deterministic citation picker** from retrieved metadata; strip model-generated URLs; validate **exactly one** allowed host. | Broken trust or policy violation. |
| **Citation not grounded** | Model cites a URL never in retrieved chunks. | Reject response; regenerate with “use only this URL: …” or render from **structured JSON** fields filled by code, not free text. | Fabricated citations. |
| **Numeric hallucination** | Correct link but wrong expense ratio not in context. | **Extractive-first** pattern: numbers must appear in retrieved text or replace with “see official document” + link; **no calculation** of returns. | Regulatory and user harm. |
| **Performance / returns question** | User asks for returns or “how much will I make.” | Per constraints: **no return calculations**; respond with **factsheet link** and minimal factual framing allowed by sources. | Implied performance advice. |
| **Unicode / markdown link leakage** | Model outputs broken markdown or raw HTML. | Sanitize for UI; enforce plain text + single URL in dedicated field. | XSS or broken rendering (see Phase 5). |
| **Footer date logic** | `max(fetched_at)` is older than user expects after partial re-ingest. | Document rule: footer reflects **chunks used in this answer** or **whole index build**—pick one and apply consistently. | Confusing “staleness” perception. |
| **Timezone display** | Dates shift a day across locales. | Store UTC ISO; display **date-only** in a fixed timezone (e.g., `Asia/Kolkata`) per product decision. | Wrong “last updated” day. |
| **Structured JSON malformation** | Schema drift; partial fields. | Validate with schema; **retry once**; else safe fallback (“Unable to format; see [link]”). | API 500s or empty UI. |
| **Degenerate retrieval** | No chunks above similarity threshold. | Do not call synthesizer for factual claims; return **insufficient sources** template + educational link (coordinate with Phase 4). | Invented answers. |
