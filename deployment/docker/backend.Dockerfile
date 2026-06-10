# Sử dụng image Python chính thức (slim version để tối ưu dung lượng)
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết (cho sqlite và build dependencies)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements.txt từ root dự án (context build là thư mục gốc)
COPY requirements.txt .

# Cài đặt các dependencies của Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn src và cấu hình liên quan vào container
COPY src/ ./src
COPY .env .

# Thiết lập cổng mạng ứng dụng FastAPI
EXPOSE 8000

# Biến môi trường mặc định cho Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Mặc định khởi chạy API server bằng Uvicorn
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
