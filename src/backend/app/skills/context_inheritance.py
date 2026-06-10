import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from .base import BaseSkill
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)

class ContextInheritanceInput(BaseModel):
    history: List[Dict[str, Any]] = Field(..., description="Lịch sử tin nhắn dạng danh sách dict với các key 'role' và 'content'")
    model_ctx_limit: Optional[int] = Field(8192, description="Giới hạn context size của model (tokens/characters)")

class ContextInheritanceOutput(BaseModel):
    needs_summarization: bool
    summary: Optional[str] = None
    character_count: int

class ContextInheritanceSkill(BaseSkill):
    name = "context_inheritance"
    description = "Kiểm tra và tóm tắt ngữ cảnh cuộc hội thoại khi phiên làm việc quá dài để bảo toàn thông tin cốt lõi."
    input_schema = ContextInheritanceInput
    output_schema = ContextInheritanceOutput
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.llm = getattr(llm_service, "llm", llm_service)
        
    async def execute(self, params: ContextInheritanceInput) -> ContextInheritanceOutput:
        # Ước lượng độ dài ký tự thô của lịch sử hội thoại
        total_chars = 0
        formatted_history = []
        
        for msg in params.history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            total_chars += len(content)
            formatted_history.append(f"{role.upper()}: {content}")
            
        history_str = "\n".join(formatted_history)
        
        # Ngưỡng kích hoạt: Khoảng 70% số ký tự giới hạn (ước lượng 1 token ≈ 4 ký tự)
        char_threshold = params.model_ctx_limit * 4.0 * 0.70
        
        logger.info(f"[ContextInheritance] Tổng số ký tự lịch sử: {total_chars} | Ngưỡng tóm tắt: {char_threshold}")
        
        if total_chars < char_threshold:
            return ContextInheritanceOutput(
                needs_summarization=False,
                character_count=total_chars
            )
            
        logger.info("[ContextInheritance] Vượt ngưỡng ngữ cảnh. Đang tiến hành tóm tắt...")
        
        summary_prompt = PromptTemplate.from_template(
            "Bạn là trợ lý AI quản lý bộ nhớ hội thoại. Hãy tóm tắt cuộc đối thoại dưới đây thành các điểm chính "
            "để chuyển tiếp sang phiên làm việc tiếp theo mà không làm mất thông tin quan trọng.\n"
            "Hãy tóm tắt ngắn gọn và tập trung vào:\n"
            "1. Tài liệu/Spec hiện tại đang làm việc.\n"
            "2. Các yêu cầu đặc biệt hoặc quyết định đã thống nhất của người dùng.\n"
            "3. Danh sách testcase đang được hoàn thiện dở dang (nếu có).\n\n"
            "Lịch sử hội thoại:\n"
            "{history_text}\n\n"
            "Bản tóm tắt ngắn gọn:"
        )
        
        try:
            chain = summary_prompt | self.llm
            response = await chain.ainvoke({"history_text": history_str})
            summary_content = response.content.strip()
            
            logger.info("[ContextInheritance] Đã tạo thành công bản tóm tắt kế thừa ngữ cảnh.")
            return ContextInheritanceOutput(
                needs_summarization=True,
                summary=summary_content,
                character_count=total_chars
            )
        except Exception as e:
            logger.error(f"Lỗi khi sinh tóm tắt ngữ cảnh: {e}")
            return ContextInheritanceOutput(
                needs_summarization=False,
                summary=None,
                character_count=total_chars,
                error=str(e)
            )
