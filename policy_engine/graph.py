import time
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from policy_engine.schemas import ClaimCaseInput, ClaimDecisionResponse, ValidationResult
from policy_engine.agents.state import ClaimAgentState
from policy_engine.agents.case_analyzer import CaseAnalysisAgent
from policy_engine.agents.evidence_retriever import PolicyEvidenceAgent
from policy_engine.agents.coverage_evaluator import CoverageEvaluatorAgent
from policy_engine.agents.decision_maker import DecisionMakerAgent
from policy_engine.agents.validator import ValidationAgent
from policy_engine.rag.hybrid_retriever import HybridRetriever

class ClaimDecisionPipeline:
    def __init__(self, hybrid_retriever: HybridRetriever = None):
        self.retriever = hybrid_retriever or HybridRetriever()
        
        self.case_analyzer = CaseAnalysisAgent()
        self.evidence_retriever = PolicyEvidenceAgent(self.retriever)
        self.coverage_evaluator = CoverageEvaluatorAgent()
        self.decision_maker = DecisionMakerAgent()
        self.validator = ValidationAgent()
        
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(ClaimAgentState)
        
        # Add nodes for each specialized agent
        builder.add_node("case_analyzer", self.case_analyzer.run)
        builder.add_node("evidence_retriever", self.evidence_retriever.run)
        builder.add_node("coverage_evaluator", self.coverage_evaluator.run)
        builder.add_node("decision_maker", self.decision_maker.run)
        builder.add_node("validator", self.validator.run)
        
        # Define sequential workflow edges
        builder.set_entry_point("case_analyzer")
        builder.add_edge("case_analyzer", "evidence_retriever")
        builder.add_edge("evidence_retriever", "coverage_evaluator")
        builder.add_edge("coverage_evaluator", "decision_maker")
        builder.add_edge("decision_maker", "validator")
        
        # Conditional edge: If Validation fails, retry/revise decision maker, else END
        def check_validation(state: ClaimAgentState) -> str:
            val: ValidationResult = state.get("validation")
            rev_count = state.get("revision_count", 0)
            if val and val.status == "FAIL" and rev_count < 1:
                state["revision_count"] = rev_count + 1
                return "decision_maker"
            return END

        builder.add_conditional_edges("validator", check_validation, {
            "decision_maker": "decision_maker",
            END: END
        })

        return builder.compile()

    def analyze_claim(self, claim_input: ClaimCaseInput) -> ClaimDecisionResponse:
        initial_state: ClaimAgentState = {
            "input_case": claim_input,
            "analysis_plan": {},
            "decision_dimensions": [],
            "missing_input_fields": [],
            "retrieved_chunks": [],
            "citations": [],
            "rule_evaluations": {},
            "applicable_limits": [],
            "is_excluded": False,
            "exclusion_reason": None,
            "waiting_period_violated": False,
            "waiting_period_reason": None,
            "decision": "NEEDS_REVIEW",
            "confidence": 0.0,
            "total_claimed": 0.0,
            "payable_amount": 0.0,
            "total_deductions": 0.0,
            "key_findings": [],
            "missing_evidence": [],
            "validation": ValidationResult(status="PASS", unsupported_claims=[]),
            "revision_count": 0,
            "trace": []
        }

        final_state = self.graph.invoke(initial_state)

        return ClaimDecisionResponse(
            case_id=claim_input.case_id,
            decision=final_state["decision"],
            confidence=final_state["confidence"],
            total_claimed_inr=final_state["total_claimed"],
            payable_amount_inr=final_state["payable_amount"],
            total_deductions_inr=final_state["total_deductions"],
            key_findings=final_state["key_findings"],
            applicable_limits=final_state["applicable_limits"],
            missing_evidence=final_state["missing_evidence"],
            citations=final_state["citations"],
            validation=final_state["validation"],
            trace=final_state["trace"]
        )

if __name__ == "__main__":
    from policy_engine.schemas import TreatmentInfo, ClaimExpenses
    pipeline = ClaimDecisionPipeline()
    test_case = ClaimCaseInput(
        case_id="TEST-001",
        policy_start_date="2025-01-01",
        claim_date="2026-03-14",
        sum_insured_inr=500000,
        continuous_coverage_months=14,
        treatment=TreatmentInfo(
            type="inpatient",
            admission_hours=96,
            diagnosis="Acute appendicitis",
            procedure="Appendectomy"
        ),
        expenses_inr=ClaimExpenses(
            room=30000,
            doctor_fees=30000,
            medicines_diagnostics=90000,
            pre_hospitalization=5000,
            post_hospitalization=7000,
            ambulance=1200
        ),
        documents=["claim_form", "discharge_summary", "itemized_bill", "doctor_prescription"]
    )
    res = pipeline.analyze_claim(test_case)
    print(f"Decision: {res.decision} | Payable: INR {res.payable_amount_inr:,.2f} | Confidence: {res.confidence}")
    print("Trace steps:", len(res.trace))
