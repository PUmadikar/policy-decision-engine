import time
import datetime
from typing import Dict, Any, List
from policy_engine.agents.state import ClaimAgentState
from policy_engine.schemas import TraceStep

class DecisionMakerAgent:
    def __init__(self):
        self.name = "Decision Agent"

    def run(self, state: ClaimAgentState) -> ClaimAgentState:
        start_time = time.time()
        inp = state["input_case"]
        missing_fields = state.get("missing_input_fields", [])
        is_excluded = state.get("is_excluded", False)
        ex_reason = state.get("exclusion_reason")
        wp_violated = state.get("waiting_period_violated", False)
        wp_reason = state.get("waiting_period_reason")
        limits = state.get("applicable_limits", [])

        # Calculate Total Claimed
        exp = inp.expenses_inr
        total_claimed = (
            exp.room +
            exp.doctor_fees +
            exp.medicines_diagnostics +
            exp.pre_hospitalization +
            exp.post_hospitalization +
            exp.ambulance
        )

        total_deductions = sum(limit.deduction_amount for limit in limits)
        key_findings = []
        missing_evidence = []

        # 1. ABSTENTION CHECK (NEEDS_REVIEW)
        if missing_fields:
            decision = "NEEDS_REVIEW"
            confidence = 0.50
            payable_amount = 0.0
            for mf in missing_fields:
                missing_evidence.append(f"Missing required evidence/proof: {mf.replace('_', ' ').title()}")
            key_findings.append(
                f"System abstained with NEEDS_REVIEW because essential claim evidence is missing ({', '.join(missing_fields)})."
            )

        # 2. NOT_ADMISSIBLE CHECK
        elif is_excluded or wp_violated:
            decision = "NOT_ADMISSIBLE"
            confidence = 0.95
            payable_amount = 0.0
            total_deductions = total_claimed
            if is_excluded:
                key_findings.append(f"Claim is NOT ADMISSIBLE: {ex_reason}")
            if wp_violated:
                key_findings.append(f"Claim is NOT ADMISSIBLE: {wp_reason}")

        # 3. ADMISSIBLE WITH LIMITS CHECK
        elif total_deductions > 0:
            decision = "ADMISSIBLE_WITH_LIMITS"
            confidence = 0.90
            payable_amount = max(0.0, total_claimed - total_deductions)
            key_findings.append(
                f"Claim is ADMISSIBLE WITH LIMITS. Total claimed INR {total_claimed:,.2f}, payable INR {payable_amount:,.2f} after INR {total_deductions:,.2f} in policy limit deductions."
            )
            for limit in limits:
                key_findings.append(
                    f"Deduction under '{limit.category}': Claimed INR {limit.claimed_amount:,.2f}, Allowed INR {limit.allowed_amount:,.2f} (Deduction: INR {limit.deduction_amount:,.2f}). Clause: {limit.clause_reference}"
                )

        # 4. FULLY ADMISSIBLE CHECK
        else:
            decision = "ADMISSIBLE"
            confidence = 0.95
            payable_amount = total_claimed
            key_findings.append(
                f"Claim is fully ADMISSIBLE. Total claimed INR {total_claimed:,.2f} is payable in full with no deductions."
            )

        duration_ms = (time.time() - start_time) * 1000.0
        
        trace_step = TraceStep(
            agent=self.name,
            action=f"Synthesized specialist findings. Final Decision: {decision}, Confidence: {confidence:.2f}, Payable: INR {payable_amount:,.2f}.",
            timestamp=datetime.datetime.now().isoformat(),
            duration_ms=duration_ms,
            metadata={
                "decision": decision,
                "confidence": confidence,
                "total_claimed": total_claimed,
                "payable_amount": payable_amount,
                "total_deductions": total_deductions
            }
        )
        
        state["decision"] = decision
        state["confidence"] = confidence
        state["total_claimed"] = total_claimed
        state["payable_amount"] = payable_amount
        state["total_deductions"] = total_deductions
        state["key_findings"] = key_findings
        state["missing_evidence"] = missing_evidence
        state["trace"].append(trace_step)
        
        return state
