# Stage 1: Build stage
FROM node:18-alpine AS builder

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Kiểm tra nếu thư mục frontend đã có package.json thì mới cài dependencies
COPY src/frontend/package*.json ./

RUN if [ -f package.json ]; then \
        npm ci; \
    else \
        echo "Frontend package.json not found, skipping dependency install."; \
    fi

# Copy mã nguồn frontend vào container
COPY src/frontend/ .

# Build code nếu package.json tồn tại, ngược lại sinh thư mục dist rỗng để tránh lỗi build
RUN if [ -f package.json ]; then \
        npm run build; \
    else \
        echo "Skipping build stage. Copying index.html to dist."; \
        mkdir -p dist && cp index.html dist/index.html; \
    fi

# Stage 2: Serve stage với Nginx
FROM nginx:stable-alpine

# Copy kết quả build từ stage 1 vào thư mục html của Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose cổng 80 cho web
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
