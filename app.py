"""NBA Player Analytics — Streamlit entry point.

This file only wires things together: load data, render the sidebar,
show the header + summary metrics, then hand off to each tab's render
function in src/views.py. All data logic, chart styling, and clustering
live in src/ so this file stays readable as a table of contents.
"""

from __future__ import annotations

from src import views
from src.config import FEATURES
from src.data import filter_data, load_data
from src.theme import card_close, card_open, eyebrow, inject_css, muted

import streamlit as st

st.set_page_config(page_title="NBA Player Analytics", page_icon="🏀", layout="wide")
inject_css()

base = load_data()

# =============================================================== SIDEBAR ===
st.sidebar.header("Filters")
st.sidebar.caption("These apply across every tab.")

seasons = sorted(base["season"].unique())
teams = sorted(base["team"].unique())
players = sorted(base["player"].unique())
positions = sorted(p for p in base["position"].unique() if p and p.upper() != "UNK")

with st.sidebar.expander("Season / Team / Player", expanded=True):
    season = st.selectbox("Season", ["All"] + seasons)
    team = st.selectbox("Team", ["All"] + teams)
    position = st.selectbox("Position", ["All"] + positions) if positions else "All"
    player = st.selectbox("Player", ["All"] + players)

with st.sidebar.expander("Minimums", expanded=True):
    min_games = st.slider("Min Games", 0, 82, 40)
    muted("Higher minimums remove small sample sizes (more reliable).")

df = filter_data(base, season=season, team=team, player=player, position=position, min_games=min_games)

# ================================================================ HEADER ===
eyebrow("Streamlit · scikit-learn · Altair")
st.title("🏀 NBA Player Analytics")
muted(
    "A dashboard for exploring player performance, custom rankings, player "
    "\u201carchetypes,\u201d and simple statistical patterns."
)
st.write("")

card_open()
st.markdown(
    "**Quick guide to the main stats:** "
    "**PTS** — points scored per game &nbsp;·&nbsp; "
    "**TS%** — scoring efficiency (points per shot attempt) &nbsp;·&nbsp; "
    "**Usage** — how involved a player is in the offense &nbsp;·&nbsp; "
    "**PER (demo)** — an overall-impact score built from box score stats "
    "(not the official NBA PER)",
    unsafe_allow_html=True,
)
card_close()
st.write("")

if df.empty:
    st.warning("No players match these filters — try lowering the games minimum or widening your selection.")
else:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Players", int(df["player"].nunique()))
    c2.metric("Total PTS", f"{df['pts'].sum():,.0f}")
    c3.metric("Avg TS%", f"{df['ts_pct'].mean():.3f}")
    c4.metric("Avg PER (demo)", f"{df['per'].mean():.2f}")
st.write("")

# ================================================================== TABS ===
tab_names = [
    "📊 Overview", "🧑 Player", "⚔️ Compare",
    "🏟 Team Hub", "🏁 Rankings", "🧩 Archetypes", "🧠 Insights",
]
overview_tab, player_tab, compare_tab, team_tab, rankings_tab, archetypes_tab, insights_tab = st.tabs(tab_names)

with overview_tab:
    views.render_overview(df)
with player_tab:
    views.render_player(base, player)
with compare_tab:
    views.render_compare(base, players)
with team_tab:
    views.render_team_hub(base, teams, min_games)
with rankings_tab:
    views.render_rankings(base, min_games)
with archetypes_tab:
    views.render_archetypes(base, min_games)
with insights_tab:
    views.render_insights(df)
