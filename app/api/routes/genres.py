from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.core.responses import STANDARD_ERROR_RESPONSES, success_response
from app.deps.auth import require_admin
from app.deps.db import get_db
from app.schemas.genres import GenreListResponse, GenreResponse
from app.services import genres as genres_svc

router = APIRouter(
    prefix="/api/v1/genres",
    tags=["genres"],
    responses=STANDARD_ERROR_RESPONSES,
)


@router.get("")
def list_genres(request: Request, db: Session = Depends(get_db)):
    items = genres_svc.list_active(db)
    payload = GenreListResponse(items=[GenreResponse.model_validate(i) for i in items])
    return success_response(
        request,
        message="Genres fetched",
        data=payload.model_dump(),
    )


@router.post("/sync", dependencies=[Depends(require_admin)], status_code=201)
def sync_genres(request: Request, db: Session = Depends(get_db)):
    synced = genres_svc.sync_from_tmdb(db)
    payload = GenreListResponse(items=[GenreResponse.model_validate(g) for g in synced])
    return success_response(
        request,
        status_code=201,
        message="Genres synced from TMDB",
        data=payload.model_dump(),
    )