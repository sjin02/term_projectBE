# Architecture

FastAPI + SQLModel (PostgreSQL) + Redis

### 개요

본 프로젝트는 영화/콘텐츠 리뷰 플랫폼을 위한 백엔드 API 서버입니다. Python의 **FastAPI** 프레임워크를 기반으로 비동기 처리를 극대화하였으며, **Docker** 환경에서 구동되도록 설계되었습니다. 인증은 JWT를 사용하며, Redis를 통해 토큰 관리 및 성능 최적화를 수행합니다.

## 전체 아키텍처

```text
       [ Client ]
(Web / Swagger / Postman)
          │
          │ HTTP (REST API)
          ▼
+-------------------------------------------------------+
|                 FastAPI Application                   |
|                                                       |
|   1. Middleware Layer                                 |
|      (CORS, Logging, RateLimit/SlowAPI)               |
|          │                                            |
|   2. Presentation Layer (Router)                      |
|      (Auth, Users, Contents, Reviews Route 등)        |
|      (Request/Response Validation via Pydantic)       |
|          │                                            |
|   3. Business Layer (Services / Core)                 |
|      (TMDB Logic, Security, Error Handling)           |
|          │                                            |
|   4. Data Access Layer (Repository)                   |
|      (CRUD Operations with SQLModel)                  |
+---------------------------+---------------------------+
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    +--------------+ +--------------+ +--------------+
    |  PostgreSQL  | |     Redis    | | External API |
    | (User/Data)  | |(Token/Cache) | | (TMDB, FCM)  |
    +--------------+ +--------------+ +--------------+

```

## 계층별 구조

### 1. Presentation Layer (API Routes)
- **역할**: HTTP 요청 수신, 입력 데이터 파싱 및 검증, 응답 포맷팅
- **위치**: `src/api/routes/*`
- **책임**:
  - `APIRouter`를 사용한 엔드포인트 정의
  - Pydantic Schema(`src/schemas`)를 이용한 Request/Response 검증
  - `Depends`를 활용한 의존성 주입 (DB 세션, 현재 사용자 주입)
  - 예외 발생 시 HTTP 에러로 변환

### 2. Business Logic Layer (Services/Repositories)
- **역할**: 비즈니스 규칙 처리 및 데이터베이스 추상화
- **위치**: `src/repositories/*`, `src/core/*`
- **책임**:
  - **Repositories**: `src/repositories/*`에서 SQLModel을 사용하여 DB CRUD 수행.
  - **Core Logic**: `src/core/security.py` (비밀번호 해시, 토큰 생성), `src/core/tmdb.py` (외부 API 연동) 등 핵심 로직 수행.
  - 트랜잭션 관리 및 데이터 무결성 보장.

### 3. Data Access Layer (DB Models)
- **역할**: 데이터베이스 스키마 정의 및 ORM 매핑
- **위치**: `src/db/models.py`, `src/db/session.py`
- **책임**:
  - `SQLModel` 클래스로 테이블 구조 정의
  - User-Review, Content-Genre 등 관계(Relationship) 설정
  - Alembic을 통한 스키마 마이그레이션 관리

## 보안 아키텍처

### JWT 인증 플로우
1. **로그인**: `POST /auth/login` 요청 시 DB에서 사용자 검증 후 Access Token(30분)과 Refresh Token(7일)을 발급합니다.
2. **토큰 저장**: 보안 강화를 위해 Refresh Token은 **Redis**에 `refresh:{user_id}` 키로 저장하여 관리합니다.
3. **요청 검증**: 모든 보호된 엔드포인트는 `get_current_user` 의존성을 통해 Access Token의 유효성을 검증합니다.
4. **토큰 갱신**: Access Token 만료 시 `POST /auth/refresh`를 통해 Redis에 저장된 Refresh Token과 대조 후 새로운 토큰 쌍을 발급받습니다(Rotation 적용).
5. **로그아웃**: 요청 시 Redis에서 해당 사용자의 Refresh Token을 삭제하여 즉시 무효화합니다.

### 주요 보안 요소
- **비밀번호 암호화**: `bcrypt` 알고리즘을 사용하여 비밀번호를 단방향 해싱 후 저장합니다.
- **CORS 정책**: `CORSMiddleware`를 사용하여 허용된 프론트엔드 도메인(Localhost, 배포 IP 등)에서만 API를 호출할 수 있도록 제한합니다.
- **Rate Limiting**: `SlowAPI`를 적용하여 IP 기반으로 분당 요청 횟수를 제한함으로써 Brute-force 공격 및 DDoS를 방지합니다.
- **환경 변수 관리**: DB 접속 정보, JWT Secret Key 등 민감한 정보는 `.env` 파일로 분리하여 컨테이너 환경 변수로 주입합니다.

## 데이터 플로우 및 예외 처리

### 데이터 흐름
1. **Request**: 클라이언트가 API 요청을 보냄.
2. **Middleware**: 로깅, CORS, Rate Limit 미들웨어가 요청을 1차적으로 처리.
3. **Router**: URL 경로에 맞는 핸들러가 매칭되며, Pydantic 모델을 통해 입력 데이터의 유효성을 검증.
4. **Service/Repository**: 비즈니스 로직을 수행하고 DB 또는 외부 API(TMDB)와 통신하여 데이터를 처리.
5. **Response**: 처리 결과를 Pydantic 모델(Response Schema)에 맞춰 JSON 형태로 변환하여 반환.

### 예외 처리 전략
- `src/core/errors.py`에 정의된 `STANDARD_ERROR_RESPONSES`를 따릅니다.
- 시스템 전반에서 발생하는 모든 예외(DB 오류, 인증 실패, 유효성 검증 실패 등)는 `Exception Handler`가 포착하여 일관된 포맷의 JSON 에러 응답을 반환합니다.
  ```json
  {
    "timestamp": "2024-12-26T12:00:00Z",
    "path": "/api/resource",
    "status": 400,
    "code": "ERROR_CODE",
    "message": "에러 메시지",
    "details": null
  }


## 배포 아키텍처 (Docker)
- **Containerization**: Python 3.10 기반의 Dockerfile을 작성하여 애플리케이션을 경량 컨테이너 이미지로 빌드합니다.

- **Orchestration**: docker-compose.yml을 사용하여 API 서버(api), 데이터베이스(db), 캐시(redis) 컨테이너를 하나의 네트워크로 묶어 통합 관리합니다.

- **CI/CD**: GitHub Actions(ci-cd.yaml)를 통해 Main 브랜치에 코드가 푸시될 때마다 자동으로 테스트를 수행하고 이미지를 빌드합니다.