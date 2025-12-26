# API Design Summary

## 현재 API 개요

- **FastAPI** 기반 REST API로, 모든 인증은 **JWT Bearer Token** (Access/Refresh)으로 보호됩니다.
- 인증 영역(`/auth`)에서는 이메일 로그인, 소셜 로그인(Firebase/Google), 토큰 갱신, 로그아웃 기능을 제공합니다.
- 사용자(`/users`)는 회원가입 후 자신의 프로필 관리, 비밀번호 변경, 회원 탈퇴를 수행할 수 있으며, 자신이 작성한 리뷰와 북마크를 모아볼 수 있습니다.
- 콘텐츠(`/contents`)는 TMDB API와 동기화된 영화 데이터를 제공하며, 검색·필터·정렬 및 상세 조회를 지원합니다. 관리자는 콘텐츠를 강제로 생성하거나 삭제할 수 있습니다.
- 커뮤니티 기능으로 리뷰(`/reviews`) 작성, 수정, 삭제, 좋아요 기능을 제공하며, 북마크(`/bookmarks`) 기능을 통해 관심 콘텐츠를 관리합니다.
- 관리자(`/admin`) 및 장르 관리(`/genres`)를 통해 플랫폼의 메타데이터와 사용자를 관리합니다.
- 운영 안정성을 위해 `/health` 체크와 **Rate Limit**(SlowAPI)이 적용되어 있습니다.

## 엔드포인트 요약

| 분류        | 메서드    | 엔드포인트 (URI)             | 설명 (기능)         | 인증 (Auth)      | Body / Query                   |
| --------- | ------ | ----------------------- | --------------- | -------------- | ------------------------------ |
| Auth      | POST   | /auth/login             | 로그인             | -              | email, password                |
|           | POST   | /auth/logout            | 로그아웃            | Bearer         | -                              |
|           | POST   | /auth/refresh           | 토큰 갱신           | Bearer         | refresh_token                  |
|           | POST   | /auth/firebase          | Firebase 소셜 로그인 | -              | token                          |
|           | POST   | /auth/google            | Google 소셜 로그인   | -              | token                          |
| Users     | POST   | /users/signup           | 회원가입            | -              | email, password, nickname      |
|           | GET    | /users/me               | 내 프로필 조회        | Bearer         | -                              |
|           | PUT    | /users/me               | 내 프로필 수정        | Bearer         | nickname                       |
|           | PATCH  | /users/me/password      | 비밀번호 변경         | Bearer         | current_password, new_password |
|           | GET    | /users/me/reviews       | 내 리뷰 목록 조회      | Bearer         | -                              |
|           | GET    | /users/me/bookmarks     | 내 북마크 목록 조회     | Bearer         | -                              |
|           | DELETE | /users/me               | 회원 탈퇴           | Bearer         | -                              |
| Contents  | GET    | /contents               | 콘텐츠 목록 조회       | -         | Query: page, size              |
|           | GET    | /contents/{id}          | 콘텐츠 상세 조회       | -         | -                              |
|           | GET    | /contents/top-rated     | 평점 높은 순 조회      | -         | -                              |
|           | POST   | /contents               | 콘텐츠 수동 등록       | Bearer (Admin) | tmdb_id                        |
|           | DELETE | /contents/{id}          | 콘텐츠 삭제          | Bearer (Admin) | -                              |
| Admin     | GET    | /users                  | 전체 회원 조회        | Bearer (Admin) | -                              |
|           | GET    | /users/{id}             | 특정 회원 조회        | Bearer (Admin) | -                              |
|           | PATCH  | /users/{id}/role        | 회원 권한 변경        | Bearer (Admin) | Query: role                    |
|           | PATCH  | /users/{id}/status      | 회원 상태 변경        | Bearer (Admin) | Query: status                  |
|           | DELETE | /users/{id}             | 회원 강제 탈퇴        | Bearer (Admin) | -                              |
| Genres    | GET    | /genres                 | 장르 목록 조회        | -              | -                              |
|           | POST   | /genres/sync            | 장르 데이터 동기화      | Bearer (Admin) | -                              |
|           | POST   | /genres                 | 장르 생성           | Bearer (Admin) | name, tmdb_genre_id            |
|           | PATCH  | /genres/{id}            | 장르 수정           | Bearer (Admin) | name, tmdb_genre_id            |
|           | DELETE | /genres/{id}            | 장르 삭제           | Bearer (Admin) | -                              |
| Reviews   | GET    | /contents/{id}/reviews  | 특정 콘텐츠 리뷰 조회    | -              | -                              |
|           | POST   | /contents/{id}/reviews  | 리뷰 작성           | Bearer         | rating, comment                |
|           | GET    | /reviews/popular        | 인기 리뷰 조회        | -         | -                              |
|           | PUT    | /reviews/{id}           | 리뷰 수정           | Bearer         | rating, comment                |
|           | DELETE | /reviews/{id}           | 리뷰 삭제           | Bearer         | -                              |
|           | POST   | /reviews/{id}/likes     | 리뷰 좋아요          | Bearer         | -                              |
|           | DELETE | /reviews/{id}/likes     | 리뷰 좋아요 취소       | Bearer         | -                              |
| Bookmarks | GET    | /bookmarks              | 북마크 목록 조회       | Bearer         | -                              |
|           | POST   | /bookmarks              | 북마크 추가          | Bearer         | content_id                     |
|           | DELETE | /bookmarks/{content_id} | 북마크 취소          | Bearer         | -                              |
| System    | GET    | /health                 | 헬스 체크           | -              | -                              |


## 주요 설계 사항 및 특징

- **계층형 라우터 구조**: 도메인별(Auth, Users, Contents, Reviews 등)로 라우터 파일(`src/api/routes/*.py`)을 분리하여 유지보수성을 높였습니다.
- **엄격한 입력 검증**: Pydantic Schema(`src/schemas`)를 활용하여 Request Body의 유효성을 검사하고, 잘못된 요청 시 `422 Unprocessable Entity` 또는 커스텀 `400 Bad Request`를 반환합니다.
- **표준화된 에러 처리**: 모든 예외 상황에 대해 `{ timestamp, path, status, code, message, details }` 형태의 일관된 JSON 응답을 반환하도록 `STANDARD_ERROR_RESPONSES`를 정의했습니다.
- **하이브리드 데이터 조회**: 콘텐츠 상세 정보 등 실시간성이 중요한 데이터는 DB에 저장된 기본 정보와 함께 TMDB API를 실시간 호출하여 최신 메타데이터(포스터, 줄거리 등)를 병합하여 반환합니다.
- **보안 및 성능**:
    - 비밀번호는 `bcrypt`로 해싱하여 저장합니다.
    - `Redis`를 활용하여 Refresh Token을 관리하고, 로그아웃 시 토큰을 무효화(Blacklist) 처리합니다.
    - `SlowAPI`를 통해 IP 기반 Rate Limiting(분당 100회)을 적용하여 DDoS 공격을 방지합니다.