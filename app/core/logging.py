import logging
import sys

def setup_logging(level: str = "INFO") -> None:
    """
    앱 전체 로깅 기본 설정.
    - stdout으로 출력
    - 포맷 통일
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

# 여기서 export 되는 logger (다른 파일들이 import해서 씀)
logger = logging.getLogger("app")