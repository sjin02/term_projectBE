import random
from datetime import date, datetime, timedelta

from sqlmodel import Session, select

# 앱 설정 및 모델 임포트
from app.db.session import engine
from app.db.models import (
    User, UserRole, UserStatus,
    Genre, Content, ContentGenreLink,
    Review, ReviewLike, Bookmark
)
from app.core.security import hash_password

# ==========================================
# 랜덤 데이터 생성 헬퍼
# ==========================================
ADJECTIVES = ["신비한", "화려한", "어두운", "즐거운", "사라진", "돌아온", "마지막", "전설의", "위대한", "조용한"]
NOUNS = ["모험", "사랑", "전설", "기억", "여행", "도시", "영웅", "비밀", "전쟁", "하루"]

def get_random_title():
    return f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)}"

def get_random_date():
    start_date = date(2000, 1, 1)
    end_date = date(2023, 12, 31)
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)


# ==========================================
# 데이터 생성 함수들
# ==========================================

def create_users(db: Session):
    print("Creating users...")
    
    # 1. 고정 관리자 및 테스트 유저 (3명)
    fixed_users = [
        ("admin@example.com", "관리자", UserRole.ADMIN),
        ("user1@example.com", "영화광1", UserRole.USER),
        ("user2@example.com", "팝콘러버", UserRole.USER),
    ]

    for email, nick, role in fixed_users:
        if not db.exec(select(User).where(User.email == email)).first():
            db.add(User(
                email=email,
                password_hash=hash_password("1234"),
                nickname=nick,
                role=role,
                status=UserStatus.ACTIVE,
            ))
    
    # 2. 랜덤 유저 추가 생성 (약 20명)
    # 이미 데이터가 많으면 스킵 (중복 생성 방지용)
    current_count = len(db.exec(select(User)).all())
    target_count = 20
    
    if current_count < target_count:
        for i in range(current_count, target_count):
            email = f"user{i+3}@example.com"
            nickname = f"유저{i+3}"
            if not db.exec(select(User).where(User.email == email)).first():
                db.add(User(
                    email=email,
                    password_hash=hash_password("1234"),
                    nickname=nickname,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                ))
    
    db.commit()


def create_genres(db: Session):
    print("Creating genres...")
    genres_data = [
        {"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"},
        {"id": 16, "name": "Animation"}, {"id": 35, "name": "Comedy"},
        {"id": 80, "name": "Crime"}, {"id": 99, "name": "Documentary"},
        {"id": 18, "name": "Drama"}, {"id": 10751, "name": "Family"},
        {"id": 14, "name": "Fantasy"}, {"id": 36, "name": "History"},
        {"id": 27, "name": "Horror"}, {"id": 10402, "name": "Music"},
        {"id": 9648, "name": "Mystery"}, {"id": 10749, "name": "Romance"},
        {"id": 878, "name": "Science Fiction"}, {"id": 10770, "name": "TV Movie"},
        {"id": 53, "name": "Thriller"}, {"id": 10752, "name": "War"},
        {"id": 37, "name": "Western"},
    ]

    for g in genres_data:
        if not db.exec(select(Genre).where(Genre.tmdb_genre_id == g["id"])).first():
            db.add(Genre(tmdb_genre_id=g["id"], name=g["name"]))
    
    db.commit()


def create_contents(db: Session):
    print("Creating contents...")
    
    # 1. 고정 영화 데이터 (5개)
    movies = [
        {"tmdb_id": 603, "title": "The Matrix", "date": date(1999, 3, 30), "runtime": 136, "genres": [28, 878]},
        {"tmdb_id": 27205, "title": "Inception", "date": date(2010, 7, 15), "runtime": 148, "genres": [28, 878, 12]},
        {"tmdb_id": 157336, "title": "Interstellar", "date": date(2014, 11, 5), "runtime": 169, "genres": [12, 18, 878]},
        {"tmdb_id": 299534, "title": "Avengers: Endgame", "date": date(2019, 4, 24), "runtime": 181, "genres": [12, 878, 28]},
        {"tmdb_id": 496243, "title": "Parasite", "date": date(2019, 5, 30), "runtime": 132, "genres": [35, 53, 18]}
    ]

    # 모든 장르 ID 가져오기 (랜덤 할당용)
    all_genre_ids = [g.id for g in db.exec(select(Genre)).all()]
    all_tmdb_genre_ids = [g.tmdb_genre_id for g in db.exec(select(Genre)).all()]

    # 2. 고정 영화 생성
    for m in movies:
        if not db.exec(select(Content).where(Content.tmdb_id == m["tmdb_id"])).first():
            content = Content(
                tmdb_id=m["tmdb_id"],
                title=m["title"],
                release_date=m["date"],
                runtime_minutes=m["runtime"]
            )
            db.add(content)
            db.commit()
            db.refresh(content)

            # 장르 연결
            for gid in m["genres"]:
                genre = db.exec(select(Genre).where(Genre.tmdb_genre_id == gid)).first()
                if genre:
                    db.add(ContentGenreLink(content_id=content.id, genre_id=genre.id))
            db.commit()

    # 3. 랜덤 영화 데이터 생성 (약 50개)
    current_count = len(db.exec(select(Content)).all())
    target_count = 50

    if current_count < target_count:
        for i in range(current_count, target_count):
            fake_tmdb_id = 100000 + i  # 실제 ID와 겹치지 않게 큰 수 사용
            title = get_random_title()
            
            content = Content(
                tmdb_id=fake_tmdb_id,
                title=title,
                release_date=get_random_date(),
                runtime_minutes=random.randint(80, 180)
            )
            db.add(content)
            db.commit()
            db.refresh(content)

            # 랜덤 장르 1~3개 연결
            if all_tmdb_genre_ids:
                random_genres = random.sample(all_tmdb_genre_ids, k=random.randint(1, 3))
                for gid in random_genres:
                    genre = db.exec(select(Genre).where(Genre.tmdb_genre_id == gid)).first()
                    if genre:
                        db.add(ContentGenreLink(content_id=content.id, genre_id=genre.id))
            db.commit()


def create_reviews_and_bookmarks(db: Session):
    print("Creating reviews, bookmarks, and likes...")

    users = db.exec(select(User)).all()
    contents = db.exec(select(Content)).all()

    if not users or not contents:
        return

    comments = [
        "정말 최고의 영화였습니다!", "시간 가는 줄 모르고 봤네요.", "기대보다는 조금 아쉬웠어요.",
        "배우들의 연기가 일품입니다.", "인생 영화 등극!", "연출이 대박이네요.",
        "스토리가 탄탄합니다.", "음악이 너무 좋아요.", "한 번 더 보고 싶어요.", "그저 그랬습니다."
    ]

    # 리뷰 목표 개수: 약 100개
    # 북마크 목표 개수: 약 50개
    
    # 1. 리뷰 생성
    review_count = 0
    for content in contents:
        for user in users:
            # 10% 확률로 리뷰 작성 (50영화 * 20유저 = 1000조합 -> 10% = 100개)
            if random.random() < 0.1:
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
                    review_count += 1

                    # 2. 리뷰 좋아요 (리뷰가 생성되면 50% 확률로 다른 유저들이 좋아요)
                    other_users = [u for u in users if u.id != user.id]
                    if other_users:
                        # 1~5개의 좋아요
                        likers = random.sample(other_users, k=random.randint(0, min(5, len(other_users))))
                        for liker in likers:
                            if not db.exec(select(ReviewLike).where(ReviewLike.user_id == liker.id, ReviewLike.review_id == review.id)).first():
                                db.add(ReviewLike(user_id=liker.id, review_id=review.id))
                        db.commit()
    
    print(f"  - Created {review_count} reviews.")

    # 3. 북마크 생성
    bookmark_count = 0
    for content in contents:
        for user in users:
            # 5% 확률로 북마크
            if random.random() < 0.05:
                if not db.exec(select(Bookmark).where(Bookmark.user_id == user.id, Bookmark.content_id == content.id)).first():
                    db.add(Bookmark(user_id=user.id, content_id=content.id))
                    bookmark_count += 1
    
    db.commit()
    print(f"  - Created {bookmark_count} bookmarks.")


def main():
    print("🌱 Initialize DB Session...")
    with Session(engine) as session:
        print("🛠️ Creating tables manually...")
        SQLModel.metadata.create_all(session.bind)
        print("✅ Tables created!")
        create_users(session)
        create_genres(session)
        create_contents(session)
        create_reviews_and_bookmarks(session)
    print("✨ Seed data created successfully! (~200+ items)")


if __name__ == "__main__":
    main()