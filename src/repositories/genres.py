from datetime import datetime
from typing import Iterable, List, Sequence, Optional
from sqlmodel import Session, select

from src.db.models import Genre
from src.schemas.genres import GenreCreate, GenreUpdate

# 단일 장르 조회
def get_genre(db: Session, genre_id: int) -> Optional[Genre]:
    return db.get(Genre, genre_id)

# 장르 생성
def create_genre(db: Session, genre_in: GenreCreate) -> Genre:
    # 중복 체크
    existing = db.exec(select(Genre).where(Genre.tmdb_genre_id == genre_in.tmdb_genre_id)).first()
    if existing:
        raise ValueError(f"이미 존재하는 장르입니다. (TMDB ID: {genre_in.tmdb_genre_id})")

    genre = Genre(
        name=genre_in.name,
        tmdb_genre_id=genre_in.tmdb_genre_id,
        created_at=datetime.utcnow()
    )
    db.add(genre)
    db.commit()
    db.refresh(genre)
    return genre

# 장르 수정
def update_genre(db: Session, genre_id: int, genre_in: GenreUpdate) -> Genre:
    genre = get_genre(db, genre_id)
    if not genre:
        raise ValueError("해당 장르를 찾을 수 없습니다.")
    
    # TMDB ID 변경 시 중복 체크
    if genre.tmdb_genre_id != genre_in.tmdb_genre_id:
        existing = db.exec(select(Genre).where(Genre.tmdb_genre_id == genre_in.tmdb_genre_id)).first()
        if existing:
            raise ValueError(f"이미 존재하는 장르입니다. (TMDB ID: {genre_in.tmdb_genre_id})")

    genre.name = genre_in.name
    genre.tmdb_genre_id = genre_in.tmdb_genre_id
    
    db.add(genre)
    db.commit()
    db.refresh(genre)
    return genre

# 장르 삭제 (Soft Delete)
def delete_genre(db: Session, genre_id: int) -> None:
    genre = get_genre(db, genre_id)
    if genre:
        genre.deleted_at = datetime.utcnow()
        db.add(genre)
        db.commit()

# ==========================================
# 기존 함수들 (TMDB 동기화 등)
# ==========================================

def upsert_genres_from_tmdb(
    db: Session, tmdb_genres: Iterable[dict]
) -> List[Genre]:
    tmdb_genres = list(tmdb_genres)
    tmdb_ids = [g["id"] for g in tmdb_genres]
    
    current = {
        g.tmdb_genre_id: g
        for g in db.exec(select(Genre).where(Genre.tmdb_genre_id.in_(tmdb_ids))).all()
    }
    result: List[Genre] = []
    now = datetime.utcnow()

    for tmdb_genre in tmdb_genres:
        gid = tmdb_genre["id"]
        name = tmdb_genre["name"]
        if gid in current:
            genre = current[gid]
            genre.name = name
            genre.deleted_at = None
        else:
            genre = Genre(tmdb_genre_id=gid, name=name, created_at=now)
        db.add(genre)
        db.flush()
        result.append(genre)

    db.commit()
    for genre in result:
        db.refresh(genre)
    return result


def soft_delete_missing(db: Session, tmdb_ids: Sequence[int]) -> None:
    now = datetime.utcnow()
    if not tmdb_ids:
        stale = db.exec(select(Genre).where(Genre.deleted_at.is_(None))).all()
    else:
        stale = db.exec(
            select(Genre).where(
                ~Genre.tmdb_genre_id.in_(tmdb_ids),
                Genre.deleted_at.is_(None),
            )
        ).all()
    for genre in stale:
        genre.deleted_at = now
        db.add(genre)
    if stale:
        db.commit()


def list_active_genres(db: Session) -> List[Genre]:
    return list(db.exec(select(Genre).where(Genre.deleted_at.is_(None))).all())