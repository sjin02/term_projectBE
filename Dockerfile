FROM python:3.10

WORKDIR /app

# 패키지 설치 등 기존 내용 ...
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -i https://mirror.kakao.com/pypi/simple -r requirements.txt

# 소스 코드 복사
COPY . .

# [추가] entrypoint.sh 복사 및 실행 권한 부여
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# [변경] ENTRYPOINT 설정
ENTRYPOINT ["/entrypoint.sh"]

# 서버 실행 명령어 (ENTRYPOINT의 "$@" 자리로 들어감)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]