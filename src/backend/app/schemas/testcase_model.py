from pydantic import BaseModel, Field
from typing import List

class TestCase(BaseModel):
    tc_id: str = Field(..., description="ID của test case (VD: TC01)")
    tc_title: str = Field(..., description="Tên test case")
    pre_condition: str = Field(..., description="Điều kiện tiên quyết")
    test_step: str = Field(..., description="Các bước thực hiện")
    test_data: str = Field(..., description="Dữ liệu test")
    expected_result: str = Field(..., description="Kết quả kỳ vọng")
    note: str = Field(..., description="Ghi chú")

class TestCaseList(BaseModel):
    """Object chứa danh sách các test case"""
    test_cases: List[TestCase]