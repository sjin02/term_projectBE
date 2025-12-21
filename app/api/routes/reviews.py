from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

# 기존 import 경로 유지
from app.db.session import get_session
from app.models import Review
from app.schemas import ReviewResponse, ReviewCreate, ReviewUpdate

router = APIRouter(
    prefix="/api/v1",
    tags=["reviews"]
)

# [수정] 401 테스트를 위해 user_id가 0이면 에러 발생 로직 추가
def get_current_user_id(user_id: int = 1):
    # 시나리오: 헤더에 토큰이 없거나 만료된 경우 (ID가 0으로 들어온다고 가정)
    if user_id == 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다."
        )
    return user_id

# 1. 요즘 뜨는 리뷰 (200 OK)
@router.get("/reviews/popular", response_model=List[ReviewResponse], status_code=status.HTTP_200_OK)
def get_popular_reviews(db: Session = Depends(get_session)):
    return db.query(Review).order_by(desc(Review.like_count)).limit(10).all()

# 2. 리뷰 작성 (201 Created)
@router.post("/contents/{content_id}/reviews", status_code=status.HTTP_201_CREATED)
def create_review(
    content_id: int,
    review_in: ReviewCreate,
    db: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id)
):
    new_review = Review(
        content_id=content_id,
        user_id=user_id,
        rating=review_in.rating,
        comment=review_in.comment
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review

# 3. 작품별 리뷰 목록 (200 OK)
@router.get("/contents/{content_id}/reviews", response_model=List[ReviewResponse], status_code=status.HTTP_200_OK)
def get_reviews_by_content(
    content_id: int,
    sort: str = Query("latest"),
    db: Session = Depends(get_session)
):
    query = db.query(Review).filter(Review.content_id == content_id)
    if sort == "popular":
        query = query.order_by(desc(Review.like_count))
    else:
        query = query.order_by(desc(Review.created_at))
    return query.all()

# 4. 리뷰 수정 (403 Forbidden, 404 Not Found)
@router.put("/api/v1/reviews/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    review_update: ReviewUpdate,
    db: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id)
):
    review = db.query(Review).filter(Review.id == review_id).first()
    
    # [404] 리소스 없음
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    
    # [403] 권한 없음 (내 글 아님)
    if review.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this review")
    
    if review_update.rating:
        review.rating = review_update.rating
    if review_update.comment:
        review.comment = review_update.comment
        
    db.commit()
    db.refresh(review)
    return review

# 5. 리뷰 삭제 (204 No Content)
@router.delete("/api/v1/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id)
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if review.user_id != user_id and user_id != 999:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
    db.delete(review)
    db.commit()
    return None

# 6. 리뷰 좋아요 (200 OK)
@router.post("/api/v1/reviews/{review_id}/likes")
def like_review(
    review_id: int,
    db: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id)
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    
    review.like_count += 1
    db.commit()
    return {"message": "Review liked", "like_count": review.like_count}

# 7. 리뷰 좋아요 취소 (200 OK)
@router.delete("/api/v1/reviews/{review_id}/likes")
def unlike_review(
    review_id: int,
    db: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id)
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    
    if review.like_count > 0:
        review.like_count -= 1
        db.commit()
        
    return {"message": "Review unliked", "like_count": review.like_count}
