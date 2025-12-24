from typing import Generator
from sqlmodel import Session
from app.db.session import engine

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI Dependency:
    요청이 들어올 때 DB 세션을 생성하고, 응답 후 닫습니다.
    """
    with Session(engine) as session:
        yield session