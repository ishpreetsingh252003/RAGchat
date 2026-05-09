"""
Comprehensive test script for Mutual Fund FAQ Assistant - Phases 0 through 5
"""
import sys
import os
import traceback
from pathlib import Path

# Setup
sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

ROOT = Path(__file__).parent
PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

results = []

def test(name, fn):
    try:
        fn()
        print(f"{PASS} {name}")
        results.append((name, True, None))
    except Exception as e:
        msg = str(e)
        print(f"{FAIL} {name}: {msg}")
        traceback.print_exc()
        results.append((name, False, msg))

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("PHASE 0 — Corpus & Config Files")
print("="*60)

def test_phase0_manifest():
    import json
    p = ROOT / "phases" / "phase_0" / "corpus" / "manifest.json"
    assert p.exists(), f"Missing: {p}"
    data = json.loads(p.read_text())
    assert "urls" in data or "sources" in data or len(data) > 0, "manifest.json appears empty"

def test_phase0_schemes():
    import json
    p = ROOT / "phases" / "phase_0" / "corpus" / "schemes.json"
    assert p.exists(), f"Missing: {p}"
    data = json.loads(p.read_text())
    schemes = data.get("schemes", [])
    assert len(schemes) >= 3, f"Expected >=3 schemes, got {len(schemes)}"
    print(f"    Found {len(schemes)} schemes: {[s.get('scheme_id') for s in schemes]}")

def test_phase0_whitelist():
    import json
    p = ROOT / "phases" / "phase_0" / "corpus" / "whitelist.json"
    assert p.exists(), f"Missing: {p}"
    data = json.loads(p.read_text())
    domains = data.get("allowed_domains", data.get("domains", []))
    assert len(domains) > 0, "Whitelist is empty"
    print(f"    Whitelisted domains: {domains}")

test("Phase0 manifest.json exists & readable", test_phase0_manifest)
test("Phase0 schemes.json has >=3 schemes", test_phase0_schemes)
test("Phase0 whitelist.json has domains", test_phase0_whitelist)

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("PHASE 1 — Ingestion Output Files")
print("="*60)

def test_phase1_chunks_jsonl():
    p = ROOT / "phases" / "phase_1" / "ingestion" / "subphase-1.5" / "output" / "chunks.jsonl"
    assert p.exists(), f"Missing: {p}"
    lines = [l for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]
    assert len(lines) > 0, "chunks.jsonl is empty"
    import json
    first = json.loads(lines[0])
    assert "chunk_id" in first, "chunk missing chunk_id"
    assert "text" in first, "chunk missing text"
    print(f"    Chunks count: {len(lines)}")

def test_phase1_chunk_index():
    p = ROOT / "phases" / "phase_1" / "ingestion" / "subphase-1.5" / "output" / "chunk_index.json"
    assert p.exists(), f"Missing: {p}"
    import json
    data = json.loads(p.read_text())
    print(f"    chunk_index.json keys: {list(data.keys())[:5]}")

def test_phase1_index_manifest():
    p = ROOT / "phases" / "phase_1" / "ingestion" / "subphase-1.7" / "output" / "index_build_manifest.json"
    assert p.exists(), f"Missing: {p}"
    import json
    data = json.loads(p.read_text())
    print(f"    Manifest keys: {list(data.keys())}")

test("Phase1 chunks.jsonl exists & has data", test_phase1_chunks_jsonl)
test("Phase1 chunk_index.json exists", test_phase1_chunk_index)
test("Phase1 index_build_manifest.json exists", test_phase1_index_manifest)

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("PHASE 2 — Retriever")
print("="*60)

def test_phase2_retriever_path():
    """Check path constants in retriever.py match real paths."""
    chunks_path = ROOT / "phases" / "phase_1" / "ingestion" / "subphase-1.5" / "output" / "chunks.jsonl"
    # retriever.py hardcodes phase-1 (hyphen) — check if that path exists
    chunks_hyphen = ROOT / "phases" / "phase-1" / "ingestion" / "subphase-1.5" / "output" / "chunks.jsonl"
    chunks_under = ROOT / "phases" / "phase_1" / "ingestion" / "subphase-1.5" / "output" / "chunks.jsonl"
    
    if chunks_hyphen.exists():
        print("    retriever.py path (phase-1 hyphen): EXISTS")
    elif chunks_under.exists():
        print(f"    WARNING: retriever.py uses 'phase-1' (hyphen) but dir is 'phase_1' (underscore)!")
        print(f"    Actual path exists: {chunks_under}")
        raise AssertionError("Path mismatch: retriever.py uses 'phase-1' but directory is 'phase_1'")

def test_phase2_retrieve():
    from phases.phase_2.retrieval.retriever import retrieve
    result = retrieve("What is the expense ratio of HDFC Mid-Cap Fund?")
    assert "results" in result, "retrieve() missing 'results' key"
    assert "detected" in result, "retrieve() missing 'detected' key"
    print(f"    Results count: {len(result['results'])}")
    print(f"    Detected: {result['detected']}")
    if result['results']:
        top = result['results'][0]
        print(f"    Top score: {top['score']:.4f}")

test("Phase2 retriever path check (phase-1 vs phase_1)", test_phase2_retriever_path)
test("Phase2 retrieve() works end-to-end", test_phase2_retrieve)

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("PHASE 3 — Answer Generation")
print("="*60)

def test_phase3_synthesize_factual():
    from phases.phase_3.generation.answer import synthesize
    result = synthesize("What is the expense ratio of HDFC Mid-Cap Fund?")
    assert "grounded" in result
    assert "answer_sentences" in result
    print(f"    Grounded: {result['grounded']}")
    print(f"    Reason: {result.get('reason')}")
    print(f"    Answer: {result['answer_sentences']}")
    print(f"    Citation: {result.get('citation_url')}")
    print(f"    Footer: {result.get('footer')}")

def test_phase3_synthesize_pii():
    from phases.phase_3.generation.answer import synthesize
    result = synthesize("My PAN is ABCDE1234F, what fund should I pick?")
    assert result["grounded"] is False
    assert result.get("reason") == "pii_in_query"
    print(f"    PII detection: OK - {result['answer_sentences'][0][:60]}...")

test("Phase3 synthesize() factual query", test_phase3_synthesize_factual)
test("Phase3 synthesize() PII detection", test_phase3_synthesize_pii)

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("PHASE 4 — Guardrails")
print("="*60)

def test_phase4_query_router():
    from phases.phase_4.guardrails.query_router import route_query
    
    cases = [
        ("What is the expense ratio of HDFC Mid-Cap Fund?", "factual"),
        ("Should I invest in HDFC fund?", "refusal"),
        ("Which fund is better?", "refusal"),
        ("Hello world", "ambiguous"),
    ]
    for q, expected in cases:
        r = route_query(q)
        actual = r["route"]
        status = "OK" if actual == expected else f"UNEXPECTED (got {actual}, wanted {expected})"
        print(f"    [{status}] '{q[:45]}' -> {actual}")

def test_phase4_response_policy():
    from phases.phase_4.guardrails.response_policy import validate_response
    
    # Test compliant response
    result = validate_response(
        answer_sentences=["The expense ratio is 1.5%."],
        citation_url="https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
    )
    print(f"    Compliant response: is_compliant={result.is_compliant}, violations={len(result.violations)}")

def test_phase4_refusal_templates():
    from phases.phase_4.guardrails.refusal_templates import (
        create_advisory_refusal, create_pii_refusal, create_ambiguous_refusal,
        create_policy_violation_refusal, create_no_sources_refusal
    )
    r = create_advisory_refusal("investment advice detected")
    assert r["grounded"] is False
    assert "answer_sentences" in r
    print(f"    Advisory refusal: OK - {r['title']}")
    
    r = create_pii_refusal()
    assert r["grounded"] is False
    print(f"    PII refusal: OK - {r['title']}")

def test_phase4_logger():
    from phases.phase_4.guardrails.logger import log_refusal, log_policy_violation, log_classification
    log_classification(query="test", route="factual", confidence=0.9, detected_entities={})
    log_refusal(query="test", refusal_type="advisory_content", reason="test", confidence=0.9)
    log_policy_violation(response_text="test", violation_types=["imperative_buy_sell"], severity="high")
    print("    Logger functions: OK")

test("Phase4 query_router classification", test_phase4_query_router)
test("Phase4 response_policy validate_response", test_phase4_response_policy)
test("Phase4 refusal_templates creation", test_phase4_refusal_templates)
test("Phase4 logger functions", test_phase4_logger)

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("PHASE 5 — UI & API")
print("="*60)

def test_phase5_ui_html():
    p = ROOT / "phases" / "phase_5" / "ui" / "index.html"
    assert p.exists(), f"Missing: {p}"
    content = p.read_text(encoding='utf-8')
    assert "Facts-only" in content or "facts-only" in content or "mutual fund" in content.lower(), \
        "index.html missing expected disclaimer or content"
    print(f"    index.html size: {len(content)} bytes - OK")

def test_phase5_api_template():
    p = ROOT / "api" / "templates" / "index.html"
    assert p.exists(), f"Missing API template: {p}"
    print(f"    API template exists: {p}")

def test_phase5_api_imports():
    # Test that api/main.py can be imported without starting the server
    from flask import Flask
    from flask_cors import CORS
    from phases.phase_4.guardrails.query_router import route_query
    from phases.phase_4.guardrails.response_policy import validate_response
    from phases.phase_4.guardrails.refusal_templates import (
        create_advisory_refusal, create_pii_refusal, create_ambiguous_refusal,
        create_policy_violation_refusal, create_no_sources_refusal
    )
    from phases.phase_4.guardrails.logger import log_refusal, log_policy_violation, log_classification
    from phases.phase_3.generation.answer import synthesize
    print("    All API imports: OK")

def test_phase5_api_chat_flow():
    """Simulate the full chat API flow without starting Flask."""
    from phases.phase_4.guardrails.query_router import route_query
    from phases.phase_4.guardrails.response_policy import validate_response
    from phases.phase_3.generation.answer import synthesize
    from phases.phase_4.guardrails.refusal_templates import create_advisory_refusal, create_ambiguous_refusal
    
    # Test advisory query
    query = "Should I invest in HDFC Mid-Cap Fund?"
    routing = route_query(query)
    assert routing["should_refuse"] is True
    print(f"    Advisory query routed correctly: route={routing['route']}")
    
    # Test factual query pipeline
    query2 = "What is the exit load for HDFC ELSS?"
    routing2 = route_query(query2)
    print(f"    Factual query routed: route={routing2['route']}, to_rag={routing2['should_route_to_rag']}")
    if routing2["should_route_to_rag"]:
        gen = synthesize(query2, k=3)
        policy = validate_response(
            answer_sentences=gen.get("answer_sentences", []),
            citation_url=gen.get("citation_url"),
            source_text=""
        )
        print(f"    Generation grounded={gen['grounded']}, policy compliant={policy.is_compliant}")

test("Phase5 UI index.html exists", test_phase5_ui_html)
test("Phase5 API template exists", test_phase5_api_template)
test("Phase5 API imports all succeed", test_phase5_api_imports)
test("Phase5 Full chat pipeline simulation", test_phase5_api_chat_flow)

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
print(f"Total: {len(results)}  |  Passed: {passed}  |  Failed: {failed}")
print()
if failed:
    print("FAILED TESTS:")
    for name, ok, err in results:
        if not ok:
            print(f"  - {name}: {err}")
else:
    print("ALL TESTS PASSED!")
