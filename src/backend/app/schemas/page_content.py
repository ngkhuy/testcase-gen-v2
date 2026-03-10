from pydantic import BaseModel
from landingai_ade.lib import pydantic_to_json_schema

class PageContent(BaseModel):
    content: str | None = None
    
page_content_schema = pydantic_to_json_schema(PageContent)