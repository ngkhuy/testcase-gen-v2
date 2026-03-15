# Testcase Generator V2

Hệ thống tự động hóa quá trình soạn thảo Technical Specification và tạo Test Cases dựa trên tài liệu yêu cầu (Requirements) sử dụng sức mạnh của AI và RAG (Retrieval-Augmented Generation).

---

## Kiến trúc hệ thống

Dự án được xây dựng theo mô hình **Event-driven** kết hợp với **RAG Pipeline**:

1.  **Watchdog (Observer)**: Giám sát thư mục `raw_doc`. Khi có file mới (`.pdf`, `.md`, `.txt`), quy trình xử lý sẽ tự động kích hoạt.
2.  **Extraction Service (LandingAI ADE)**: Trích xuất nội dung từ các file phức tạp (đặc biệt là PDF có bảng biểu) sang định dạng Markdown chuẩn.
3.  **Spec Generation Service (Ollama LLM)**: Sử dụng các mô hình ngôn ngữ lớn (như Qwen 3.5) để chuyển đổi nội dung thô thành bản **Technical Specification** chuyên nghiệp (Actors, Functional Requirements, Business Rules).
4.  **Vector Storage (FAISS)**: Chẻ nhỏ (chunking) bản Spec và lưu trữ vào Vector Database để phục vụ truy vấn tìm kiếm ngữ cảnh.
5.  **RAG / Testcase Generation**: Cung cấp khả năng truy vấn thông minh và tạo danh sách các Test Cases chi tiết từ bản Spec đã được chuẩn hóa.

---

## Công nghệ sử dụng

*   **Ngôn ngữ**: Python 3.10+
*   **AI Framework**: LangChain (Classic & Core)
*   **LLM & Embeddings**: [Ollama](https://ollama.com/) (Qwen 3.5, embedding models)
*   **Document Parsing**: [LandingAI ADE](https://landing.ai/)
*   **Vector Database**: FAISS (CPU version)
*   **File Monitoring**: Watchdog
*   **Validation**: Pydantic v2

---

## Cấu trúc dự án

```text
testcase-gen-v2/
├── src/
│   ├── backend/             # Source code backend (Python)
│   │   ├── app/
│   │   │   ├── api/         # Route handlers (FastAPI - upcoming)
│   │   │   ├── core/        # Cấu hình hệ thống, Watchdog logic
│   │   │   ├── schemas/     # Pydantic models (Data validation)
│   │   │   ├── services/    # Logic nghiệp vụ (LLM, Vector, ADE...)
│   │   │   └── utils/       # Prompt templates, helpers
│   │   └── main.py          # Entry point - Bộ não điều khiển
│   └── frontend/            # Giao diện người dùng (upcoming)
├── storage/                 # Lưu trữ dữ liệu (Specs, Vector DB, Logs)
├── raw_doc/                 # Thư mục chứa tài liệu đầu vào
├── requirements.txt         # Danh sách thư viện cần thiết
└── extraction.ipynb         # Notebook thử nghiệm quy trình trích xuất
```

---

## Cài đặt & Sử dụng

### 1. Yêu cầu hệ thống
- Đã cài đặt [Ollama](https://ollama.com/) và tải model:
  ```bash
  ollama pull qwen3.5:4b
  ollama pull qwen3-embedding:0.6b
  ```

### 2. Cấu hình môi trường
Tạo file `.env` trong thư mục `src/backend/` dựa trên mẫu `.env.sample`:
```env
LANDING_AI_API_KEY=your_api_key_here
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen3.5:4b
OLLAMA_EMBEDDING_MODEL=qwen3-embedding:0.6b
```

### 3. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 4. Khởi chạy Backend
```bash
cd src/backend
python main.py
```

### 5. Sử dụng
- Copy file yêu cầu (`.pdf`, `.md`, `.txt`) vào thư mục `src/backend/raw_doc/`.
- Theo dõi Terminal để xem AI trích xuất và soạn thảo Spec.
- Bản Spec hoàn thiện sẽ được lưu tại `src/backend/storage/specs/`.

---

## Lộ trình phát triển (Roadmap)
- [x] Thiết lập Project Structure & Package.
- [x] Tích hợp LandingAI ADE & Ollama.
- [x] Triển khai Watchdog tự động hóa pipeline.
- [ ] Xây dựng REST API bằng FastAPI.
- [ ] Phát triển Giao diện người dùng (Frontend).
- [ ] Tích hợp cơ chế Feedback vòng lặp cho LLM.

---
Any issues cause in running this project, please open an issue.

*Phát triển bởi @ngkhuy.*
