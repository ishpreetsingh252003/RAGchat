## Phase 0 Policy Constraints (Facts-only Mutual Fund FAQ Assistant)

These constraints come from `problemstatement.md` and are enforced across later phases.

### Allowed behavior

- Answer **factual, verifiable** questions about the in-scope schemes.
- Use only the **curated corpus** defined by Phase 0 (see `../corpus/manifest.json`).
- Use only URLs whose hosts are in `../corpus/whitelist.json`.

### Disallowed behavior

- **No investment advice**, opinions, or recommendations.
- **No performance comparisons** or “which is better” answers.
- **No return calculations**. If asked about performance, return **one official factsheet link** (when available in corpus).

### Response format constraints

- **Max 3 sentences** per response.
- **Exactly one citation link** per response.
- Always append: `Last updated from sources: <date>`

### Refusal handling (advisory / non-factual queries)

If the user asks for advice (e.g., “Should I invest?”, “Which fund is better?”), respond with:

- A polite refusal that reinforces the facts-only limitation.
- **Exactly one** educational link chosen from `../corpus/refusal-education-links.json`.

### Privacy & security constraints

Do not collect, store, or process:

- PAN or Aadhaar numbers
- Account numbers
- OTPs
- Email addresses or phone numbers

Operationally:

- Avoid storing raw user queries in logs; redact if sensitive patterns are detected.

