import time
import datetime
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

# Global pipeline instance initialized on startup
pipeline: ClaimDecisionPipeline = None

@app.on_event("startup")
def startup_event():
    global pipeline
    pipeline = ClaimDecisionPipeline()

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "HEALTHY",
        "service": "Claim Decision Engine",
        "llm_provider": settings.LLM_PROVIDER,
        "policy_chunks": len(pipeline.retriever.chunks) if pipeline else 0,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.post("/analyze", response_model=ClaimDecisionResponse, tags=["Analysis"])
def analyze_claim_endpoint(claim_input: ClaimCaseInput):
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Claim decision pipeline is not initialized."
        )
    try:
        response = pipeline.analyze_claim(claim_input)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing claim decision: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
