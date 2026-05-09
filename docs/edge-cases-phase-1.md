# Edge Cases — Phase 1 (Ingestion, Parsing, and Indexing)

**Related architecture:** [architecture-phase-wise.md §4](architecture-phase-wise.md) (Phase 1).

Covers **fetch**, **parse**, **chunk**, **embed**, and **index upsert** when reality does not match happy-path HTML/PDF.

| Edge case | What goes wrong | Suggested handling | If ignored |
|-----------|-----------------|--------------------|------------|
| **`robots.txt` / ToS** | Fetcher is disallowed or blocked; legal/compliance risk if ignored. | Honor **robots.txt** where applicable; if disallowed, **manual download + manifest** with static file hash, or use only distributor APIs permitted by policy. | Blocked IP, legal exposure, or silent empty corpus. |
| **Rate limits & transient 5xx** | Thundering herd on AMC site; intermittent failures. | **Backoff + jitter**, per-host concurrency caps, idempotent retries with max attempts; record last success time per URL. | Partial index, nondeterministic “last updated” dates. |
| **PDF: scanned image, no text layer** | Extractor returns empty or garbage text. | OCR path with **confidence threshold**; if below threshold, flag document as **low quality** and exclude or require manual text layer. | Wrong numbers in retrieval (“hallucination fuel”). |
| **PDF: multi-column / tables** | Rows merge; expense ratio table becomes unreadable lines. | Table-aware extraction or **section-specific parsers** for known factsheet layouts; validate numeric fields with regex where possible. | Silent corruption of tabular facts. |
| **HTML: client-rendered content** | Static GET returns empty body; real text only in browser. | Headless fetch only if policy allows; otherwise **alternative official URL** (PDF factsheet) or skip page. | Empty chunks indexed. |
| **Mixed encodings & mojibake** | Devanagari or special symbols break chunk boundaries. | Normalize to UTF-8; test with sample pages; fail parse on invalid encoding. | Broken search and odd generations. |
| **Chunk boundary splits a fact** | “Exit load” sentence split so half is in each chunk. | Use **overlap** and prefer breaks on headings; post-validate critical labels stay with values in same chunk when possible. | Retrieved context missing the number next to the label. |
| **Duplicate URL in manifest** | Same URL ingested twice with different labels. | Deduplicate on **canonical URL** before fetch; single `content_hash` per snapshot. | Duplicate vectors, citation confusion. |
| **Re-ingest: document shrinks** | New version removes a section users still ask about. | Keep **previous snapshot** for audit; answer may become “not in current official document—see archive” per product policy. | Answering from stale memory without transparency. |
| **Embedding model upgrade** | New model dimension or space; old index incompatible. | **Version** embedder in index name; full re-embed on upgrade; do not mix vectors from different models. | Broken similarity or random retrieval quality. |
| **Clock skew** | `fetched_at` wrong on builder machine. | Use **UTC** and NTP-corrected builders; store source `Last-Modified` / PDF `CreationDate` when trustworthy as secondary signals. | Misleading “Last updated from sources” footer. |
