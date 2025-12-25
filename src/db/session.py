from sqlmodel import create_engine
from src.core.config import settings

# DB 연결 설정 (Engine 생성)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    # echo=True  # 쿼리 로그를 보고 싶다면 주석 해제
)