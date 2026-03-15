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
    
    BẮT BUỘC:
    1. Câu trả lời PHẢI là một JSON object hợp lệ.
    2. Nếu không có thông tin, hãy trả về mảng test_cases rỗng [] trong JSON.

    CONTEXT:
    {context}

    CÂU HỎI CỦA NGƯỜI DÙNG:
    {human_query}
    """