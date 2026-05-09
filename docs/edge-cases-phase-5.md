# Edge Cases — Phase 5 (Minimal User Interface)

**Related architecture:** [architecture-phase-wise.md §8](architecture-phase-wise.md) (Phase 5).

Covers the **welcome flow**, **example prompts**, **disclaimer**, and **chat display** when clients, networks, or content behave badly.

| Edge case | What goes wrong | Suggested handling | If ignored |
|-----------|-----------------|--------------------|------------|
| **XSS via chat** | User sends `<script>` or `javascript:` in message; reflected in DOM. | **Escape** all user text; use framework defaults; **sanitize** any markdown; open links with `rel="noopener noreferrer"`. | Account/session risk on shared machines. |
| **Link phishing display** | Answer shows a look-alike URL. | Render URL as **read-only text** from backend; do not allow user-controlled hrefs in assistant output without allowlist check (same as Phase 3). | User tricked into bad site. |
| **PII pasted in chat** | User pastes PAN, phone, account number. | **Do not persist** client-side history to server beyond session if possible; display **one-time notice** that PII should not be entered; strip or redact in logs (Phase 4). | Privacy violation. |
| **Very long input** | User pastes entire PDF text. | **Max length** on input; show friendly error; rate limit. | Cost blowup, DoS, bad retrieval. |
| **Disclaimer below fold** | On mobile, “Facts-only. No investment advice.” not visible before send. | **Sticky** disclaimer or inline reminder near send button; first-run modal if required. | Compliance visibility gap. |
| **Example questions drift** | Examples reference metrics that changed or funds renamed. | Point examples at **stable informational patterns** (“What is the minimum SIP…”) not volatile numbers; periodic review. | Misleading onboarding. |
| **Streaming partial answers** | UI shows answer before citation/footer appended. | Buffer until **minimum complete payload** (answer + link + footer) or show skeleton with clear “loading.” | User screenshots incomplete compliance text. |
| **Offline / API errors** | Network failure, 502, timeout. | Clear **retry** message; no cached advisory text; do not show stale answers without date. | Confusion and support tickets. |
| **Accessibility** | Screen reader skips disclaimer or link. | Semantic headings, `aria` for status updates, focus management on new messages. | Exclusion, compliance risk. |
| **Deep link to prefill harmful query** | URL encodes advisory prompt for virality. | Rate limit; router still **refuses**; no special-casing in UI. | Prompt injection via sharing. |
