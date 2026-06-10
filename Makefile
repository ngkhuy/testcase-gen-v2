# Makefile cho Testcase Generator V2

.PHONY: help install build pull-models run-api run-cli docker-up docker-down clean

help:
	@echo "Các lệnh khả dụng:"
	@echo "  make install      - Cài đặt các thư viện phụ thuộc từ requirements.txt"
	@echo "  make build        - Build các docker images bằng Docker Compose"
	@echo "  make pull-models  - Tải về (pull) các mô hình LLM và Embedding của Ollama"
	@echo "  make run-api      - Khởi chạy API Web Server (FastAPI)"
	@echo "  make run-cli      - Khởi chạy Giao diện tương tác CLI (Interactive Chat)"
	@echo "  make docker-up    - Khởi chạy ứng dụng bằng Docker Compose"
	@echo "  make docker-down  - Dừng ứng dụng Docker Compose"
	@echo "  make clean        - Dọn dẹp các file cache Python (__pycache__)"

install:
	pip install -r requirements.txt

build:
	docker compose -f deployment/docker-compose.yaml build

pull-models:
	@docker exec -i testcase_gen_ollama ollama pull qwen3.5:4b || ollama pull qwen3.5:4b
	@docker exec -i testcase_gen_ollama ollama pull qwen3-embedding:0.6b || ollama pull qwen3-embedding:0.6b

run-api:
	uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload

run-cli:
	python src/backend/main.py

docker-up:
	docker compose -f deployment/docker-compose.yaml up -d

docker-down:
	docker compose -f deployment/docker-compose.yaml down

clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__') if p.is_dir()]; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc') if p.is_file()]"
