from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from .testcase import TestCase

class ChatMessage(BaseModel):
    role: str = Field(..., description="Vai trò gửi tin nhắn: 'user' hoặc 'assistant'")
    content: str = Field(..., description="Nội dung tin nhắn")

class ChatRequest(BaseModel):
    query: str = Field(..., description="Câu hỏi hoặc yêu cầu từ người dùng")
    history: List[ChatMessage] = Field(default=[], description="Lịch sử trò chuyện trong phiên hiện tại")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="Phản hồi bằng văn bản từ Agent")
    state: str = Field(..., description="Trạng thái hội thoại hiện tại (ConversationState)")
    test_cases: Optional[List[TestCase]] = Field(None, description="Danh sách testcase nếu đã được sinh hoặc cập nhật")
    excel_file: Optional[str] = Field(None, description="Tên file Excel được xuất ra (nếu có)")
