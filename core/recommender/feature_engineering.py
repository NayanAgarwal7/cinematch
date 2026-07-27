import pandas as pd

from config.settings import FEATURE_WEIGHTS

MAX_CAST_MEMBERS = 3


def _collapse_tokens(values: list[str]) -> list[str]:
    """Strips spaces out of multi-word entities so 'Science Fiction' becomes
    'sciencefiction' and 'Christopher Nolan' becomes 'christophernolan'.
    Without this, TF-IDF treats 'science' and 'fiction' as independent tokens
    and the vectorizer starts matching movies on words like 'fiction' alone,
    which pollutes similarity with unrelated dramas and thrillers."""
    return [value.lower().replace(" ", "").replace("-", "") for value in values if value]


def build_movie_tags(movie_row: pd.Series) -> str:
    genre_tokens = _collapse_tokens(movie_row["genres"]) * FEATURE_WEIGHTS["genres"]
    keyword_tokens = _collapse_tokens(movie_row["keywords"]) * FEATURE_WEIGHTS["keywords"]

    cast_list = movie_row["cast"][:MAX_CAST_MEMBERS]
    cast_tokens = _collapse_tokens(cast_list) * FEATURE_WEIGHTS["cast"]

    director = movie_row.get("director") or ""
    director_tokens = _collapse_tokens([director]) * FEATURE_WEIGHTS["director"]

    overview_tokens = (movie_row.get("overview") or "").lower().split()

    all_tokens = genre_tokens + keyword_tokens + cast_tokens + director_tokens + overview_tokens
    return " ".join(all_tokens)


def build_feature_corpus(movies: pd.DataFrame) -> pd.Series:
    return movies.apply(build_movie_tags, axis=1)
