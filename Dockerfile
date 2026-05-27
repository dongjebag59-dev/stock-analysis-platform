FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 (matplotlib 한글 폰트 지원)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스 복사
COPY . .

# 포트 노출
EXPOSE 8501 8502
