from abc import ABC, abstractmethod
from enum import Enum
import logging
from typing import Dict, Type, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ConversationState(str, Enum):
    """Định nghĩa các trạng thái hội thoại chính"""
    COLLECTING_REQ = "COLLECTING_REQ"  # Thu thập yêu cầu từ user
    DRAFTING = "DRAFTING"              # Sinh bản thảo testcase thô
    REFINING = "REFINING"              # Tinh chỉnh testcase theo feedback
    CONFIRMING = "CONFIRMING"          # User đang xem xét và chuẩn bị chốt
    EXECUTING = "EXECUTING"            # Thực thi tạo file Excel/Testcase cuối

class BaseSkill(ABC):
    """
    Interface cơ sở cho các kỹ năng (Skills) của Agent.
    """
    name: str = ""
    description: str = ""
    input_schema: Type[BaseModel] = BaseModel
    output_schema: Type[BaseModel] = BaseModel
    
    @abstractmethod
    async def execute(self, params: Any) -> Any:
        """Thực thi skill với tham số đã được validate qua input_schema"""
        pass

class SkillManager:
    """
    Quản lý các Kỹ năng và điều phối việc gọi công cụ kèm theo
    bộ lọc kiểm soát trạng thái hội thoại (Guardrails).
    """
    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}
        self.current_state = ConversationState.COLLECTING_REQ
        self.confirmed_testcases = []  # Lưu giữ danh sách testcase đã chốt
        
    def register_skill(self, skill: BaseSkill):
        self.skills[skill.name.lower()] = skill
        logger.info(f"Đã đăng ký skill: {skill.name}")
        
    def set_state(self, state: ConversationState):
        logger.info(f"Chuyển trạng thái hội thoại: {self.current_state.value} -> {state.value}")
        self.current_state = state
        
    def get_state(self) -> ConversationState:
        return self.current_state
        
    def set_confirmed_testcases(self, test_cases: list):
        self.confirmed_testcases = test_cases
        if test_cases:
            self.set_state(ConversationState.CONFIRMING)
            
    async def run_skill(self, skill_name: str, params: Dict[str, Any]) -> Any:
        name_clean = skill_name.strip().lower()
        if name_clean not in self.skills:
            raise ValueError(f"Skill '{skill_name}' không tồn tại.")
            
        skill = self.skills[name_clean]
        
        # --- BỘ LỌC KIỂM SOÁT TỰ ĐỘNG (GUARDRAILS) ---
        if name_clean == "excel_export":
            # Guardrail: Chỉ cho phép xuất file excel khi đã chốt phương án
            if self.current_state not in [ConversationState.CONFIRMING, ConversationState.EXECUTING]:
                logger.warning("Cảnh báo: LLM cố gắng gọi excel_export khi chưa chốt phương án.")
                return {
                    "success": False,
                    "error": "Chưa thể xuất file Excel. Hãy hiển thị danh sách testcase thô trên khung chat "
                             "và yêu cầu người dùng xác nhận bằng cách gõ 'Đồng ý/Xuất file' trước khi gọi kỹ năng này."
                }
            if not self.confirmed_testcases and not params.get("test_cases"):
                logger.warning("Cảnh báo: LLM cố gắng gọi excel_export với danh sách testcase trống.")
                return {
                    "success": False,
                    "error": "Danh sách testcase xuất ra đang rỗng. Vui lòng tạo danh sách testcase trước."
                }
                
        # Thực hiện gọi skill
        logger.info(f"Đang thực thi skill: {skill.name}...")
        try:
            # Validate input qua Pydantic schema
            validated_params = skill.input_schema(**params)
            result = await skill.execute(validated_params)
            return result
        except Exception as e:
            logger.error(f"Lỗi khi thực thi skill {skill.name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
