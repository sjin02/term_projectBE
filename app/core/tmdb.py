from datetime import date
from typing import Any, Dict, List

import httpx

from app.core.config import settings
from app.core.errors import ErrorCode, http_error


def _params() -> dict:
    if not settings.TMDB_API_KEY:
        raise http_error(
            status_code=500,
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="TMDB API key is not configured",
        )
    return {"api_key": settings.TMDB_API_KEY, "language": "ko-KR"}


def fetch_movie_detail(tmdb_id: int) -> Dict[str, Any]:
    url = f"{settings.TMDB_API_BASE}/movie/{tmdb_id}"
    resp = httpx.get(url, params=_params())
    if resp.status_code != 200:
        raise http_error(
            status_code=502,
            code=ErrorCode.UNKNOWN_ERROR,
            message="TMDB movie fetch failed",
            details={"status_code": resp.status_code, "body": resp.text},
        )
    data = resp.json()
    release_date_raw = data.get("release_date")
    if release_date_raw:
        try:
            data["release_date"] = date.fromisoformat(release_date_raw)
        except ValueError:
            data["release_date"] = None
    return data


def fetch_genre_list() -> List[dict]:
    url = f"{settings.TMDB_API_BASE}/genre/movie/list"
    resp = httpx.get(url, params=_params())
    if resp.status_code != 200:
        raise http_error(
            status_code=502,
            code=ErrorCode.UNKNOWN_ERROR,
            message="TMDB genre fetch failed",
            details={"status_code": resp.status_code, "body": resp.text},
        )
    return resp.json().get("genres", [])
