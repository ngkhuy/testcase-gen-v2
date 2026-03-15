import time
import os
import logging
import asyncio

from langchain_core.documents import Document
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ..services.vector_service import VectorService
from ..services.spec_generation_service import SpecGeneratorService
from .config import settings
from ..utils.clean_table_tag import transform_tables

logger = logging.getLogger(__name__)

class DocHandler(FileSystemEventHandler):
    def __init__(self, vector_service: VectorService, sqlite_service, spec_service: SpecGeneratorService, extraction_service, loop: asyncio.AbstractEventLoop):
        self.vector_service = vector_service
        self.sqlite_service = sqlite_service
        self.spec_service = spec_service
        self.extraction_service = extraction_service
        self.loop = loop
        self._last_event_times = {} 
        self._processing_files = set() 

    def _is_duplicate_event(self, path):
        path = os.path.abspath(path).lower() # Chuẩn hóa đường dẫn
        current_time = time.time()
        
        if path in self._processing_files:
            return True
            
        last_time = self._last_event_times.get(path, 0)
        if current_time - last_time < 10:  # Tăng cooldown lên 10 giây để tránh loop OS
            return True
        
        return False

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith((".pdf", ".md", ".txt")):
            if self._is_duplicate_event(event.src_path):
                return
            logger.info(f"Phát hiện tài liệu mới: {event.src_path}")
            self._run_safe_workflow(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith((".pdf", ".md", ".txt")):
            if self._is_duplicate_event(event.src_path):
                return
            logger.info(f"Tài liệu thay đổi: {event.src_path}")
            self._run_safe_workflow(event.src_path)

    def _run_safe_workflow(self, path):
        abs_path = os.path.abspath(path).lower()
        try:
            self._processing_files.add(abs_path)
            self._process_workflow(path)
        finally:
            self._last_event_times[abs_path] = time.time()
            self._processing_files.remove(abs_path)

    def on_deleted(self, event):
        if not event.is_directory:
            file_name = os.path.basename(event.src_path)
            logger.info(f"Đang xóa dữ liệu của {file_name} khỏi Vector DB & SQLite FTS...")
            self.vector_service.delete_by_source(file_name)
            self.sqlite_service.delete_by_source(file_name)

    def _process_workflow(self, file_path):
        """Dây chuyền xử lý tự động sử dụng thread-safe async"""
        try:
            file_name = os.path.basename(file_path)
            logger.info(f"Đang trích xuất nội dung từ {file_name}...")
            
            # Sử dụng run_coroutine_threadsafe để chạy trên Event Loop chính
            # Tránh lỗi 'Event loop is closed'
            def run_async(coro):
                future = asyncio.run_coroutine_threadsafe(coro, self.loop)
                return future.result()

            raw = run_async(self.extraction_service.parse_document(document_path=file_path))
            raw_markdown = raw.markdown
            
            raw_response = run_async(self.extraction_service.extract_content(markdown=raw_markdown))
            raw_content = raw_response.content if hasattr(raw_response, 'content') else str(raw_response)
            
            content = transform_tables(raw_content) 
            
            logger.info(f"LLM đang soạn thảo Technical Spec...")
            # spec_service.generate_detailed_spec không async nên gọi trực tiếp
            spec_path, spec_content = self.spec_service.generate_detailed_spec(content, file_name)
            
            logger.info(f"Đang nạp Spec vào Vector Database...")
            chunks = self.vector_service.chunk_document(Document(page_content=spec_content, metadata={"source": file_name}))
            
            self.vector_service.delete_by_source(file_name)
            self.sqlite_service.delete_by_source(file_name)
            
            self.vector_service.add_documents(chunks)
            self.sqlite_service.add_documents(chunks)
            
            logger.info(f"Hoàn tất! Hệ thống đã sẵn sàng truy vấn cho: {file_name}")
            
        except Exception as e:
            logger.error(f"Lỗi dây chuyền xử lý: {str(e)}")

class DocWatchdog:
    def __init__(self, vector_service, sqlite_service, spec_service, extraction_service, loop=None):
        self.observer = Observer()
        # Lấy loop hiện tại nếu không truyền vào
        current_loop = loop or asyncio.get_event_loop()
        self.handler = DocHandler(vector_service, sqlite_service, spec_service, extraction_service, current_loop)
        self.watch_dir = settings.RAW_DOC_DIR

    def start(self):
        if not os.path.exists(self.watch_dir):
            os.makedirs(self.watch_dir, exist_ok=True)
            
        self.observer.schedule(self.handler, self.watch_dir, recursive=False)
        self.observer.start()
        logger.info(f"Watchdog khởi động thành công! Đang quan sát: {self.watch_dir}")

    def stop(self):
        self.observer.stop()
        self.observer.join()
        logger.info("Watchdog đã dừng.")