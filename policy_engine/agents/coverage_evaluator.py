import time
import datetime
from typing import Dict, Any, List
from policy_engine.agents.state import ClaimAgentState
from policy_engine.schemas import ApplicableLimit, TraceStep

class CoverageEvaluatorAgent:
    def __init__(self):
        self.name = "Coverage & Exclusion Agent"

    def run(self, state: ClaimAgentState) -> ClaimAgentState:
        start_time = time.time()
        inp = state["input_case"]
        plan = state.get("analysis_plan", {})
        
        diag = inp.treatment.diagnosis.lower()
        proc = (inp.treatment.procedure or "").lower()
        ttype = inp.treatment.type.lower()
        adm_hours = inp.treatment.admission_hours or 0.0
        eff_months = plan.get("effective_coverage_months", 0)
        si = inp.sum_insured_inr
        exp = inp.expenses_inr
        
        is_excluded = False
        exclusion_reason = None
        waiting_period_violated = False
        waiting_period_reason = None
        applicable_limits: List[ApplicableLimit] = []

        # --- 1. EXCLUSIONS EVALUATION ---
        if "cosmetic" in diag or "cosmetic" in proc or "plastic surgery" in proc:
            is_excluded = True
            exclusion_reason = "Excluded under Policy Exclusion 5 (Cosmetic or Plastic Surgery)."
            
        elif inp.treatment.experimental or "experimental" in diag or "experimental" in proc or "unproven" in proc or "stem cell" in proc:
            is_excluded = True
            exclusion_reason = "Excluded under Policy Exclusion 14 (Experimental, unproven, or non-IMC approved treatments)."

        # --- 2. WAITING PERIOD EVALUATION ---
        elif inp.continuous_coverage_months == 0 and eff_months < 1 and "accident" not in diag:
            waiting_period_violated = True
            waiting_period_reason = "Claim falls within the initial 30-day waiting period from policy inception (Exclusion 2)."
            
        elif ("cataract" in diag or "cataract" in proc) and eff_months < 12:
            waiting_period_violated = True
            waiting_period_reason = "Cataract treatment requires 12 months of continuous coverage (Exclusion 3)."
            
        elif inp.treatment.pre_existing and eff_months < 48:
            waiting_period_violated = True
            waiting_period_reason = f"Pre-existing condition '{inp.treatment.diagnosis}' requires 48 months of continuous coverage (Exclusion 1). Current continuous coverage: {eff_months} months."

        # --- 3. DOMICILIARY TREATMENT EVALUATION ---
        if ttype == "domiciliary":
            # Domiciliary duration check (only if explicitly specified > 0 and < 72 hrs)
            dom_duration = (inp.evidence_context or {}).get("domiciliary_duration_days")
            if (adm_hours > 0 and adm_hours < 72) or (dom_duration is not None and dom_duration < 3):
                is_excluded = True
                exclusion_reason = "Domiciliary treatment not exceeding 3 days (72 hours) is excluded under Exclusion 19."
            elif any(c in diag for c in ["hypertension", "diabetes", "asthma", "bronchitis", "psychiatric", "tonsillitis"]):
                is_excluded = True
                exclusion_reason = f"Domiciliary treatment for '{inp.treatment.diagnosis}' is specifically excluded under Exclusion 20."
            else:
                # Sub-limit cap: 20% of Basic Sum Insured
                dom_cap = 0.20 * si
                total_dom_claimed = exp.doctor_fees + exp.medicines_diagnostics
                if total_dom_claimed > dom_cap:
                    applicable_limits.append(ApplicableLimit(
                        category="Domiciliary Hospitalization Sub-limit",
                        claimed_amount=total_dom_claimed,
                        allowed_amount=dom_cap,
                        deduction_amount=total_dom_claimed - dom_cap,
                        clause_reference="Scope of Cover NB2: Domiciliary hospitalization capped at 20% of Basic Sum Insured."
                    ))

        # --- 4. SUB-LIMITS & DEDUCTIONS EVALUATION (If Admissible) ---
        if not is_excluded and not waiting_period_violated and ttype != "domiciliary":
            days = max(1.0, round(adm_hours / 24.0)) if adm_hours > 0 else 1.0
            
            # A. Room Rent Cap (1% SI/day)
            room_cap_per_day = 0.01 * si
            total_room_cap = room_cap_per_day * days
            if exp.room > total_room_cap:
                applicable_limits.append(ApplicableLimit(
                    category="Room Rent Sub-limit (1% SI/day)",
                    claimed_amount=exp.room,
                    allowed_amount=total_room_cap,
                    deduction_amount=exp.room - total_room_cap,
                    clause_reference="Scope of Cover 1(a): Normal Room expenses capped at 1.0% of Basic Sum Insured per day."
                ))

            # B. Doctor / Consultant / Surgeon Fees Cap (25% SI)
            doc_cap = 0.25 * si
            if exp.doctor_fees > doc_cap:
                applicable_limits.append(ApplicableLimit(
                    category="Medical Practitioner / Surgeon Fees Sub-limit (25% SI)",
                    claimed_amount=exp.doctor_fees,
                    allowed_amount=doc_cap,
                    deduction_amount=exp.doctor_fees - doc_cap,
                    clause_reference="Scope of Cover 2: Medical Practitioner/Surgeon fees capped at 25% of Sum Insured."
                ))

            # C. OT / Medicines / Diagnostics Cap (40% SI)
            med_cap = 0.40 * si
            if exp.medicines_diagnostics > med_cap:
                applicable_limits.append(ApplicableLimit(
                    category="Medicines, Diagnostics, OT Sub-limit (40% SI)",
                    claimed_amount=exp.medicines_diagnostics,
                    allowed_amount=med_cap,
                    deduction_amount=exp.medicines_diagnostics - med_cap,
                    clause_reference="Scope of Cover 3: Medicines, Diagnostics, OT, Anesthesia capped at 40% of Sum Insured."
                ))

            # D. Ambulance Cap (1% SI or Rs 1,000 max)
            amb_cap = min(0.01 * si, 1000.0)
            if exp.ambulance > amb_cap:
                applicable_limits.append(ApplicableLimit(
                    category="Ambulance Charges Sub-limit",
                    claimed_amount=exp.ambulance,
                    allowed_amount=amb_cap,
                    deduction_amount=exp.ambulance - amb_cap,
                    clause_reference="Scope of Cover 4(b): Ambulance charges capped at 1.0% of Sum Insured or Rs. 1,000 max."
                ))

        rule_evaluations = {
            "is_excluded": is_excluded,
            "exclusion_reason": exclusion_reason,
            "waiting_period_violated": waiting_period_violated,
            "waiting_period_reason": waiting_period_reason,
            "limits_count": len(applicable_limits)
        }

        duration_ms = (time.time() - start_time) * 1000.0
        
        trace_step = TraceStep(
            agent=self.name,
            action=f"Evaluated policy rules. Excluded: {is_excluded}, Waiting Period Violated: {waiting_period_violated}, Limits Applied: {len(applicable_limits)}.",
            timestamp=datetime.datetime.now().isoformat(),
            duration_ms=duration_ms,
            metadata=rule_evaluations
        )
        
        state["rule_evaluations"] = rule_evaluations
        state["applicable_limits"] = applicable_limits
        state["is_excluded"] = is_excluded
        state["exclusion_reason"] = exclusion_reason
        state["waiting_period_violated"] = waiting_period_violated
        state["waiting_period_reason"] = waiting_period_reason
        state["trace"].append(trace_step)
        
        return state
