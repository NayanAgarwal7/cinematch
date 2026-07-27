import pickle

import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

from config.settings import TFIDF_MAX_FEATURES, VECTORIZER_PATH


def fit_vectorizer(corpus: pd.Series) -> tuple[TfidfVectorizer, csr_matrix]:
    vectorizer = TfidfVectorizer(
        max_features=TFIDF_MAX_FEATURES,
        stop_words="english",
        ngram_range=(1, 1),
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)
    return vectorizer, tfidf_matrix


def save_vectorizer(vectorizer: TfidfVectorizer, path=VECTORIZER_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as handle:
        pickle.dump(vectorizer, handle)


def load_vectorizer(path=VECTORIZER_PATH) -> TfidfVectorizer:
    with open(path, "rb") as handle:
        return pickle.load(handle)
