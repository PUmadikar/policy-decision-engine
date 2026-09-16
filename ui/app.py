import json
import os
import streamlit as st
from policy_engine.schemas import ClaimCaseInput, ClaimDecisionResponse
from policy_engine.graph import ClaimDecisionPipeline
from policy_engine.config import settings

st.set_page_config(
    page_title="Policy-Aware RAG Claim Decision Engine",
    page_icon="🏥",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0rem; }
    .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
    .badge-admissible { background-color: #059669; color: white; padding: 0.4rem 1rem; border-radius: 6px; font-weight: 600; font-size: 1.2rem; }
    .badge-limits { background-color: #2563EB; color: white; padding: 0.4rem 1rem; border-radius: 6px; font-weight: 600; font-size: 1.2rem; }
    .badge-not-admissible { background-color: #DC2626; color: white; padding: 0.4rem 1rem; border-radius: 6px; font-weight: 600; font-size: 1.2rem; }
    .badge-needs-review { background-color: #D97706; color: white; padding: 0.4rem 1rem; border-radius: 6px; font-weight: 600; font-size: 1.2rem; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_pipeline():
    return ClaimDecisionPipeline()

pipeline = load_pipeline()

# Load Test Cases
PUBLIC_CASES_PATH = settings.PUBLIC_CASES_PATH
CANDIDATE_CASES_PATH = settings.CANDIDATE_CASES_PATH

@st.cache_data
def load_all_test_cases():
    cases_dict = {}
    if os.path.exists(PUBLIC_CASES_PATH):
        with open(PUBLIC_CASES_PATH, "r", encoding="utf-8") as f:
            for c in json.load(f):
                cases_dict[f"[Public] {c['case_id']} - {c['treatment'].get('diagnosis')}"] = c
    if os.path.exists(CANDIDATE_CASES_PATH):
        with open(CANDIDATE_CASES_PATH, "r", encoding="utf-8") as f:
            for c in json.load(f):
                cases_dict[f"[Candidate] {c['case_id']} - {c['treatment'].get('diagnosis')}"] = c
    return cases_dict

cases = load_all_test_cases()

st.markdown('<p class="main-header">🏥 Policy-Aware Multi-Agent RAG Claim Decision Engine</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Universal Sompo Health Insurance Policy Decisioning System (LangGraph + FAISS + BM25 + Llama 3)</p>', unsafe_allow_html=True)

# Sidebar - Case Selection
st.sidebar.header("📋 Claim Case Selection")
case_choice = st.sidebar.selectbox("Select Test Case", list(cases.keys()))
selected_case_data = cases[case_choice]

st.sidebar.markdown("---")
st.sidebar.markdown("### ✏️ Edit or Upload Custom Case JSON")
raw_json = st.sidebar.text_area(
    "Case Payload JSON",
    value=json.dumps(selected_case_data, indent=2),
    height=300
)

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📝 Claim Input Details")
    try:
        case_input_dict = json.loads(raw_json)
        inp_model = ClaimCaseInput(**case_input_dict)
        
        st.info(f"**Case ID:** {inp_model.case_id} | **Policy ID:** {inp_model.policy_id}")
        st.write(f"**Policy Start Date:** `{inp_model.policy_start_date}` | **Claim Date:** `{inp_model.claim_date}`")
        st.write(f"**Continuous Coverage:** `{inp_model.continuous_coverage_months}` months (Prior: `{inp_model.prior_insurer_continuous_years}` yrs)")
        st.write(f"**Sum Insured:** `INR {inp_model.sum_insured_inr:,.2f}`")
        
        st.markdown("#### Treatment Information")
        st.write(f"- **Diagnosis:** {inp_model.treatment.diagnosis}")
        st.write(f"- **Procedure:** {inp_model.treatment.procedure}")
        st.write(f"- **Type & Admission:** `{inp_model.treatment.type}` ({inp_model.treatment.admission_hours} hrs)")
        st.write(f"- **Pre-existing:** `{inp_model.treatment.pre_existing}` | **Experimental:** `{inp_model.treatment.experimental}`")
        
        st.markdown("#### Claimed Expenses (INR)")
        exp = inp_model.expenses_inr
        st.json({
            "Room Rent": exp.room,
            "Doctor/Surgeon Fees": exp.doctor_fees,
            "Medicines/Diagnostics": exp.medicines_diagnostics,
            "Pre-Hospitalization": exp.pre_hospitalization,
            "Post-Hospitalization": exp.post_hospitalization,
            "Ambulance": exp.ambulance,
            "TOTAL CLAIMED": sum([exp.room, exp.doctor_fees, exp.medicines_diagnostics, exp.pre_hospitalization, exp.post_hospitalization, exp.ambulance])
        })
        
        st.write(f"**Documents Provided:** `{', '.join(inp_model.documents)}`")
        if inp_model.task:
            st.caption(f"**Task Note:** {inp_model.task}")

    except Exception as e:
        st.error(f"Invalid JSON Input: {e}")

with col2:
    st.subheader("⚡ Automated Decision Engine")
    if st.button("🔍 Run Multi-Agent Claim Decision", type="primary", use_container_width=True):
        with st.spinner("Executing LangGraph Multi-Agent RAG Workflow..."):
            try:
                response: ClaimDecisionResponse = pipeline.analyze_claim(inp_model)
                st.session_state["latest_response"] = response
            except Exception as ex:
                st.error(f"Analysis failed: {ex}")

    if "latest_response" in st.session_state:
        res: ClaimDecisionResponse = st.session_state["latest_response"]
        
        # Display Decision Badge
        dec = res.decision
        if dec == "ADMISSIBLE":
            st.markdown(f'### Status: <span class="badge-admissible">✅ {dec}</span>', unsafe_allow_html=True)
        elif dec == "ADMISSIBLE_WITH_LIMITS":
            st.markdown(f'### Status: <span class="badge-limits">⚖️ {dec}</span>', unsafe_allow_html=True)
        elif dec == "NOT_ADMISSIBLE":
            st.markdown(f'### Status: <span class="badge-not-admissible">❌ {dec}</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'### Status: <span class="badge-needs-review">⚠️ {dec} (ABSTAIN)</span>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Display Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Confidence", f"{res.confidence * 100:.0f}%")
        m2.metric("Total Claimed", f"₹{res.total_claimed_inr:,.0f}")
        m3.metric("Payable Amount", f"₹{res.payable_amount_inr:,.0f}")
        m4.metric("Deductions", f"₹{res.total_deductions_inr:,.0f}")
        
        st.markdown("---")

        # Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📌 Key Findings",
            "📊 Limits & Deductions",
            "⚠️ Missing Evidence",
            "📖 Policy Citations",
            "🔍 Execution Trace"
        ])
        
        with tab1:
            st.markdown("#### Key Decision Findings")
            for finding in res.key_findings:
                st.write(f"- {finding}")
                
        with tab2:
            st.markdown("#### Applicable Limits & Deductions")
            if res.applicable_limits:
                limit_table = []
                for lim in res.applicable_limits:
                    limit_table.append({
                        "Category": lim.category,
                        "Claimed (INR)": f"₹{lim.claimed_amount:,.2f}",
                        "Allowed (INR)": f"₹{lim.allowed_amount:,.2f}",
                        "Deduction (INR)": f"₹{lim.deduction_amount:,.2f}",
                        "Clause Reference": lim.clause_reference
                    })
                st.table(limit_table)
            else:
                st.info("No policy sub-limit deductions were applied.")

        with tab3:
            st.markdown("#### Missing Evidence & Abstention Signals")
            if res.missing_evidence:
                st.warning("The system abstained from making a final decision because the following evidence is unestablished:")
                for me in res.missing_evidence:
                    st.write(f"- 🚩 {me}")
            else:
                st.success("All required evidence and document criteria are established.")

        with tab4:
            st.markdown("#### Traceable Policy Citations")
            for idx, cite in enumerate(res.citations):
                with st.expander(f"Citation {idx+1}: Page {cite.page} | Section: {cite.section} ({cite.chunk_id})"):
                    st.write(f"**Policy Source:** `{cite.source}` (Page {cite.page})")
                    st.write(f"**Section Heading:** `{cite.section}`")
                    st.caption(f"**Excerpt:**\n{cite.snippet}")

        with tab5:
            st.markdown("#### Genuine Multi-Agent Execution Trace")
            for step in res.trace:
                st.markdown(f"**[{step.agent}]** `{step.timestamp}` (Duration: `{step.duration_ms:.1f} ms`)")
                st.write(f"└─ *Action:* {step.action}")
                if step.metadata:
                    st.json(step.metadata)
                st.markdown("---")
