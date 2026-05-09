# Edge Cases — Phase 6 (Quality Assurance and Operational Readiness)

**Related architecture:** [architecture-phase-wise.md §9](architecture-phase-wise.md) (Phase 6).

Covers **golden sets**, **regression**, **drift**, and **documentation of limitations** when the system or ecosystem changes.

| Edge case | What goes wrong | Suggested handling | If ignored |
|-----------|-----------------|--------------------|------------|
| **Flaky LLM outputs** | Same golden prompt sometimes fails sentence/link rules. | Prefer **deterministic checks** in CI; use **seed/temperature 0** where applicable; **snapshot** model version; consider template-heavy generation for critical fields. | CI noise; false green releases. |
| **Golden data rot** | Official numbers in expected answers change after re-ingest. | Separate tests: **structural** (has citation, refusal on advisory) vs **exact string** for numbers; or assert against **grounded spans** in allowed docs. | Perpetual test failures or silent wrong baselines. |
| **AMFI/SEBI site redesign** | Scraped selectors break; educational links 404. | **Link health check** job; versioned link list; fallback educational URL. | Broken refusals and bad UX. |
| **Scheme merger / name change** | HDFC internal corporate actions rename schemes. | Manifest **event log**; router message “scheme updated—see current official name on AMFI”; re-run alias table update. | Wrong or obsolete answers. |
| **Partial index production** | Ingestion job half-succeeds; some URLs missing. | **Gate release** on minimum URL success rate; surface **index build report**; do not claim freshness for missing sections. | Silent coverage holes. |
| **Security dependency CVE** | Embeddings lib or server has critical patch. | Dependency scanning; pin versions; patch playbook. | Compromised deployment. |
| **Load / abuse** | Public demo hammered with tokens. | Rate limits, captcha, or API key for heavy use; cost alerts. | Bill shock or outage. |
| **“Last updated” vs user perception** | Site says updated today but PDF inside is months old. | Clarify in README: date is **fetch time** or **document date** per policy; avoid implying intra-day regulatory freshness. | Trust disputes. |
| **Human review backlog** | Edge cases accumulate without owners. | Link each new edge from runbooks to **Phase owner**; quarterly review of this `docs/edge-cases-phase-*.md` set. | Repeated incidents. |
| **README limitations out of sync** | Code handles Hindi; README still says English only. | Treat limitations as **release artifact**; update with each version that changes language, corpus, or citation policy. | Mis-set expectations. |

---

## Index of phase edge-case documents

| Phase | Document |
|-------|----------|
| 0 — Scope, corpus, compliance | [edge-cases-phase-0.md](edge-cases-phase-0.md) |
| 1 — Ingestion, parsing, indexing | [edge-cases-phase-1.md](edge-cases-phase-1.md) |
| 2 — Retrieval | [edge-cases-phase-2.md](edge-cases-phase-2.md) |
| 3 — Generation, citations | [edge-cases-phase-3.md](edge-cases-phase-3.md) |
| 4 — Guardrails | [edge-cases-phase-4.md](edge-cases-phase-4.md) |
| 5 — UI | [edge-cases-phase-5.md](edge-cases-phase-5.md) |
| 6 — QA & operations | [edge-cases-phase-6.md](edge-cases-phase-6.md) |
