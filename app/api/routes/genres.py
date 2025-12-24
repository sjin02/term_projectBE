from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.core.docs import success_example
from app.core.errors import success_response, STANDARD_ERROR_RESPONSES
from app.deps.auth import require_admin
from app.deps.db import get_db
from app.repositories import genres as genres_repo
from app.core import tmdb as tmdb_svc
from app.schemas.genres import GenreListResponse, GenreResponse

router = APIRouter(
    prefix="/genres",
    tags=["genres"],
    responses=STANDARD_ERROR_RESPONSES,
)


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


@router.post(
    "/sync",
    dependencies=[Depends(require_admin)],
    status_code=201,
    response_model=GenreListResponse,
    responses={**success_example(GenreListResponse, message="동기화 완료", status_code=201)},
)
def sync_genres(request: Request, db: Session = Depends(get_db)):
    # 1. TMDB Fetch
    tmdb_genres = tmdb_svc.fetch_genre_list()
    # 2. Upsert
    synced = genres_repo.upsert_genres_from_tmdb(db, tmdb_genres)
    # 3. Delete Missing
    genres_repo.soft_delete_missing(db, [g["id"] for g in tmdb_genres])
    
    payload = GenreListResponse(items=[GenreResponse.model_validate(g) for g in synced])
    return success_response(
        request,
        status_code=201,
        message="TMDB 장르 동기화가 완료되었습니다.",
        data=payload.model_dump(),
    )