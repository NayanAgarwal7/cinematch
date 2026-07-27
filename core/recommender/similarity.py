import pickle

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import linear_kernel

from config.settings import MOVIE_INDEX_PATH, SIMILARITY_MATRIX_PATH, TOP_K_RECOMMENDATIONS


def build_similarity_matrix(tfidf_matrix: csr_matrix) -> np.ndarray:
    # TF-IDF vectors from scikit-learn are L2-normalized, so the linear
    # kernel (a plain dot product) is mathematically equivalent to cosine
    # similarity here, without the overhead of computing norms twice.
    return linear_kernel(tfidf_matrix, tfidf_matrix)


def build_movie_index(movies: pd.DataFrame) -> dict[int, int]:
    """Maps a movie_id to its row position in the similarity matrix."""
    return {movie_id: position for position, movie_id in enumerate(movies["movie_id"])}


def save_similarity_matrix(matrix: np.ndarray, path=SIMILARITY_MATRIX_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as handle:
        pickle.dump(matrix, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_similarity_matrix(path=SIMILARITY_MATRIX_PATH) -> np.ndarray:
    with open(path, "rb") as handle:
        return pickle.load(handle)


def save_movie_index(index: dict[int, int], path=MOVIE_INDEX_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as handle:
        pickle.dump(index, handle)


def load_movie_index(path=MOVIE_INDEX_PATH) -> dict[int, int]:
    with open(path, "rb") as handle:
        return pickle.load(handle)


def _rescale_scores(raw_scores: np.ndarray) -> np.ndarray:
    """Raw cosine similarity on a sparse bag-of-words tends to sit in a
    narrow band (roughly 0.1-0.4), which reads as 'nothing matches well'
    even for genuinely strong recommendations. Rescaling within the
    candidate pool gives a display score that reflects relative fit rather
    than an absolute, hard-to-interpret cosine value."""
    lowest, highest = raw_scores.min(), raw_scores.max()
    if highest == lowest:
        return np.full_like(raw_scores, 70.0)
    return 50 + 50 * (raw_scores - lowest) / (highest - lowest)


def get_similar_movies(
    movie_id: int,
    movies: pd.DataFrame,
    similarity_matrix: np.ndarray,
    movie_index: dict[int, int],
    top_k: int = TOP_K_RECOMMENDATIONS,
) -> pd.DataFrame:
    if movie_id not in movie_index:
        return movies.iloc[0:0]

    row_position = movie_index[movie_id]
    similarity_scores = similarity_matrix[row_position]

    candidate_positions = np.argsort(similarity_scores)[::-1]
    candidate_positions = candidate_positions[candidate_positions != row_position][:top_k]

    raw_scores = similarity_scores[candidate_positions]
    display_scores = _rescale_scores(raw_scores)

    recommendations = movies.iloc[candidate_positions].copy()
    recommendations["match_score"] = np.round(display_scores, 1)
    recommendations["source_movie_id"] = movie_id
    return recommendations
