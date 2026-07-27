import streamlit as st

from components.layout import configure_page, render_theme_toggle
from components.movie_card import render_movie_grid
from core.data.loader import load_movies

configure_page("Favorites")
render_theme_toggle()

st.title("♥ Your Favorites")

favorite_ids = st.session_state.setdefault("favorite_ids", set())

if not favorite_ids:
    st.info("You haven't saved any movies yet — tap the ♡ on a movie card to add one.")
    if st.button("Browse movies"):
        st.switch_page("app/Home.py")
    st.stop()

movies = load_movies()
favorites = movies[movies["movie_id"].isin(favorite_ids)]

st.caption(f"{len(favorites)} saved title{'s' if len(favorites) != 1 else ''}")
render_movie_grid(favorites, key_prefix="favorites")
