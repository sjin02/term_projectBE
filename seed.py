import random
from datetime import date, datetime

from sqlmodel import Session, select

# 앱 설정 및 모델 임포트
from app.db.session import engine
from app.db.models import (
    User, UserRole, UserStatus,
    Genre, Content, ContentGenreLink,
    Review, ReviewLike, Bookmark
)
from app.core.security import hash_password

def create_users(db: Session):
    print("Creating users...")
    
    # 1. 관리자 (admin@example.com / 1234)
    if not db.exec(select(User).where(User.email == "admin@example.com")).first():
        admin = User(
            email="admin@example.com",
            password_hash=hash_password("1234"),
            nickname="관리자",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )
        db.add(admin)

    # 2. 일반 유저 1 (user1@example.com / 1234)
    if not db.exec(select(User).where(User.email == "user1@example.com")).first():
        user1 = User(
            email="user1@example.com",
            password_hash=hash_password("1234"),
            nickname="영화광1",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        db.add(user1)

    # 3. 일반 유저 2 (user2@example.com / 1234)
    if not db.exec(select(User).where(User.email == "user2@example.com")).first():
        user2 = User(
            email="user2@example.com",
            password_hash=hash_password("1234"),
            nickname="팝콘러버",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        db.add(user2)
    
    db.commit()


def create_genres(db: Session):
    print("Creating genres...")
    # TMDB 기준 주요 장르 ID 및 이름
    genres_data = [
        {"id": 28, "name": "Action"},
        {"id": 12, "name": "Adventure"},
        {"id": 16, "name": "Animation"},
        {"id": 35, "name": "Comedy"},
        {"id": 80, "name": "Crime"},
        {"id": 99, "name": "Documentary"},
        {"id": 18, "name": "Drama"},
        {"id": 10751, "name": "Family"},
        {"id": 14, "name": "Fantasy"},
        {"id": 36, "name": "History"},
        {"id": 27, "name": "Horror"},
        {"id": 10402, "name": "Music"},
        {"id": 9648, "name": "Mystery"},
        {"id": 10749, "name": "Romance"},
        {"id": 878, "name": "Science Fiction"},
        {"id": 10770, "name": "TV Movie"},
        {"id": 53, "name": "Thriller"},
        {"id": 10752, "name": "War"},
        {"id": 37, "name": "Western"},
    ]

    for g in genres_data:
        if not db.exec(select(Genre).where(Genre.tmdb_genre_id == g["id"])).first():
            genre = Genre(tmdb_genre_id=g["id"], name=g["name"])
            db.add(genre)
    
    db.commit()


def create_contents(db: Session):
    print("Creating contents...")
    
    # 예시 영화 데이터
    movies = [
        {
            "tmdb_id": 603, 
            "title": "The Matrix", 
            "release_date": date(1999, 3, 30), 
            "runtime": 136,
            "genre_ids": [28, 878] # Action, Sci-Fi
        },
        {
            "tmdb_id": 27205, 
            "title": "Inception", 
            "release_date": date(2010, 7, 15), 
            "runtime": 148,
            "genre_ids": [28, 878, 12] # Action, Sci-Fi, Adventure
        },
        {
            "tmdb_id": 157336, 
            "title": "Interstellar", 
            "release_date": date(2014, 11, 5), 
            "runtime": 169,
            "genre_ids": [12, 18, 878] # Adventure, Drama, Sci-Fi
        },
        {
            "tmdb_id": 299534, 
            "title": "Avengers: Endgame", 
            "release_date": date(2019, 4, 24), 
            "runtime": 181,
            "genre_ids": [12, 878, 28] 
        },
        {
            "tmdb_id": 496243, 
            "title": "Parasite", 
            "release_date": date(2019, 5, 30), 
            "runtime": 132,
            "genre_ids": [35, 53, 18] # Comedy, Thriller, Drama
        }
    ]

    for m in movies:
        content = db.exec(select(Content).where(Content.tmdb_id == m["tmdb_id"])).first()
        if not content:
            # 콘텐츠 생성
            content = Content(
                tmdb_id=m["tmdb_id"],
                title=m["title"],
                release_date=m["release_date"],
                runtime_minutes=m["runtime"]
            )
            db.add(content)
            db.commit()
            db.refresh(content)

            # 장르 연결
            for gid in m["genre_ids"]:
                genre = db.exec(select(Genre).where(Genre.tmdb_genre_id == gid)).first()
                if genre:
                    link = ContentGenreLink(content_id=content.id, genre_id=genre.id)
                    db.add(link)
            db.commit()


def create_reviews_and_bookmarks(db: Session):
    print("Creating reviews, bookmarks, and likes...")

    users = db.exec(select(User)).all()
    contents = db.exec(select(Content)).all()

    if not users or not contents:
        return

    # 리뷰 멘트 샘플
    comments = [
        "정말 최고의 영화였습니다!",
        "시간 가는 줄 모르고 봤네요.",
        "기대보다는 조금 아쉬웠어요.",
        "배우들의 연기가 일품입니다.",
        "인생 영화 등극!",
        "연출이 대박이네요."
    ]

    for content in contents:
        for user in users:
            # 50% 확률로 리뷰 작성
            if random.choice([True, False]):
                if not db.exec(select(Review).where(Review.user_id == user.id, Review.content_id == content.id)).first():
                    review = Review(
                        user_id=user.id,
                        content_id=content.id,
                        rating=random.randint(3, 5),
                        comment=random.choice(comments)
                    )
                    db.add(review)
                    db.commit()
                    db.refresh(review)

                    # 30% 확률로 리뷰 좋아요 (다른 유저가)
                    other_users = [u for u in users if u.id != user.id]
                    for other in other_users:
                         if random.random() < 0.3:
                             like = ReviewLike(user_id=other.id, review_id=review.id)
                             db.add(like)

            # 30% 확률로 북마크
            if random.random() < 0.3:
                if not db.exec(select(Bookmark).where(Bookmark.user_id == user.id, Bookmark.content_id == content.id)).first():
                    bookmark = Bookmark(user_id=user.id, content_id=content.id)
                    db.add(bookmark)
    
    db.commit()


def main():
    print("Initialize DB Session...")
    with Session(engine) as session:
        create_users(session)
        create_genres(session)
        create_contents(session)
        create_reviews_and_bookmarks(session)
    print("Seed data created successfully!")


if __name__ == "__main__":
    main()