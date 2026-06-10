import os
import logging
from langchain_core.documents import Document
from ..utils.local_reader import LocalDocumentReader
from ..utils.clean_table_tag import transform_tables

logger = logging.getLogger(__name__)

class DocumentProcessingPipeline:
    """
    Pipeline dịch vụ hợp nhất để xử lý tài liệu thô:
    1. Đọc file cục bộ (PDF, Word, TXT, MD) qua LocalDocumentReader.
    2. Chuẩn hóa bảng biểu và định dạng.
    3. Soạn Spec chi tiết qua SpecGeneratorService.
    4. Chia nhỏ (chunk) spec và nạp vào SQLite FTS & Vector DB.
    """
    def __init__(self, vector_db, sqlite_db, spec_gen_service):
        self.vector_db = vector_db
        self.sqlite_db = sqlite_db
        self.spec_gen_service = spec_gen_service
        self.reader = LocalDocumentReader()

    async def process_document(self, file_path: str) -> str:
        """
        Thực hiện toàn bộ quy trình xử lý tài liệu từ file thô.
        Trả về đường dẫn tới file Spec đã được sinh ra.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

        file_name = os.path.basename(file_path)
        logger.info(f"[Pipeline] Bắt đầu xử lý tài liệu: {file_name}")

        # 1. Đọc nội dung thô cục bộ
        doc_data = self.reader.read_file(file_path)
        raw_content = doc_data["content"]
        
        # 2. Chuẩn hóa bảng biểu html (nếu có)
        content = transform_tables(raw_content)

        # 3. Soạn thảo tài liệu Technical Spec bằng LLM
        logger.info(f"[Pipeline] Đang gửi nội dung sang LLM để soạn Technical Spec...")
        spec_path, spec_content = self.spec_gen_service.generate_detailed_spec(content, file_name)
        logger.info(f"[Pipeline] Đã lưu Spec tại: {spec_path}")

        # 4. Nạp Spec vào cơ sở dữ liệu
        logger.info(f"[Pipeline] Đang nạp nội dung Spec vào Vector DB và SQLite FTS...")
        spec_doc = Document(
            page_content=spec_content,
            metadata={"source": file_name, "spec_path": spec_path}
        )
        
        # Chia nhỏ tài liệu thành các chunk
        chunks = self.vector_db.chunk_document(spec_doc)
        
        # Xóa dữ liệu cũ của file cùng tên nếu có (đảm bảo cập nhật bản mới nhất)
        self.vector_db.delete_by_source(file_name)
        self.sqlite_db.delete_by_source(file_name)
        
        # Ghi các chunk mới
        self.vector_db.add_documents(chunks)
        self.sqlite_db.add_documents(chunks)
        
        logger.info(f"[Pipeline] Hoàn tất nạp dữ liệu cho file: {file_name}")
        return spec_path
