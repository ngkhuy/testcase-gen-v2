import time
import os
import logging
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .config import settings
from ..services.document_pipeline import DocumentProcessingPipeline

logger = logging.getLogger(__name__)

class DocHandler(FileSystemEventHandler):
    def __init__(self, pipeline: DocumentProcessingPipeline, loop: asyncio.AbstractEventLoop):
        self.pipeline = pipeline
        self.loop = loop
        self._last_event_times = {} 
        self._processing_files = set() 

    def _is_duplicate_event(self, path):
        path = os.path.abspath(path).lower() # Chuẩn hóa đường dẫn
        current_time = time.time()
        
        if path in self._processing_files:
            return True
            
        last_time = self._last_event_times.get(path, 0)
        if current_time - last_time < 10:  # Cooldown 10 giây
            return True
        
        return False

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith((".pdf", ".md", ".txt", ".docx")):
            if self._is_duplicate_event(event.src_path):
                return
            logger.info(f"Phát hiện tài liệu mới: {event.src_path}")
            self._run_safe_workflow(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith((".pdf", ".md", ".txt", ".docx")):
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
            self.pipeline.vector_db.delete_by_source(file_name)
            self.pipeline.sqlite_db.delete_by_source(file_name)

    def _process_workflow(self, file_path):
        """Kích hoạt pipeline xử lý bằng thread-safe async"""
        try:
            def run_async(coro):
                future = asyncio.run_coroutine_threadsafe(coro, self.loop)
                return future.result()

            # Gọi pipeline xử lý tập trung
            run_async(self.pipeline.process_document(file_path))
            
        except Exception as e:
            logger.error(f"Lỗi dây chuyền xử lý Watchdog: {str(e)}")

class DocWatchdog:
    def __init__(self, pipeline: DocumentProcessingPipeline, loop=None):
        self.observer = Observer()
        current_loop = loop or asyncio.get_event_loop()
        self.handler = DocHandler(pipeline, current_loop)
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