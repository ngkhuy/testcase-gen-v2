import logging
from typing import Generator
from ..core.config import settings
from ..services.embedding_service import EmbeddingService
from ..services.database.vector_db import VectorDatabaseService
from ..services.database.sqlite_db import SQLiteDatabaseService
from ..services.spec_gen import SpecGeneratorService
from ..services.document_pipeline import DocumentProcessingPipeline
from ..services.llm.factory import LLMFactory
from ..services.retriever import AdvancedRetriever
from ..skills.base import SkillManager
from ..skills.excel_export import ExcelExportSkill
from ..skills.file_reader import FileReaderSkill
from ..skills.context_inheritance import ContextInheritanceSkill
from ..skills.sub_agent import SubAgentSkill

logger = logging.getLogger(__name__)

# Singletons được khởi tạo lười (lazy-initialized) để tránh nạp chậm lúc startup
_embedding_service = None
_vector_db = None
_sqlite_db = None
_llm_json_service = None
_llm_text_service = None
_spec_gen_service = None
_document_pipeline = None
_retriever = None
_skill_manager = None

def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

def get_vector_db() -> VectorDatabaseService:
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDatabaseService(embedding_service=get_embedding_service())
    return _vector_db

def get_sqlite_db() -> SQLiteDatabaseService:
    global _sqlite_db
    if _sqlite_db is None:
        _sqlite_db = SQLiteDatabaseService()
    return _sqlite_db

def get_llm_json_service():
    global _llm_json_service
    if _llm_json_service is None:
        # Mặc định sử dụng Ollama cho hệ thống
        _llm_json_service = LLMFactory.get_service(provider="ollama", output_format="json")
    return _llm_json_service

def get_llm_text_service():
    global _llm_text_service
    if _llm_text_service is None:
        _llm_text_service = LLMFactory.get_service(provider="ollama", output_format="text")
    return _llm_text_service

def get_spec_gen_service() -> SpecGeneratorService:
    global _spec_gen_service
    if _spec_gen_service is None:
        _spec_gen_service = SpecGeneratorService(llm_service=get_llm_text_service())
    return _spec_gen_service

def get_document_pipeline() -> DocumentProcessingPipeline:
    global _document_pipeline
    if _document_pipeline is None:
        _document_pipeline = DocumentProcessingPipeline(
            vector_db=get_vector_db(),
            sqlite_db=get_sqlite_db(),
            spec_gen_service=get_spec_gen_service()
        )
    return _document_pipeline

def get_retriever() -> AdvancedRetriever:
    global _retriever
    if _retriever is None:
        _retriever = AdvancedRetriever(
            vector_service=get_vector_db(),
            sqlite_service=get_sqlite_db(),
            llm_service=get_llm_json_service()
        )
    return _retriever

def get_skill_manager() -> SkillManager:
    global _skill_manager
    if _skill_manager is None:
        _skill_manager = SkillManager()
        
        # Khởi tạo và đăng ký các Skill
        llm_json = get_llm_json_service()
        
        _skill_manager.register_skill(ExcelExportSkill())
        _skill_manager.register_skill(FileReaderSkill())
        _skill_manager.register_skill(ContextInheritanceSkill(llm_service=llm_json))
        _skill_manager.register_skill(SubAgentSkill(llm_service=llm_json))
        
    return _skill_manager
