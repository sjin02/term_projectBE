# API Design Summary

## 현재 API 개요

- **FastAPI** 기반 REST API로, 모든 인증은 **JWT Bearer Token** (Access/Refresh)으로 보호됩니다.
- 인증 영역(`/auth`)에서는 이메일 로그인, 소셜 로그인(Firebase/Google), 토큰 갱신, 로그아웃 기능을 제공합니다.
- 사용자(`/users`)는 회원가입 후 자신의 프로필 관리, 비밀번호 변경, 회원 탈퇴를 수행할 수 있으며, 자신이 작성한 리뷰와 북마크를 모아볼 수 있습니다.
- 콘텐츠(`/contents`)는 TMDB API와 동기화된 영화 데이터를 제공하며, 검색·필터·정렬 및 상세 조회를 지원합니다. 관리자는 콘텐츠를 강제로 생성하거나 삭제할 수 있습니다.
- 커뮤니티 기능으로 리뷰(`/reviews`) 작성, 수정, 삭제, 좋아요 기능을 제공하며, 북마크(`/bookmarks`) 기능을 통해 관심 콘텐츠를 관리합니다.
- 관리자(`/admin`) 및 장르 관리(`/genres`)를 통해 플랫폼의 메타데이터와 사용자를 관리합니다.
- 운영 안정성을 위해 `/health` 체크와 **Rate Limit**(SlowAPI)이 적용되어 있습니다.

## 주요 엔드포인트 요약

| 영역 | 메서드 & 경로 | 설명 | 권한 |
| :--- | :--- | :--- | :--- |
| **인증** | `POST /auth/login` | 이메일/비밀번호 로그인 (JWT 발급) | ALL |
| | `POST /auth/refresh` | Access Token 만료 시 재발급 | ALL |
| | `POST /auth/social`, `/auth/google` | 소셜(Firebase/Google) 로그인 | ALL |
| | `POST /auth/logout` | 로그아웃 (Refresh Token 폐기) | USER+ |
| **사용자** | `POST /users/signup` | 이메일 회원가입 | ALL |
| | `GET /users/me` | 내 프로필 정보 조회 | USER+ |
| | `PUT /users/me`, `PATCH /users/me/password` | 프로필 수정 및 비밀번호 변경 | USER+ |
| | `DELETE /users/me` | 회원 탈퇴 (Soft Delete) | USER+ |
| **개인화** | `GET /users/me/reviews` | 내가 작성한 리뷰 목록 조회 | USER+ |
| | `GET /users/me/bookmarks` | 내 북마크 목록 조회 | USER+ |
| **콘텐츠** | `GET /contents` | 영화 목록 조회 (검색, 정렬, 필터) | ALL |
| | `GET /contents/{id}` | 영화 상세 정보 조회 (TMDB 연동) | ALL |
| | `GET /contents/top-rated` | 평점 높은 영화 목록 조회 | ALL |
| | `POST /contents`, `DELETE /contents/{id}` | 콘텐츠 수동 생성(복구) 및 삭제 | ADMIN |
| **리뷰** | `GET /contents/{id}/reviews` | 특정 콘텐츠의 리뷰 목록 조회 | ALL |
| | `POST /contents/{id}/reviews` | 리뷰 작성 | USER+ |
| | `PUT /reviews/{id}`, `DELETE /reviews/{id}` | 리뷰 수정 및 삭제 | OWNER/ADMIN |
| | `POST/DELETE /reviews/{id}/likes` | 리뷰 좋아요 추가 및 취소 | USER+ |
| **북마크** | `POST /contents/{id}/bookmark` | 북마크 토글 (추가/취소) | USER+ |
| **관리/기타** | `GET /genres`, `POST /genres` | 장르 목록 조회 및 추가 | ALL/ADMIN |
| | `GET /health` | 서버 헬스 체크 | ALL |

## 주요 설계 사항 및 특징

- **계층형 라우터 구조**: 도메인별(Auth, Users, Contents, Reviews 등)로 라우터 파일(`src/api/routes/*.py`)을 분리하여 유지보수성을 높였습니다.
- **엄격한 입력 검증**: Pydantic Schema(`src/schemas`)를 활용하여 Request Body의 유효성을 검사하고, 잘못된 요청 시 `422 Unprocessable Entity` 또는 커스텀 `400 Bad Request`를 반환합니다.
- **표준화된 에러 처리**: 모든 예외 상황에 대해 `{ timestamp, path, status, code, message, details }` 형태의 일관된 JSON 응답을 반환하도록 `STANDARD_ERROR_RESPONSES`를 정의했습니다.
- **하이브리드 데이터 조회**: 콘텐츠 상세 정보 등 실시간성이 중요한 데이터는 DB에 저장된 기본 정보와 함께 TMDB API를 실시간 호출하여 최신 메타데이터(포스터, 줄거리 등)를 병합하여 반환합니다.
- **보안 및 성능**:
    - 비밀번호는 `bcrypt`로 해싱하여 저장합니다.
    - `Redis`를 활용하여 Refresh Token을 관리하고, 로그아웃 시 토큰을 무효화(Blacklist) 처리합니다.
    - `SlowAPI`를 통해 IP 기반 Rate Limiting(분당 100회)을 적용하여 DDoS 공격을 방지합니다.