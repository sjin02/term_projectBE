from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import src.db.models as models

# 찜하기 추가
def create_bookmark(db: Session, user_id: int, content_id: int) -> None:
    # 중복 체크
    existing = db.query(models.Bookmark).filter(
        models.Bookmark.user_id == user_id,
        models.Bookmark.content_id == content_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Already bookmarked")

    new_bookmark = models.Bookmark(user_id=user_id, content_id=content_id)
    db.add(new_bookmark)
    db.commit()

# 찜하기 취소
def delete_bookmark(db: Session, user_id: int, content_id: int) -> None:
    bookmark = db.query(models.Bookmark).filter(
        models.Bookmark.user_id == user_id,
        models.Bookmark.content_id == content_id
    ).first()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
        
    db.delete(bookmark)
    db.commit()