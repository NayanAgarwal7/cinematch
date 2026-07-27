import streamlit as st

from config.settings import POSTER_SIZE, TMDB_IMAGE_BASE_URL

PLACEHOLDER_POSTER = "https://placehold.co/300x450?text=No+Poster"


def _poster_url(poster_path: str | None) -> str:
    if not poster_path:
        return PLACEHOLDER_POSTER
    return f"{TMDB_IMAGE_BASE_URL}/{POSTER_SIZE}{poster_path}"


def _toggle_favorite(movie_id: int) -> None:
    favorites = st.session_state.setdefault("favorite_ids", set())
    if movie_id in favorites:
        favorites.remove(movie_id)
    else:
        favorites.add(movie_id)


def render_movie_card(movie: dict, key_prefix: str, match_score: float | None = None, reason: str | None = None) -> None:
    favorites = st.session_state.setdefault("favorite_ids", set())
    is_favorite = movie["movie_id"] in favorites

    with st.container(border=True):
        st.image(_poster_url(movie.get("poster_path")))

        st.markdown(f"**{movie['title']}**")

        year = movie.get("release_year")
        rating = movie.get("vote_average")
        meta_line = f"{int(year)}" if year else "Year unknown"
        if rating:
            meta_line += f"  ·  ⭐ {rating:.1f}"
        st.caption(meta_line)

        if match_score is not None:
            st.progress(min(match_score / 100, 1.0), text=f"{match_score:.0f}% match")

        if reason:
            st.caption(reason)

        button_row = st.columns([1, 1])
        with button_row[0]:
            if st.button("Details", key=f"{key_prefix}_details_{movie['movie_id']}", use_container_width=True):
                st.session_state["selected_movie_id"] = int(movie["movie_id"])
                st.switch_page("pages/1_Movie_Details.py")

        with button_row[1]:
            favorite_label = "♥ Saved" if is_favorite else "♡ Save"
            if st.button(favorite_label, key=f"{key_prefix}_fav_{movie['movie_id']}", use_container_width=True):
                _toggle_favorite(movie["movie_id"])
                st.rerun()


def render_movie_grid(movies, columns: int = 4, key_prefix: str = "grid", score_column: str | None = None, reason_column: str | None = None) -> None:
    if movies.empty:
        st.info("No movies match these filters yet — try loosening one of them.")
        return

    rows = [movies.iloc[i:i + columns] for i in range(0, len(movies), columns)]
    for row in rows:
        row_columns = st.columns(columns)
        for column, (_, movie) in zip(row_columns, row.iterrows()):
            with column:
                render_movie_card(
                    movie.to_dict(),
                    key_prefix=key_prefix,
                    match_score=movie.get(score_column) if score_column else None,
                    reason=movie.get(reason_column) if reason_column else None,
                )
