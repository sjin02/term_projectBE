from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.deps.db import get_db
from app import schemas # schemas 경로 확인
# [중요] 서비스 모듈 임포트
from app.repositories import reviews as review_service 

router = APIRouter(
    prefix="/api/v1",
    tags=["reviews"]
)

def get_current_user_id(user_id: int = 1):
    if user_id == 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다."
        )
    return user_id

@router.get("/reviews/popular", response_model=List[schemas.ReviewResponse], status_code=status.HTTP_200_OK)
def get_popular_reviews(db: Session = Depends(get_db)):
    return review_service.get_popular_reviews(db)

@router.post("/contents/{content_id}/reviews", status_code=status.HTTP_201_CREATED)
def create_review(
    content_id: int,
    review_in: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return review_service.create_review(db, content_id, user_id, review_in)

@router.get("/contents/{content_id}/reviews", response_model=List[schemas.ReviewResponse], status_code=status.HTTP_200_OK)
def get_reviews_by_content(
    content_id: int,
    sort: str = Query("latest"),
    db: Session = Depends(get_db)
):
    return review_service.get_reviews_by_content(db, content_id, sort)

@router.put("/api/v1/reviews/{review_id}", response_model=schemas.ReviewResponse)
def update_review(
    review_id: int,
    review_update: schemas.ReviewUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return review_service.update_review(db, review_id, user_id, review_update)

@router.delete("/api/v1/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    review_service.delete_review(db, review_id, user_id)
    return None

@router.post("/api/v1/reviews/{review_id}/likes")
def like_review(
    review_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    review = review_service.like_review(db, review_id)
    return {"message": "Review liked", "like_count": review.like_count}

@router.delete("/api/v1/reviews/{review_id}/likes")
def unlike_review(
    review_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    review = review_service.unlike_review(db, review_id)
    return {"message": "Review unliked", "like_count": review.like_count}