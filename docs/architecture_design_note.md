# Architecture & Design Note
## Policy-Aware Multi-Agent RAG Claim Decision Engine

### Executive Summary
This document presents the architectural design, agent boundaries, state transitions, retrieval mechanics, and engineering trade-offs of the **Policy-Aware Multi-Agent RAG Claim Decision Engine**. Built for Universal Sompo General Insurance policy decisioning, the system combines **LangGraph** multi-agent state machines, **FAISS** dense semantic search, **BM25** sparse keyword retrieval, Reciprocal Rank Fusion (RRF) reranking, **FastAPI**, **Streamlit**, and **Llama 3**.

---

### 1. System Architecture & Multi-Agent Boundaries

The system enforces a strict separation of concerns across 5 specialized agents that exchange a typed, structured state (`ClaimAgentState`):

```
+-------------------------------------------------------------------------------+
|                             LangGraph Workflow                                |
|                                                                               |
|  [Case Analysis] -> [Policy Evidence] -> [Coverage & Exclusion] -> [Decision] |
|       (Fact            (Hybrid RAG            (Rule Evaluation &       (Amount|
|    Extraction)          Retrieval)                Sub-limits)         Calc)   |
|                                                                          |    |
|                                                                          v    |
|                                                                     [Validation]|
|                                                                      (Pass/Fail)|
+-------------------------------------------------------------------------------+
```

#### Agent Responsibilities & Contracts

1. **Case Analysis Agent (`case_analyzer.py`)**:
   - **Responsibility**: Ingests raw claim JSON, extracts diagnosis, procedure, admission hours, policy start date vs claim date, expenses, and document manifest.
   - **Output**: 5-dimensional investigation plan and flags missing fields (e.g. missing discharge summary or hospital criteria proof).

2. **Policy Evidence Agent (`evidence_retriever.py`)**:
   - **Responsibility**: Formulates targeted RAG queries based on the case dimensions and retrieves exact policy clauses.
   - **Output**: Top relevant policy chunks with metadata (source PDF, page number, section heading, chunk ID).

3. **Coverage & Exclusion Agent (`coverage_evaluator.py`)**:
   - **Responsibility**: Evaluates policy rules (initial 30-day waiting period, 12/24-month specific disease waiting periods, 48-month pre-existing condition waiting period with portability credits, domiciliary 3-day rule, day-care procedure waivers, cosmetic/experimental exclusions, and sub-limits).
   - **Output**: `rule_evaluations` and `applicable_limits` (room rent 1% SI/day, ICU 2% SI/day, doctor fee 25% SI, OT/meds 40% SI, domiciliary 20% SI, ambulance 1% SI / Rs 1,000 max).

4. **Decision Agent (`decision_maker.py`)**:
   - **Responsibility**: Synthesizes all specialist findings. If required evidence is missing, it abstains with `NEEDS_REVIEW`. Otherwise, it computes payable amount vs deductions and outputs `ADMISSIBLE`, `ADMISSIBLE_WITH_LIMITS`, `PARTIALLY_ADMISSIBLE`, or `NOT_ADMISSIBLE`.
   - **Output**: Decision status, confidence score, itemized deductions, payable amount, and key findings.

5. **Validation Agent (`validator.py`)**:
   - **Responsibility**: Audits decision statements against retrieved citations. Ensures no material claim is made without verifiable policy citation grounding.
   - **Output**: `PASS`/`FAIL` validation status, unsupported claims list, and auto-correction trigger.

---

### 2. RAG & Retrieval Engineering Design

To prevent reliance on generic vector search alone, the RAG pipeline employs a **Hybrid Dense-Sparse RRF Architecture**:

1. **Non-Naive Policy Indexing**:
   - The 17-page policy document (`USGIC-CSCIndividualHealthInsurance_2017-2018.pdf`) is parsed using **PyMuPDF (`fitz`)**.
   - Text is segmented into 133 heading-aware, non-naive chunks, preserving page numbers, section headers (DEFINITIONS, SCOPE OF COVER, EXCLUSIONS, WAITING PERIODS, EXTENSIONS, PORTABILITY), and sub-sections.

2. **Dual Indexing & RRF Fusion**:
   - **Dense Index**: FAISS vector store using `sentence-transformers/all-MiniLM-L6-v2` embeddings (Cosine Similarity / Inner Product).
   - **Sparse Index**: BM25 keyword index (`rank_bm25.BM25Okapi`) targeting exact domain terms ("1.0%", "30 days", "cataract", "domiciliary", "24 hours", "pre-existing").
   - **Reciprocal Rank Fusion (RRF)**: Merges dense and sparse ranks via $RRF(d) = \sum \frac{1}{60 + r(d)}$, followed by exact term match boosting.

---

### 3. Abstention & Reliability Principles

1. **Abstention (`NEEDS_REVIEW`)**:
   - When required documents (e.g. discharge summary, doctor prescription) or hospital registration criteria are missing, the system abstains rather than hallucinating a policy decision.

2. **Portability Credit Calculation**:
   - Automatically credits prior continuous years with another Indian insurer (`prior_insurer_continuous_years`) towards reducing pre-existing (48m) and specific disease (12m/24m) waiting periods.

3. **Sub-limit Cap Enforcement**:
   - Automatically applies daily room rent cap (1% Sum Insured), ICU cap (2% Sum Insured), doctor fee cap (25% Sum Insured), medicines/OT cap (40% Sum Insured), and ambulance cap (1% SI or Rs 1,000 max).

---

### 4. Trade-Offs & Future Enhancements

| Design Choice | Selection | Rationale & Trade-off |
|---|---|---|
| **Orchestration** | LangGraph StateGraph | **Pros:** Deterministic, stateful, auditable multi-agent workflow. **Cons:** Requires explicit state schema definition. |
| **Vector Store** | FAISS + In-Memory BM25 | **Pros:** Ultra-fast (<100ms retrieval), zero external server dependency. **Cons:** Single-node local storage. |
| **RAG Strategy** | RRF Hybrid (Dense + BM25) | **Pros:** Captures both semantic meaning and exact numbers/policy clauses. **Cons:** Slightly higher indexing time. |
| **LLM Provider** | Llama 3 (Ollama / Groq) | **Pros:** High reasoning capability, zero cloud lock-in. **Cons:** Local inference speed depends on hardware. |
