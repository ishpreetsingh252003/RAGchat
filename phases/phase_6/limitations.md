# System Limitations and Edge Cases

This document outlines the known limitations of the Mutual Fund FAQ Assistant as of Phase 6.

## 1. Data Freshness (Drift)
- **Stale PDFs**: Official factsheets and KIM/SID documents are updated periodically (monthly or quarterly). The system's "Last Updated" date reflects the ingestion time, not necessarily the document's internal revision date.
- **Dynamic Content**: Some source URLs (like Groww scheme pages) may change their HTML structure, which can cause parsing errors or missing data until the next ingestion cycle.

## 2. Ingestion & Parsing
- **OCR Errors**: Scanned PDF documents or tables within PDFs may occasionally be misread by the parser, leading to incorrect figures (e.g., expense ratios).
- **Table Complexity**: Complex nested tables in official documents may be flattened into text, potentially losing the relationship between headers and values.
- **Empty/Dynamic Shells**: URLs that require heavy JavaScript rendering may result in "empty" snapshots if the fetcher does not execute JS.

## 3. Retrieval & Semantic Understanding
- **Scheme Name Ambiguity**: Users may use colloquial names (e.g., "HDFC Midcap" instead of "HDFC Mid-Cap Fund - Direct Growth"). While the retriever uses semantic similarity, high ambiguity can lead to cross-linking between similar schemes.
- **Topic Overlap**: Questions that overlap multiple sections (e.g., "What are the risks and loads?") may only retrieve the most relevant section due to the small `k` constraint.

## 4. Generation & Citations
- **Single Citation Constraint**: Per requirements, only one citation is provided. If an answer draws from multiple sources (e.g., a factsheet and an FAQ), only the primary source is linked.
- **Sentence Limit**: The 3-sentence limit may result in the omission of secondary details for complex queries.

## 5. Guardrails
- **Refusal False Positives**: Highly specific factual questions that sound like advice (e.g., "Is the 1.5% expense ratio good?") might be routed to refusal to maintain a strict safety margin.
- **PII Detection**: The system uses pattern matching for PII (PAN, etc.). Obfuscated or non-standard PII formats might not be caught, although no PII is stored.

## 6. Compliance
- **No Performance Comparisons**: The system intentionally refuses to compare performance across funds or provide "top fund" lists to avoid being classified as an investment advisor.
