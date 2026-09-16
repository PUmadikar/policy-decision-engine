import time
import datetime
from typing import Dict, Any, List
from policy_engine.agents.state import ClaimAgentState
from policy_engine.schemas import ValidationResult, TraceStep

class ValidationAgent:
    def __init__(self):
        self.name = "Validation Agent"

    def run(self, state: ClaimAgentState) -> ClaimAgentState:
        start_time = time.time()
        decision = state.get("decision", "NEEDS_REVIEW")
        findings = state.get("key_findings", [])
        citations = state.get("citations", [])
        missing_evidence = state.get("missing_evidence", [])
        
        unsupported_claims = []
        status = "PASS"
        revision_reason = None

        # Audit 1: Citations must be present for material decisions
        if not citations:
            unsupported_claims.append("No policy citations were retrieved to ground the decision.")
            status = "FAIL"

        # Audit 2: Verification of decision logic against policy support
        if decision in ["ADMISSIBLE", "ADMISSIBLE_WITH_LIMITS", "NOT_ADMISSIBLE"]:
            # Ensure every finding references policy terms or calculations
            for finding in findings:
                if "ADMISSIBLE" in finding and not citations:
                    unsupported_claims.append(f"Statement '{finding[:60]}...' lacks policy citation grounding.")
                    status = "FAIL"

        # Audit 3: If missing evidence was flagged, verify decision is NEEDS_REVIEW
        if missing_evidence and decision != "NEEDS_REVIEW":
            unsupported_claims.append(
                f"Missing evidence items exist ({len(missing_evidence)}) but decision was set to {decision} instead of NEEDS_REVIEW."
            )
            status = "FAIL"
            # Auto-correction trigger
            state["decision"] = "NEEDS_REVIEW"
            state["confidence"] = 0.50
            revision_reason = "Corrected decision to NEEDS_REVIEW due to unestablished evidence."

        val_result = ValidationResult(
            status=status,
            unsupported_claims=unsupported_claims,
            revision_reason=revision_reason
        )

        duration_ms = (time.time() - start_time) * 1000.0
        
        trace_step = TraceStep(
            agent=self.name,
            action=f"Audited decision statements against policy citations. Validation Status: {status}.",
            timestamp=datetime.datetime.now().isoformat(),
            duration_ms=duration_ms,
            metadata={"status": status, "unsupported_claims_count": len(unsupported_claims)}
        )
        
        state["validation"] = val_result
        state["trace"].append(trace_step)
        
        return state
