from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.core.docs import success_example, error_example
from app.core.errors import ErrorCode, http_error, success_response, STANDARD_ERROR_RESPONSES
from app.deps.auth import require_admin
from app.deps.db import get_db
from app.repositories import genres as genres_repo
from app.core import tmdb as tmdb_svc
from app.schemas.genres import (
    GenreListResponse, 
    GenreResponse, 
    GenreCreate, 
    GenreUpdate
)

# Prefix는 main.py 설정에 따라 '/genres'가 됩니다.
router = APIRouter(
    prefix="/genres",
    tags=["genres"],
    responses=STANDARD_ERROR_RESPONSES,
)

# 1. 목록 조회 (GET /genres)
@router.get(
    "",
    response_model=GenreListResponse,
    responses={**success_example(GenreListResponse)},
)
def list_genres(request: Request, db: Session = Depends(get_db)):
    items = genres_repo.list_active_genres(db)
    payload = GenreListResponse(items=[GenreResponse.model_validate(i) for i in items])
    return success_response(
        request,
        message="장르 목록 조회 성공",
        data=payload.model_dump(),
    )

# 2. TMDB 동기화 (POST /genres/sync)
@router.post(
    "/sync",
    dependencies=[Depends(require_admin)],
    status_code=201,
    response_model=GenreListResponse,
    responses={**success_example(GenreListResponse, message="동기화 완료", status_code=201)},
)
def sync_genres(request: Request, db: Session = Depends(get_db)):
    tmdb_genres = tmdb_svc.fetch_genre_list()
    synced = genres_repo.upsert_genres_from_tmdb(db, tmdb_genres)
    genres_repo.soft_delete_missing(db, [g["id"] for g in tmdb_genres])
    
    payload = GenreListResponse(items=[GenreResponse.model_validate(g) for g in synced])
    return success_response(
        request,
        status_code=201,
        message="TMDB 장르 동기화가 완료되었습니다.",
        data=payload.model_dump(),
    )

# 3. 생성 (POST /genres) - 관리자 전용
@router.post(
    "",
    dependencies=[Depends(require_admin)],
    status_code=201,
    response_model=GenreResponse,
    responses={
        **success_example(GenreResponse, message="장르 생성 완료", status_code=201),
        409: error_example(409, ErrorCode.DUPLICATE_RESOURCE, "이미 존재하는 장르입니다."),
    },
)
def create_genre(
    request: Request,
    body: GenreCreate,
    db: Session = Depends(get_db)
):
    try:
        genre = genres_repo.create_genre(db, body)
    except ValueError as e:
        raise http_error(409, ErrorCode.DUPLICATE_RESOURCE, str(e))

    return success_response(
        request,
        status_code=201,
        message="장르가 생성되었습니다.",
        data=GenreResponse.model_validate(genre).model_dump(),
    )

# 4. 수정 (PATCH /genres/{genre_id}) - 관리자 전용
@router.patch(
    "/{genre_id}",
    dependencies=[Depends(require_admin)],
    response_model=GenreResponse,
    responses={
        **success_example(GenreResponse, message="장르 수정 완료"),
        404: error_example(404, ErrorCode.RESOURCE_NOT_FOUND, "장르를 찾을 수 없습니다."),
    },
)
def update_genre(
    request: Request,
    genre_id: int,
    body: GenreUpdate,
    db: Session = Depends(get_db)
):
    try:
        updated_genre = genres_repo.update_genre(db, genre_id, body)
    except ValueError as e:
        if "not found" in str(e):
            raise http_error(404, ErrorCode.RESOURCE_NOT_FOUND, "장르를 찾을 수 없습니다.")
        raise http_error(409, ErrorCode.DUPLICATE_RESOURCE, str(e))

    return success_response(
        request,
        message="장르 정보가 수정되었습니다.",
        data=GenreResponse.model_validate(updated_genre).model_dump(),
    )

# 5. 삭제 (DELETE /genres/{genre_id}) - 관리자 전용
@router.delete(
    "/{genre_id}",
    dependencies=[Depends(require_admin)],
    status_code=200,
    responses={
        **success_example(message="장르 삭제 완료"),
        404: error_example(404, ErrorCode.RESOURCE_NOT_FOUND, "장르를 찾을 수 없습니다."),
    },
)
def delete_genre(
    request: Request,
    genre_id: int,
    db: Session = Depends(get_db)
):
    genre = genres_repo.get_genre(db, genre_id)
    if not genre:
        raise http_error(404, ErrorCode.RESOURCE_NOT_FOUND, "장르를 찾을 수 없습니다.")

    genres_repo.delete_genre(db, genre_id)

    return success_response(
        request,
        message="장르가 삭제되었습니다.",
        data={"genreId": genre_id},
    )