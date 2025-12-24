#!/bin/bash

# 에러가 나면 스크립트 중단 (선택 사항)
set -e 
echo "⏳ Waiting for database connection at db:5432..."

while ! python3 -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(1); exit(0) if s.connect_ex(('db', 5432)) == 0 else exit(1)"; do
  sleep 1
done
echo "🚀 배포 환경 시작: DB Seeding 시도..."
# 시딩 스크립트 실행
python -m app.db.seed

echo "🔥 메인 서버 실행..."
# Dockerfile의 CMD에서 전달된 명령어(uvicorn ...)를 실행
exec "$@"