from langchain_classic.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_classic.retrievers import BM25Retriever
from langchain_classic.retrievers.document_compressors import FlashrankRerank
import logging
from core.config import settings
from flashrank import Ranker

logger = logging.getLogger(__name__)

class AdvancedRetriever:
    def __init__(self, vector_service, llm_service, chunks: list):
        self.vector_db = vector_service.vector_db
        self.llm = llm_service.llm
        self.chunks = chunks
        
        # init Ranker
        logger.info("Khởi tạo Flashrank Ranker")
        self.flashrank_client = Ranker(
            model_name="rank-T5-flan",
            cache_dir="models/ranker_model_cache",
            max_length=512
        )
        
        logger.info("Khởi tạo Compressor")
        self.compressor = FlashrankRerank(client=self.flashrank_client, top_n=5)
        
        logger.info("Đang khởi tạo BM25 index...")
        self.bm25_base = BM25Retriever.from_documents(self.chunks)
        
        self._cached_k = None
        self._cache_retriever = None
        
    def _build_retriever_chain(self, k: int):
        """Xây dựng toàn bộ chain logic"""
        search_k = k * 4 
        
        self.bm25_base.k = search_k
        faiss_retriever = self.vector_db.as_retriever(search_kwargs={"k": search_k})
        
        hybrid_retriever = EnsembleRetriever(
            retrievers=[self.bm25_base, faiss_retriever],
            weights=[0.4, 0.6] # ưu tiên meaning search
        )
        
        multi_query_retriever = MultiQueryRetriever.from_llm(
            llm=self.llm,
            retriever=hybrid_retriever,
        )
        
        self.compressor.top_n = k 
        
        ultimate_retriever = ContextualCompressionRetriever(
            base_compressor=self.compressor,
            base_retriever=multi_query_retriever
        )
        return ultimate_retriever
    async def search(self, query: str, k: int = 5):
        """Hàm thực thi chính với cơ chế Lazy Loading / Caching"""
        if self._cache_retriever is None or self._cached_k != k:
            self._cache_retriever = self._build_retriever_chain(k)
            self._cached_k = k
            
        return await self._cache_retriever.ainvoke(query)