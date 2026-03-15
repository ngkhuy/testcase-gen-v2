import sqlite3
import os
import logging
from typing import List, Dict
from langchain_core.documents import Document

from ..core.config import settings

logger = logging.getLogger(__name__)

class SQLiteService:
    def __init__(self):
        self.db_path = settings.SQLITE_DB_PATH
        self._init_db()

    def _get_connection(self):
        """Tạo kết nối tới SQLite"""
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Khởi tạo bảng FTS5 nếu chưa tồn tại"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with self._get_connection() as conn:
            # Tạo bảng ảo (Virtual Table) sử dụng engine FTS5
            # content, source, metadata_json là các cột dữ liệu
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    content,
                    source UNINDEXED,
                    metadata_json UNINDEXED,
                    tokenize='unicode61'
                );
            """)
            conn.commit()
            logger.info("SQLite FTS5 đã sẵn sàng.")

    def add_documents(self, documents: List[Document]):
        """
        Thêm tài liệu vào bộ lọc từ khóa (Incremental Add)
        """
        try:
            with self._get_connection() as conn:
                for doc in documents:
                    import json
                    conn.execute(
                        "INSERT INTO documents_fts (content, source, metadata_json) VALUES (?, ?, ?)",
                        (doc.page_content, doc.metadata.get("source", ""), json.dumps(doc.metadata))
                    )
                conn.commit()
            logger.info(f"Đã thêm {len(documents)} bản ghi vào SQLite FTS")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi thêm data vào SQLite: {e}")
            return False

    def search(self, query: str, top_k: int = 5) -> List[Document]:
        """
        Tìm kiếm bằng thuật ngữ BM25 tích hợp sẵn trong SQLite FTS5
        """
        try:
            import json
            # Làm sạch query cho FTS5:
            # Bọc trong dấu ngoặc kép để thực hiện phrase search an toàn, tránh lỗi syntax khi có dấu câu
            clean_query = query.replace('"', '""')
            fts_query = f'"{clean_query}"'
            
            with self._get_connection() as conn:
                cursor = conn.execute(f"""
                    SELECT content, metadata_json, bm25(documents_fts) as score
                    FROM documents_fts
                    WHERE documents_fts MATCH ?
                    ORDER BY score
                    LIMIT ?
                """, (fts_query, top_k))
                
                rows = cursor.fetchall()
                
                results = []
                for content, meta_json, score in rows:
                    results.append(Document(
                        page_content=content,
                        metadata=json.loads(meta_json)
                    ))
                
                logger.debug(f"SQLite FTS tìm thấy {len(results)} kết quả cho '{query}'")
                return results
                
        except Exception as e:
            logger.error(f"Lỗi tìm kiếm SQLite FTS: {e}")
            return []

    def delete_by_source(self, source: str):
        """Xóa tài liệu theo nguồn (Dùng khi cập nhật file)"""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM documents_fts WHERE source = ?", (source,))
                conn.commit()
            logger.info(f"Đã xóa dữ liệu nguồn '{source}' khỏi SQLite")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi xóa dữ liệu SQLite: {e}")
            return False

    def clear_all(self):
        """Xóa toàn bộ database"""
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                self._init_db()
                logger.info("Đã xóa toàn bộ SQLite database.")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi reset SQLite: {e}")
            return False
