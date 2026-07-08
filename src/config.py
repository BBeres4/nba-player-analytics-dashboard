"""Central place for paths, column lists, and the app's color palette.

Keeping these in one module means every other file (data loading, charts,
theme) references the same names instead of re-typing magic strings.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------- paths ----
APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
CSV_PATH = DATA_DIR / "player_stats.csv"
DB_PATH = DATA_DIR / "nba_stats.sqlite"

# ------------------------------------------------------------- columns ----
NUMERIC_COLS = [
    "games", "minutes", "pts", "ast", "reb", "stl", "blk",
    "tov", "fga", "fgm", "fta", "ftm",
]

# The six derived stats used throughout the app for rankings, archetypes,
# and correlations.
FEATURES = ["pts", "reb", "ast", "ts_pct", "usage_rate", "per"]

PRETTY_NAMES = {
    "pts": "PTS (Scoring)",
    "reb": "REB (Rebounds)",
    "ast": "AST (Assists)",
    "ts_pct": "TS% (Efficiency)",
    "usage_rate": "Usage (Involvement)",
    "per": "PER (Overall Impact)",
}

# ------------------------------------------------------------- palette ----
# Mirrors the ink / gold / teal palette used on the rest of the portfolio
# site so the live app feels like part of the same brand, not a bolted-on
# demo.
BRAND = {
    "ink": "#10151f",
    "ink_soft": "#1b2333",
    "paper": "#f2efe4",
    "gold": "#c1953c",
    "gold_soft": "#e7d3a4",
    "teal": "#2f6f5e",
    "muted": "#a9b0c0",
}

# 10 distinct colors for the 10 player archetypes, built from tints and
# shades of the brand palette so the style map reads as one coherent chart
# instead of a default rainbow.
ARCHETYPE_PALETTE = [
    "#c1953c", "#2f6f5e", "#5c7a99", "#b0752c", "#6fae9c",
    "#8a6d3b", "#33405a", "#d1b46a", "#3d8c73", "#9c6b9e",
]
