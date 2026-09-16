import sys
import json
import os
import time
import datetime
from typing import List, Dict, Any

sys.stdout.reconfigure(encoding='utf-8')

from policy_engine.schemas import ClaimCaseInput, ClaimDecisionResponse
from policy_engine.graph import ClaimDecisionPipeline
from policy_engine.config import settings

def run_evaluation():
    print("="*60)
    print("STARTING E2E EVALUATION SUITE FOR CLAIM DECISION ENGINE")
    print("="*60)
    
    pipeline = ClaimDecisionPipeline()
    
    public_path = settings.PUBLIC_CASES_PATH
    candidate_path = settings.CANDIDATE_CASES_PATH
    
    with open(public_path, "r", encoding="utf-8") as f:
        public_cases = json.load(f)
        
    with open(candidate_path, "r", encoding="utf-8") as f:
        candidate_cases = json.load(f)

    # Ground truth expected decisions
    ground_truth = {
        "PUB-001": "ADMISSIBLE_WITH_LIMITS",
        "PUB-002": "NOT_ADMISSIBLE",
        "PUB-003": "NOT_ADMISSIBLE",
        "PUB-004": "ADMISSIBLE_WITH_LIMITS",
        "PUB-005": "ADMISSIBLE",
        "PUB-006": "NEEDS_REVIEW",
        "PUB-007": "ADMISSIBLE_WITH_LIMITS",
        "PUB-008": "NOT_ADMISSIBLE",
        "PUB-009": "ADMISSIBLE",
        "PUB-010": "ADMISSIBLE",
        "PUB-011": "NEEDS_REVIEW",
        "PUB-012": "NOT_ADMISSIBLE",
        "CAND-001": "NEEDS_REVIEW",
        "CAND-002": "NEEDS_REVIEW",
        "CAND-003": "NOT_ADMISSIBLE",
        "CAND-004": "ADMISSIBLE_WITH_LIMITS",
        "CAND-005": "NOT_ADMISSIBLE"
    }

    all_cases = [("Public", c) for c in public_cases] + [("Candidate", c) for c in candidate_cases]
    
    results_summary = []
    correct_decisions = 0
    total_cases = len(all_cases)
    citation_hits = 0
    abstention_correct = 0
    total_abstention_cases = 4  # PUB-006, PUB-011, CAND-001, CAND-002

    start_eval_time = time.time()

    for category, raw_case in all_cases:
        cid = raw_case["case_id"]
        case_input = ClaimCaseInput(**raw_case)
        expected_decision = ground_truth.get(cid, "UNKNOWN")
        
        t0 = time.time()
        response: ClaimDecisionResponse = pipeline.analyze_claim(case_input)
        elapsed_ms = (time.time() - t0) * 1000.0
        
        actual_decision = response.decision
        is_match = (actual_decision == expected_decision)
        if is_match:
            correct_decisions += 1
            
        if expected_decision == "NEEDS_REVIEW" and actual_decision == "NEEDS_REVIEW":
            abstention_correct += 1
            
        if len(response.citations) > 0:
            citation_hits += 1

        match_str = "[PASS]" if is_match else "[FAIL]"
        print(f"[{category:9s}] Case {cid:8s} | Expected: {expected_decision:22s} | Actual: {actual_decision:22s} | Match: {match_str} | Citations: {len(response.citations)} | Time: {elapsed_ms:.1f}ms")
        
        results_summary.append({
            "category": category,
            "case_id": cid,
            "diagnosis": case_input.treatment.diagnosis,
            "expected_decision": expected_decision,
            "actual_decision": actual_decision,
            "match": is_match,
            "confidence": response.confidence,
            "total_claimed_inr": response.total_claimed_inr,
            "payable_amount_inr": response.payable_amount_inr,
            "deductions_inr": response.total_deductions_inr,
            "citations_count": len(response.citations),
            "missing_evidence_count": len(response.missing_evidence),
            "elapsed_ms": elapsed_ms
        })

    total_eval_duration = time.time() - start_eval_time
    accuracy_pct = (correct_decisions / total_cases) * 100.0
    citation_hit_pct = (citation_hits / total_cases) * 100.0
    abstention_pct = (abstention_correct / total_abstention_cases) * 100.0

    print("\n" + "="*60)
    print("EVALUATION RESULTS SUMMARY")
    print("="*60)
    print(f"Total Test Cases Evaluated : {total_cases} (12 Public + 5 Candidate)")
    print(f"Decision Accuracy         : {correct_decisions}/{total_cases} ({accuracy_pct:.1f}%)")
    print(f"Abstention Precision      : {abstention_correct}/{total_abstention_cases} ({abstention_pct:.1f}%)")
    print(f"Citation Hit Rate         : {citation_hits}/{total_cases} ({citation_hit_pct:.1f}%)")
    print(f"Total Evaluation Duration : {total_eval_duration:.2f} seconds")
    print("="*60)

    # Save evaluation_results.json
    results_json_path = r"d:\Aptino\eval\evaluation_results.json"
    os.makedirs(r"d:\Aptino\eval", exist_ok=True)
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics": {
                "total_cases": total_cases,
                "accuracy_pct": accuracy_pct,
                "abstention_pct": abstention_pct,
                "citation_hit_pct": citation_hit_pct,
                "duration_seconds": total_eval_duration
            },
            "cases": results_summary
        }, f, indent=2)

    # Save evaluation_report.md
    report_md_path = r"d:\Aptino\eval\evaluation_report.md"
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write("# Policy Decision Engine - Evaluation Report\n\n")
        f.write(f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Summary Metrics\n\n")
        f.write(f"- **Total Cases Evaluated:** {total_cases} (12 Public Cases + 5 Candidate Cases)\n")
        f.write(f"- **Decision Accuracy / Concordance:** **{accuracy_pct:.1f}%** ({correct_decisions}/{total_cases})\n")
        f.write(f"- **Abstention Correctness (`NEEDS_REVIEW`):** **{abstention_pct:.1f}%** ({abstention_correct}/{total_abstention_cases})\n")
        f.write(f"- **Policy Citation Hit Rate:** **{citation_hit_pct:.1f}%** ({citation_hits}/{total_cases})\n")
        f.write(f"- **Average Duration Per Case:** **{(total_eval_duration / total_cases)*1000:.1f} ms**\n\n")
        
        f.write("## Case-by-Case Breakdown\n\n")
        f.write("| Category | Case ID | Diagnosis | Expected Decision | Actual Decision | Match | Citations | Duration (ms) |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for item in results_summary:
            match_icon = "PASS" if item["match"] else "FAIL"
            f.write(f"| {item['category']} | {item['case_id']} | {item['diagnosis']} | `{item['expected_decision']}` | `{item['actual_decision']}` | {match_icon} | {item['citations_count']} | {item['elapsed_ms']:.1f} |\n")

    print(f"\nSaved evaluation outputs to {results_json_path} and {report_md_path}")

if __name__ == "__main__":
    run_evaluation()
