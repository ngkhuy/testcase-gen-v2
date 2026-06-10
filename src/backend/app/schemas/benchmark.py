from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class BenchmarkRequest(BaseModel):
    spec_file: str = Field(..., description="Đường dẫn đến file Spec cần đánh giá")
    approach: str = Field("ragas", description="Hướng tiếp cận benchmark: 'ragas' hoặc 'unit_test'")
    model_name: Optional[str] = Field(None, description="Tên model muốn chạy benchmark")

class RagasScores(BaseModel):
    faithfulness: float = Field(..., description="Độ trung thực so với Spec gốc (0-1)")
    answer_relevance: float = Field(..., description="Độ liên quan của câu trả lời (0-1)")
    context_recall: float = Field(..., description="Khả năng truy hồi ngữ cảnh (0-1)")

class UnitTestScores(BaseModel):
    total_tests: int = Field(..., description="Tổng số testcases được kiểm thử")
    pass_tests: int = Field(..., description="Số testcase vượt qua")
    fail_tests: int = Field(..., description="Số testcase thất bại")
    pass_rate: float = Field(..., description="Tỷ lệ vượt qua (%)")
    diagnostic_report: str = Field(..., description="Báo cáo phân tích lỗi chi tiết")

class PerformanceMetrics(BaseModel):
    latency_sec: float = Field(..., description="Thời gian phản hồi trung bình (giây)")
    inference_speed: Optional[float] = Field(None, description="Tốc độ suy luận (tokens/giây)")
    turns_to_success: int = Field(..., description="Số câu hỏi phản hồi để đạt kết quả chốt")

class BenchmarkResponse(BaseModel):
    success: bool
    approach: str
    model_tested: str
    ragas_scores: Optional[RagasScores] = None
    unit_test_scores: Optional[UnitTestScores] = None
    performance: PerformanceMetrics
    message: str
