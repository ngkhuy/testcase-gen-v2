# Hướng Dẫn Quản Lý & Tải Mô Hình Ollama (Ollama Models Guide)

Dự án **Testcase Generator V2** sử dụng Ollama cho việc sinh Technical Spec, trả lời câu hỏi Chat, và tạo Embeddings phục vụ RAG. Để dự án chạy chính xác, bạn cần tải về (pull) hai mô hình chính:
1.  **LLM Chat & Spec Gen:** `qwen3.5:4b` (hoặc model khác tùy cấu hình)
2.  **Embeddings:** `qwen3-embedding:0.6b`

Dưới đây là hướng dẫn chi tiết cách tải và kiểm tra mô hình đối với từng môi trường.

---

## 🛠️ Cách 1: Tải Mô Hình Khi Chạy Bằng Docker Compose (Khuyên dùng)

Nếu bạn chạy ứng dụng qua Docker Compose (`make docker-up`), Ollama sẽ chạy dưới dạng một container có tên `testcase_gen_ollama`. 

Để tải mô hình vào container này, bạn chạy các lệnh sau từ terminal máy chủ (Host):

```bash
# Tải mô hình LLM chính
docker exec -it testcase_gen_ollama ollama pull qwen3.5:4b

# Tải mô hình Embedding
docker exec -it testcase_gen_ollama ollama pull qwen3-embedding:0.6b
```

---

## 💻 Cách 2: Tải Mô Hình Khi Chạy Ollama Cục Bộ Trên Máy Thật (Host OS)

Nếu bạn cài đặt Ollama trực tiếp trên Windows/macOS/Linux thông qua phần mềm Ollama chạy ngầm (không dùng Docker), bạn chỉ cần mở Terminal/PowerShell của máy tính và chạy trực tiếp:

```bash
# Tải mô hình LLM chính
ollama pull qwen3.5:4b

# Tải mô hình Embedding
ollama pull qwen3-embedding:0.6b
```

---

## ⚡ Sử Dụng Phím Tắt Tiện Lợi Bằng Makefile

Chúng tôi đã cấu hình phím tắt trong `Makefile` để tự động phát hiện và tải mô hình phù hợp cho cả 2 môi trường. Bạn chỉ cần chạy lệnh duy nhất tại thư mục gốc:

```bash
make pull-models
```

---

## 🔍 Kiểm Tra Các Mô Hình Đã Tải Thành Công

### Trên Docker:
```bash
docker exec -it testcase_gen_ollama ollama list
```

### Trên máy thật (Host OS):
```bash
ollama list
```

Kết quả hiển thị mong đợi phải có đủ `qwen3.5:4b` và `qwen3-embedding:0.6b` như sau:
```text
NAME                     ID              SIZE      MODIFIED
qwen3.5:4b               e7c050b1d033    2.4 GB    1 minute ago
qwen3-embedding:0.6b     b3c85a2f58e1    650 MB    1 minute ago
```

---

## ⚠️ Khắc Phục Sự Cố (Troubleshooting)

### Lỗi `ConnectionError: Failed to connect to Ollama`
*   **Nguyên nhân:** Container backend không kết nối được tới cổng của Ollama.
*   **Khắc phục:** Đảm bảo container `testcase_gen_ollama` đang chạy (`docker ps`). Nếu dùng Ollama trên máy thật, hãy kiểm tra xem phần mềm Ollama Desktop đã được bật chưa.

### Lỗi GPU không hoạt động (Tốc độ sinh text rất chậm)
*   **Nguyên nhân:** Docker chưa nhận được NVIDIA GPU do thiếu Drivers hoặc Container Toolkit trên máy host.
*   **Khắc phục:** Đảm bảo bạn đã cài đặt **NVIDIA Container Toolkit** trên máy host. Bạn có thể kiểm tra bằng lệnh `nvidia-smi` từ máy host để xác minh driver GPU hoạt động bình thường.
