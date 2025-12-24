from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.deps.db import get_db
from app import schemas
from app.repositories import genres as genre_service

router = APIRouter(
    prefix="/api/v1", 
    tags=["Genres"]
)

def verify_admin(user_id: int = 999): 
    if user_id != 999:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="관리자 권한이 필요합니다."
        )
    return user_id

@router.get("/contents/genres", response_model=List[schemas.GenreResponse], summary="장르 목록 조회")
def get_genres(
    db: Session = Depends(get_db),
    simulate_error: bool = False
):
    return genre_service.get_genres(db, simulate_error)

@router.post("/genres", status_code=status.HTTP_201_CREATED, response_model=schemas.GenreResponse)
def create_genre(
    genre_in: schemas.GenreCreate, 
    db: Session = Depends(get_db),
    admin_id: int = Depends(verify_admin)
):
    return genre_service.create_genre(db, genre_in)

@router.patch("/genres/{genre_id}", response_model=schemas.GenreResponse)
def update_genre(
    genre_id: int,
    genre_in: schemas.GenreUpdate,
    db: Session = Depends(get_db),
    admin_id: int = Depends(verify_admin)
):
    return genre_service.update_genre(db, genre_id, genre_in)

@router.delete("/genres/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_genre(
    genre_id: int,
    db: Session = Depends(get_db),
    admin_id: int = Depends(verify_admin)
):
    genre_service.delete_genre(db, genre_id)
    return None