import os
import sys
import time
import datetime
from pathlib import Path

# Add project root directory to sys.path for cloud deployment and subfolder execution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from policy_engine.schemas import ClaimCaseInput, ClaimDecisionResponse
from policy_engine.graph import ClaimDecisionPipeline
from policy_engine.config import settings

app = FastAPI(
    title="Policy-Aware RAG Claim Decision Engine API",
    description="Multi-agent RAG system for health insurance claim decisions using LangGraph, FAISS, BM25, and Llama 3.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance - lazily initialized on first request to reduce startup RAM usage
pipeline: ClaimDecisionPipeline = None

def get_pipeline() -> ClaimDecisionPipeline:
    global pipeline
    if pipeline is None:
        pipeline = ClaimDecisionPipeline()
    return pipeline

@app.get("/health", tags=["Health"])
def health_check():
    p = get_pipeline()
    return {
        "status": "HEALTHY",
        "service": "Claim Decision Engine",
        "llm_provider": settings.LLM_PROVIDER,
        "policy_chunks": len(p.retriever.chunks) if p else 0,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.post("/analyze", response_model=ClaimDecisionResponse, tags=["Analysis"])
def analyze_claim_endpoint(claim_input: ClaimCaseInput):
    try:
        p = get_pipeline()
        response = p.analyze_claim(claim_input)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing claim decision: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
