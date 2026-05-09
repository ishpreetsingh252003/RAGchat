# Edge Cases — Phase 2 (Retrieval Layer)

**Related architecture:** [architecture-phase-wise.md §5](architecture-phase-wise.md) (Phase 2).

Covers **query preprocessing**, **filters**, **top-k**, and **deduplication** when user language or corpus metadata do not align.

| Edge case | What goes wrong | Suggested handling | If ignored |
|-----------|-----------------|--------------------|------------|
| **Scheme out of scope** | User asks about a fund not in the five HDFC schemes / not in index. | Short-circuit: **polite boundary message** + link to AMFI scheme search or AMC home (per policy); **do not** retrieve random chunks. | Irrelevant or misleading answers from nearest-neighbor noise. |
| **Ambiguous scheme reference** | “HDFC tax saver” could mean ELSS product naming variants. | Use **alias table + metadata filter**; if still ambiguous, one **clarifying question** that does not constitute advice (e.g., “Do you mean HDFC ELSS Tax Saver — Direct Plan Growth?”). | Wrong fund facts. |
| **Typos & transliteration** | “ELSS locin”, “expence ratio”. | Fuzzy match on scheme names; **spell-normalization** for common MF terms; slightly higher `k` before filter, then **re-rank**. | Missed retrieval → empty or generic answers. |
| **Multi-scheme question** | “Compare exit load of X and Y.” | Problem statement forbids **performance comparisons** and advisory framing; treat as **refusal or factsheet-only** policy (Phase 4). Do not synthesize a comparison table. | Accidental advisory or implied ranking. |
| **No metadata for filter** | User names a scheme but chunks lack `scheme_id`. | Fallback to **semantic-only** retrieval with scheme name in query; log gap to fix metadata. | Weak precision, more hallucination risk. |
| **Conflicting chunks** | Two chunks show different exit load effective dates. | Prefer **newest `fetched_at`** and **factsheet** doc type; if conflict remains, answer with **single official link** and narrow wording (“per factsheet dated …”) or refuse to pick—per product policy. | User trust loss. |
| **Overly broad query** | “Explain mutual funds.” | Low similarity to scheme corpus; **generic AMFI/SEBI** educational retrieval if whitelisted, or short definition + one educational link without scheme-specific claims. | Rambling or off-domain generation. |
| **Exact duplicate chunks** | Same paragraph ingested twice (pagination mirrors). | **Near-duplicate dedup** in candidate list so `k` is not wasted. | Redundant context, wrong diversity assumption. |
| **Language mix** | Hindi question, English corpus. | If out of scope for MVP, respond with **supported languages** notice + AMFI link; if supporting Hindi, need **Hindi official pages** in corpus. | Nonsense retrieval scores. |
| **“Download statement” without platform** | User omits HDFC vs registrar vs statement type. | Retrieve **generic official guide** chunk; answer steps that are **source-backed** only; avoid platform-specific guesses. | Wrong procedural advice. |
