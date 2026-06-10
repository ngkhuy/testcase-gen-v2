import logging
from typing import Any, Dict, Optional
from langchain_community.chat_models import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseLLMService
from ...schemas.testcase_model import TestCaseList
from ...core.config import settings

logger = logging.getLogger(__name__)

class OpenAILLMService(BaseLLMService):
    def __init__(self, output_format: str = "json", model_name: Optional[str] = None):
        self.output_format = output_format
        self.model_name = model_name or "gpt-4o-mini"
        api_key = settings.OPENAI_API_KEY
        
        if not api_key:
            logger.warning("Không tìm thấy OPENAI_API_KEY. Sẽ sử dụng giả lập hoặc lỗi nếu gọi API OpenAI.")
            
        if output_format == "json":
            self.parser = JsonOutputParser(pydantic_object=TestCaseList)
            # Khởi tạo OpenAI chat model hỗ trợ JSON Mode
            self.llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=api_key,
                temperature=0.1,
                model_kwargs={"response_format": {"type": "json_object"}}
            )
        else:
            self.parser = StrOutputParser()
            self.llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=api_key,
                temperature=0.1
            )
            
    def get_chain(self, prompt_template: ChatPromptTemplate) -> Any:
        return prompt_template | self.llm | self.parser
        
    def generate(self, prompt_template: ChatPromptTemplate, input_variables: Dict[str, Any] = None) -> Any:
        try:
            chain = self.get_chain(prompt_template=prompt_template)
            return chain.invoke(input_variables or {})
        except Exception as e:
            logger.error(f"Lỗi thực thi OpenAI: {str(e)}")
            return {"error": str(e)}
