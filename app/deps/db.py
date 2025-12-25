from typing import Generator
from sqlmodel import Session
from app.db.session import engine

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI Dependency:
    요청이 들어올 때 DB 세션을 생성하고, 응답 후 닫습니다.
    (with 문 대신 try-finally를 사용하여 예외 전파 문제를 방지합니다)
    """
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()