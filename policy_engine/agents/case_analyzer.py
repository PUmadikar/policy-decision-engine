import time
import datetime
from typing import Dict, Any, List
from policy_engine.agents.state import ClaimAgentState
from policy_engine.schemas import TraceStep

class CaseAnalysisAgent:
    def __init__(self):
        self.name = "Case Analysis Agent"

    def run(self, state: ClaimAgentState) -> ClaimAgentState:
        start_time = time.time()
        inp = state["input_case"]
        
        dimensions = [
            "waiting_period_dimension",
            "coverage_scope_dimension",
            "sub_limits_dimension",
            "pre_post_window_dimension",
            "evidence_sufficiency_dimension"
        ]
        
        missing_fields = []
        doc_list = inp.documents or []
        
        # Check required documents
        if "discharge_summary" not in doc_list and inp.treatment.type == "inpatient":
            missing_fields.append("discharge_summary")
        if "itemized_bill" not in doc_list:
            missing_fields.append("itemized_bill")
            
        # Check evidence context if present
        ctx = inp.evidence_context or {}
        if ctx.get("hospital_registered") is None and ctx.get("hospital_minimum_criteria_documented") is False:
            missing_fields.append("hospital_minimum_criteria_proof")
        if ctx.get("discharge_summary_present") is False:
            if "discharge_summary" not in missing_fields:
                missing_fields.append("discharge_summary")
        if ctx.get("treating_doctor_prescription_present") is False:
            missing_fields.append("treating_doctor_prescription")
            
        analysis_plan = {
            "case_id": inp.case_id,
            "diagnosis": inp.treatment.diagnosis,
            "procedure": inp.treatment.procedure,
            "treatment_type": inp.treatment.type,
            "admission_hours": inp.treatment.admission_hours,
            "continuous_coverage_months": inp.continuous_coverage_months,
            "prior_insurer_continuous_years": inp.prior_insurer_continuous_years,
            "effective_coverage_months": inp.continuous_coverage_months + (inp.prior_insurer_continuous_years * 12),
            "pre_existing": inp.treatment.pre_existing,
            "experimental": inp.treatment.experimental,
            "sum_insured_inr": inp.sum_insured_inr,
            "missing_fields": missing_fields
        }

        duration_ms = (time.time() - start_time) * 1000.0
        
        trace_step = TraceStep(
            agent=self.name,
            action="Extracted claim facts, created 5-dimensional investigation plan, and audited document completeness.",
            timestamp=datetime.datetime.now().isoformat(),
            duration_ms=duration_ms,
            metadata={"decision_dimensions": dimensions, "missing_input_fields": missing_fields}
        )
        
        state["analysis_plan"] = analysis_plan
        state["decision_dimensions"] = dimensions
        state["missing_input_fields"] = missing_fields
        if "trace" not in state or state["trace"] is None:
            state["trace"] = []
        state["trace"].append(trace_step)
        
        return state
