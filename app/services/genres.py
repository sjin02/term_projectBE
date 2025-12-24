from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import models, schemas

# 장르 목록 조회 (활성 상태만)
def get_active_genres(db: Session) -> list[models.Genre]:
    return db.query(models.Genre).filter(models.Genre.is_active == True).all()

# 장르 생성
def create_genre(db: Session, genre_in: schemas.GenreCreate) -> models.Genre:
    existing = db.query(models.Genre).filter(models.Genre.name == genre_in.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="이미 존재하는 장르입니다.")

    new_genre = models.Genre(name=genre_in.name)
    db.add(new_genre)
    db.commit()
    db.refresh(new_genre)
    return new_genre

# 장르 수정
def update_genre(db: Session, genre_id: int, genre_in: schemas.GenreUpdate) -> models.Genre:
    genre = db.query(models.Genre).filter(models.Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    
    if genre_in.name:
        genre.name = genre_in.name
        
    db.commit()
    db.refresh(genre)
    return genre

# 장르 삭제 (Soft Delete)
def soft_delete_genre(db: Session, genre_id: int) -> None:
    genre = db.query(models.Genre).filter(models.Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    
    genre.is_active = False 
    db.commit()