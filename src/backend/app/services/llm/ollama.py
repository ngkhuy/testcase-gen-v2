import logging
import re
from typing import Any, Dict, Optional
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseLLMService
from ...schemas.testcase_model import TestCaseList
from ...core.config import settings

logger = logging.getLogger(__name__)

class OllamaLLMService(BaseLLMService):
    def __init__(self, output_format: str = "json", model_name: Optional[str] = None):
        self.output_format = output_format
        self.model_name = model_name or settings.OLLAMA_MODEL
        
        if output_format == "json":
            self.parser = JsonOutputParser(pydantic_object=TestCaseList)
            self.llm = ChatOllama(
                model=self.model_name,
                base_url=settings.OLLAMA_BASE_URL,
                reasoning=False,
                validate_model_on_init=False,
                temperature=0.1,
                top_k=50,
                top_p=0.5,
                num_ctx=8192,
                format=TestCaseList.model_json_schema(),
                keep_alive="10m"
            )
        else:
            self.parser = StrOutputParser()
            self.llm = ChatOllama(
                model=self.model_name,
                base_url=settings.OLLAMA_BASE_URL,
                reasoning=False,
                validate_model_on_init=False,
                temperature=0.1,
                top_k=50,
                top_p=0.5,
                num_ctx=8192,
                keep_alive="10m"
            )
            
    def get_chain(self, prompt_template: ChatPromptTemplate) -> Any:
        return prompt_template | self.llm | self.parser
        
    def generate(self, prompt_template: ChatPromptTemplate, input_variables: Dict[str, Any] = None) -> Any:
        try:
            chain = self.get_chain(prompt_template=prompt_template)
            return chain.invoke(input_variables or {})
        except Exception as e:
            error_msg = str(e)
            if "OutputParserException" in error_msg or "Invalid json" in error_msg:
                logger.warning(f"Ollama không trả về JSON chuẩn: {error_msg[:100]}...")
                match = re.search(r"content='(.*?)'", error_msg, re.DOTALL)
                if match:
                    return {"error": "JSON parsing failed", "raw_content": match.group(1)}
            
            logger.error(f"Lỗi thực thi Ollama: {str(e)}")
            return {"error": str(e)}
