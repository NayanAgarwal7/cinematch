import streamlit as st

from components.layout import configure_page, render_theme_toggle
from core.data.loader import get_movie

configure_page("Movie Details")
render_theme_toggle()

movie_id = st.session_state.get("selected_movie_id")

if movie_id is None:
    st.info("Pick a movie from Home first, then come back here.")
    if st.button("Go to Home"):
        st.switch_page("Home.py")
    st.stop()

movie = get_movie(movie_id)

if movie is None:
    st.error("That movie isn't in the catalog anymore.")
    st.stop()

favorites = st.session_state.setdefault("favorite_ids", set())
is_favorite = movie["movie_id"] in favorites

poster_column, info_column = st.columns([1, 2])

with poster_column:
    poster_url = (
        f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
        if movie.get("poster_path")
        else "https://placehold.co/400x600?text=No+Poster"
    )
    st.image(poster_url)

    favorite_label = "♥ Remove from Favorites" if is_favorite else "♡ Add to Favorites"
    if st.button(favorite_label, use_container_width=True):
        if is_favorite:
            favorites.remove(movie["movie_id"])
        else:
            favorites.add(movie["movie_id"])
        st.rerun()

    if st.button("🎯 See Similar Movies", use_container_width=True, type="primary"):
        st.session_state["recommend_for_movie_id"] = movie["movie_id"]
        st.switch_page("pages/2_Recommendations.py")

with info_column:
    st.title(movie["title"])

    meta_parts = []
    if movie.get("release_year"):
        meta_parts.append(str(int(movie["release_year"])))
    if movie.get("runtime"):
        meta_parts.append(f"{int(movie['runtime'])} min")
    if movie.get("original_language"):
        meta_parts.append(movie["original_language"].upper())
    st.caption("  ·  ".join(meta_parts))

    if movie.get("vote_average"):
        st.metric("TMDb Rating", f"{movie['vote_average']:.1f} / 10", f"{int(movie.get('vote_count', 0))} votes")

    genres = movie.get("genres")

    if genres is not None and len(genres) > 0:
        st.write(" ".join(f"`{genre}`" for genre in genres))

    st.subheader("Overview")
    st.write(movie.get("overview") or "No overview available for this title.")

    director = movie.get("director")

    if director:
        st.write(f"**Director:** {director}")

    cast = movie.get("cast")

    if cast is not None and len(cast) > 0:
        st.write(f"**Cast:** {', '.join(cast[:5])}")
