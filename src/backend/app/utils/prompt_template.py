def get_system_prompt(role: str = "ba") -> str:
    prompts = {
        "ba": "Bạn là một Senior Business Analyst chuyên nghiệp. Câu trả lời của bạn phải logic, cấu trúc và mang tính kỹ thuật cao.",
        "tester": "Bạn là một Senior QC/Tester. Bạn tập trung vào các trường hợp kiểm thử, điều kiện biên và trải nghiệm người dùng."
    }
    return prompts.get(role, prompts["ba"])

def create_spec_generation_prompt() -> str:
    return """
    Dựa trên nội dung Markdown từ tài liệu yêu cầu (Requirement) dưới đây, hãy soạn thảo một bản Technical Specification chuẩn.
    
    Yêu cầu:
    - Khâu các trang bị đứt đoạn (được đánh dấu bằng START PAGE).
    - Cấu trúc: Narrative, Actor, Functional Requirements (đánh ID chi tiết), Business Rules.
    - Làm sạch các thẻ HTML/Anchor ID còn sót lại.

    NỘI DUNG RAW:
    {raw_markdown}
    """

def create_rag_query_prompt() -> str:
    return """
    Sử dụng thông tin từ ngữ cảnh (Context) dưới đây để hỗ trợ người dùng. 
    
    BẮT BUỘC TRẢ VỀ JSON VỚI CÁC KEY SAU:
    - test_cases: mảng danh sách các test case. 
    Trong mỗi test case phải có đúng các key này:
    - tc_id: string (ID test case, ví dụ: TC01)
    - tc_title: string (Tên test case)
    - pre_condition: string (Điều kiện tiên quyết)
    - test_step: string (Các bước thực hiện)
    - test_data: string (Dữ liệu test)
    - expected_result: string (Kết quả kỳ vọng)
    - note: string (Ghi chú nếu có)

    Nếu không có thông tin, hãy trả về {{"test_cases": []}}.
    Tuyệt đối không trả về bất kỳ text nào ngoài JSON.

    CONTEXT:
    {context}

    CÂU HỎI CỦA NGƯỜI DÙNG:
    {human_query}
    """