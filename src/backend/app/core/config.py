from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LANDING_AI_API_KEY: str
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "qwen3.5:4b"
    OLLAMA_EMBEDDING_MODEL: str = "qwen3-embedding:0.6b"
    FAISS_INDEX_PATH: str = "storage/faiss_index"
    SPEC_DIR: str = "storage/specs"
    RAW_DOC_DIR: str = "raw_doc"

    class Config:
        env_file = ".env"
    
settings = Settings()