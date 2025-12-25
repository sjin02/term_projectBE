# Movie (FastAPI)

이 프로젝트는 TMDB API를 활용한 영화/TV 시리즈 정보 제공, 리뷰 작성, 북마크 관리 기능을 제공하는 RESTful API 서버입니다.
<br>
FastAPI를 기반으로 구축되었으며, JWT 인증, RBAC 권한 관리, Redis 캐싱, Docker 컨테이너 배포 환경을 포함하고 있습니다.
---

## Tech Stack

- **Backend**: FastAPI
- **ORM**: SQLModel (SQLAlchemy) + Alembic (Migration)
- **DB**: PostgreSQL
- **Auth**: JWT, Firebase Auth, google OAuth
- **Cache**: Redis
- **Docs**: Swagger (OpenAPI)
- **Infra**: GitHub Actions (CI/CD)
- **External API**: TMDB API, Firebase Auth, google OAuth
- **Container**: Docker, Docker Compose

---

## 1. 프로젝트 개요

###  문제 정의
- 방대한 영화 데이터 속에서 사용자에게 유의미한 정보를 제공하고, 소통할 수 있는 플랫폼 부재.
- 기존 영화 API의 단순 정보 제공을 넘어, 자체적인 커뮤니티(리뷰, 평점, 찜하기) 기능 통합 필요.

###  주요 기능
- **영화 정보 관리**: TMDB API 연동을 통한 영화/장르 데이터 동기화 및 관리.
- **사용자 인증**: JWT(Access/Refresh) 기반 로그인, 소셜 로그인(구글/파이어베이스), RBAC(관리자/일반) 권한 제어.
- **커뮤니티 기능**: 영화별 리뷰 작성(CRUD), 평점 부여, 리뷰 좋아요, 인기 리뷰 조회.
- **개인화 기능**: 관심 영화 북마크(찜하기), 마이페이지(내가 쓴 리뷰/북마크 관리).
- **관리자 기능**: 전체 회원 조회, 악성 유저 차단/강제 탈퇴, 권한 변경, 콘텐츠 관리.

---

## 2. 실행 방법

이 프로젝트는 Docker Compose를 통한 실행을 권장합니다.

###  Docker 실행
Redis, DB, API 서버가 한 번에 실행되며 초기 데이터(Seed)가 자동으로 주입됩니다.

```bash
# 1. 프로젝트 클론
git clone <REPOSITORY_URL>
cd term_projectBE

# 2. 환경 변수 설정 (.env.example 복사 후 값 채우기)
cp .env.example .env

# 3. 컨테이너 빌드 및 실행 (Background)
docker-compose up -d --build

# 4. 로그 확인
docker-compose logs -f api
```
## Run Locally (Docker 없이)
Python 3.10+ 환경이 필요합니다.

```bash
# 1. 가상환경 생성 및 활성화
# 1. 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 로컬 DB(Postgres, Redis) 실행 (Docker 활용)
docker-compose up -d db redis

# 4. DB 마이그레이션 및 시드 데이터 주입
alembic upgrade head
python seed/seed.py

# 5. 서버 실행
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 테스트
Pytest를 사용하여 단위 및 통합 테스트를 수행합니다.

```bash
# 전체 테스트 실행
pytest

# 상세 로그와 함께 실행
pytest -vv
```
* 깃허브 액션으로 자동 테스트가 진행됩니다.
---
## 3. 환경변수 설명 (.env)
.env.example 파일을 참고하여 .env 파일을 생성해야 합니다.

| 변수명              | 설명               | 예시 값                                           |
| ---------------- | ---------------- | ---------------------------------------------- |
| DATABASE_URL     | PostgreSQL 연결 주소 | `postgresql://postgres:password@db:5432/movie` |
| JWT_SECRET       | 토큰 서명용 비밀키       | `your_secret_key`                              |
| JWT_ALGORITHM    | 암호화 알고리즘         | `HS256`                                        |
| REDIS_URL        | Redis 연결 주소      | `0.1.0`                           |
| APP_VERSION        | 버전      | `redis://redis:6379`                           |
| BUILD_TIME        | 시간      | `2025-12-20`                           |
| TMDB_API_KEY     | TMDB API 발급 키    | `d1c4...`                                      |
| GOOGLE_CLIENT_ID | 구글 로그인 클라이언트 ID  | `...apps.googleusercontent.com`                |

---
## 4. 배포 주소
JCloud 환경에 배포되어 있으며 아래 주소로 접근 가능합니다.

Base URL: http://113.198.66.75:10093

Swagger UI (API 문서): http://113.198.66.75:10093/docs

Health Check: http://113.198.66.75:10093/health

---
## 5. 인증 플로우
1. 로그인: POST /auth/login 요청 시 access_token(30분)과 refresh_token(7일) 발급.
2. 토큰 검증: Redis 화이트리스트 전략을 사용하여 refresh_token의 유효성을 서버 측에서 2중 검증.
3. 갱신: Access Token 만료 시 POST /auth/refresh로 재발급 요청 (Body에 Refresh Token 포함).
4. 로그아웃: Redis에서 해당 유저의 Refresh Token을 삭제하여 즉시 무효화.

---
## 6. 역할 및 권한 (RBAC)

| 기능                 | USER (일반) | ADMIN (관리자) |
| ------------------ | --------- | ----------- |
| 영화 목록 조회 / 검색      | ✅         | ✅           |
| 영화 상세 정보 조회        | ✅         | ✅           |
| 리뷰 작성 / 수정 / 삭제    | ✅ (본인 것만) | ✅    |
| 리뷰 좋아요 / 북마크       | ✅         | ✅           |
| 영화 데이터 Sync (TMDB) | ❌         | ✅           |
| 영화 생성 / 수정 / 삭제    | ❌         | ✅           |
| 회원 관리 (조회 / 차단)    | ❌         | ✅           |


---
## 7. 예제 계정 (Seed Data)

| 역할      | 이메일                                           | 비밀번호 | 비고            |
| ------- | --------------------------------------------- | ---- | ------------- |
| 관리자     | [admin@example.com](mailto:admin@example.com) | 1234 | 모든 API 접근 가능  |
| 일반 유저 1 | [user1@example.com](mailto:user1@example.com) | 1234 | 리뷰 / 북마크 테스트용 |
| 일반 유저 2 | [user2@example.com](mailto:user2@example.com) | 1234 | 좋아요 테스트용      |


---
## 8. DB 연결 정보 (개발/테스트)
Docker Compose 환경 기준 정보입니다.

* Host: 113.198.66.75 (외부 접속 시 포트포워딩 필요, 현재 내부망 통신)
* Internal Host: db (Docker Network)
* Port: 5432
* Database: movie
* user : postgres
* password 정보는 텍스트 파일로 제출하겠습니다.

---
## 9. 주요 엔드포인트 요약

| 태그        | URL                      | Method | 설명                      |
| --------- | ------------------------ | ------ | ----------------------- |
| Auth      | /auth/login              | POST   | 이메일 로그인                 |
|           | /auth/refresh            | POST   | 토큰 갱신                   |
| Contents  | /contents                | GET    | 영화 목록 조회 (검색 / 정렬 / 필터) |
|           | /contents/{id}           | GET    | 영화 상세 조회                |
| Reviews   | /contents/{id}/reviews   | POST   | 리뷰 작성                   |
|           | /reviews/{id}/likes      | POST   | 리뷰 좋아요                  |
| Genres    | /genres                  | GET    | 장르 목록 조회                |
| Bookmarks | /contents/{id}/bookmarks | POST   | 영화 찜하기                  |
| Admin     | /users                   | GET    | 전체 회원 목록 조회             |
|           | /users/{id}/status       | PATCH  | 회원 상태 변경 (차단 / 복구)      |

* 자세한 api는 postman 문서 혹은 swagger 문서를 확인하세요.
---

## 10. 성능 및 보안 고려사항

### 10.1 표준화된 에러 응답
모든 API 예외 상황에 대해 통일된 JSON 포맷을 반환하여 클라이언트 처리를 용이하게 했습니다.

```JSON
{
  "timestamp": "2025-12-25T12:00:00Z",
  "path": "/api/contents/99999",
  "status": 404,
  "code": "RESOURCE_NOT_FOUND",
  "message": "해당 콘텐츠를 찾을 수 없습니다.",
  "details": null
}
```
### 10.2 보안 (Security)
* 비밀번호 해시: bcrypt를 사용하여 비밀번호를 단방향 암호화하여 저장합니다.

* JWT 인증: Stateless한 인증 방식을 사용하며, Access/Refresh Token rotation을 적용했습니다.

* RBAC: Depends(require_admin) 등을 통해 API 레벨에서 역할을 엄격하게 검증합니다.

* CORS: 허용된 오리진에서만 요청 가능하도록 설정했습니다.

### 10.3 성능 (Performance)
* Redis Caching: Refresh Token을 Redis에 저장하여 탈취된 토큰을 서버에서 즉시 무효화할 수 있도록 보안을 강화했습니다.

* Rate Limiting: slowapi를 사용하여 IP 기반의 요청 제한을 걸어 DDoS 및 어뷰징을 방지했습니다.

* N+1 문제 해결: SQLModel(SQLAlchemy)의 selectinload 등을 활용하여 관계형 데이터 조회 시 쿼리를 최적화했습니다.

* Pagination: 대량의 영화/리뷰 데이터 조회 시 DB 부하를 줄이기 위해 page, size, 쿼리, 정렬 기반 오프셋 페이징을 적용했습니다.

* Soft Delete: deleted_at 컬럼을 사용하여 데이터를 물리적으로 삭제하지 않고 보존하여, 실수로 인한 데이터 손실 방지 및 복구 기능을 구현했습니다.


### 10.4 CI/CD (추가점수 기능 구현)
GitHub Actions: .github/workflows/ci-cd.yaml을 통해 main 브랜치 푸시 시 자동 테스트 및 Docker 이미지 빌드가 수행됩니다.

---

## 11. 한계 및 개선 계획
* TMDB 의존성: 외부 API 장애 시 영화 정보 갱신이 불가능함. -> 배치(Batch) 작업을 통해 주기적으로 데이터를 백업하는 로직 강화 필요.
* 추천 알고리즘: 현재는 단순 평점/최신순 정렬만 제공. -> 사용자 활동(북마크, 리뷰) 기반의 협업 필터링 추천 도입 예정.