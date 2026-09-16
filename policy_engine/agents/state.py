from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict
from policy_engine.schemas import (
    ClaimCaseInput,
    Citation,
    ApplicableLimit,
    ValidationResult,
    TraceStep
)

class ClaimAgentState(TypedDict):
    input_case: ClaimCaseInput
    
    # 1. Case Analysis Agent Output
    analysis_plan: Dict[str, Any]
    decision_dimensions: List[str]
    missing_input_fields: List[str]
    
    # 2. Policy Evidence Agent Output
    retrieved_chunks: List[Dict[str, Any]]  # Serialized PolicyChunk + score
    citations: List[Citation]
    
    # 3. Coverage & Exclusion Agent Output
    rule_evaluations: Dict[str, Any]
    applicable_limits: List[ApplicableLimit]
    is_excluded: bool
    exclusion_reason: Optional[str]
    waiting_period_violated: bool
    waiting_period_reason: Optional[str]
    
    # 4. Decision Agent Output
    decision: str  # ADMISSIBLE, ADMISSIBLE_WITH_LIMITS, PARTIALLY_ADMISSIBLE, NOT_ADMISSIBLE, NEEDS_REVIEW
    confidence: float
    total_claimed: float
    payable_amount: float
    total_deductions: float
    key_findings: List[str]
    missing_evidence: List[str]
    
    # 5. Validation Agent Output
    validation: ValidationResult
    revision_count: int
    
    # Trace steps recorded during execution
    trace: List[TraceStep]
