from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
import src.db.models as models
import src.schemas as schemas

# 리뷰 생성
def create_review(db: Session, content_id: int, user_id: int, review_in: schemas.ReviewCreate) -> models.Review:
    # (선택) 해당 컨텐츠가 존재하는지 확인하는 로직 추가 가능
    new_review = models.Review(
        content_id=content_id,
        user_id=user_id,
        rating=review_in.rating,
        comment=review_in.comment
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review

# 작품별 리뷰 조회
def get_reviews_by_content(db: Session, content_id: int, sort: str) -> list[models.Review]:
    query = db.query(models.Review).filter(models.Review.content_id == content_id)
    
    if sort == "popular":
        query = query.order_by(desc(models.Review.like_count))
    else:
        query = query.order_by(desc(models.Review.created_at))
        
    return query.all()

# 인기 리뷰 조회
def get_popular_reviews(db: Session) -> list[models.Review]:
    return db.query(models.Review).order_by(desc(models.Review.like_count)).limit(10).all()

# 리뷰 수정
def update_review(db: Session, review_id: int, user_id: int, review_update: schemas.ReviewUpdate) -> models.Review:
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if review.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this review")
    
    if review_update.rating:
        review.rating = review_update.rating
    if review_update.comment:
        review.comment = review_update.comment
        
    review.updated_at = datetime.now() # 수정 시간 갱신
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

# 리뷰 삭제
def delete_review(db: Session, review_id: int, user_id: int) -> None:
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # 관리자(999) 혹은 본인만 삭제 가능
    if review.user_id != user_id and user_id != 999:
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")
        
    db.delete(review)
    db.commit()

# 리뷰 좋아요
def like_review(db: Session, review_id: int) -> models.Review:
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review.like_count += 1
    db.commit()
    db.refresh(review)
    return review

# 리뷰 좋아요 취소
def unlike_review(db: Session, review_id: int) -> models.Review:
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if review.like_count > 0:
        review.like_count -= 1
        db.commit()
        db.refresh(review)
        
    return review