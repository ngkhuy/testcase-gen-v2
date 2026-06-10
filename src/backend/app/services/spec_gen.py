import os
import logging
from langchain_core.prompts import ChatPromptTemplate
from ..utils.prompt_template import create_spec_generation_prompt, get_system_prompt
from ..core.config import settings

logger = logging.getLogger(__name__)

class SpecGeneratorService:
    def __init__(self, llm_service):
        # Chấp nhận cả LLMService thô hoặc instance từ BaseLLMService của chúng ta
        self.llm_service = llm_service
        self.llm = getattr(llm_service, "llm", llm_service)
        self.spec_dir = settings.SPEC_DIR

    def generate_detailed_spec(self, raw_markdown: str, file_name: str):
        sys_prompt = get_system_prompt(role="ba")
        user_prompt_template = create_spec_generation_prompt()

        chat_template = ChatPromptTemplate.from_messages([
            ("system", sys_prompt),
            ("human", user_prompt_template)
        ])

        logger.info(f"LLM đang soạn thảo Spec cho {file_name}...")
        
        # Hỗ trợ cả hai cách gọi: dùng wrapper generate hoặc dùng invoke trực tiếp của langchain
        if hasattr(self.llm_service, "generate"):
            # Đối với LLMService cũ hoặc wrapper của chúng ta
            messages = chat_template.format_messages(raw_markdown=raw_markdown)
            # Một số LLMService generate nhận template và variables
            try:
                response = self.llm_service.generate(chat_template, {"raw_markdown": raw_markdown})
                content = response if isinstance(response, str) else response.content
            except Exception:
                response = self.llm.invoke(messages)
                content = response.content
        else:
            response = self.llm.invoke(chat_template.format_messages(raw_markdown=raw_markdown))
            content = response.content
        
        spec_file_name = f"spec_{file_name.replace('.pdf', '').replace('.docx', '').replace('.doc', '').replace('.md', '')}.md"
        spec_path = os.path.join(self.spec_dir, spec_file_name)
        
        os.makedirs(self.spec_dir, exist_ok=True)
        with open(spec_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return spec_path, content
