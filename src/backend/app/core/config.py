from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LANDING_AI_API_KEY: str
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    FAISS_INDEX_PATH: str = "storage/faiss_index"

    class Config:
        env_file = ".env"
    
settings = Settings()