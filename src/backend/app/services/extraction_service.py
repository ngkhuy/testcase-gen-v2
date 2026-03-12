### Tạo 1 class extraction với ADE của Lading AI
### API key của Landing AI sẽ được chứa trong file .env

import os
from landingai_ade import AsyncLandingAIADE
from pathlib import Path
from landingai_ade.types import ParseResponse
from schemas.page_content import page_content_schema
from core.config import settings

class ADEExtraction:
    def __init__(self):
        self.api_key = settings.LANDING_AI_API_KEY
        self.client = AsyncLandingAIADE(apikey=self.api_key)
        self.page_content_schema = page_content_schema
        
    def parse_document(self, document_path: str):
        
        # check if document exist
        if not os.path.exists(document_path):
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        # create client parse response
        parse_result: ParseResponse = self.client.parse(
            document=Path(document_path),
            model="dpt-2-latest",
            split="page"
        )

        return parse_result
    
    def extract_content(self, markdown: str):
        extract_result: ParseResponse = self.client.extract(
            schema=self.page_content_schema,
            markdown=markdown
        )
        return extract_result.extraction['content']