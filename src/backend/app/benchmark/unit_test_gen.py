import logging
import tempfile
import sys
import os
import subprocess
from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate

logger = logging.getLogger(__name__)

class UnitTestGenerator:
    """
    Sử dụng khả năng viết mã của LLM để sinh ra bộ Unit Test bằng Python
    dựa trên tài liệu Spec kỹ thuật, sau đó thực thi chúng để chẩn đoán.
    """
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.llm = getattr(llm_service, "llm", llm_service)
        
    async def generate_and_run(self, spec_path: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Đọc Spec
        with open(spec_path, "r", encoding="utf-8") as f:
            spec_content = f.read()
            
        logger.info("[UnitTestGen] Đang sinh Unit Test từ Spec...")
        
        prompt = PromptTemplate.from_template(
            "Bạn là một kỹ sư kiểm thử tự động viết mã Python giỏi.\n"
            "Hãy viết một bộ mã nguồn Unit Test bằng Python sử dụng thư viện `unittest` hoặc `pytest` để kiểm chứng "
            "danh sách test cases dưới đây có khớp với tài liệu đặc tả kỹ thuật (Spec) hay không.\n"
            "Mỗi test case trong danh sách đầu vào cần tương ứng với một hàm test trong code.\n\n"
            "Đặc tả Spec:\n"
            "{spec}\n\n"
            "Danh sách các testcase đầu vào:\n"
            "{test_cases}\n\n"
            "Yêu cầu:\n"
            "- Trả về duy nhất mã nguồn Python chạy được, đặt trong codeblock ```python.\n"
            "- Bộ test phải kiểm tra tính hợp lệ của pre_condition, test_step, và expected_result đối chiếu với Spec.\n"
            "- Đảm bảo code chạy độc lập, tự định nghĩa các mock data nếu cần."
        )
        
        try:
            chain = prompt | self.llm
            response = await chain.ainvoke({
                "spec": spec_content[:4000],  # Tránh tràn context thô
                "test_cases": str(test_cases)
            })
            
            code_content = response.content.strip()
            # Trích xuất python code block
            if "```python" in code_content:
                code_content = code_content.split("```python")[1].split("```")[0].strip()
            elif "```" in code_content:
                code_content = code_content.split("```")[1].split("```")[0].strip()
                
            # Ghi code vào file tạm để chạy
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as temp_file:
                temp_file.write(code_content)
                temp_file_path = temp_file.name
                
            logger.info(f"[UnitTestGen] Đang chạy bộ Unit Test tự động tại: {temp_file_path}")
            
            # Chạy file script python vừa sinh ra
            run_result = subprocess.run(
                [sys.executable, temp_file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Xóa file tạm sau khi chạy
            try:
                os.remove(temp_file_path)
            except Exception:
                pass
                
            stdout = run_result.stdout
            stderr = run_result.stderr
            return_code = run_result.returncode
            
            # Phân tích kết quả chạy
            total_tests = len(test_cases)
            # Phân tích chuỗi stderr để đếm số test pass/fail (unittest xuất kết quả vào stderr)
            pass_tests = total_tests
            fail_tests = 0
            
            if "FAILED" in stderr:
                # Phân tích số lượng lỗi đơn giản
                import re
                failures_match = re.search(r"failures=(\d+)", stderr)
                errors_match = re.search(r"errors=(\d+)", stderr)
                
                fails = int(failures_match.group(1)) if failures_match else 0
                errs = int(errors_match.group(1)) if errors_match else 0
                fail_tests = fails + errs
                pass_tests = max(0, total_tests - fail_tests)
                
            pass_rate = (pass_tests / total_tests) * 100 if total_tests > 0 else 100.0
            
            diagnostic_report = (
                f"=== KẾT QUẢ CHẠY UNIT TEST CHI TIẾT ===\n"
                f"Stdout:\n{stdout}\n"
                f"Stderr:\n{stderr}\n"
                f"Mã thoát: {return_code}"
            )
            
            return {
                "total_tests": total_tests,
                "pass_tests": pass_tests,
                "fail_tests": fail_tests,
                "pass_rate": round(pass_rate, 2),
                "diagnostic_report": diagnostic_report
            }
            
        except Exception as e:
            logger.error(f"Lỗi khi sinh/thực thi Unit Test: {e}")
            return {
                "total_tests": len(test_cases),
                "pass_tests": 0,
                "fail_tests": len(test_cases),
                "pass_rate": 0.0,
                "diagnostic_report": f"Lỗi thực thi: {str(e)}"
            }
