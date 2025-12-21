from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models, schemas

router = APIRouter(
    prefix="/api/v1", 
    tags=["Genres"]
)

# 관리자 권한 체크
def verify_admin(user_id: int = 999): 
    if user_id != 999:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="관리자 권한이 필요합니다."
        )
    return user_id

# 1. 장르 목록 조회 (200 OK, 500 Internal Server Error)
@router.get("/contents/genres", response_model=List[schemas.GenreResponse], summary="장르 목록 조회")
def get_genres(
    db: Session = Depends(get_db),
    simulate_error: bool = False # 과제용 에러 트리거 파라미터
):
    # [500 Error 시뮬레이션]
    # 과제용: 파라미터로 simulate_error=True가 오면 서버 내부 오류 발생
    if simulate_error:
        # FastAPI는 Python 코드 에러를 자동으로 500으로 처리하지만,
        # 명시적으로 보여주기 위해 500 예외 발생
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DB 연결에 실패했습니다. (테스트용)"
        )

    return db.query(models.Genre).filter(models.Genre.is_active == True).all()

# 2. 장르 생성 (201 Created, 400 Bad Request, 409 Conflict, 503 Service Unavailable)
@router.post("/genres", status_code=status.HTTP_201_CREATED, response_model=schemas.GenreResponse)
def create_genre(
    genre_in: schemas.GenreCreate, 
    db: Session = Depends(get_db),
    admin_id: int = Depends(verify_admin)
):
    # [503 Error 시뮬레이션]
    # 시나리오: 장르명이 'maintenance'면 점검 중이라고 응답
    if genre_in.name == "maintenance":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="현재 시스템 점검 중입니다."
        )

    # [400 Bad Request]
    # 시나리오: 장르명이 너무 짧으면 잘못된 요청 처리
    if len(genre_in.name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="장르명은 2글자 이상이어야 합니다."
        )

    # [409 Conflict]
    # 시나리오: 이미 있는 장르명
    existing = db.query(models.Genre).filter(models.Genre.name == genre_in.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 존재하는 장르입니다."
        )

    new_genre = models.Genre(name=genre_in.name)
    db.add(new_genre)
    db.commit()
    db.refresh(new_genre)
    return new_genre

# 3. 장르 수정 (200 OK)
@router.patch("/genres/{genre_id}", response_model=schemas.GenreResponse)
def update_genre(
    genre_id: int,
    genre_in: schemas.GenreUpdate,
    db: Session = Depends(get_db),
    admin_id: int = Depends(verify_admin)
):
    genre = db.query(models.Genre).filter(models.Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genre not found")
    
    if genre_in.name:
        genre.name = genre_in.name
        
    db.commit()
    db.refresh(genre)
    return genre

# 4. 장르 삭제 (204 No Content)
@router.delete("/genres/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_genre(
    genre_id: int,
    db: Session = Depends(get_db),
    admin_id: int = Depends(verify_admin)
):
    genre = db.query(models.Genre).filter(models.Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genre not found")
    
    genre.is_active = False 
    db.commit()
    return None
