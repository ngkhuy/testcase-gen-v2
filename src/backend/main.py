import os
import sys
import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openpyxl import Workbook
from openpyxl.styles import Font

# Thêm đường dẫn hiện tại vào sys.path để tránh lỗi import khi chạy từ thư mục gốc
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.core.config import settings
from app.api.deps import (
    get_vector_db,
    get_sqlite_db,
    get_spec_gen_service,
    get_document_pipeline,
    get_retriever,
    get_llm_json_service,
    get_skill_manager
)
from app.core.watchdog import DocWatchdog
from app.skills.base import ConversationState
from app.api.v1 import chat, document, benchmark

# Khởi tạo thư mục log và cấu hình logging
os.makedirs(settings.LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(settings.LOG_DIR, "backend.log"), encoding="utf-8")
    ]
)
logger = logging.getLogger("BackendMain")

# =====================================================================
# Khởi tạo Ứng Dụng FastAPI
# =====================================================================
app = FastAPI(
    title="Testcase Generator API",
    description="Hệ thống tự động sinh và quản lý testcase dựa trên Spec kỹ thuật sử dụng LLM & RAG.",
    version="2.0.0"
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các API Routers
app.include_router(chat.router, prefix="/v1/chat", tags=["Chat & Agent"])
app.include_router(document.router, prefix="/v1/document", tags=["Document Management"])
app.include_router(benchmark.router, prefix="/v1/benchmark", tags=["Benchmark Engine"])

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Testcase Generator V2 Backend API",
        "version": "2.0.0",
        "watchdog_enabled": settings.ENABLE_WATCHDOG
    }

# =====================================================================
# Luồng Khởi Chạy CLI Tương Tác & Watchdog
# =====================================================================
def init_env():
    """Khởi tạo cấu trúc lưu trữ của dự án"""
    required_dirs = [
        settings.SPEC_DIR,
        settings.RAW_DOC_DIR,
        os.path.dirname(settings.FAISS_INDEX_PATH),
        settings.LOG_DIR,
        settings.MODELS_DIR
    ]
    for directory in required_dirs:
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

async def run_cli():
    logger.info("="*50)
    logger.info("      TESTCASE GENERATOR V2 - CLI INTERACTION      ")
    logger.info("="*50)
    
    init_env()
    
    # Khởi tạo các dịch vụ thông qua Dependency injection
    vector_db = get_vector_db()
    sqlite_db = get_sqlite_db()
    document_pipeline = get_document_pipeline()
    retriever = get_retriever()
    llm_service = get_llm_json_service()
    skill_manager = get_skill_manager()

    # Bật Watchdog nếu được cấu hình
    watchdog = None
    if settings.ENABLE_WATCHDOG:
        logger.info(f"Khởi động Watchdog giám sát: {settings.RAW_DOC_DIR}")
        watchdog = DocWatchdog(pipeline=document_pipeline)
        watchdog.start()
    else:
        logger.info("DocWatchdog đang bị TẮT theo cấu hình ENABLE_WATCHDOG=False.")

    logger.info("Chào mừng đến với AI chat sinh testcase (phiên bản OOP & Skill-based)")
    logger.info("Nhập 'exit' hoặc 'quit' để thoát.")

    async def handle_query(query: str):
        try:
            query_clean = query.strip()
            export_keywords = ["đồng ý", "xuất file", "ok", "chốt", "excel", "xuất excel"]
            is_export = any(kw in query_clean.lower() for kw in export_keywords)
            
            if is_export:
                # Gọi Excel Skill
                skill_manager.set_state(ConversationState.CONFIRMING)
                
                # Trong CLI, chúng ta giả định danh sách test case gần nhất được lưu trong Session.
                # Do CLI chạy đồng bộ liên tục, ta có thể dùng biến lưu trữ nội bộ của skill manager.
                if skill_manager.confirmed_testcases:
                    skill_manager.set_state(ConversationState.EXECUTING)
                    excel_result = await skill_manager.run_skill("excel_export", {
                        "test_cases": skill_manager.confirmed_testcases,
                        "base_filename": "testcases"
                    })
                    print(f"\nBrain: {excel_result.message}")
                else:
                    print("\nBrain: Chưa có danh sách testcase nào được sinh ra để xuất Excel. Hãy yêu cầu sinh testcase trước.")
                return

            # Luồng tìm kiếm & sinh bình thường
            skill_manager.set_state(ConversationState.DRAFTING)
            retrieved_docs = await retriever.search(query_clean)
            if not retrieved_docs:
                print("\nBrain: Xin lỗi, tôi không tìm thấy thông tin liên quan trong database.")
                return

            context = "\n---\n".join([doc.page_content for doc in retrieved_docs])
            from app.utils.prompt_template import create_rag_query_prompt, get_system_prompt
            from langchain_core.prompts import ChatPromptTemplate
            
            sys_prompt = get_system_prompt(role="tester")
            human_template = create_rag_query_prompt()
            
            chat_template = ChatPromptTemplate.from_messages([
                ("system", sys_prompt),
                ("human", human_template)
            ])
            
            print("\nBrain: Đang suy luận và tạo testcases...")
            response = llm_service.generate(chat_template, {
                "context": context,
                "human_query": query_clean
            })
            
            if isinstance(response, dict) and "test_cases" in response:
                tcs = response["test_cases"]
                skill_manager.set_confirmed_testcases(tcs)
                print(f"\nBrain: Đã sinh thành công {len(tcs)} test cases. Bạn có đồng ý xuất file excel không?")
                # In ra các testcase thô
                for tc in tcs:
                    print(f" - [{tc.get('tc_id', '')}] {tc.get('tc_title', '')}")
            else:
                print(f"\nBrain: {response}")

        except Exception as e:
            logger.error(f"Lỗi khi xử lý câu hỏi: {e}", exc_info=True)

    # Vòng lặp chat
    while True:
        try:
            query = await asyncio.to_thread(input, "\nBạn: ")
            if not query.strip():
                continue
            if query.lower() in ["exit", "quit"]:
                break
            await handle_query(query)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Lỗi hệ thống: {e}")

    if watchdog:
        watchdog.stop()
    logger.info("Ứng dụng CLI đã dừng.")

# =====================================================================
# Startup hook cho FastAPI
# =====================================================================
@app.on_event("startup")
async def startup_event():
    init_env()
    # Nếu bật watchdog khi khởi chạy API server
    if settings.ENABLE_WATCHDOG:
        logger.info("[FastAPI] Khởi chạy DocWatchdog nền...")
        loop = asyncio.get_event_loop()
        app.state.watchdog = DocWatchdog(pipeline=get_document_pipeline(), loop=loop)
        app.state.watchdog.start()

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, "watchdog"):
        logger.info("[FastAPI] Dừng DocWatchdog nền...")
        app.state.watchdog.stop()

if __name__ == "__main__":
    # Nếu chạy trực tiếp script: mặc định khởi động giao diện CLI
    asyncio.run(run_cli())
