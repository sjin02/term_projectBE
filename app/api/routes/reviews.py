from datetime import datetime
from math import ceil

from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session, select, func

from app.core.errors import ErrorCode, http_error, success_response, STANDARD_ERROR_RESPONSES
from app.core.docs import success_example, error_example
from app.db.models import Content, Review, ReviewLike
from app.deps.auth import get_current_user
from app.deps.db import get_db
from app.schemas.reviews import (
    ReviewCreate,
    ReviewListResponse,
    ReviewResponse,
    ReviewUpdate,
)

router = APIRouter(
    prefix="",
    tags=["reviews"],
    responses=STANDARD_ERROR_RESPONSES,
)


# ==========================================
# Helpers
# ==========================================

def _sort_clause(sort: str):
    allowed = {
        "createdAt": Review.created_at,
        "rating": Review.rating,
    }
    try:
        field, direction = sort.split(",")
    except ValueError:
        raise http_error(
            400, ErrorCode.INVALID_QUERY_PARAM, "정렬 형식은 field,DESC|ASC 여야 합니다."
        )

    if field not in allowed or direction.upper() not in ("ASC", "DESC"):
        raise http_error(
            400, ErrorCode.INVALID_QUERY_PARAM, "지원하지 않는 정렬 필드 혹은 방향입니다.",
            details={"sort": sort}
        )

    column = allowed[field]
    return column.desc() if direction.upper() == "DESC" else column.asc()


def _review_to_response(review: Review, like_count: int) -> ReviewResponse:
    return ReviewResponse(
        **review.model_dump(),
        like_count=like_count,
    )


def _like_count_subquery():
    return (
        select(
            Review.id,
            func.count(ReviewLike.user_id).label("like_count"),
        )
        .join(ReviewLike, ReviewLike.review_id == Review.id, isouter=True)
        .group_by(Review.id)
        .subquery()
    )


# ==========================================
# Routes
# ==========================================

@router.get(
    "/reviews/popular",
    responses={**success_example(description="인기 리뷰 목록 조회")}
)
def get_popular_reviews(
    request: Request,
    db: Session = Depends(get_db),
):
    like_counts = _like_count_subquery()
    stmt = (
        select(Review, like_counts.c.like_count)
        .join(like_counts, like_counts.c.id == Review.id)
        .order_by(like_counts.c.like_count.desc(), Review.created_at.desc())
        .limit(10)
    )
    rows = db.exec(stmt).all()
    responses = [
        _review_to_response(review, like_count or 0) for review, like_count in rows
    ]
    return success_response(
        request,
        message="인기 리뷰 목록 조회 성공",
        data=[r.model_dump() for r in responses],
    )


@router.post(
    "/contents/{content_id}/reviews",
    status_code=201,
    responses={
        **success_example(ReviewResponse, status_code=201, message="리뷰가 등록되었습니다."),
        404: error_example(404, ErrorCode.RESOURCE_NOT_FOUND, "콘텐츠를 찾을 수 없습니다."),
    }
)
def create_review(
    request: Request,
    content_id: int,
    body: ReviewCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    content = db.get(Content, content_id)
    if not content or content.deleted_at is not None:
        raise http_error(
            404, ErrorCode.RESOURCE_NOT_FOUND, "요청하신 콘텐츠를 찾을 수 없습니다.",
            details={"contentId": content_id}
        )

    # (선택) 한 유저가 같은 콘텐츠에 중복 리뷰를 남기지 못하게 하려면 여기서 체크
    # existing = db.exec(select(Review).where(Review.user_id == user.id, Review.content_id == content_id)).first()
    # if existing: raise http_error(409, ErrorCode.DUPLICATE_RESOURCE, "이미 리뷰를 작성했습니다.")

    review = Review(
        content_id=content_id,
        user_id=user.id,
        rating=body.rating,
        comment=body.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    response = _review_to_response(review, like_count=0)
    return success_response(
        request,
        status_code=201,
        message="리뷰가 등록되었습니다.",
        data=response.model_dump(),
    )


@router.get(
    "/contents/{content_id}/reviews",
    responses={
        **success_example(ReviewListResponse, message="리뷰 목록이 조회되었습니다."),
        404: error_example(404, ErrorCode.RESOURCE_NOT_FOUND, "콘텐츠를 찾을 수 없습니다."),
    }
)
def get_reviews_by_content(
    request: Request,
    content_id: int,
    sort: str = Query("createdAt,DESC"),
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=50),
    keyword: str | None = Query(None, description="리뷰 내용 검색"),
    rating_min: int | None = Query(None, ge=1, le=5, alias="ratingMin"),
    rating_max: int | None = Query(None, ge=1, le=5, alias="ratingMax"),
    date_from: datetime | None = Query(None, alias="dateFrom"),
    date_to: datetime | None = Query(None, alias="dateTo"),
    db: Session = Depends(get_db),
):
    content = db.get(Content, content_id)
    if not content or content.deleted_at is not None:
        raise http_error(
            404, ErrorCode.RESOURCE_NOT_FOUND, "요청하신 콘텐츠를 찾을 수 없습니다.",
            details={"contentId": content_id}
        )

    like_counts = _like_count_subquery()
    stmt = (
        select(Review, like_counts.c.like_count)
        .join(like_counts, like_counts.c.id == Review.id)
        .where(Review.content_id == content_id)
    )

    if keyword:
        stmt = stmt.where(Review.comment.ilike(f"%{keyword}%"))
    if rating_min is not None:
        stmt = stmt.where(Review.rating >= rating_min)
    if rating_max is not None:
        stmt = stmt.where(Review.rating <= rating_max)
    if date_from:
        stmt = stmt.where(Review.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Review.created_at <= date_to)

    stmt = stmt.order_by(_sort_clause(sort))

    total = db.exec(select(func.count()).select_from(stmt.subquery())).one()
    rows = db.exec(stmt.offset(page * size).limit(size)).all()

    responses = [
        _review_to_response(review, like_count or 0) for review, like_count in rows
    ]
    payload = ReviewListResponse(
        content=responses,
        page=page,
        size=size,
        totalElements=int(total),
        totalPages=ceil(int(total) / size) if size else 0,
        sort=sort,
    )
    return success_response(
        request,
        message="리뷰 목록이 조회되었습니다.",
        data=payload.model_dump(),
    )


@router.put(
    "/reviews/{review_id}",
    responses={
        **success_example(ReviewResponse, message="리뷰가 수정되었습니다."),
        403: error_example(403, ErrorCode.FORBIDDEN, "수정 권한이 없습니다."),
        404: error_example(404, ErrorCode.RESOURCE_NOT_FOUND, "리뷰를 찾을 수 없습니다."),
    }
)
def update_review(
    request: Request,
    review_id: int,
    body: ReviewUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    like_counts = _like_count_subquery()
    stmt = (
        select(Review, like_counts.c.like_count)
        .join(like_counts, like_counts.c.id == Review.id)
        .where(Review.id == review_id)
    )
    row = db.exec(stmt).first()
    if not row:
        raise http_error(
            404, ErrorCode.RESOURCE_NOT_FOUND, "리뷰를 찾을 수 없습니다.",
            details={"reviewId": review_id}
        )

    review, like_count = row
    if review.user_id != user.id:
        raise http_error(403, ErrorCode.FORBIDDEN, "자신이 작성한 리뷰만 수정할 수 있습니다.")

    if body.rating is not None:
        review.rating = body.rating
    if body.comment is not None:
        review.comment = body.comment

    review.updated_at = datetime.utcnow()
    db.add(review)
    db.commit()
    db.refresh(review)

    response = _review_to_response(review, like_count or 0)
    return success_response(
        request,
        message="리뷰가 수정되었습니다.",
        data=response.model_dump(),
    )


@router.delete(
    "/reviews/{review_id}",
    responses={
        **success_example(message="리뷰가 삭제되었습니다."),
        403: error_example(403, ErrorCode.FORBIDDEN, "삭제 권한이 없습니다."),
        404: error_example(404, ErrorCode.RESOURCE_NOT_FOUND, "리뷰를 찾을 수 없습니다."),
    }
)
def delete_review(
    request: Request,
    review_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    review = db.get(Review, review_id)
    if not review:
        raise http_error(
            404, ErrorCode.RESOURCE_NOT_FOUND, "리뷰를 찾을 수 없습니다.",
            details={"reviewId": review_id}
        )

    if review.user_id != user.id:
        raise http_error(403, ErrorCode.FORBIDDEN, "자신이 작성한 리뷰만 삭제할 수 있습니다.")

    db.delete(review)
    db.commit()
    return success_response(
        request,
        message="리뷰가 삭제되었습니다.",
        data={"reviewId": review_id},
    )


@router.post(
    "/reviews/{review_id}/likes",
    status_code=201,
    responses={
        **success_example(message="리뷰에 좋아요를 남겼습니다.", status_code=201),
        404: error_example(404, ErrorCode.RESOURCE_NOT_FOUND, "리뷰를 찾을 수 없습니다."),
        409: error_example(409, ErrorCode.DUPLICATE_RESOURCE, "이미 좋아요를 눌렀습니다."),
    }
)
def like_review(
    request: Request,
    review_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    review = db.get(Review, review_id)
    if not review:
        raise http_error(
            404, ErrorCode.RESOURCE_NOT_FOUND, "리뷰를 찾을 수 없습니다.",
            details={"reviewId": review_id}
        )

    existing = db.exec(
        select(ReviewLike).where(
            ReviewLike.review_id == review_id,
            ReviewLike.user_id == user.id,
        )
    ).first()
    if existing:
        raise http_error(409, ErrorCode.DUPLICATE_RESOURCE, "이미 좋아요를 눌렀습니다.")

    like = ReviewLike(review_id=review_id, user_id=user.id)
    db.add(like)
    db.commit()

    # 최신 좋아요 수 조회
    like_count = db.exec(
        select(func.count()).select_from(
            select(ReviewLike).where(ReviewLike.review_id == review_id).subquery()
        )
    ).one()
    
    return success_response(
        request,
        status_code=201,
        message="리뷰에 좋아요를 남겼습니다.",
        data={"reviewId": review_id, "likeCount": int(like_count)},
    )


@router.delete(
    "/reviews/{review_id}/likes",
    responses={
        **success_example(message="좋아요가 취소되었습니다."),
        404: error_example(404, ErrorCode.RESOURCE_NOT_FOUND, "좋아요 정보를 찾을 수 없습니다."),
    }
)
def unlike_review(
    request: Request,
    review_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    like = db.exec(
        select(ReviewLike).where(
            ReviewLike.review_id == review_id,
            ReviewLike.user_id == user.id,
        )
    ).first()
    if not like:
        raise http_error(
            404, ErrorCode.RESOURCE_NOT_FOUND, "좋아요 정보를 찾을 수 없습니다.",
            details={"reviewId": review_id}
        )

    db.delete(like)
    db.commit()

    like_count = db.exec(
        select(func.count()).select_from(
            select(ReviewLike).where(ReviewLike.review_id == review_id).subquery()
        )
    ).one()

    return success_response(
        request,
        message="좋아요가 취소되었습니다.",
        data={"reviewId": review_id, "likeCount": int(like_count)},
    )