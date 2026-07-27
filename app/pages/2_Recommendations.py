import streamlit as st

from components.layout import configure_page, render_theme_toggle
from components.movie_card import render_movie_grid
from core.data.loader import get_movie, load_movies, search_by_title
from core.recommender.explain import explain_recommendation
from core.recommender.similarity import get_similar_movies, load_movie_index, load_similarity_matrix

configure_page("Recommendations")
render_theme_toggle()


@st.cache_resource
def load_model():
    return load_similarity_matrix(), load_movie_index()


similarity_matrix, movie_index = load_model()
movies = load_movies()

st.title("🎯 Find Similar Movies")

preselected_id = st.session_state.pop("recommend_for_movie_id", None) or st.session_state.get("selected_movie_id")
default_title = ""
if preselected_id:
    preselected_movie = get_movie(preselected_id)
    if preselected_movie:
        default_title = preselected_movie["title"]

query = st.text_input("Pick a movie you like", value=default_title, placeholder="Start typing a title...")

source_movie_id = None
if query:
    matches = search_by_title(query, limit=5)
    if matches.empty:
        st.warning("No titles matched that search.")
    else:
        titles = matches["title"].tolist()
        chosen_title = st.selectbox("Did you mean", titles, index=0)
        source_movie_id = int(matches[matches["title"] == chosen_title].iloc[0]["movie_id"])

if source_movie_id:
    source_movie = movies[movies["movie_id"] == source_movie_id].iloc[0]

    st.divider()
    st.subheader(f"Because you liked {source_movie['title']}")

    recommendations = get_similar_movies(
        movie_id=source_movie_id,
        movies=movies,
        similarity_matrix=similarity_matrix,
        movie_index=movie_index,
    )

    recommendations["reason"] = recommendations.apply(
        lambda candidate: explain_recommendation(source_movie, candidate), axis=1
    )

    render_movie_grid(
        recommendations,
        key_prefix="recs",
        score_column="match_score",
        reason_column="reason",
    )
else:
    st.info("Search for a movie above to get tailored recommendations.")
