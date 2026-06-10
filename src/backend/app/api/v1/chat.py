import logging
from fastapi import APIRouter, Depends, HTTPException
from ...schemas.chat import ChatRequest, ChatResponse
from ...schemas.testcase import TestCaseList, TestCase
from ..deps import get_retriever, get_llm_json_service, get_skill_manager
from ...skills.base import ConversationState
from ...utils.prompt_template import create_rag_query_prompt, get_system_prompt
from langchain_core.prompts import ChatPromptTemplate
import json

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat_interaction(
    request: ChatRequest,
    retriever = Depends(get_retriever),
    llm_service = Depends(get_llm_json_service),
    skill_manager = Depends(get_skill_manager)
):
    try:
        query = request.query.strip()
        logger.info(f"Nhận yêu cầu hội thoại: '{query}'")
        
        # 1. Kiểm tra trạng thái hội thoại và các cờ chốt phương án
        export_keywords = ["đồng ý", "xuất file", "ok", "chốt", "export excel", "tạo file"]
        is_export_request = any(kw in query.lower() for kw in export_keywords)
        
        if is_export_request:
            # Chuyển trạng thái sang CONFIRMING/EXECUTING để chuẩn bị chạy skill
            skill_manager.set_state(ConversationState.CONFIRMING)
            
            # Giả định danh sách test case trước đó đã được lưu trữ trong SkillManager.
            # Đối với một request API không lưu trạng thái (stateless), chúng ta có thể parse lịch sử chat
            # để khôi phục test cases hoặc lấy trực tiếp từ tham số người dùng truyền lên.
            # Ở đây chúng ta khôi phục test cases từ tin nhắn cuối cùng của assistant trong lịch sử.
            last_tc_list = []
            for msg in reversed(request.history):
                if msg.role == "assistant":
                    # Cố gắng tìm và parse cấu trúc JSON danh sách test case
                    try:
                        content = msg.content
                        # Tìm phần chứa JSON trong markdown codeblock nếu có
                        if "```json" in content:
                            content = content.split("```json")[1].split("```")[0].strip()
                        elif "```" in content:
                            content = content.split("```")[1].split("```")[0].strip()
                        else:
                            # Nếu không có markdown codeblock, trích xuất chuỗi JSON từ dấu { đầu tiên đến } cuối cùng
                            start = content.find('{')
                            end = content.rfind('}')
                            if start != -1 and end != -1:
                                content = content[start:end+1].strip()
                            
                        data = json.loads(content)
                        if isinstance(data, dict) and "test_cases" in data:
                            last_tc_list = data["test_cases"]
                            break
                    except Exception:
                        continue
            
            if last_tc_list:
                skill_manager.set_confirmed_testcases(last_tc_list)
                skill_manager.set_state(ConversationState.EXECUTING)
                
                # Thực thi Skill Excel Export
                excel_result = await skill_manager.run_skill("excel_export", {
                    "test_cases": last_tc_list,
                    "base_filename": "testcases"
                })
                
                if excel_result.success:
                    return ChatResponse(
                        answer=excel_result.message,
                        state=ConversationState.EXECUTING.value,
                        test_cases=[TestCase(**tc) for tc in last_tc_list],
                        excel_file=excel_result.filename
                    )
                else:
                    return ChatResponse(
                        answer=f"Gặp lỗi khi tạo Excel: {excel_result.message}",
                        state=ConversationState.CONFIRMING.value,
                        test_cases=[TestCase(**tc) for tc in last_tc_list]
                    )
            else:
                # Không tìm thấy test case nào để export
                return ChatResponse(
                    answer="Tôi chưa tìm thấy danh sách testcase nào được sinh ra trong lịch sử để xuất Excel. Hãy yêu cầu sinh testcase trước.",
                    state=ConversationState.COLLECTING_REQ.value
                )

        # 2. Luồng sinh test case bình thường (COLLECTING_REQ / DRAFTING / REFINING)
        skill_manager.set_state(ConversationState.DRAFTING)
        
        # Tìm kiếm tài liệu spec liên quan
        retrieved_docs = await retriever.search(query)
        if not retrieved_docs:
            return ChatResponse(
                answer="Xin lỗi, tôi không tìm thấy thông tin liên quan trong database. Vui lòng tải tài liệu lên trước.",
                state=ConversationState.COLLECTING_REQ.value
            )
            
        context = "\n---\n".join([doc.page_content for doc in retrieved_docs])
        sys_prompt = get_system_prompt(role="tester")
        human_template = create_rag_query_prompt()
        
        chat_template = ChatPromptTemplate.from_messages([
            ("system", sys_prompt),
            ("human", human_template)
        ])
        
        # Sinh câu trả lời dưới dạng JSON (TestCaseList)
        logger.info("Đang tạo test cases...")
        response = llm_service.generate(chat_template, {
            "context": context,
            "human_query": query
        })
        
        # 3. Phân tích kết quả trả về từ LLM
        answer_text = ""
        test_cases_list = None
        
        if isinstance(response, dict) and "test_cases" in response:
            test_cases_list = response["test_cases"]
            # Chuẩn bị hiển thị thô dạng text hoặc định dạng đẹp cho người dùng
            answer_text = f"Đã sinh thành công {len(test_cases_list)} test cases dựa trên Spec tìm thấy:\n\n```json\n"
            answer_text += json.dumps(response, indent=2, ensure_ascii=False)
            answer_text += "\n```"
            skill_manager.set_state(ConversationState.REFINING)
        elif isinstance(response, dict) and "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
        else:
            answer_text = str(response)
            skill_manager.set_state(ConversationState.COLLECTING_REQ)
            
        # 4. Kiểm tra kế thừa ngữ cảnh (Context Inheritance) khi lịch sử quá dài
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]
        # Thêm câu hiện tại
        history_dicts.append({"role": "user", "content": query})
        
        inheritance_result = await skill_manager.run_skill("context_inheritance", {
            "history": history_dicts,
            "model_ctx_limit": 8192
        })
        
        if inheritance_result.needs_summarization:
            answer_text += f"\n\n[Hệ thống tự động tóm tắt bộ nhớ vì phiên chat đã dài]:\n{inheritance_result.summary}"
            
        return ChatResponse(
            answer=answer_text,
            state=skill_manager.get_state().value,
            test_cases=[TestCase(**tc) for tc in test_cases_list] if test_cases_list else None
        )
        
    except Exception as e:
        logger.error(f"Lỗi endpoint chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
