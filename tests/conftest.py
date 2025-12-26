import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.main import app
from src.deps.db import get_db
from src.deps.redis import get_redis
from src.db.models import User, UserRole, UserStatus, Content, Genre
from src.core.security import hash_password, create_token

# 테스트용 인메모리 SQLite DB
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# DB 초기화 및 세션 오버라이드
@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

# Redis 오버라이드 (테스트에선 Redis 사용 안 함)
@pytest.fixture(name="mock_redis")
def mock_redis_fixture():
    return None

# 클라이언트 생성 (의존성 주입 오버라이드)
@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    
    def get_redis_override():
        yield None

    app.dependency_overrides[get_db] = get_session_override
    app.dependency_overrides[get_redis] = get_redis_override
    
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

# [Helper] 테스트용 유저 생성 및 토큰 발급
@pytest.fixture
def user_token_headers(client: TestClient, session: Session):
    user = User(
        email="test@example.com",
        password_hash=hash_password("password123"),
        nickname="tester",
        role=UserRole.USER,
        status=UserStatus.ACTIVE
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    token = create_token(str(user.id), "access", 60)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_token_headers(client: TestClient, session: Session):
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("admin123"),
        nickname="admin",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE
    )
    session.add(admin)
    session.commit()
    
    token = create_token(str(admin.id), "access", 60)
    return {"Authorization": f"Bearer {token}"}