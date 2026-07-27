import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import settings
from core.tmdb.cache import build_cache_key, get_cached, set_cached

logger = logging.getLogger(__name__)


class TMDbUnavailableError(Exception):
    """Raised when TMDb cannot be reached and no cached fallback exists."""


def _build_session() -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=settings.TMDB_MAX_RETRIES,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    return session


_session = _build_session()


def _request(endpoint: str, params: dict | None = None, ttl: int | None = None) -> dict:
    params = params or {}
    cache_key = build_cache_key(endpoint, **params)

    cached_response = get_cached(cache_key)
    if cached_response is not None:
        return cached_response

    if not settings.TMDB_API_KEY:
        raise TMDbUnavailableError("TMDB_API_KEY is not configured.")

    request_params = {**params, "api_key": settings.TMDB_API_KEY}
    url = f"{settings.TMDB_API_BASE_URL}{endpoint}"

    try:
        response = _session.get(url, params=request_params, timeout=settings.TMDB_REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as error:
        logger.warning("TMDb request failed for %s: %s", endpoint, error)
        raise TMDbUnavailableError(str(error)) from error

    payload = response.json()
    set_cached(cache_key, payload, ttl=ttl or settings.TMDB_CACHE_TTL_SECONDS)
    return payload


def get_movie_details(tmdb_id: int) -> dict:
    return _request(f"/movie/{tmdb_id}")


def get_movie_credits(tmdb_id: int) -> dict:
    return _request(f"/movie/{tmdb_id}/credits")


def get_movie_keywords(tmdb_id: int) -> dict:
    return _request(f"/movie/{tmdb_id}/keywords")


def get_trending_movies(time_window: str = "week") -> list[dict]:
    payload = _request(f"/trending/movie/{time_window}", ttl=60 * 60 * 6)
    return payload.get("results", [])


def build_poster_url(poster_path: str | None, size: str = settings.POSTER_SIZE) -> str | None:
    if not poster_path:
        return None
    return f"{settings.TMDB_IMAGE_BASE_URL}/{size}{poster_path}"
