import streamlit as st

from core.data.loader import list_all_genres, list_all_languages, load_movies

SORT_OPTIONS = {
    "Most popular": "popularity",
    "Highest rated": "rating",
    "Newest first": "newest",
    "Title (A-Z)": "title",
}


def render_sidebar_filters(key_prefix: str = "filters") -> dict:
    movies = load_movies()
    min_year = int(movies["release_year"].min())
    max_year = int(movies["release_year"].max())

    st.sidebar.subheader("Filters")

    genre = st.sidebar.selectbox("Genre", list_all_genres(), key=f"{key_prefix}_genre")

    year_range = st.sidebar.slider(
        "Release year",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        key=f"{key_prefix}_year",
    )

    min_rating = st.sidebar.slider(
        "Minimum rating",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.5,
        key=f"{key_prefix}_rating",
    )

    language = st.sidebar.selectbox("Language", list_all_languages(), key=f"{key_prefix}_language")

    sort_label = st.sidebar.radio("Sort by", list(SORT_OPTIONS.keys()), key=f"{key_prefix}_sort")

    return {
        "genre": genre,
        "year_range": year_range,
        "min_rating": min_rating,
        "language": language,
        "sort_by": SORT_OPTIONS[sort_label],
    }
