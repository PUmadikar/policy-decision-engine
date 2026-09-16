import time
import datetime
from typing import Dict, Any, List
from policy_engine.agents.state import ClaimAgentState
from policy_engine.rag.hybrid_retriever import HybridRetriever
from policy_engine.schemas import Citation, TraceStep

class PolicyEvidenceAgent:
    def __init__(self, hybrid_retriever: HybridRetriever = None):
        self.name = "Policy Evidence Agent"
        self.retriever = hybrid_retriever or HybridRetriever()

    def run(self, state: ClaimAgentState) -> ClaimAgentState:
        start_time = time.time()
        inp = state["input_case"]
        plan = state.get("analysis_plan", {})
        
        diag = inp.treatment.diagnosis
        proc = inp.treatment.procedure or ""
        ttype = inp.treatment.type
        
        # Build targeted RAG queries
        queries = [
            f"Scope of cover hospitalization expenses {diag} {proc} room rent sub-limits doctor fee 25 percent medicines 40 percent",
            f"Exclusions pre-existing diseases 48 months initial 30 days waiting period {diag}",
            f"Day care procedures 140 minimum stay 24 hours waived {proc} {diag}",
            f"Domiciliary hospitalization sub-limit 20 percent 3 days minimum excluded diseases",
            f"Exclusions cosmetic plastic surgery experimental unproven treatment outpatient OPD",
            f"Pre-hospitalization 30 days post-hospitalization 60 days ambulance limit 1000 rupees"
        ]
        
        retrieved_chunks_map = {}
        citations: List[Citation] = []
        
        for q in queries:
            results = self.retriever.retrieve(q, top_k=3)
            for chunk, score in results:
                if chunk.chunk_id not in retrieved_chunks_map:
                    retrieved_chunks_map[chunk.chunk_id] = {
                        "chunk": chunk,
                        "score": score
                    }

        # Format citations
        for cid, item in retrieved_chunks_map.items():
            chunk = item["chunk"]
            citations.append(Citation(
                claim=f"Policy clause from section '{chunk.section}' governing claim evaluation.",
                source="USGIC-CSCIndividualHealthInsurance_2017-2018.pdf",
                page=chunk.page,
                section=chunk.section,
                chunk_id=chunk.chunk_id,
                snippet=chunk.text[:250] + "..."
            ))

        duration_ms = (time.time() - start_time) * 1000.0
        
        trace_step = TraceStep(
            agent=self.name,
            action=f"Executed hybrid RAG search across {len(queries)} targeted queries; retrieved {len(citations)} policy evidence chunks.",
            timestamp=datetime.datetime.now().isoformat(),
            duration_ms=duration_ms,
            metadata={"queries_executed": len(queries), "retrieved_chunks_count": len(citations)}
        )
        
        state["retrieved_chunks"] = [
            {
                "chunk_id": item["chunk"].chunk_id,
                "page": item["chunk"].page,
                "section": item["chunk"].section,
                "sub_section": item["chunk"].sub_section,
                "text": item["chunk"].text,
                "score": item["score"]
            }
            for item in retrieved_chunks_map.values()
        ]
        state["citations"] = citations
        state["trace"].append(trace_step)
        
        return state
