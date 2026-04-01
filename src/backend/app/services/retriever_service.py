from langchain_classic.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers.document_compressors import FlashrankRerank
import logging
from ..core.config import settings
from flashrank import Ranker

logger = logging.getLogger(__name__)

class AdvancedRetriever:
    def __init__(self, vector_service, sqlite_service, llm_service):
        self.vector_service = vector_service
        self.sqlite_service = sqlite_service
        self.llm = llm_service.llm
        
        # init Ranker
        logger.info("Khởi tạo Flashrank Ranker")
        self.flashrank_client = Ranker(
            model_name=settings.RERANK_MODEL,
            cache_dir=settings.MODELS_DIR,
            max_length=512
        )
        
        logger.info("Khởi tạo Compressor")
        self.compressor = FlashrankRerank(client=self.flashrank_client, top_n=5)
        
    async def _get_expanded_queries(self, query: str) -> list[str]:
        """Sử dụng LLM để mở rộng câu hỏi"""
        try:
            from langchain_core.prompts import PromptTemplate
            prompt = PromptTemplate.from_template(
                "Bạn là trợ lý AI. Hãy tạo ra 3 phiên bản khác nhau của câu hỏi dưới đây "
                "để giúp tìm kiếm tài liệu chính xác hơn. Mỗi phiên bản một dòng.\n"
                "Câu hỏi: {query}\n"
                "Trả lời:"
            )
            chain = prompt | self.llm
            response = await chain.ainvoke({"query": query})
            queries = [query] + response.content.strip().split("\n")
            return [q.strip() for q in queries if q.strip()]
        except Exception as e:
            logger.error(f"Lỗi mở rộng query: {e}")
            return [query]

    async def search(self, query: str, k: int = 5):
        search_k = k * 4
        
        queries = await self._get_expanded_queries(query)
        
        all_docs = []
        seen_contents = set()

        for q in queries:
            vector_results = self.vector_service.search(q, top_k=search_k)
            
            keyword_results = self.sqlite_service.search(q, top_k=search_k)
            
            for doc in vector_results + keyword_results:
                if doc.page_content not in seen_contents:
                    all_docs.append(doc)
                    seen_contents.add(doc.page_content)

        if not all_docs:
            return []

        logger.info(f"Đang Rerank {len(all_docs)} kết quả từ Hybrid Search...")
        self.compressor.top_n = k
        compressed_docs = self.compressor.compress_documents(all_docs, query)
        
        return compressed_docs
