import redis
from typing import Generator, Optional
from app.core.config import settings

def get_redis() -> Generator[Optional[redis.Redis], None, None]:
    client = None
    try:
        # 1. Redis 연결 생성 시도
        pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL, 
            decode_responses=True
        )
        client = redis.Redis(connection_pool=pool)
        # client.ping() # 연결 확인 필요 시 주석 해제
    except Exception as e:
        # 연결 단계 에러만 출력하고 None 반환
        print(f"Redis connection failed: {e}")
        yield None
        return

    # 2. 클라이언트 제공 (여기서는 예외를 잡지 않음)
    try:
        yield client
    finally:
        # 3. 리소스 정리
        if client:
            client.close()