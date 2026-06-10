import os
import logging
from typing import Dict, Any
import pdfplumber
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)

class LocalDocumentReader:
    """
    Trình đọc tài liệu cục bộ hỗ trợ trích xuất văn bản từ PDF, DOCX, TXT, MD.
    Không phụ thuộc vào API bên thứ ba.
    """
    
    @staticmethod
    def read_pdf(file_path: str) -> str:
        """Đọc và trích xuất text từ file PDF sử dụng pdfplumber"""
        text_content = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
                    
                    # Trích xuất bảng biểu nếu có và định dạng thô dạng Markdown
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            table_text = []
                            for row in table:
                                # Lọc bỏ các dòng None và nối các cột bằng '|'
                                filtered_row = [str(cell) if cell is not None else "" for cell in row]
                                table_text.append("| " + " | ".join(filtered_row) + " |")
                            if table_text:
                                text_content.append("\n" + "\n".join(table_text) + "\n")
                                
            return "\n\n--- Page Break ---\n\n".join(text_content)
        except Exception as e:
            logger.error(f"Lỗi khi đọc file PDF cục bộ {file_path}: {e}")
            raise e

    @staticmethod
    def read_docx(file_path: str) -> str:
        """Đọc và trích xuất text từ file DOCX sử dụng python-docx"""
        try:
            doc = DocxDocument(file_path)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
                
            # Đọc thêm bảng biểu trong file DOCX
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells]
                    full_text.append("| " + " | ".join(row_text) + " |")
                    
            return "\n".join(full_text)
        except Exception as e:
            logger.error(f"Lỗi khi đọc file DOCX cục bộ {file_path}: {e}")
            raise e

    @staticmethod
    def read_txt(file_path: str) -> str:
        """Đọc file text/markdown thô"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Lỗi khi đọc file văn bản {file_path}: {e}")
            raise e

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Đọc tài liệu dựa trên định dạng đuôi mở rộng.
        Trả về dictionary chứa nội dung thô và metadata.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")
            
        ext = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path)
        logger.info(f"Đang phân tích file cục bộ: {file_name} với định dạng {ext}")
        
        if ext == ".pdf":
            content = self.read_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            # Note: Thư viện python-docx chủ yếu hỗ trợ .docx. 
            # Với .doc cũ, khuyến cáo đổi tên hoặc convert, nhưng chúng ta vẫn thử map qua docx parser.
            content = self.read_docx(file_path)
        elif ext in [".txt", ".md"]:
            content = self.read_txt(file_path)
        else:
            raise ValueError(f"Định dạng file không được hỗ trợ: {ext}")
            
        return {
            "content": content,
            "metadata": {
                "source": file_name,
                "file_path": file_path,
                "file_type": ext.replace(".", ""),
                "char_count": len(content)
            }
        }
