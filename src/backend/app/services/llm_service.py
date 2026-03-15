from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
import logging
from ..schemas.testcase_model import TestCaseList
from ..core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            reasoning=False,
            validate_model_on_init=True,
            num_gpu=1,
            num_predict=-1,
            temperature=0.1,
            top_k=50,
            top_p=0.5,
            num_ctx=8192,
            format=TestCaseList.model_json_schema(),
            keep_alive="5m" # 5 phút
        )
        self.parser = JsonOutputParser()
        
    def get_chain(self, prompt_template: str):
        return prompt_template | self.llm | self.parser
    
    def generate(self, prompt_template: str, input_variables: dict):
        try:
            chain = self.get_chain(prompt_template=prompt_template)
            return chain.invoke(input_variables)
        except Exception as e:
            logger.error(f"Lỗi thực thi LLM (Ollama Native): {str(e)}")
            return f"Error: {str(e)}"
