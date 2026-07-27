import pandas as pd
import streamlit as st

from components.filters import render_sidebar_filters
from components.layout import configure_page, render_header, render_theme_toggle
from components.movie_card import render_movie_grid
from config.settings import MIN_VOTE_COUNT_FOR_QUALITY
from core.data.loader import (
    filter_movies,
    get_trending_fallback,
    load_movies,
    search_by_title,
    sort_movies,
)
from core.tmdb.client import TMDbUnavailableError, get_trending_movies

configure_page("Home")
render_header("Movies worth your time, matched to what you already love.")
render_theme_toggle()


@st.cache_data(ttl=60 * 60 * 6)
def load_trending() -> pd.DataFrame:
    movies = load_movies()
    try:
        trending_payload = get_trending_movies()
    except TMDbUnavailableError:
        return get_trending_fallback()

    trending_tmdb_ids = {item["id"] for item in trending_payload}
    trending_movies = movies[movies["tmdb_id"].isin(trending_tmdb_ids)]

    if trending_movies.empty:
        return get_trending_fallback()

    order = {tmdb_id: position for position, tmdb_id in enumerate(trending_tmdb_ids)}
    return trending_movies.assign(_order=trending_movies["tmdb_id"].map(order)).sort_values("_order").drop(columns="_order")


def handle_surprise_me() -> None:
    movies = load_movies()
    qualified = movies[movies["vote_count"] >= MIN_VOTE_COUNT_FOR_QUALITY]
    pool = qualified if not qualified.empty else movies
    chosen = pool.sample(1).iloc[0]
    st.session_state["selected_movie_id"] = int(chosen["movie_id"])
    st.switch_page("pages/1_Movie_Details.py")


search_column, surprise_column = st.columns([5, 1])
with search_column:
    query = st.text_input("Search movies", placeholder="Try 'Inception' or 'The Dark Knight'", label_visibility="collapsed")
with surprise_column:
    if st.button("🎲 Surprise Me", use_container_width=True):
        handle_surprise_me()

filters = render_sidebar_filters(key_prefix="home")

if query:
    st.subheader(f"Results for \"{query}\"")
    results = search_by_title(query, limit=24)
    render_movie_grid(results, key_prefix="search")
else:
    st.subheader("🔥 Trending this week")
    trending = load_trending()
    render_movie_grid(trending.head(8), key_prefix="trending")

    st.divider()
    st.subheader("Browse the catalog")
    catalog = filter_movies(
        load_movies(),
        genre=filters["genre"],
        year_range=filters["year_range"],
        min_rating=filters["min_rating"],
        language=filters["language"],
    )
    catalog = sort_movies(catalog, by=filters["sort_by"])
    render_movie_grid(catalog.head(24), key_prefix="browse")
