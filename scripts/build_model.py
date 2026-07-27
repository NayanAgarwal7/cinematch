"""
Builds everything the app needs to run without touching TMDb at request time:

    MovieLens (movies.csv + links.csv)
        -> enrich each title with TMDb (cast, crew, keywords, overview, poster)
        -> data/processed/movies.parquet
        -> TF-IDF corpus -> vectorizer.pkl
        -> cosine similarity -> similarity_matrix.pkl + movie_index.pkl

Run with:
    python -m scripts.build_model --limit 3000 --workers 8

The --limit flag exists because TMDb enrichment is the slow part of this
pipeline (one API call per movie, times three endpoints) — useful for local
iteration without waiting on the full MovieLens catalog every run.
"""

import argparse
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from tqdm import tqdm

from config import settings
from core.recommender import feature_engineering, similarity, vectorizer
from core.tmdb.client import TMDbUnavailableError, get_movie_credits, get_movie_details, get_movie_keywords

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger("build_model")


def load_movielens_source() -> pd.DataFrame:
    movies = pd.read_csv(settings.MOVIELENS_MOVIES_PATH)
    links = pd.read_csv(settings.MOVIELENS_LINKS_PATH, dtype={"tmdbId": "Int64"})

    merged = movies.merge(links, on="movieId", how="left").dropna(subset=["tmdbId"])
    merged["genres"] = merged["genres"].apply(_parse_movielens_genres)
    return merged.rename(columns={"movieId": "movie_id", "tmdbId": "tmdb_id"})


def _parse_movielens_genres(raw_genres: str) -> list[str]:
    if not raw_genres or raw_genres == "(no genres listed)":
        return []
    return raw_genres.split("|")


def _extract_director(credits_payload: dict) -> str | None:
    crew = credits_payload.get("crew", [])
    for member in crew:
        if member.get("job") == "Director":
            return member.get("name")
    return None


def _extract_top_cast(credits_payload: dict, limit: int = 5) -> list[str]:
    cast = credits_payload.get("cast", [])
    return [member["name"] for member in cast[:limit] if member.get("name")]


def enrich_with_tmdb(movie_row: pd.Series) -> dict | None:
    tmdb_id = int(movie_row["tmdb_id"])
    try:
        details = get_movie_details(tmdb_id)
        credits_payload = get_movie_credits(tmdb_id)
        keywords_payload = get_movie_keywords(tmdb_id)
    except TMDbUnavailableError as error:
        logger.warning("Skipping tmdb_id=%s (%s): %s", tmdb_id, movie_row["title"], error)
        return None

    release_date = details.get("release_date") or ""
    release_year = int(release_date[:4]) if len(release_date) >= 4 else None

    return {
        "movie_id": int(movie_row["movie_id"]),
        "tmdb_id": tmdb_id,
        "title": details.get("title") or movie_row["title"],
        "genres": movie_row["genres"] or [g["name"] for g in details.get("genres", [])],
        "keywords": [k["name"] for k in keywords_payload.get("keywords", [])],
        "cast": _extract_top_cast(credits_payload),
        "director": _extract_director(credits_payload),
        "overview": details.get("overview") or "",
        "release_year": release_year,
        "runtime": details.get("runtime"),
        "vote_average": details.get("vote_average", 0.0),
        "vote_count": details.get("vote_count", 0),
        "popularity": details.get("popularity", 0.0),
        "original_language": details.get("original_language"),
        "poster_path": details.get("poster_path"),
    }


def build_enriched_catalog(source_movies: pd.DataFrame, workers: int) -> pd.DataFrame:
    enriched_records = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(enrich_with_tmdb, row): row["movie_id"]
            for _, row in source_movies.iterrows()
        }

        for future in tqdm(as_completed(futures), total=len(futures), desc="Enriching from TMDb"):
            record = future.result()
            if record is not None:
                enriched_records.append(record)

    return pd.DataFrame(enriched_records)


def build_recommendation_model(movies: pd.DataFrame) -> None:
    logger.info("Building feature corpus for %d movies", len(movies))
    corpus = feature_engineering.build_feature_corpus(movies)

    logger.info("Fitting TF-IDF vectorizer")
    fitted_vectorizer, tfidf_matrix = vectorizer.fit_vectorizer(corpus)
    vectorizer.save_vectorizer(fitted_vectorizer)

    logger.info("Computing cosine similarity matrix (%d x %d)", len(movies), len(movies))
    similarity_matrix = similarity.build_similarity_matrix(tfidf_matrix)
    similarity.save_similarity_matrix(similarity_matrix)

    movie_index = similarity.build_movie_index(movies)
    similarity.save_movie_index(movie_index)


def main(limit: int | None, workers: int) -> None:
    started_at = time.time()

    logger.info("Loading MovieLens source data")
    source_movies = load_movielens_source()
    if limit:
        source_movies = source_movies.sort_values("movie_id").head(limit)
    logger.info("Working with %d movies after MovieLens/TMDb link join", len(source_movies))

    enriched_movies = build_enriched_catalog(source_movies, workers=workers)
    if enriched_movies.empty:
        logger.error("No movies were successfully enriched — check TMDB_API_KEY and network access.")
        sys.exit(1)

    settings.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    enriched_movies.to_parquet(settings.MOVIES_PARQUET_PATH, index=False)
    logger.info("Saved processed catalog to %s", settings.MOVIES_PARQUET_PATH)

    build_recommendation_model(enriched_movies)

    elapsed = time.time() - started_at
    logger.info("Build complete in %.1fs — %d movies ready to serve", elapsed, len(enriched_movies))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the CineMatch recommendation model")
    parser.add_argument("--limit", type=int, default=None, help="Cap the number of movies processed")
    parser.add_argument("--workers", type=int, default=8, help="Concurrent TMDb enrichment requests")
    args = parser.parse_args()

    main(limit=args.limit, workers=args.workers)
