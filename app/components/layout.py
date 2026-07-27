import streamlit as st

from config.settings import APP_ICON, APP_TITLE

DARK_THEME_CSS = """
<style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    [data-testid="stSidebar"] { background-color: #161a23; }
</style>
"""

LIGHT_THEME_CSS = """
<style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    [data-testid="stSidebar"] { background-color: #f5f5f7; }
</style>
"""


def configure_page(page_title: str) -> None:
    st.set_page_config(
        page_title=f"{page_title} · {APP_TITLE}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _apply_theme()


def _apply_theme() -> None:
    theme = st.session_state.setdefault("theme", "dark")
    st.markdown(DARK_THEME_CSS if theme == "dark" else LIGHT_THEME_CSS, unsafe_allow_html=True)


def render_theme_toggle() -> None:
    theme = st.session_state.setdefault("theme", "dark")
    toggle_label = "☀️ Light mode" if theme == "dark" else "🌙 Dark mode"
    if st.sidebar.button(toggle_label, use_container_width=True):
        st.session_state["theme"] = "light" if theme == "dark" else "dark"
        st.rerun()


def render_header(subtitle: str | None = None) -> None:
    st.title(f"{APP_ICON} {APP_TITLE}")
    if subtitle:
        st.caption(subtitle)