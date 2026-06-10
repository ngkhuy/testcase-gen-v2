import os
import shutil
import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from ...core.config import settings
from ..deps import get_document_pipeline, get_vector_db, get_sqlite_db

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    pipeline = Depends(get_document_pipeline)
):
    """
    Endpoint tải tài liệu lên (PDF, Word, TXT, MD),
    tự động kích hoạt pipeline xử lý và nạp dữ liệu vào database.
    """
    try:
        filename = file.filename
        logger.info(f"Yêu cầu upload tài liệu: {filename}")
        
        # Kiểm tra phần mở rộng
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".pdf", ".docx", ".doc", ".txt", ".md"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Định dạng file {ext} không được hỗ trợ. Chỉ hỗ trợ PDF, DOCX, DOC, TXT, MD."
            )
            
        # Lưu file thô vào thư mục RAW_DOC_DIR
        os.makedirs(settings.RAW_DOC_DIR, exist_ok=True)
        file_path = os.path.join(settings.RAW_DOC_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"Đã lưu file thô tại: {file_path}")
        
        # Kích hoạt pipeline xử lý tự động
        spec_path = await pipeline.process_document(file_path)
        
        return {
            "success": True,
            "filename": filename,
            "spec_path": spec_path,
            "message": f"Tải tài liệu và sinh spec thành công cho file: {filename}"
        }
        
    except Exception as e:
        logger.error(f"Lỗi khi upload tài liệu: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{filename}")
async def delete_document(
    filename: str,
    vector_db = Depends(get_vector_db),
    sqlite_db = Depends(get_sqlite_db)
):
    """
    Xóa tài liệu khỏi database và xóa các file vật lý tương ứng.
    """
    try:
        logger.info(f"Yêu cầu xóa tài liệu: {filename}")
        
        # 1. Xóa khỏi database
        vector_deleted = vector_db.delete_by_source(filename)
        sqlite_deleted = sqlite_db.delete_by_source(filename)
        
        # 2. Xóa file thô vật lý
        raw_file_path = os.path.join(settings.RAW_DOC_DIR, filename)
        if os.path.exists(raw_file_path):
            os.remove(raw_file_path)
            
        # 3. Xóa file Spec vật lý tương ứng
        spec_filename = f"spec_{filename.replace('.pdf', '').replace('.docx', '').replace('.doc', '').replace('.md', '')}.md"
        spec_file_path = os.path.join(settings.SPEC_DIR, spec_filename)
        if os.path.exists(spec_file_path):
            os.remove(spec_file_path)
            
        return {
            "success": True,
            "filename": filename,
            "database_cleaned": vector_deleted or sqlite_deleted,
            "message": f"Đã xóa toàn bộ dữ liệu liên quan đến file: {filename}"
        }
        
    except Exception as e:
        logger.error(f"Lỗi khi xóa tài liệu: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    Tải file Excel đã xuất từ thư mục storage/exports.
    """
    try:
        exports_dir = os.path.join(os.path.dirname(settings.SPEC_DIR), "exports")
        file_path = os.path.join(exports_dir, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File không tồn tại hoặc đã bị xóa.")
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        logger.error(f"Lỗi khi tải file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
