from langchain_classic.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_classic.retrievers import BM25Retriever
from langchain_classic.retrievers.document_compressors import FlashrankRerank
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class AdvancedRetriever:
    def __init__(self, vector_service, llm_service, chunks: list):
        self.vector_db = vector_service.vector_db
        self.llm = llm_service.llm
        self.chunks = chunks
        
        logger.info("Đang khởi tạo BM25 index...")
        self.bm25_retriever = BM25Retriever.from_documents(self.chunks)
        
        self.compressor = FlashrankRerank(model=settings.FLASHRANK_MODEL)

    def get_ultimate_retriever(self, k: int = 5):
        self.bm25_retriever.k = k * 2
        faiss_retriever = self.vector_db.as_retriever(search_kwargs={"k": k * 2})
        
        hybrid_retriever = EnsembleRetriever(
            retrievers=[self.bm25_retriever, faiss_retriever],
            weights=[0.4, 0.6]
        )
        
        multi_query_retriever = MultiQueryRetriever.from_llm(
            llm=self.llm,
            retriever=hybrid_retriever,
        )
        
        ultimate_retriever = ContextualCompressionRetriever(
            base_compressor=self.compressor,
            base_retriever=multi_query_retriever
        )
        
        return ultimate_retriever

    def search(self, query: str, k: int = 5):
        """Hàm thực thi chính"""
        retriever = self.get_ultimate_retriever(k)
        return retriever.invoke(query)