from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PatientInfo(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None

class HospitalInfo(BaseModel):
    name: Optional[str] = None
    network_provider: Optional[bool] = None

class TreatmentInfo(BaseModel):
    type: str = "inpatient"  # inpatient, day_care, domiciliary
    admission_hours: Optional[float] = 0.0
    diagnosis: str
    procedure: Optional[str] = ""
    pre_existing: bool = False
    experimental: bool = False

class ClaimExpenses(BaseModel):
    room: float = 0.0
    doctor_fees: float = 0.0
    medicines_diagnostics: float = 0.0
    pre_hospitalization: float = 0.0
    post_hospitalization: float = 0.0
    ambulance: float = 0.0

class ClaimCaseInput(BaseModel):
    case_id: str
    policy_id: str = "USGIC-CSC-2017-2018"
    policy_start_date: str
    claim_date: str
    sum_insured_inr: float
    continuous_coverage_months: int = 0
    prior_insurer_continuous_years: int = 0
    patient: Optional[PatientInfo] = None
    hospital: Optional[HospitalInfo] = None
    treatment: TreatmentInfo
    expenses_inr: ClaimExpenses
    documents: List[str] = []
    evidence_context: Optional[Dict[str, Any]] = None
    expense_timing: Optional[Dict[str, Any]] = None
    task: Optional[str] = ""

class Citation(BaseModel):
    claim: str = Field(..., description="Statement supported by policy")
    source: str = "USGIC-CSCIndividualHealthInsurance_2017-2018.pdf"
    page: int = Field(..., description="Page number in policy document")
    section: str = Field(..., description="Policy section/heading name")
    chunk_id: str = Field(..., description="Chunk identifier")
    snippet: Optional[str] = None

class ValidationResult(BaseModel):
    status: str = "PASS"  # PASS or FAIL
    unsupported_claims: List[str] = []
    revision_reason: Optional[str] = None

class TraceStep(BaseModel):
    agent: str
    action: str
    timestamp: str
    duration_ms: float
    metadata: Optional[Dict[str, Any]] = None

class ApplicableLimit(BaseModel):
    category: str
    claimed_amount: float
    allowed_amount: float
    deduction_amount: float
    clause_reference: str

class ClaimDecisionResponse(BaseModel):
    case_id: str
    decision: str = Field(
        ...,
        description="ADMISSIBLE, ADMISSIBLE_WITH_LIMITS, PARTIALLY_ADMISSIBLE, NOT_ADMISSIBLE, or NEEDS_REVIEW"
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    total_claimed_inr: float = 0.0
    payable_amount_inr: float = 0.0
    total_deductions_inr: float = 0.0
    key_findings: List[str] = []
    applicable_limits: List[ApplicableLimit] = []
    missing_evidence: List[str] = []
    citations: List[Citation] = []
    validation: ValidationResult
    trace: List[TraceStep] = []
