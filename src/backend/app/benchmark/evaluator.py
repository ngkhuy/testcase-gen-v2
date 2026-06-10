import logging
import time
from typing import Dict, Any, Optional
from .unit_test_gen import UnitTestGenerator
from .ragas_metrics import RagasEvaluator

logger = logging.getLogger(__name__)

class BenchmarkEvaluator:
    """
    Điều phối toàn bộ quy trình đo đạc (Benchmark) hiệu năng và chất lượng.
    """
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.ut_generator = UnitTestGenerator(llm_service=llm_service)
        self.ragas_evaluator = RagasEvaluator(llm_service=llm_service)
        
    async def run_evaluation(
        self, 
        spec_path: str, 
        approach: str = "ragas", 
        test_cases: list = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"[BenchmarkEvaluator] Bắt đầu đánh giá cho file Spec: {spec_path} qua {approach}")
        
        result = {
            "success": False,
            "approach": approach,
            "latency_sec": 0.0,
            "scores": {}
        }
        
        try:
            if approach == "unit_test":
                # Kích hoạt hướng tiếp cận 1: LLM sinh Unit Tests và thực thi
                scores = await self.ut_generator.generate_and_run(spec_path, test_cases)
                result["scores"] = scores
                result["success"] = True
            else:
                # Kích hoạt hướng tiếp cận 2: Sử dụng Ragas để đo chất lượng văn bản
                scores = await self.ragas_evaluator.evaluate_quality(spec_path, test_cases)
                result["scores"] = scores
                result["success"] = True
                
            result["latency_sec"] = time.time() - start_time
            return result
        except Exception as e:
            logger.error(f"Lỗi trong quá trình chạy Benchmark: {e}", exc_info=True)
            result["error"] = str(e)
            return result
