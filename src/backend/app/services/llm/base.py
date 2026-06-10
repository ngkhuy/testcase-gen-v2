from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from langchain_core.prompts import ChatPromptTemplate

class BaseLLMService(ABC):
    """
    Interface cơ sở trừu tượng cho tất cả các dịch vụ LLM.
    """
    
    @abstractmethod
    def __init__(self, output_format: str = "json", model_name: Optional[str] = None):
        """Khởi tạo LLM service với định dạng output và tên model"""
        pass
        
    @abstractmethod
    def get_chain(self, prompt_template: ChatPromptTemplate) -> Any:
        """Trả về chuỗi xử lý LangChain (Chain)"""
        pass
        
    @abstractmethod
    def generate(self, prompt_template: ChatPromptTemplate, input_variables: Dict[str, Any] = None) -> Any:
        """Thực thi sinh văn bản/JSON từ prompt và variables"""
        pass
