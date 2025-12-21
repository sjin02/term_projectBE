from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(
    prefix="/api/v1/contents",
    tags=["Bookmarks"]
)

def get_current_user_id():
    return 1 

# 1. 작품 찜하기 추가 (201 Created, 409 Conflict, 429 Too Many Requests)
@router.post("/{content_id}/bookmarks", status_code=status.HTTP_201_CREATED, summary="작품 찜하기")
def create_bookmark(
    content_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    # [429 Error 시뮬레이션]
    # 과제용: content_id가 9999면 도배로 간주하고 429 발생
    if content_id == 9999:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="찜하기 요청이 너무 많습니다. 잠시 후 시도해주세요."
        )

    # 1. 중복 체크 (409 Conflict)
    existing = db.query(models.Bookmark).filter(
        models.Bookmark.user_id == user_id,
        models.Bookmark.content_id == content_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="이미 찜한 작품입니다."
        )

    # 2. 저장
    new_bookmark = models.Bookmark(user_id=user_id, content_id=content_id)
    db.add(new_bookmark)
    db.commit()
    return {"message": "Bookmarked successfully"}

# 2. 작품 찜하기 취소 (204 No Content, 404 Not Found)
@router.delete("/{content_id}/bookmarks", status_code=status.HTTP_204_NO_CONTENT, summary="찜하기 취소")
def delete_bookmark(
    content_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    bookmark = db.query(models.Bookmark).filter(
        models.Bookmark.user_id == user_id,
        models.Bookmark.content_id == content_id
    ).first()
    
    # [404] 찜 내역 없음
    if not bookmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
        
    db.delete(bookmark)
    db.commit()
    return None
