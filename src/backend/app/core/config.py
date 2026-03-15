import os
from pydantic_settings import BaseSettings
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.resolve()

class Settings(BaseSettings):
    LANDING_AI_API_KEY: str
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    OLLAMA_EMBEDDING_MODEL: str = "qwen2.5:latest" 
    
    # Paths relative to project root
    FAISS_INDEX_PATH: str = str(PROJECT_ROOT / "storage" / "faiss_index")
    SPEC_DIR: str = str(PROJECT_ROOT / "storage" / "specs")
    RAW_DOC_DIR: str = str(PROJECT_ROOT / "storage" / "raw_docs")
    LOG_DIR: str = str(PROJECT_ROOT / "storage" / "logs")
    MODELS_DIR: str = str(PROJECT_ROOT / "models" / "ranker_model_cache")
    SQLITE_DB_PATH: str = str(PROJECT_ROOT / "storage" / "sqlite_fts.db")
    
    RERANK_MODEL: str = "rank-T5-flan"

    class Config:
        env_file = ".env"
    
settings = Settings()