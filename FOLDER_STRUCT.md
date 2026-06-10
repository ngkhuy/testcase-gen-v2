# Cấu Trúc Thư Mục Chuẩn Sau Refactor (Target Folder Structure)

Tài liệu này chi tiết hóa cấu trúc thư mục của dự án **Testcase Generator V2** sau khi thực hiện refactor. Cấu trúc này được thiết kế theo hướng đối tượng (OOP), phân lớp trách nhiệm rõ ràng (Clean Architecture), sẵn sàng cho API FastAPI và đồng bộ dữ liệu chặt chẽ với Frontend.

---

## 1. Sơ Đồ Cấu Trúc Tổng Quan

```text
src/
├── backend/
│   ├── app/
│   │   ├── api/                      # Tầng giao tiếp (FastAPI Routers & Controllers)
│   │   │   ├── v1/
│   │   │   │   ├── chat.py           # API endpoint cho hội thoại và tương tác Agent
│   │   │   │   ├── document.py       # API endpoint quản lý file tài liệu (upload, parse, delete)
│   │   │   │   └── benchmark.py      # API endpoint kích hoạt và xem kết quả benchmark
│   │   │   └── deps.py               # Dependency Injection cho FastAPI (DB connections, Services)
│   │   │
│   │   ├── core/                     # Cấu hình lõi & Watchdog hệ thống
│   │   │   ├── config.py             # Quản lý cấu hình & biến môi trường (Pydantic Settings)
│   │   │   └── watchdog.py           # Giám sát thư mục tài liệu tự động (DocWatchdog)
│   │   │
│   │   ├── schemas/                  # Khai báo cấu trúc dữ liệu truyền nhận (Pydantic Models)
│   │   │   ├── chat.py               # Schema đầu vào/ra cho luồng chat (Session, Messages, State)
│   │   │   ├── testcase.py           # Schema chặt chẽ cho TestCase & TestCaseList
│   │   │   └── benchmark.py          # Schema cho cấu hình đo lường và báo cáo kết quả
│   │   │
│   │   ├── services/                 # Tầng hạ tầng kỹ thuật (Infrastructure Services)
│   │   │   ├── llm/                  # Đóng gói kết nối và cấu hình LLM (Factory Pattern)
│   │   │   │   ├── base.py           # Định nghĩa interface BaseLLMService
│   │   │   │   ├── ollama.py         # Cấu hình gọi Ollama cục bộ qua LangChain/Native
│   │   │   │   ├── openai.py         # Cấu hình gọi OpenAI API
│   │   │   │   └── factory.py        # Factory lựa chọn provider tại thời điểm khởi tạo
│   │   │   ├── database/             # Tầng lưu trữ dữ liệu nền tảng
│   │   │   │   ├── vector_db.py      # Quản lý Vector DB (FAISS) - Lưu trữ spec nhúng
│   │   │   │   └── sqlite_db.py      # Quản lý SQLite FTS5 - Tìm kiếm BM25 thô
│   │   │   ├── document_pipeline.py  # Pipeline xử lý tài liệu chung (dùng cho cả API & Watchdog)
│   │   │   ├── spec_gen.py           # Dịch vụ sinh Technical Specification từ Markdown thô
│   │   │   └── retriever.py          # Advanced Retriever (Mở rộng query + Hybrid Search + Flashrank Rerank)
│   │   │
│   │   ├── skills/                   # Các Kỹ năng đóng gói độc lập của Agent (OOP Skills)
│   │   │   ├── base.py               # Interface BaseSkill và SkillManager điều hướng
│   │   │   ├── excel_export.py       # Kỹ năng xuất danh sách TestCase ra file Excel chuyên nghiệp
│   │   │   ├── file_reader.py        # Kỹ năng đọc tài liệu cục bộ (PDF, Word) thay thế LandingAI API
│   │   │   ├── context_inheritance.py # Kỹ năng tóm tắt hội thoại & kế thừa ngữ cảnh khi sắp hết session
│   │   │   └── sub_agent.py          # Kỹ năng chia nhỏ tác vụ thông qua việc tạo sub-agent
│   │   │
│   │   └── benchmark/                # Công cụ Benchmark chất lượng & hiệu năng
│   │       ├── evaluator.py          # Quản lý quy trình chạy thử nghiệm toàn cục
│   │       ├── unit_test_gen.py      # Code sinh & thực thi unit test tự động bằng LLM coding
│   │       └── ragas_metrics.py      # Tích hợp đánh giá chất lượng sinh văn bản với RAGAS
│   │
│   ├── main.py                       # Điểm khởi chạy CLI và cấu hình chạy FastAPI Dev Server
│   └── requirements.txt              # Danh sách các thư viện phụ thuộc (pdfplumber, docx, ragas,...)
├── frontend/                         # Thư mục Frontend (React / Vue / Next.js)
├── deployment/                       # Thư mục chứa cấu hình triển khai dự án
│   ├── docker/
│   │   ├── backend.Dockerfile        # Đóng gói dịch vụ Backend FastAPI
│   │   └── frontend.Dockerfile       # Đóng gói dịch vụ Frontend Nginx
│   └── docker-compose.yaml           # Điều phối container (Backend, Frontend, Ollama)
└── .env                              # Cấu hình biến môi trường toàn cục
```

---

## 2. Chi Tiết Nhiệm Vụ & Quy Tắc Của Từng Thư Mục

### 📂 Tầng 1: `src/backend/app/api/`
Nhiệm vụ chính là tiếp nhận các request HTTP từ Frontend, thực hiện kiểm tra quyền/phân phối tác vụ thông qua các Controller, và trả về dữ liệu định dạng JSON chuẩn.
*   `v1/chat.py`: Tiếp nhận các câu hỏi chat của người dùng, duy trì trạng thái của Agent và trả dữ liệu dạng stream hoặc text.
*   `v1/document.py`: Xử lý Upload/Download tài liệu thủ công từ UI Frontend, đồng bộ hóa dữ liệu với Vector DB.
*   `deps.py`: Quản lý các dependency (như connection pool tới SQLite, instance của Retriever hay LLMService) theo cơ chế Dependency Injection của FastAPI để dễ dàng viết Unit Test cho API.

### 📂 Tầng 2: `src/backend/app/core/`
Chứa các thành phần xương sống của backend, không liên quan trực tiếp đến nghiệp vụ xử lý ngôn ngữ hay kỹ năng agent.
*   `config.py`: Đọc cấu hình từ file `.env` bằng `pydantic-settings`. Tất cả cấu hình hệ thống (như đường dẫn lưu trữ, tên model, API key) đều được tập trung tại đây và ép kiểu nghiêm ngặt.
*   `watchdog.py`: Module chạy nền theo dõi thư mục `storage/raw_docs`. Khi có file mới, nó tự động trích xuất cục bộ, sinh spec và nạp vào DB thông qua `DocumentProcessingPipeline`. **Đây là thành phần tùy chọn**, có thể bật/tắt bằng biến cấu hình `ENABLE_WATCHDOG=True/False` trong `.env`.

### 📂 Tầng 3: `src/backend/app/schemas/`
Đây là khu vực quan trọng để ánh xạ 1:1 với Frontend.
*   Tất cả các schema đầu vào (Requests) và đầu ra (Responses) đều kế thừa từ `pydantic.BaseModel`.
*   Giúp FastAPI tự động sinh tài liệu Swagger UI (`/docs`) chính xác. Frontend có thể sử dụng các công cụ như `openapi-typescript` để sinh mã nguồn kiểu dữ liệu (TypeScript Types) tự động từ Swagger này, tránh sai lệch tham số truyền nhận giữa Backend và Frontend.

### 📂 Tầng 4: `src/backend/app/services/`
Tập hợp các dịch vụ nền tảng (Infrastructure Services), thực hiện các tác vụ kỹ thuật phức tạp nhưng không chứa quy trình nghiệp vụ hội thoại (Conversation Logic).
*   `services/llm/`: Cung cấp giao thức giao tiếp chung với LLM. Dễ dàng đổi từ mô hình chạy local (Ollama) sang mô hình Cloud (OpenAI, Gemini) chỉ bằng cách đổi biến môi trường.
*   `services/database/`: Tách biệt lưu trữ Vector (FAISS) phục vụ tìm kiếm ngữ nghĩa sâu và SQLite (FTS5) phục vụ tìm kiếm từ khóa BM25 chuẩn xác.
*   `services/document_pipeline.py`: Pipeline xử lý tài liệu tập trung (Nhận file -> Đọc cục bộ -> Tạo spec -> Lưu trữ DB). Giúp tái sử dụng giữa API Upload `/v1/document` và `DocWatchdog`.
*   `services/retriever.py`: Giữ nguyên và đóng gói luồng tìm kiếm nâng cao (Hybrid Search kết hợp Vector + Keyword, sau đó Rerank qua Flashrank).

### 📂 Tầng 5: `src/backend/app/skills/`
Chứa các kỹ năng nghiệp vụ thực tế của Agent. Tất cả các skill đều phải thừa kế từ lớp trừu tượng `BaseSkill` và định nghĩa phương thức `execute()`.
*   `excel_export.py`: Chỉ nhận dữ liệu là Pydantic model `TestCaseList` hợp lệ và tạo file Excel.
*   `file_reader.py`: Chứa các parser cục bộ (`pdfplumber` để trích xuất text/table từ PDF, `python-docx` để đọc file Word). Không phụ thuộc API bên thứ 3.
*   `context_inheritance.py`: Thực hiện nghiệp vụ tóm lược ngữ cảnh phiên hội thoại.
*   `sub_agent.py`: Khởi chạy các agent nhỏ có context cô đọng để thực thi công việc phụ trợ.

### 📂 Tầng 6: `src/backend/app/benchmark/`
Chứa toàn bộ logic đánh giá chất lượng sinh test case độc lập với luồng chạy chính của ứng dụng.
*   Dễ dàng kích hoạt thông qua dòng lệnh CLI hoặc API `/v1/benchmark`.
*   Chạy các bài kiểm thử tự động, trích xuất dữ liệu, chạy thư viện RAGAS và lưu báo cáo hiệu năng vào `storage/logs/benchmark/`.

---

## 3. Quy Tắc Lập Trình (Development Guidelines)

> [!IMPORTANT]
> **Quy tắc 1: Hướng đối tượng (OOP) luôn đi đầu**
> Mọi service và skill đều phải được thiết kế dưới dạng Class. Sử dụng kế thừa (Inheritance) để tái sử dụng logic chung và tính đa hình (Polymorphism) để triển khai các logic cụ thể (ví dụ: các LLM providers khác nhau).

> [!TIP]
> **Quy tắc 2: Ràng buộc Pydantic chặt chẽ**
> Tuyệt đối không truyền dữ liệu thô dưới dạng `dict` không rõ cấu trúc qua các tầng dịch vụ. Hãy đóng gói chúng vào các Pydantic Model để dễ debug và tránh lỗi KeyError khi chạy.

> [!WARNING]
> **Quy tắc 3: Bảo toàn tính tương thích ngược**
> Khi chuyển dịch các hàm trong `main.py` cũ và `extraction_service.py` sang cấu trúc mới, hãy tạo các unit test kiểm tra đầu ra để đảm bảo chất lượng tìm kiếm và tạo testcase vẫn giữ nguyên hoặc tốt hơn ban đầu.
