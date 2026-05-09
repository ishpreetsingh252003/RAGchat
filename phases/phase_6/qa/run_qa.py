import sys
import os
import json
import time
from pathlib import Path

# Setup paths
ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

from phases.phase_4.guardrails.query_router import route_query
from phases.phase_3.generation.answer import synthesize
from phases.phase_4.guardrails.response_policy import validate_response

def run_qa():
    test_cases_path = Path(__file__).parent / "test_cases.json"
    with open(test_cases_path, "r") as f:
        data = json.load(f)

    results = {
        "passed": 0,
        "failed": 0,
        "details": []
    }

    print("\n" + "="*60)
    print("PHASE 6 — QA & REGRESSION SUITE")
    print("="*60)

    # 1. Golden Questions (Factual Accuracy & Citations)
    print("\n[Section 1: Golden Questions]")
    for case in data["golden_questions"]:
        query = case["query"]
        print(f"Testing {case['id']} ({case['category']}): {query[:50]}...")
        
        # Simulate pipeline
        routing = route_query(query)
        if routing["route"] != "factual":
            print(f"  [FAIL] Expected factual route, got {routing['route']}")
            results["failed"] += 1
            results["details"].append({"id": case["id"], "status": "FAIL", "reason": f"Wrong route: {routing['route']}"})
            continue
            
        response = synthesize(query)
        
        # Basic validation
        passed = True
        reasons = []
        
        if not response["grounded"]:
            passed = False
            reasons.append("Response not grounded")
            
        if not response["citation_url"]:
            passed = False
            reasons.append("Missing citation URL")
            
        # Keyword check
        answer_text = " ".join(response["answer_sentences"]).lower()
        missing_keywords = [kw for kw in case["expected_keywords"] if kw.lower() not in answer_text]
        if missing_keywords:
            # We don't fail strictly on keyword matching as LLM wording varies, but we log it
            print(f"  [WARN] Missing keywords: {missing_keywords}")
            
        if passed:
            # Avoid encoding issues on Windows console by encoding to ascii with backslashreplace
            ans_display = ' '.join(response['answer_sentences'])[:100]
            try:
                print(f"  [PASS] Answer: {ans_display}...")
            except UnicodeEncodeError:
                print(f"  [PASS] Answer: {ans_display.encode('ascii', 'backslashreplace').decode()}...")
            results["passed"] += 1
            results["details"].append({"id": case["id"], "status": "PASS"})
        else:
            print(f"  [FAIL] Reasons: {', '.join(reasons)}")
            results["failed"] += 1
            results["details"].append({"id": case["id"], "status": "FAIL", "reason": ", ".join(reasons)})

    # 2. Regression Checks (Refusals)
    print("\n[Section 2: Regression Checks (Refusals)]")
    for case in data["regression_checks"]:
        query = case["query"]
        print(f"Testing {case['id']} ({case['category']}): {query[:50]}...")
        
        routing = route_query(query)
        actual_route = routing["route"]
        
        if actual_route == case["expected_route"]:
            print(f"  [PASS] Correctly routed to {actual_route}")
            results["passed"] += 1
            results["details"].append({"id": case["id"], "status": "PASS"})
        else:
            print(f"  [FAIL] Expected {case['expected_route']}, got {actual_route}")
            results["failed"] += 1
            results["details"].append({"id": case["id"], "status": "FAIL", "reason": f"Expected {case['expected_route']}, got {actual_route}"})

    # 3. Policy Enforcement
    print("\n[Section 3: Policy Enforcement]")
    for case in data["metadata_checks"]:
        query = case["query"]
        print(f"Testing {case['id']} ({case['category']}): {query[:50]}...")
        
        response = synthesize(query)
        policy = validate_response(
            answer_sentences=response["answer_sentences"],
            citation_url=response["citation_url"]
        )
        
        if policy.is_compliant:
            print(f"  [PASS] Policy compliant")
            results["passed"] += 1
            results["details"].append({"id": case["id"], "status": "PASS"})
        else:
            print(f"  [FAIL] Policy violations: {policy.violations}")
            results["failed"] += 1
            results["details"].append({"id": case["id"], "status": "FAIL", "reason": str(policy.violations)})

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total Tests: {results['passed'] + results['failed']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    
    # Save report
    report_path = Path(__file__).parent / "qa_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nReport saved to {report_path}")

if __name__ == "__main__":
    run_qa()
