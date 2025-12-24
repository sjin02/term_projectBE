import redis
from typing import Optional

def get_redis() -> Optional[redis.Redis]:
    # Redis 없이 동작하도록 설정
    return None