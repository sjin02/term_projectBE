from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


# ======================
# Enums
# ======================

class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    DELETED = "DELETED"


# ======================
# User
# ======================

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)

    email: str = Field(index=True, unique=True)
    password_hash: str
    nickname: str

    role: UserRole = Field(default=UserRole.USER)
    status: UserStatus = Field(default=UserStatus.ACTIVE)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)

    reviews: List["Review"] = Relationship(back_populates="user")
    bookmarks: List["Bookmark"] = Relationship(back_populates="user")
    watch_histories: List["WatchHistory"] = Relationship(back_populates="user")


# ======================
# Content ↔ Genre Link
# ======================

class ContentGenreLink(SQLModel, table=True):
    __tablename__ = "content_genres"

    content_id: int = Field(
        foreign_key="contents.id",
        primary_key=True,
    )
    genre_id: int = Field(
        foreign_key="genres.id",
        primary_key=True,
    )


# ======================
# Genre
# ======================

class Genre(SQLModel, table=True):
    __tablename__ = "genres"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)

    contents: List["Content"] = Relationship(
        back_populates="genres",
        link_model=ContentGenreLink,
    )


# ======================
# Content
# ======================

class Content(SQLModel, table=True):
    __tablename__ = "contents"

    id: Optional[int] = Field(default=None, primary_key=True)

    title: str = Field(index=True)
    description: Optional[str] = None

    release_year: int
    runtime_minutes: int

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)

    genres: List["Genre"] = Relationship(
        back_populates="contents",
        link_model=ContentGenreLink,
    )
    reviews: List["Review"] = Relationship(back_populates="content")
    bookmarks: List["Bookmark"] = Relationship(back_populates="content")


# ======================
# Review
# ======================

class Review(SQLModel, table=True):
    __tablename__ = "reviews"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="users.id")
    content_id: int = Field(foreign_key="contents.id")

    rating: int = Field(ge=1, le=5)
    comment: str

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="reviews")
    content: Content = Relationship(back_populates="reviews")
    likes: List["ReviewLike"] = Relationship(back_populates="review")


# ======================
# Review Like
# ======================

class ReviewLike(SQLModel, table=True):
    __tablename__ = "review_likes"

    user_id: int = Field(
        foreign_key="users.id",
        primary_key=True,
    )
    review_id: int = Field(
        foreign_key="reviews.id",
        primary_key=True,
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    review: Review = Relationship(back_populates="likes")


# ======================
# Bookmark
# ======================

class Bookmark(SQLModel, table=True):
    __tablename__ = "bookmarks"

    user_id: int = Field(
        foreign_key="users.id",
        primary_key=True,
    )
    content_id: int = Field(
        foreign_key="contents.id",
        primary_key=True,
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="bookmarks")
    content: Content = Relationship(back_populates="bookmarks")


# ======================
# Watch History
# ======================

class WatchHistory(SQLModel, table=True):
    __tablename__ = "watch_histories"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="users.id")
    content_id: int = Field(foreign_key="contents.id")

    watched_minutes: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="watch_histories")
