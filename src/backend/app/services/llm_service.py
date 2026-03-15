from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
import logging
from ..schemas.testcase_model import TestCaseList
from ..core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, output_format: str = "json"):
        if output_format == "json":
            self.parser = JsonOutputParser()
            self.llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            reasoning=False,
            validate_model_on_init=True,
            temperature=0.1,
            top_k=50,
            top_p=0.5,
            num_ctx=8192,
            format=TestCaseList.model_json_schema(),
            keep_alive="5m" # 5 phút
        )
        else:
            self.parser = StrOutputParser()
            self.llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            reasoning=False,
            validate_model_on_init=True,
            temperature=0.1,
            top_k=50,
            top_p=0.5,
            num_ctx=8192,
            keep_alive="5m" # 5 phút
        )
        
    def get_chain(self, prompt_template: str):
        return prompt_template | self.llm | self.parser
    
    def generate(self, prompt_template, input_variables: dict = None):
        try:
            chain = self.get_chain(prompt_template=prompt_template)
            return chain.invoke(input_variables or {})
        except Exception as e:
            # Nếu là lỗi Parsing (không phải JSON), ta cố gắng trả về thông tin hữu ích hơn
            error_msg = str(e)
            if "OutputParserException" in error_msg or "Invalid json" in error_msg:
                logger.warning(f"Model không trả về JSON chuẩn: {error_msg[:100]}...")
                # Trả về chuỗi thô nếu Parser thất bại nhưng ta muốn thấy nội dung
                import re
                match = re.search(r"content='(.*?)'", error_msg, re.DOTALL)
                if match:
                    return f"Raw Response (JSON Parsing Failed): {match.group(1)}"
            
            logger.error(f"Lỗi thực thi LLM (Ollama Native): {str(e)}")
            return f"Error: {str(e)}"
