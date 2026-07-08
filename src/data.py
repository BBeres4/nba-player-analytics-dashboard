"""Loading, cleaning, feature engineering, and filtering for player data."""

from __future__ import annotations

import sqlite3

import numpy as np
import pandas as pd
import streamlit as st

from src.config import CSV_PATH, DATA_DIR, DB_PATH, NUMERIC_COLS


def load_raw_data() -> pd.DataFrame:
    """Load the raw player-season CSV and normalize columns/types."""
    if not CSV_PATH.exists():
        st.error("Missing NBA data. Run: python scripts/fetch_nba_data.py")
        st.stop()

    df = pd.read_csv(CSV_PATH)
    df.columns = [c.lower().strip() for c in df.columns]

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Guard rate stats against divide-by-zero on tiny sample sizes.
    if "games" in df.columns:
        df["games"] = df["games"].clip(lower=1)
    if "minutes" in df.columns:
        df["minutes"] = df["minutes"].clip(lower=1)

    for col in ("team", "player", "position", "season"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    if "team" in df.columns:
        df["team"] = df["team"].str.upper()
    if "position" in df.columns:
        df["position"] = df["position"].str.upper()

    return df


def add_advanced_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Derive TS%, usage rate, and a demo PER-like impact score.

    These are simplified stand-ins for real advanced metrics — good enough
    for exploring patterns, not meant to match the official NBA formulas.
    """
    df = df.copy()

    # TS% = scoring efficiency, including free throws in the shot count.
    denom = 2 * (df["fga"] + 0.44 * df["fta"])
    df["ts_pct"] = (df["pts"] / denom).replace([np.inf, -np.inf], 0).fillna(0)

    # Usage proxy = share of a player's minutes spent ending possessions.
    df["usage_rate"] = ((df["fga"] + 0.44 * df["fta"] + df["tov"]) / df["minutes"]) * 100

    # Demo "overall impact" score, NOT the official NBA PER.
    df["per"] = (
        (df["pts"] + df["reb"] * 1.2 + df["ast"] * 1.5 + df["stl"] * 2 + df["blk"] * 2)
        / df["games"]
        - df["tov"] * 0.5
    )
    return df


def ensure_db() -> None:
    """Build the SQLite cache once so reruns don't re-parse the CSV."""
    DATA_DIR.mkdir(exist_ok=True)
    if DB_PATH.exists():
        return

    df = add_advanced_stats(load_raw_data())
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("players", conn, if_exists="replace", index=False)


@st.cache_data(show_spinner="Loading player data…")
def load_data() -> pd.DataFrame:
    """Read the processed dataset from SQLite (cached across reruns)."""
    ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql("SELECT * FROM players", conn)


def filter_data(
    df: pd.DataFrame,
    *,
    season: str = "All",
    team: str = "All",
    player: str = "All",
    position: str = "All",
    min_games: int = 0,
) -> pd.DataFrame:
    """Apply the shared sidebar filters used across every tab."""
    out = df
    if season != "All":
        out = out[out["season"] == season]
    if team != "All":
        out = out[out["team"] == team]
    if player != "All":
        out = out[out["player"] == player]
    if position != "All":
        out = out[out["position"] == position]
    out = out[out["games"] >= min_games]
    return out
