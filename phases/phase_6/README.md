# Phase 6 — Quality Assurance and Operational Readiness

**Architecture reference:** `docs/architecture-phase-wise.md` (Phase 6).

This folder implements the final phase of the RAG Chatbot, focusing on quality control and operational stability.

## Components Implemented:

1. **QA Suite**:
   - [test_cases.json](qa/test_cases.json): Curated "Golden Questions" and regression checks.
   - [run_qa.py](qa/run_qa.py): Automated test runner that validates routing, grounding, and policy compliance.
   - `qa/qa_report.json`: Automatically generated report after test execution.

2. **System Limitations**:
   - [limitations.md](limitations.md): Documentation of known edge cases, parsing limitations, and compliance boundaries.

3. **Operational Readiness (Drift Handling)**:
   - [.github/workflows/refresh-corpus.yml](../../.github/workflows/refresh-corpus.yml): GitHub Actions workflow for daily automated ingestion and index updates.

## How to Run QA:
```bash
python phases/phase_6/qa/run_qa.py
```

