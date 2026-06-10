import os
import datetime
import logging
from typing import Optional, List
from pydantic import BaseModel, Field
from .base import BaseSkill
from ..schemas.testcase_model import TestCaseList, TestCase
from openpyxl import Workbook
from openpyxl.styles import Font
from ..core.config import settings

logger = logging.getLogger(__name__)

class ExcelExportInput(BaseModel):
    test_cases: List[TestCase] = Field(..., description="Danh sách các test case cần xuất ra Excel")
    base_filename: Optional[str] = Field("testcases", description="Tên file cơ sở (không gồm timestamp)")

class ExcelExportOutput(BaseModel):
    success: bool
    filepath: Optional[str] = None
    filename: Optional[str] = None
    message: str

class ExcelExportSkill(BaseSkill):
    name = "excel_export"
    description = "Xuất danh sách test cases đã được người dùng chốt ra định dạng file Excel (.xlsx)."
    input_schema = ExcelExportInput
    output_schema = ExcelExportOutput
    
    async def execute(self, params: ExcelExportInput) -> ExcelExportOutput:
        try:
            # Tạo tên file kèm timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{params.base_filename}_{timestamp}.xlsx"
            
            # Lưu file tại thư mục storage/exports (để persist ra host qua Docker Volume)
            exports_dir = os.path.join(os.path.dirname(settings.SPEC_DIR), "exports")
            filepath = os.path.join(exports_dir, filename)
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Test Cases"
            
            # Headers
            headers = ["ID", "Title", "Pre-condition", "Steps", "Data", "Expected Result", "Note"]
            ws.append(headers)
            
            # Format header row
            for cell in ws[1]:
                cell.font = Font(bold=True)
                
            # Ghi dữ liệu
            for tc in params.test_cases:
                ws.append([
                    tc.tc_id or "",
                    tc.tc_title or "",
                    tc.pre_condition or "",
                    tc.test_step or "",
                    tc.test_data or "",
                    tc.expected_result or "",
                    tc.note or ""
                ])
                
            # Tự động căn chỉnh độ rộng cột
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except Exception:
                        pass
                adjusted_width = (max_length + 2)
                ws.column_dimensions[column_letter].width = min(adjusted_width, 50)
                
            # Lưu workbook
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            wb.save(filepath)
            
            logger.info(f"Đã xuất thành công file Excel testcases tại: {filepath}")
            return ExcelExportOutput(
                success=True,
                filepath=filepath,
                filename=filename,
                message=f"Đã xuất danh sách test cases ra file Excel: {filename}"
            )
            
        except Exception as e:
            logger.error(f"Lỗi khi xuất file Excel trong skill: {e}")
            return ExcelExportOutput(
                success=False,
                message=f"Không thể xuất file Excel: {str(e)}"
            )
