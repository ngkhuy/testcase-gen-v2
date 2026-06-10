import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from .base import BaseSkill
from ..utils.local_reader import LocalDocumentReader

logger = logging.getLogger(__name__)

class FileReaderInput(BaseModel):
    file_path: str = Field(..., description="Đường dẫn vật lý tới file cần đọc (PDF, DOCX, TXT, MD)")

class FileReaderOutput(BaseModel):
    success: bool
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class FileReaderSkill(BaseSkill):
    name = "file_reader"
    description = "Đọc và trích xuất nội dung văn bản từ các file tài liệu PDF, Word (DOCX), hoặc file Text/Markdown cục bộ."
    input_schema = FileReaderInput
    output_schema = FileReaderOutput
    
    def __init__(self):
        self.reader = LocalDocumentReader()
        
    async def execute(self, params: FileReaderInput) -> FileReaderOutput:
        try:
            logger.info(f"FileReaderSkill bắt đầu đọc file: {params.file_path}")
            result = self.reader.read_file(params.file_path)
            
            return FileReaderOutput(
                success=True,
                content=result["content"],
                metadata=result["metadata"]
            )
        except Exception as e:
            logger.error(f"FileReaderSkill gặp lỗi: {e}")
            return FileReaderOutput(
                success=False,
                error=str(e)
            )
