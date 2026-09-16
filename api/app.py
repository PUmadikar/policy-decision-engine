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

# Global pipeline — lazily initialized on first request.
# ALL heavy ML imports (sentence_transformers/PyTorch, FAISS, LangGraph) are
# deferred inside get_pipeline() so uvicorn can bind the port before any
# heavy computation. This is essential for Render's 512MB free tier.
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        from policy_engine.graph import ClaimDecisionPipeline  # deferred heavy import
        _pipeline = ClaimDecisionPipeline()
    return _pipeline


@app.get("/", tags=["Root"])
def root():
    return {"message": "API is live. Visit /docs for Swagger UI."}


@app.get("/health", tags=["Health"])
def health_check():
    """Lightweight — does NOT trigger pipeline init. Returns immediately."""
    return {
        "status": "HEALTHY",
        "service": "Claim Decision Engine",
        "timestamp": datetime.datetime.now().isoformat()
    }


@app.post("/analyze", tags=["Analysis"])
def analyze_claim_endpoint(claim_input: dict):
    """Analyze a claim. First call triggers cold-start pipeline init (~30-60s)."""
    try:
        from policy_engine.schemas import ClaimCaseInput
        p = get_pipeline()
        response = p.analyze_claim(ClaimCaseInput(**claim_input))
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
