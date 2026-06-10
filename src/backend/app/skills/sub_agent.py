import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from .base import BaseSkill
from langchain_core.prompts import ChatPromptTemplate
from ..schemas.testcase_model import TestCaseList

logger = logging.getLogger(__name__)

class SubAgentInput(BaseModel):
    agent_type: str = Field("drafting", description="Loại sub-agent cần kích hoạt: 'drafting' (soạn thảo) hoặc 'reviewer' (kiểm duyệt)")
    content: str = Field(..., description="Nội dung Spec hoặc văn bản thô đầu vào để xử lý")
    user_requirements: Optional[str] = Field(None, description="Yêu cầu cụ thể từ người dùng")

class SubAgentOutput(BaseModel):
    success: bool
    result: Any
    message: str

class SubAgentSkill(BaseSkill):
    name = "sub_agent"
    description = "Ủy thác các tác vụ soạn thảo thô hoặc soát lỗi sang các Sub-Agent chuyên môn có ngữ cảnh cô đọng."
    input_schema = SubAgentInput
    output_schema = SubAgentOutput
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.llm = getattr(llm_service, "llm", llm_service)
        
    async def execute(self, params: SubAgentInput) -> SubAgentOutput:
        agent_type = params.agent_type.lower().strip()
        logger.info(f"[SubAgent] Bắt đầu kích hoạt Sub-Agent: {agent_type}")
        
        if agent_type == "drafting":
            return await self._run_drafting_agent(params.content, params.user_requirements)
        elif agent_type == "reviewer":
            return await self._run_reviewer_agent(params.content)
        else:
            return SubAgentOutput(
                success=False,
                result=None,
                message=f"Loại Sub-Agent không hợp lệ: {agent_type}"
            )
            
    async def _run_drafting_agent(self, content: str, user_req: Optional[str]) -> SubAgentOutput:
        # Soạn thảo bản thảo thô cho từng phần nhỏ của spec
        system_prompt = (
            "Bạn là Sub-Agent Soạn thảo (Drafting Agent) chuyên trách viết test cases thô.\n"
            "Hãy đọc đoạn tài liệu sau và thiết lập các testcase thô (chưa cần hoàn toàn chuẩn JSON).\n"
            "Chỉ phản hồi danh sách testcase thô rõ ràng, dễ hiểu."
        )
        
        user_prompt = f"Tài liệu Spec:\n{content}\n\nYêu cầu bổ sung: {user_req or 'Không có'}\n\nHãy viết danh sách testcase thô:"
        
        chat_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt)
        ])
        
        try:
            chain = chat_template | self.llm
            response = await chain.ainvoke({})
            return SubAgentOutput(
                success=True,
                result=response.content,
                message="Đã tạo thành công bản thảo testcase thô."
            )
        except Exception as e:
            logger.error(f"Lỗi khi chạy Drafting Sub-Agent: {e}")
            return SubAgentOutput(
                success=False,
                result=None,
                message=f"Lỗi Drafting Agent: {str(e)}"
            )

    async def _run_reviewer_agent(self, content: str) -> SubAgentOutput:
        # Reviewer Agent nhận bản thảo thô và format/kiểm duyệt ra JSON chuẩn
        system_prompt = (
            "Bạn là Sub-Agent Kiểm duyệt (Reviewer Agent) chuyên trách kiểm tra lỗi logic và định dạng.\n"
            "Hãy đọc danh sách testcase thô dưới đây, lọc bỏ các case trùng lặp, chuẩn hóa các trường thông tin "
            "và trả về kết quả dạng JSON chuẩn."
        )
        
        user_prompt = f"Bản thảo testcase thô:\n{content}\n\nHãy chuẩn hóa và trả về định dạng JSON."
        
        chat_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt)
        ])
        
        try:
            # Nếu LLM hỗ trợ sinh có cấu trúc
            if hasattr(self.llm_service, "output_format") and self.llm_service.output_format == "json":
                chain = chat_template | self.llm_service.llm | self.llm_service.parser
                response = await chain.ainvoke({})
                result = response
            else:
                chain = chat_template | self.llm
                response = await chain.ainvoke({})
                result = response.content
                
            return SubAgentOutput(
                success=True,
                result=result,
                message="Đã kiểm duyệt và chuẩn hóa danh sách testcase."
            )
        except Exception as e:
            logger.error(f"Lỗi khi chạy Reviewer Sub-Agent: {e}")
            return SubAgentOutput(
                success=False,
                result=None,
                message=f"Lỗi Reviewer Agent: {str(e)}"
            )
