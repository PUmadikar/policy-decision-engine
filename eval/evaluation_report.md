# Policy Decision Engine - Evaluation Report

**Date:** 2026-09-16 17:58:13

## Summary Metrics

- **Total Cases Evaluated:** 17 (12 Public Cases + 5 Candidate Cases)
- **Decision Accuracy / Concordance:** **100.0%** (17/17)
- **Abstention Correctness (`NEEDS_REVIEW`):** **100.0%** (4/4)
- **Policy Citation Hit Rate:** **100.0%** (17/17)
- **Average Duration Per Case:** **98.2 ms**

## Case-by-Case Breakdown

| Category | Case ID | Diagnosis | Expected Decision | Actual Decision | Match | Citations | Duration (ms) |
|---|---|---|---|---|---|---|---|
| Public | PUB-001 | Acute appendicitis | `ADMISSIBLE_WITH_LIMITS` | `ADMISSIBLE_WITH_LIMITS` | PASS | 16 | 202.8 |
| Public | PUB-002 | Viral fever | `NOT_ADMISSIBLE` | `NOT_ADMISSIBLE` | PASS | 16 | 93.4 |
| Public | PUB-003 | Pre-existing thyroid disorder with complications | `NOT_ADMISSIBLE` | `NOT_ADMISSIBLE` | PASS | 16 | 90.3 |
| Public | PUB-004 | Condition requiring home treatment | `ADMISSIBLE_WITH_LIMITS` | `ADMISSIBLE_WITH_LIMITS` | PASS | 17 | 89.9 |
| Public | PUB-005 | Cataract | `ADMISSIBLE` | `ADMISSIBLE` | PASS | 16 | 92.1 |
| Public | PUB-006 | Acute infection | `NEEDS_REVIEW` | `NEEDS_REVIEW` | PASS | 15 | 90.6 |
| Public | PUB-007 | Cancer | `ADMISSIBLE_WITH_LIMITS` | `ADMISSIBLE_WITH_LIMITS` | PASS | 16 | 93.5 |
| Public | PUB-008 | Cosmetic condition | `NOT_ADMISSIBLE` | `NOT_ADMISSIBLE` | PASS | 15 | 100.1 |
| Public | PUB-009 | Acute appendicitis | `ADMISSIBLE` | `ADMISSIBLE` | PASS | 16 | 84.5 |
| Public | PUB-010 | Cataract | `ADMISSIBLE` | `ADMISSIBLE` | PASS | 16 | 97.4 |
| Public | PUB-011 | Acute appendicitis | `NEEDS_REVIEW` | `NEEDS_REVIEW` | PASS | 16 | 84.5 |
| Public | PUB-012 | Experimental condition | `NOT_ADMISSIBLE` | `NOT_ADMISSIBLE` | PASS | 16 | 85.4 |
| Candidate | CAND-001 | Acute Myocardial Infarction | `NEEDS_REVIEW` | `NEEDS_REVIEW` | PASS | 16 | 95.5 |
| Candidate | CAND-002 | Hypertension and Diabetes Management | `NEEDS_REVIEW` | `NEEDS_REVIEW` | PASS | 16 | 93.3 |
| Candidate | CAND-003 | Acute Cholecystitis | `NOT_ADMISSIBLE` | `NOT_ADMISSIBLE` | PASS | 16 | 92.4 |
| Candidate | CAND-004 | Severe Osteoarthritis Right Knee | `ADMISSIBLE_WITH_LIMITS` | `ADMISSIBLE_WITH_LIMITS` | PASS | 16 | 97.1 |
| Candidate | CAND-005 | Degenerative Disc Disease | `NOT_ADMISSIBLE` | `NOT_ADMISSIBLE` | PASS | 16 | 86.4 |
