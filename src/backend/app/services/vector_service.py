class VectorService:
    def __init__(self, embedding_service: EmbeddingService):
        self.embed_model = embedding_service.get_model()
        self.index_path = "storage/faiss_index"
        self.vector_db = self.load_vector_db()

    def create_vector_db(self, chunks: list):
        try:
            logger.info(f"Tạo vector DB với {len(chunks)} chunks")
            vector_db = FAISS.from_documents(chunks, self.embed_model)
            return vector_db
        except Exception as e:
            logger.error(f"Lỗi khi tạo Vector DB: {str(e)}")
            return None

    def save_vector_db(self, vector_db):
        if not os.path.exists(self.index_path):
            os.makedirs(self.index_path, exist_ok=True)

        vector_db.save_local(str(self.index_path))
        logger.info(f"Lưu index tại {self.index_path}")
        self.vector_db = vector_db

    def load_vector_db(self):
        """Load FAISS index từ ổ cứng lên RAM để tìm kiếm"""
        try:
            if os.path.exists(os.path.join(self.index_path, "index.faiss")):
                return FAISS.load_local(
                    str(self.index_path), 
                    self.embed_model,
                    allow_dangerous_deserialization=True # Cần thiết cho FAISS
                )
            logger.warning("Không tìm thấy file FAISS index để load.")
            return None
        except Exception as e:
            logger.error(f"Lỗi khi load Vector DB: {str(e)}")
            return None

    def search(self, query: str, k: int = 4):
        """Tìm kiếm các đoạn văn bản liên quan nhất"""
        if self.vector_db:
            return self.vector_db.similarity_search(query, k=k)
        return []