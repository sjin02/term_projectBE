FROM python:3.10

WORKDIR /app

# 1. pip 최신화
RUN pip install --upgrade pip

# 2. 패키지 설치 (기본 PyPI 사용, 중복 제거)
COPY requirements.txt .

# 타임아웃 시간을 늘려 안정성 확보
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# 3. 소스 복사 및 설정
COPY . .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONPATH=/app

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]