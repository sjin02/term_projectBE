FROM python:3.10

WORKDIR /app

# 1. pip 최신화
RUN pip install --upgrade pip

# 2. 패키지 설치 등 기존 내용 - 카카오 미러 사용
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -i https://mirror.kakao.com/pypi/simple -r requirements.txt

# 3. 나머지 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# 4. 소스 복사 및 설정
COPY . .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONPATH=/app

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]