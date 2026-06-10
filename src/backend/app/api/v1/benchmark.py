import logging
import time
from fastapi import APIRouter, Depends, HTTPException
from ...schemas.benchmark import BenchmarkRequest, BenchmarkResponse, RagasScores, UnitTestScores, PerformanceMetrics
from ..deps import get_llm_json_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/run", response_model=BenchmarkResponse)
async def run_benchmark(
    request: BenchmarkRequest,
    llm_service = Depends(get_llm_json_service)
):
    """
    Kích hoạt đánh giá benchmark chất lượng và hiệu năng sinh testcase.
    Hỗ trợ hai hướng: đánh giá RAGAS hoặc tạo Unit Test tự động bằng LLM.
    """
    try:
        start_time = time.time()
        spec_file = request.spec_file
        approach = request.approach.lower().strip()
        model_name = request.model_name or settings.OLLAMA_MODEL if 'settings' in globals() else "qwen3.5:4b"
        
        logger.info(f"Khởi động Benchmark: Model '{model_name}' | Phương thức: {approach}")
        
        # Giả lập xử lý benchmark trong 1.5 giây
        time.sleep(1.5)
        
        latency = time.time() - start_time
        
        if approach == "ragas":
            # Tạo điểm số giả lập cho RAGAS (sử dụng thư viện Ragas trong thực tế)
            ragas_scores = RagasScores(
                faithfulness=0.89,
                answer_relevance=0.91,
                context_recall=0.85
            )
            return BenchmarkResponse(
                success=True,
                approach="ragas",
                model_tested=model_name,
                ragas_scores=ragas_scores,
                performance=PerformanceMetrics(
                    latency_sec=latency,
                    inference_speed=18.5,
                    turns_to_success=2
                ),
                message="Đã hoàn thành đánh giá chất lượng qua bộ đo RAGAS."
            )
            
        elif approach == "unit_test":
            # Tạo kết quả chạy Unit Test tự động giả lập
            unit_scores = UnitTestScores(
                total_tests=15,
                pass_tests=13,
                fail_tests=2,
                pass_rate=86.67,
                diagnostic_report="[Đạt] 13/15 testcases đáp ứng đầy đủ Pre-conditions và Expected Results.\n"
                                  "[Thất bại] TC04 và TC11 thiếu thông tin dữ liệu kiểm thử bắt buộc (test_data)."
            )
            return BenchmarkResponse(
                success=True,
                approach="unit_test",
                model_tested=model_name,
                unit_test_scores=unit_scores,
                performance=PerformanceMetrics(
                    latency_sec=latency,
                    inference_speed=15.2,
                    turns_to_success=3
                ),
                message="Đã hoàn thành sinh và thực thi unit tests chẩn đoán lỗi."
            )
        else:
            raise HTTPException(status_code=400, detail=f"Không hỗ trợ hướng tiếp cận benchmark: {approach}")
            
    except Exception as e:
        logger.error(f"Lỗi khi chạy benchmark: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
