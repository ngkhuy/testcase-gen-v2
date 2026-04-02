import os
import sys
import logging
import asyncio
import datetime
from openpyxl import Workbook
from openpyxl.styles import Font

# Thêm đường dẫn hiện tại vào sys.path để tránh lỗi import khi chạy từ thư mục gốc
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.sqlite_service import SQLiteService
from app.services.llm_service import LLMService
from app.services.spec_generation_service import SpecGeneratorService
from app.services.extraction_service import ADEExtraction
from app.services.retriever_service import AdvancedRetriever
from app.core.watchdog import DocWatchdog
from app.utils.prompt_template import create_rag_query_prompt, get_system_prompt
from langchain_core.prompts import ChatPromptTemplate

# Khởi tạo thư mục trước khi cấu hình logging
os.makedirs(settings.LOG_DIR, exist_ok=True)

# Cấu hình logging toàn cục
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(settings.LOG_DIR, "backend.log"), encoding="utf-8")
    ]
)
logger = logging.getLogger("BrainMain")

def export_to_excel(data, base_filename="testcases"):
    """Lưu danh sách test cases vào file Excel"""
    try:
        # Kiểm tra nếu data là dictionary và có key test_cases
        if not isinstance(data, dict) or "test_cases" not in data:
            return None
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_filename}_{timestamp}.xlsx"
        filepath = os.path.join(current_dir, filename)
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Test Cases"
        
        # Headers
        headers = ["ID", "Title", "Pre-condition", "Steps", "Data", "Expected Result", "Note"]
        ws.append(headers)
        
        # Style headers
        for cell in ws[1]:
            cell.font = Font(bold=True)
            
        # Data
        for tc in data["test_cases"]:
            # Linh hoạt lấy dữ liệu theo nhiều key khác nhau đề phòng LLM output sai key
            ws.append([
                tc.get("tc_id") or tc.get("id") or tc.get("tc_no") or "",
                tc.get("tc_title") or tc.get("title") or tc.get("test_case_name") or "",
                tc.get("pre_condition") or tc.get("preconditions") or tc.get("precondition") or "",
                tc.get("test_step") or tc.get("test_steps") or tc.get("steps") or "",
                tc.get("test_data") or tc.get("data") or "",
                tc.get("expected_result") or tc.get("expected_results") or tc.get("expect") or "",
                tc.get("note") or tc.get("description") or tc.get("priority") or ""
            ])
            
        # Tự động chỉnh độ rộng cột (cơ bản)
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column_letter].width = min(adjusted_width, 50)
            
        wb.save(filepath)
        return filename
    except Exception as e:
        logger.error(f"Lỗi khi xuất file Excel: {e}")
        return None

def init_env():
    """Khởi tạo cấu trúc dự án"""
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

async def main():
    logger.info("="*50)
    logger.info("      TESTCASE GENERATOR V2 - BACKEND BRAIN      ")
    logger.info("="*50)
    
    try:
        init_env()

        extraction_service = ADEExtraction()
        embedding_service = EmbeddingService()
        
        vector_service = VectorService(embedding_service=embedding_service)
        sqlite_service = SQLiteService()
        
        llm_service = LLMService(output_format="text")
        spec_service = SpecGeneratorService(llm_service=llm_service)
        
        query_llm_service = LLMService(output_format="json")
        
        retriever = AdvancedRetriever(
            vector_service=vector_service, 
            sqlite_service=sqlite_service, 
            llm_service=query_llm_service
        )

        logger.info(f"Khởi động Watchdog giám sát: {settings.RAW_DOC_DIR}")
        watchdog = DocWatchdog(
            vector_service=vector_service, 
            sqlite_service=sqlite_service,
            spec_service=spec_service, 
            extraction_service=extraction_service
        )
        
        watchdog.start()

        logger.info("Chào mừng đến với AI chat sinh testcase")
        logger.info("Nhấn Ctrl+C để thoát")

        async def handle_query(query: str):
            try:
                # 1. Tìm kiếm tài liệu
                logger.info("Đang tìm kiếm tài liệu cho query...")
                retrieved_docs = await retriever.search(query)

                if not retrieved_docs:
                    print("Brain: Xin lỗi, tôi không tìm thấy thông tin liên quan trong database.")
                    return

                # 2. Tạo ngữ cảnh
                context = "\n---\n".join([doc.page_content for doc in retrieved_docs])
                sys_prompt = get_system_prompt(role="tester")
                human_template = create_rag_query_prompt()
                
                chat_template = ChatPromptTemplate.from_messages([
                    ("system", sys_prompt),
                    ("human", human_template)
                ])
                
                # 3. Tạo câu trả lời
                logger.info("Đang tạo câu trả lời...")
                response = query_llm_service.generate(chat_template, {
                    "context": context,
                    "human_query": query
                })
                
                print(f"\nBrain: {response}")
                
                # 4. Xuất file Excel nếu là JSON hợp lệ
                if isinstance(response, dict) and "test_cases" in response:
                    excel_file = export_to_excel(response)
                    if excel_file:
                        print(f"==> Đã xuất danh sách test cases ra file: {excel_file}")

            except Exception as e:
                logger.error(f"Lỗi khi xử lý câu hỏi: {e}")

        # Vòng lặp Chat (Sử dụng threaded input để không chặn log)
        while True:
            try:
                query = await asyncio.to_thread(input, "\nBạn: ")
                
                if not query.strip():
                    continue

                if query.lower() in ["exit", "quit"]:
                    break

                # Thực thi xử lý query
                await handle_query(query)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Lỗi hệ thống trong vòng lặp: {e}")

        watchdog.stop()

    except Exception as e:
        logger.critical(f"Lỗi khởi động nghiêm trọng: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
