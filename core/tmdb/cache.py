import diskcache

from config.settings import TMDB_CACHE_PATH, TMDB_CACHE_TTL_SECONDS

_cache = diskcache.Cache(str(TMDB_CACHE_PATH))


def build_cache_key(endpoint: str, **params) -> str:
    sorted_params = sorted(params.items())
    param_string = "&".join(f"{key}={value}" for key, value in sorted_params)
    return f"{endpoint}?{param_string}"


def get_cached(key: str):
    return _cache.get(key, default=None)


def set_cached(key: str, value, ttl: int = TMDB_CACHE_TTL_SECONDS) -> None:
    _cache.set(key, value, expire=ttl)


def clear_cache() -> None:
    _cache.clear()
