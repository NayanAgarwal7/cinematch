import pandas as pd

MAX_SHARED_GENRES = 2
MAX_SHARED_CAST = 2


def _shared_items(source_items: list[str], candidate_items: list[str], limit: int) -> list[str]:
    seen = set()
    shared = []
    for item in candidate_items:
        if item in source_items and item not in seen:
            shared.append(item)
            seen.add(item)
        if len(shared) == limit:
            break
    return shared


def explain_recommendation(source_movie: pd.Series, candidate_movie: pd.Series) -> str:
    reasons = []

    shared_genres = _shared_items(source_movie["genres"], candidate_movie["genres"], MAX_SHARED_GENRES)
    if shared_genres:
        reasons.append(f"same {'/'.join(shared_genres)} vibe")

    if source_movie.get("director") and source_movie["director"] == candidate_movie.get("director"):
        reasons.append(f"also directed by {candidate_movie['director']}")

    shared_cast = _shared_items(source_movie["cast"], candidate_movie["cast"], MAX_SHARED_CAST)
    if shared_cast:
        reasons.append(f"features {' and '.join(shared_cast)}")

    shared_keywords = _shared_items(source_movie["keywords"], candidate_movie["keywords"], 1)
    if shared_keywords and not reasons:
        reasons.append(f"shares the theme of {shared_keywords[0]}")

    if not reasons:
        return f"Because you liked {source_movie['title']}"

    return f"Because you liked {source_movie['title']} — {', '.join(reasons)}"
