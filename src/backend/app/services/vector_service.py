import os
import shutil
import logging
from uuid import uuid4
from langchain_classic.vectorstores import FAISS
from langchain_core.documents import Document
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self, embedding_service: EmbeddingService):
        self.embed_model = embedding_service.get_model()
        self.index_path = "storage/faiss_index"
        self.vector_db = self.load_vector_db()
        
    def create_vector_db(self, documents: list[Document]):
        """
        Tạo mới vector database 
        """
        try:
            logger.info(f"Tạo vector database mới với {len(documents)} tài liệu")
            
            uuids = [str(uuid4()) for _ in documents]
            self.vector_db = FAISS.from_documents(
                documents=documents,
                embedding=self.embed_model,
                ids=uuids
            )
            
            # lưu vào persist storage
            self.save_vector_db()
            
            return self.vector_db
        except Exception as e:
            logger.error(f"Lỗi khi tao vector database: {e}")
            return None
        
    def add_documents(self, documents: list[Document]):
        """
        Thêm tài liệu vào vector database hiện tại
        """
        try:
            if self.vector_db is None:
                return self.create_vector_db(documents=documents)
            
            logger.info(f"Thêm {len(documents)} tài liệu vào vector database hiện tại")
            uuids = [str(uuid4()) for _ in range(len(documents))]
            
            self.vector_db.add_documents(documents=documents, ids=uuids)
            self.save_vector_db()
            return True
        except Exception as e:
            logger.error(f"Lỗi khi thêm tài liệu vào vector database: {e}")
            return False
        
    def save_vector_db(self):
        try:
            if self.vector_db:
                if not os.path.exists(self.index_path):
                    os.makedirs(self.index_path, exist_ok=True)

                self.vector_db.save_local(self.index_path)
                logger.info(f"Vector database đã được lưu tại {self.index_path}")
        except Exception as e:
            logger.error(f"Lỗi khi lưu vector database: {e}")
            
    def load_vector_db(self):
        try:
            faiss_file = os.path.join(self.index_path, "index.faiss")
            if os.path.exists(faiss_file):
                logger.info(f"Tải vector database từ {faiss_file}")
                return FAISS.load_local(
                    folder_path=self.index_path,
                    embeddings=self.embed_model,
                    allow_dangerous_deserialization=True
                )
            logger.info("Không tìm thấy vector database, sẽ tạo mới khi cần thiết")
            return None
        except Exception as e:
            logger.error(f"Lỗi khi tải vector database: {e}")
            return None
        
    def delete_by_source(self, source: str):
        """
        Xóa tài liệu khỏi vector database dựa trên nguồn
        Sử dụng khi file bị trùng tên
        """
        if not self.vector_db:
            logger.warning("Không có vector database để xóa tài liệu")
            return False
        
        try:
            doc_dict = self.vector_db.docstore.__dict__
            ids_to_delete = [
                obj_id for obj_id, doc in doc_dict.items()
                if doc.metadata.get("source") == source
            ]
            
            if ids_to_delete:
                self.vector_db.delete(ids=ids_to_delete)
                self.save_vector_db()
                logger.info(f"Đã xóa {len(ids_to_delete)} tài liệu có nguồn '{source}' khỏi vector database")
                return True
        except Exception as e:
            logger.error(f"Lỗi khi xóa tài liệu theo nguồn '{source}': {e}")
            return False
        
    def clear_all(self):
        try:
            self.vector_db = None
            if os.path.exists(self.index_path):
                shutil.rmtree(self.index_path)
                logger.info(f"Đã xóa toàn bộ vector database tại {self.index_path}")
                return True
        except Exception as e:
            logger.error(f"Lỗi khi xóa toàn bộ vector database: {e}")
            return False
        
    def search(self, query: str, top_k: int = 5):
        if not self.vector_db:
            logger.warning("Không có vector database để tìm kiếm")
            return []
        
        try:
            results = self.vector_db.similarity_search(query=query, k=top_k)
            logger.info(f"Tìm kiếm với query '{query}' trả về {len(results)} kết quả")
            return results
        except Exception as e:
            logger.error(f"Lỗi khi tìm kiếm trong vector database: {e}")
            return []