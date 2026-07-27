from functools import lru_cache

import pandas as pd
from rapidfuzz import fuzz, process

from config import settings


@lru_cache(maxsize=1)
def load_movies() -> pd.DataFrame:
    """Loads the processed movie catalog into memory. Cached because this
    file is read constantly across a session and never changes at runtime."""
    if not settings.MOVIES_PARQUET_PATH.exists():
        raise FileNotFoundError(
            f"Processed dataset not found at {settings.MOVIES_PARQUET_PATH}. "
            "Run scripts/build_model.py first."
        )
    return pd.read_parquet(settings.MOVIES_PARQUET_PATH)


def get_movie(movie_id: int) -> dict | None:
    movies = load_movies()
    match = movies.loc[movies["movie_id"] == movie_id]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def search_by_title(query: str, limit: int = 8) -> pd.DataFrame:
    query = query.strip()
    if not query:
        return load_movies().iloc[0:0]

    movies = load_movies()
    titles = movies["title"].tolist()
    matches = process.extract(query, titles, scorer=fuzz.WRatio, limit=limit)

    matched_titles = [title for title, score, _ in matches if score >= 55]
    if not matched_titles:
        return movies.iloc[0:0]

    result = movies[movies["title"].isin(matched_titles)].copy()
    result["_match_order"] = result["title"].apply(matched_titles.index)
    return result.sort_values("_match_order").drop(columns="_match_order")


def browse_by_genre(genre: str) -> pd.DataFrame:
    movies = load_movies()
    if genre == "All":
        return movies
    return movies[movies["genres"].apply(lambda genre_list: genre in genre_list)]


def list_all_genres() -> list[str]:
    movies = load_movies()
    unique_genres = set()
    for genre_list in movies["genres"]:
        unique_genres.update(genre_list)
    return ["All"] + sorted(unique_genres)


def list_all_languages() -> list[str]:
    movies = load_movies()
    languages = movies["original_language"].dropna().unique().tolist()
    return ["All"] + sorted(languages)


def filter_movies(
    movies: pd.DataFrame,
    genre: str | None = None,
    year_range: tuple[int, int] | None = None,
    min_rating: float | None = None,
    language: str | None = None,
) -> pd.DataFrame:
    filtered = movies

    if genre and genre != "All":
        filtered = filtered[filtered["genres"].apply(lambda g: genre in g)]

    if year_range:
        start_year, end_year = year_range
        filtered = filtered[
            (filtered["release_year"] >= start_year)
            & (filtered["release_year"] <= end_year)
        ]

    if min_rating:
        filtered = filtered[filtered["vote_average"] >= min_rating]

    if language and language != "All":
        filtered = filtered[filtered["original_language"] == language]

    return filtered


def sort_movies(movies: pd.DataFrame, by: str = "popularity") -> pd.DataFrame:
    sort_column = {
        "rating": "vote_average",
        "popularity": "popularity",
        "newest": "release_year",
        "title": "title",
    }.get(by, "popularity")

    ascending = sort_column == "title"
    return movies.sort_values(sort_column, ascending=ascending)


def get_trending_fallback(limit: int = 20) -> pd.DataFrame:
    """Used when the TMDb trending endpoint is unavailable — a reasonable
    stand-in built entirely from local data so the UI never shows an empty
    trending section."""
    movies = load_movies()
    qualified = movies[movies["vote_count"] >= settings.MIN_VOTE_COUNT_FOR_QUALITY]
    return qualified.sort_values("popularity", ascending=False).head(limit)
