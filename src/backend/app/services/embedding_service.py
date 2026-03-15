import logging
from core.config import settings
from langchain_ollama import OllamaEmbeddings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        try:
            self.embeddings = OllamaEmbeddings(
                model=settings.OLLAMA_EMBEDDING_MODEL,
                validate_model_on_init=True,
            )
        except Exception as e:
            logger.error(f"Lỗi khởi tạo Ollama Embeddings: {str(e)}")
            raise e
    
    def get_model(self):
        return self.embeddings
    
    def embed_query(self, text: str):
        """Dùng để chuyển câu hỏi của User thành vector (dùng khi Search)"""
        return self.embeddings.embed_query(text)

    def embed_documents(self, texts: list[str]):
        """Dùng để chuyển danh sách các chunk thành danh sách vector (dùng khi Indexing)"""
        return self.embeddings.embed_documents(texts)