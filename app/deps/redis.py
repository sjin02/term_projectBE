import redis
from typing import Generator, Optional
from app.core.config import settings

def get_redis() -> Generator[Optional[redis.Redis], None, None]:
    try:
        # Docker의 redis 서비스 URL (환경변수 REDIS_URL 사용)
        pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL, 
            decode_responses=True # 데이터를 문자열로 자동 변환
        )
        client = redis.Redis(connection_pool=pool)
        yield client
        client.close()
    except Exception as e:
        print(f"Redis connection failed: {e}")
        yield None