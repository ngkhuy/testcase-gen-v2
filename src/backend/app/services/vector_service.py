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
    
    def clear_all_data(self):
        """
        Xóa sổ toàn bộ index: cả trên RAM lẫn ổ cứng (Flush)
        """
        try:
            # 1. Reset biến trên RAM
            self.vector_db = None
            
            # 2. Xóa thư mục lưu trữ trên ổ cứng
            if os.path.exists(self.index_path):
                shutil.rmtree(self.index_path)
                logger.info(f"Đã xóa sạch toàn bộ dữ liệu tại {self.index_path}")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi clear index: {str(e)}")
            return False

    def delete_by_source(self, source_name: str):
        if not self.vector_db:
            logger.warning("Không có index để xóa.")
            return False

        try:
            dict_index = self.vector_db.docstore._dict
            ids_to_delete = [
                obj_id for obj_id, doc in dict_index.items() 
                if doc.metadata.get("source") == source_name
            ]

            if ids_to_delete:
                self.vector_db.delete(ids_to_delete)
                self.save_vector_db(self.vector_db) # Lưu lại sau khi xóa
                logger.info(f"Đã xóa {len(ids_to_delete)} chunks từ nguồn: {source_name}")
                return True
            else:
                logger.warning(f"Không tìm thấy dữ liệu nào từ nguồn: {source_name}")
                return False
        except Exception as e:
            logger.error(f"Lỗi khi xóa vector theo source: {str(e)}")
            return False