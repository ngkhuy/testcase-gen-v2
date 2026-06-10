# Hệ Thống Tự Động Sinh Testcase (Testcase Generator V2)

Hệ thống tự động sinh và quản lý testcase dựa trên tài liệu đặc tả yêu cầu (Technical Specification) sử dụng sức mạnh của Trí tuệ nhân tạo (AI), RAG (Retrieval-Augmented Generation), và kiến trúc Agent/Skill hướng đối tượng (OOP).

Dự án đã được refactor toàn diện từ CLI thô sơ sang **Kiến trúc hướng dịch vụ (FastAPI Ready)** với các ràng buộc dữ liệu chặt chẽ bằng Pydantic và xử lý văn bản cục bộ không phụ thuộc bên thứ 3.

---

## 🛠️ Công Nghệ Sử Dụng (Tech Stack)

*   **Ngôn ngữ lập trình:** Python 3.10+
*   **Web Framework:** FastAPI & Uvicorn (Sẵn sàng tích hợp frontend)
*   **AI Framework:** LangChain (Classic & Core)
*   **LLM & Embeddings:** Ollama Cục bộ (Hỗ trợ Qwen, Llama,...) hoặc Cloud APIs (OpenAI/Gemini)
*   **Trích xuất văn bản cục bộ:** `pdfplumber` (PDF) và `python-docx` (DOCX/DOC) - *Hoàn toàn không dùng LandingAI API cũ*.
*   **CSDL Vector & Từ khóa:** FAISS (Vector DB) & SQLite FTS5 (BM25 Keyword Search)
*   **Tìm kiếm nâng cao:** `AdvancedRetriever` (MultiQuery Expansion + Hybrid Search + Flashrank Reranker)
*   **Quản lý Excel:** `openpyxl` (Đóng gói thành ExcelExportSkill)

---

## 📂 Sơ Đồ Cấu Trúc Dự Án Sau Refactor

Xem chi tiết ý nghĩa từng file tại [FOLDER_STRUCT.md](file:///d:/testcase-gen-v2/FOLDER_STRUCT.md).

```text
src/
├── backend/
│   ├── app/
│   │   ├── api/                  # FastAPI Endpoints (/v1/chat, /v1/document, /v1/benchmark)
│   │   ├── core/                 # Cấu hình lõi (Pydantic Settings) & watchdog.py
│   │   ├── schemas/              # Khai báo Pydantic Models truyền nhận chặt chẽ
│   │   ├── services/             # Infrastructure Services (LLM Factory, SQLite, FAISS, Retriever)
│   │   ├── skills/               # OOP Skills (Excel Export, FileReader, Context Inheritance, Sub-Agent)
│   │   └── benchmark/            # Công cụ đo lường chất lượng & tốc độ (Ragas & Unit Test)
│   └── main.py                   # Entrypoint chính (CLI / FastAPI App)
├── deployment/
│   ├── docker/
│   │   ├── backend.Dockerfile    # Dockerfile đóng gói Backend
│   │   └── frontend.Dockerfile   # Dockerfile đóng gói Frontend Nginx
│   └── docker-compose.yaml       # Docker Compose điều phối Backend, Frontend & Ollama
```

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Ứng Dụng

### 1. Chuẩn Bị (Yêu cầu nếu chạy cục bộ)
*   Cài đặt **Ollama** tại: https://ollama.com/
*   Tải về các mô hình cần thiết (Ví dụ sử dụng dòng Qwen):
    ```bash
    ollama pull qwen3.5:4b
    ollama pull qwen3-embedding:0.6b
    ```

### 2. Cấu Hình File Môi Trường `.env`
Sao chép cấu hình mẫu vào file `.env` ở thư mục gốc dự án:
```env
# API Keys (Nếu sử dụng mô hình đám mây, để trống nếu dùng Ollama cục bộ)
OPENAI_API_KEY=""
GEMINI_API_KEY=""

# Cấu hình Ollama Cục Bộ
OLLAMA_BASE_URL="http://localhost:11434/v1"
OLLAMA_MODEL="qwen3.5:4b"
OLLAMA_EMBEDDING_MODEL="qwen3-embedding:0.6b"

# Cấu hình Reranking
RERANK_MODEL="rank-T5-flan"

# Cấu hình Watchdog (Mặc định là False để chạy qua API-first)
ENABLE_WATCHDOG=False
```

---

## 💻 Cách Chạy Cục Bộ (Local Run)

### Cách 1: Chạy nhanh bằng Makefile (Khuyên dùng)
Nếu máy bạn có cài đặt `make`, bạn có thể dùng các phím tắt lệnh sau tại thư mục gốc dự án:
*   **Cài đặt dependencies:**
    ```bash
    make install
    ```
*   **Khởi chạy API Web Server (FastAPI):**
    ```bash
    make run-api
    ```
*   **Khởi chạy Giao diện CLI tương tác (Interactive Chat):**
    ```bash
    make run-cli
    ```
*   **Chạy ứng dụng bằng Docker Compose (chạy ngầm):**
    ```bash
    make docker-up
    ```
*   **Build các Docker images:**
    ```bash
    make build
    ```
*   **Dừng ứng dụng Docker Compose:**
    ```bash
    make docker-down
    ```
*   **Dọn dẹp cache file Python (`__pycache__` & `*.pyc`):**
    ```bash
    make clean
    ```

> [!NOTE]
> Trên hệ điều hành Windows, nếu chưa cài đặt `make`, bạn có thể cài đặt thông qua **Chocolatey** (`choco install make`) hoặc **winget** (`winget install GnuWin32.Make`). Hoặc bạn có thể chạy trực tiếp các lệnh Python/Docker truyền thống dưới đây.

### Cách 2: Chạy bằng Docker Compose
Bạn không cần cài đặt Python hay thư viện trên máy cá nhân, chỉ cần chạy lệnh sau tại thư mục gốc dự án:
```bash
docker compose -f deployment/docker-compose.yaml up --build
```
*   API Backend sẽ lắng nghe tại: `http://localhost:8000`
*   Tài liệu Swagger UI tự động sinh tại: `http://localhost:8000/docs`
*   *Lưu ý:* Mặc định, container backend sẽ tự động kết nối đến container `ollama` được khởi chạy trong Docker Compose thông qua địa chỉ `http://ollama:11434/v1` (đã cấu hình GPU NVIDIA). Nếu bạn muốn dùng Ollama chạy trên máy thật (Host OS) thay vì Docker, bạn chỉ cần sửa hoặc xóa dòng `OLLAMA_BASE_URL` trong phần `environment` của `backend` trong file `docker-compose.yaml` (khi đó nó sẽ dùng mặc định hoặc kết nối qua `http://host.docker.internal:11434/v1` thông qua `extra_hosts`).

### Cách 3: Chạy trực tiếp bằng Python
**Bước 1: Cài đặt các thư viện phụ thuộc**
```bash
pip install -r requirements.txt
```

**Bước 2: Khởi chạy API Web Server (FastAPI)**
```bash
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload
```
*   Truy cập Swagger UI tại: `http://localhost:8000/docs` để test các API `/upload`, `/chat`, `/benchmark` dễ dàng.

**Bước 3: Khởi chạy Giao diện tương tác CLI cũ (Interactive Chat)**
Nếu bạn vẫn muốn chat trực tiếp trên terminal như phiên bản trước:
```bash
python src/backend/main.py
```

---

## 🔄 Luồng Nghiệp Vụ Của Hệ Thống

1.  **Nạp tài liệu (Ingestion):** Người dùng upload tài liệu (.pdf, .docx, .txt) qua API `/v1/document/upload` hoặc ném vào thư mục `storage/raw_docs/` (nếu bật `ENABLE_WATCHDOG=True`).
2.  **Đọc file cục bộ:** Hệ thống sử dụng `pdfplumber`/`python-docx` để đọc văn bản và cấu trúc bảng biểu thô mà không tốn chi phí gọi API LandingAI.
3.  **Tạo Đặc tả (Spec Generation):** LLM tự động soạn thảo bản Spec kỹ thuật chất lượng cao và lưu trữ tại `storage/specs/`.
4.  **Lưu trữ DB:** Văn bản Spec được phân đoạn và nạp song song vào SQLite FTS5 (BM25) và FAISS (Vector DB).
5.  **Hỏi đáp & Sinh Testcase:** Người dùng trò chuyện qua API `/v1/chat`. Hệ thống truy hồi thông tin lai, sinh testcase dạng cấu trúc JSON, hiển thị lên chat.
6.  **Chốt phương án & Xuất Excel:** Khi người dùng chốt phương án ("Đồng ý", "Xuất file"), `SkillManager` sẽ kích hoạt `ExcelExportSkill` để ghi dữ liệu ra file `.xlsx` trong thư mục backend.
7.  **Đo đạc chất lượng (Benchmark):** Gọi API `/v1/benchmark/run` với phương thức `ragas` hoặc `unit_test` để đánh giá chất lượng sinh testcase và tốc độ suy luận của LLM.
