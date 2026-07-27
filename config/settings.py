import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
MODEL_DATA_DIR = BASE_DIR / "data" / "model"

MOVIES_PARQUET_PATH = PROCESSED_DATA_DIR / "movies.parquet"
VECTORIZER_PATH = MODEL_DATA_DIR / "vectorizer.pkl"
SIMILARITY_MATRIX_PATH = MODEL_DATA_DIR / "similarity_matrix.pkl"
MOVIE_INDEX_PATH = MODEL_DATA_DIR / "movie_index.pkl"

MOVIELENS_RATINGS_PATH = RAW_DATA_DIR / "ratings.csv"
MOVIELENS_MOVIES_PATH = RAW_DATA_DIR / "movies.csv"
MOVIELENS_LINKS_PATH = RAW_DATA_DIR / "links.csv"

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_API_BASE_URL = os.getenv("TMDB_API_BASE_URL", "https://api.themoviedb.org/3")
TMDB_IMAGE_BASE_URL = os.getenv("TMDB_IMAGE_BASE_URL", "https://image.tmdb.org/t/p")

POSTER_SIZE = "w500"
BACKDROP_SIZE = "w780"

TMDB_CACHE_PATH = BASE_DIR / "data" / "tmdb_cache"
TMDB_CACHE_TTL_SECONDS = 60 * 60 * 6  # 6 hours, enrichment data goes stale slowly
TMDB_REQUEST_TIMEOUT = 8
TMDB_MAX_RETRIES = 3

MIN_VOTE_COUNT_FOR_QUALITY = 20  # filters out movies with too few ratings to trust
TOP_K_RECOMMENDATIONS = 12
TFIDF_MAX_FEATURES = 20000

FEATURE_WEIGHTS = {
    "genres": 1,
    "keywords": 1,
    "cast": 1,
    "director": 2,  # repeated in the corpus so it carries more weight in TF-IDF
}

APP_TITLE = "CineMatch"
APP_ICON = "🎬"
