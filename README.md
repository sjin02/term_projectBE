# Movie (FastAPI)

FastAPI 기반 영화 DB 백엔드 API 서버입니다.  
JWT 인증, 소셜 로그인, RBAC, CRUD API, 통계 기능을 포함합니다.

---

## Tech Stack

- **Backend**: FastAPI
- **ORM**: SQLModel (선택)
- **DB**: PostgreSQL (prod), SQLite (local)
- **Auth**: JWT, Firebase Auth, Kakao OAuth
- **Cache**: Redis
- **Docs**: Swagger (OpenAPI)
- **Container**: Docker, Docker Compose

---

## Run Locally (Docker 없이)

### 1. 가상환경 생성 및 실행

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
# or
.venv\Scripts\Activate.ps1      # PowerShell
```

### 2.설치

```bash
pip install -r requirements.txt
```

### 3.실행

```bash
python -m uvicorn app.main:app --reload
```
