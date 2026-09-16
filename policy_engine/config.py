import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    POLICY_PDF_PATH: str = os.getenv(
        "POLICY_PDF_PATH",
        str(BASE_DIR / "policy" / "USGIC-CSCIndividualHealthInsurance_2017-2018.pdf")
        if (BASE_DIR / "policy" / "USGIC-CSCIndividualHealthInsurance_2017-2018.pdf").exists()
        else str(BASE_DIR / "Aptino_Candidate_Package_FINAL" / "policy" / "USGIC-CSCIndividualHealthInsurance_2017-2018.pdf")
    )
    PUBLIC_CASES_PATH: str = os.getenv(
        "PUBLIC_CASES_PATH",
        str(BASE_DIR / "candidate_data" / "public_test_cases.json")
        if (BASE_DIR / "candidate_data" / "public_test_cases.json").exists()
        else str(BASE_DIR / "Aptino_Candidate_Package_FINAL" / "candidate_data" / "public_test_cases.json")
    )
    CANDIDATE_CASES_PATH: str = os.getenv(
        "CANDIDATE_CASES_PATH",
        str(BASE_DIR / "candidate_data" / "candidate_test_cases.json")
    )
    
    INDEX_DIR: str = os.getenv("INDEX_DIR", str(BASE_DIR / "data" / "index"))
    
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama") # "ollama" or "openai" or "groq"
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3:latest") # or llama3.1:8b
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    
    # Embedding Model
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    
    # Retrieval Hyperparameters
    DENSE_TOP_K: int = 5
    SPARSE_TOP_K: int = 5
    HYBRID_TOP_K: int = 6

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
