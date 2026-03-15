import os
import sys
import logging
from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.llm_service import LLMService
from app.services.spec_generation_service import SpecGeneratorService
from app.services.extraction_service import ADEExtraction
from app.core.watchdog import DocWatchdog

# Cấu hình logging toàn cục
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("storage/logs/backend.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("BrainMain")

def init_env():
    """Khởi tạo các tài nguyên và thư mục cần thiết"""
    logger.info("Đang kiểm tra môi trường và cấu trúc thư mục...")
    
    # Danh sách các thư mục cần đảm bảo tồn tại
    required_dirs = [
        settings.SPEC_DIR,
        settings.RAW_DOC_DIR,
        os.path.dirname(settings.FAISS_INDEX_PATH),
        "storage/logs",
        "models/ranker_model_cache"
    ]
    
    for directory in required_dirs:
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Đã tạo thư mục: {directory}")

def main():
    """
    Hàm thực thi chính - Bộ não điều khiển toàn bộ backend.
    Hiện tại đóng vai trò là Orchestrator khởi chạy Watchdog để xử lý tài liệu tự động.
    """
    print("\n" + "="*50)
    print("      TESTCASE GENERATOR V2 - BACKEND BRAIN      ")
    print("="*50 + "\n")
    
    try:
        # 1. Khởi tạo môi trường
        init_env()

        # 2. Khởi tạo các dịch vụ chính (Core Services)
        logger.info("Đang khởi tạo các dịch vụ lõi...")
        
        # Service nhúng (Vectorization)
        embedding_service = EmbeddingService()
        
        # Service quản lý Vector Database (FAISS)
        vector_service = VectorService(embedding_service=embedding_service)
        
        # Service ngôn ngữ lớn (LLM - Ollama)
        llm_service = LLMService()
        
        # Service trích xuất nội dung (LandingAI ADE)
        extraction_service = ADEExtraction()
        
        # Service soạn thảo Technical Spec
        spec_service = SpecGeneratorService(llm_service=llm_service)

        logger.info("Tất cả dịch vụ đã sẵn sàng.")

        # 3. Khởi chạy Watchdog (Giám sát file tự động)
        # Watchdog sẽ tự động gọi extraction -> spec generation -> indexing
        logger.info(f"Bắt đầu khởi động Watchdog tại thư mục: ./{settings.RAW_DOC_DIR}")
        watchdog = DocWatchdog(
            vector_service=vector_service,
            spec_service=spec_service,
            extraction_service=extraction_service
        )
        
        # watchdog.start() là hàm chặn (blocking call) với vòng lặp vô tận
        watchdog.start()

    except KeyboardInterrupt:
        logger.info("Nhận tín hiệu dừng từ người dùng. Đang thoát...")
    except Exception as e:
        logger.critical(f"Lỗi nghiêm trọng không thể khởi động Backend: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
