import logging
from typing import Optional
from .ollama import OllamaLLMService
from .openai import OpenAILLMService
from .base import BaseLLMService

logger = logging.getLogger(__name__)

class LLMFactory:
    """
    Factory Class chịu trách nhiệm khởi tạo nhà cung cấp dịch vụ LLM phù hợp
    dựa trên cấu hình hoặc tham số đầu vào.
    """
    
    @staticmethod
    def get_service(
        provider: str = "ollama", 
        output_format: str = "json", 
        model_name: Optional[str] = None
    ) -> BaseLLMService:
        provider_clean = provider.strip().lower()
        
        logger.info(f"Khởi tạo LLM Provider: '{provider_clean}' | Định dạng: {output_format}")
        
        if provider_clean == "ollama":
            return OllamaLLMService(output_format=output_format, model_name=model_name)
        elif provider_clean in ["openai", "gpt"]:
            return OpenAILLMService(output_format=output_format, model_name=model_name)
        else:
            logger.warning(f"Không hỗ trợ LLM provider '{provider_clean}', tự động chuyển sang Ollama làm mặc định.")
            return OllamaLLMService(output_format=output_format, model_name=model_name)
