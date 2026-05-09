# Edge Cases — Phase 0 (Scope, Corpus, and Compliance Baseline)

**Related architecture:** [architecture-phase-wise.md §3](architecture-phase-wise.md) (Phase 0).

This file lists non-obvious situations that break assumptions about **AMC/scheme scope**, **URL inventory**, **whitelisting**, **citation rules**, and **PII policy**.

| Edge case | What goes wrong | Suggested handling | If ignored |
|-----------|-----------------|--------------------|------------|
| **Scheme naming drift** | Official documents use variants (“HDFC Mid-Cap Opportunities Fund” vs retail label “Mid-Cap Fund”); manifest `scheme_id` does not line up with user language. | Maintain a **canonical scheme table** (internal id, common aliases, ISIN if used only for disambiguation—do not ask users for it). | Retrieval filters miss the right fund or answers feel “about the wrong scheme.” |
| **Redirect off-whitelist** | A whitelisted URL 302s to a blog, CDN, or short link on a non-whitelisted host. | After redirect, **validate final URL host** against the whitelist; fail ingest or flag for manual review. | Silent violation of “closed corpus” or unsafe citations. |
| **Groww URL change or retirement** | Path changes; old Groww links 404 while fund still exists. | Version the manifest; **monitor HTTP status** on scheduled runs; alert on 404/410. | Broken user-facing catalogue and broken deep links in tests or UI copy. |
| **Dynamic / authenticated pages** | Groww or AMC pages return shell HTML without public facts (geo block, bot challenge). | Detect **empty or tokenized** parse output; treat as fetch failure; do not index placeholder text. | Index pollution and nonsense answers. |
| **Corpus size vs problem statement** | Fewer than **15–25 URLs** ship in early iterations. | Document **MVP subset** explicitly in README; keep a backlog list of required official URLs to reach full count. | Audit/review gaps; inconsistent “last updated” across topics. |
| **Overlapping documents** | Same metric (e.g., expense ratio) appears in factsheet, KIM, and AMFI with **different effective dates**. | In manifest, tag **document role** and **as_of** semantics; Phase 2–3 rules prefer **newest official factsheet** for figures. | Users see conflicting numbers with no explanation. |
| **Citation policy vs source mix** | Problem statement prioritizes **official** sources; project also whitelists **groww.in**. | Decide per answer type **which domains may be cited** (e.g., Groww for navigation copy only, HDFC PDF for numbers—or one consistent rule). Document in manifest. | Compliance drift; regulators or reviewers challenge non-official citations. |
| **PII in URL or query params** | Marketing links include `utm_` + email hashes or session ids (should not be stored). | **Normalize URLs** in manifest (strip tracking query params where safe); never log full volatile query strings as PII-rich. | Accidental storage of sensitive-adjacent data in logs. |
| **Team extends whitelist ad hoc** | New hosts added without review (“just one more PDF host”). | **Change control** on whitelist file (PR + reason); automated test that only allowed hosts appear in index metadata. | Corpus grows to unvetted third parties. |

**Refusal / clarification (Phase 0 design only):** If scope is unclear (e.g., user asks about a fund **not** in the five Groww scheme list), product copy and router spec should say whether to **refuse**, **clarify**, or **answer from generic AMFI/SEBI**—record that decision here when fixed.
