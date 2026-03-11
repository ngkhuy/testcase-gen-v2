import time
import os
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from services.vector_service import VectorService
from services.spec_generator_service import SpecGeneratorService

logger = logging.getLogger(__name__)

class DocHandler(FileSystemEventHandler):
    def __init__(self, vector_service: VectorService, spec_service: SpecGeneratorService, extraction_service):
        self.vector_service = vector_service
        self.spec_service = spec_service
        self.extraction_service = extraction_service

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith((".pdf", ".md", ".txt")):
            logger.info(f"Phát hiện tài liệu mới: {event.src_path}")
            self._process_workflow(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith((".pdf", ".md", ".txt")):
            logger.info(f"Tài liệu thay đổi: {event.src_path}")
            self._process_workflow(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            file_name = os.path.basename(event.src_path)
            logger.info(f"Đang xóa dữ liệu của {file_name} khỏi Vector DB...")
            self.vector_service.delete_by_source(file_name)

    def _process_workflow(self, file_path):
        """Dây chuyền xử lý tự động"""
        try:
            file_name = os.path.basename(file_path)
            
            #Trích xuất Text thô từ Requirement (PDF/TXT)
            logger.info(f"Đang trích xuất nội dung từ {file_name}...")
            raw_markdown = self.extraction_service.extract_raw(file_path)
            
            #Dùng LLM biến Requirement thô thành Spec xịn (Dùng Prompt Utils)
            logger.info(f"LLM đang soạn thảo Technical Spec...")
            spec_path, spec_content = self.spec_service.generate_detailed_spec(raw_markdown, file_name)
            
            #Chặt nhỏ bản Spec vừa tạo (Chunking)
            logger.info(f"Đang nạp Spec vào Vector Database...")
            chunks = self.extraction_service.split_text(spec_content, source=file_name)
            
            #Cập nhật Vector DB
            self.vector_service.delete_by_source(file_name)
            self.vector_service.create_vector_db(chunks)
            
            logger.info(f"Hoàn tất! Hệ thống đã sẵn sàng truy vấn cho: {file_name}")
            
        except Exception as e:
            logger.error(f"Lỗi dây chuyền xử lý: {str(e)}")

class DocWatchdog:
    def __init__(self, vector_service, spec_service, extraction_service):
        self.observer = Observer()
        self.handler = DocHandler(vector_service, spec_service, extraction_service)
        self.watch_dir = "raw_doc"

    def start(self):
        if not os.path.exists(self.watch_dir):
            os.makedirs(self.watch_dir)
            
        self.observer.schedule(self.handler, self.watch_dir, recursive=False)
        self.observer.start()
        logger.info(f"Watchdog khởi động thành công! Đang quan sát: /{self.watch_dir}")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
            logger.info("Watchdog đã dừng.")
        self.observer.join()