from .llm_service import LLMService
from ..utils.prompt_template import create_spec_generation_prompt, get_system_prompt
from langchain_core.messages import SystemMessage, HumanMessage
import os
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

class SpecGeneratorService:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service.llm
        self.spec_dir = settings.SPEC_DIR

    def generate_detailed_spec(self, raw_markdown: str, file_name: str):
        sys_prompt = get_system_prompt(role="ba")
        user_prompt_template = create_spec_generation_prompt()

        from langchain_core.prompts import ChatPromptTemplate
        chat_template = ChatPromptTemplate.from_messages([
            ("system", sys_prompt),
            ("human", user_prompt_template)
        ])

        logger.info(f"LLM đang soạn thảo Spec cho {file_name}...")
        response = self.llm.invoke(chat_template.format_messages(raw_markdown=raw_markdown))
        
        spec_file_name = f"spec_{file_name.replace('.pdf', '').replace('.md', '')}.md"
        spec_path = os.path.join(self.spec_dir, spec_file_name)
        
        with open(spec_path, "w", encoding="utf-8") as f:
            f.write(response.content)
            
        return spec_path, response.content