from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.deps.db import get_db 
from app.repositories import bookmarks as bookmark_service

router = APIRouter(
    prefix="/contents",
    tags=["Bookmarks"]
)

def get_current_user_id():
    return 1 

@router.post("/{content_id}/bookmarks", status_code=status.HTTP_201_CREATED, summary="작품 찜하기")
def create_bookmark(
    content_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    bookmark_service.create_bookmark(db, user_id, content_id)
    return {"message": "Bookmarked successfully"}

@router.delete("/{content_id}/bookmarks", status_code=status.HTTP_204_NO_CONTENT, summary="찜하기 취소")
def delete_bookmark(
    content_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    bookmark_service.delete_bookmark(db, user_id, content_id)
    return None