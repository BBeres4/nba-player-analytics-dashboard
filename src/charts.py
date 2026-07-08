"""Altair chart builders shared across tabs.

Centralizing these keeps every chart in the app using the same color
palette, fonts, and sizing — instead of each tab re-declaring its own
one-off Altair spec.
"""

from __future__ import annotations

import altair as alt
import pandas as pd

from src.config import ARCHETYPE_PALETTE, BRAND, PRETTY_NAMES

ACCENT = BRAND["gold"]


def histogram(df: pd.DataFrame, metric: str) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_bar(opacity=0.9, color=ACCENT, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X(f"{metric}:Q", bin=alt.Bin(maxbins=24), title=""),
            y=alt.Y("count():Q", title="Number of players"),
            tooltip=["count():Q"],
        )
        .properties(height=320)
    )


def trend_line(trend_df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(trend_df)
        .mark_line(point=True, strokeWidth=2.5)
        .encode(
            x=alt.X("season:N", title="Season"),
            y=alt.Y("value:Q", title="Value"),
            color=alt.Color(
                "metric:N",
                title="Metric",
                scale=alt.Scale(range=[BRAND["gold"], BRAND["teal"], BRAND["muted"]]),
            ),
            tooltip=["season", "metric", "value"],
        )
        .properties(height=340)
    )


def style_map(x: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(x.reset_index())
        .mark_circle(size=100, opacity=0.85)
        .encode(
            x=alt.X("pca1:Q", title="Style Map (left / right)"),
            y=alt.Y("pca2:Q", title="Style Map (up / down)"),
            color=alt.Color("role:N", title="Archetype", scale=alt.Scale(range=ARCHETYPE_PALETTE)),
            tooltip=["player:N", "role:N"],
        )
        .interactive()
        .properties(height=440)
    )


def correlation_heatmap(corr_long: pd.DataFrame, cols: list[str]) -> alt.Chart:
    return (
        alt.Chart(corr_long)
        .mark_rect()
        .encode(
            x=alt.X("stat_x:N", title="", sort=cols),
            y=alt.Y("stat_y:N", title="", sort=cols),
            color=alt.Color(
                "corr:Q",
                title="Correlation",
                scale=alt.Scale(domain=[-1, 1], range=[BRAND["teal"], BRAND["paper"], BRAND["gold"]]),
            ),
            tooltip=[
                alt.Tooltip("stat_x:N", title="Stat A"),
                alt.Tooltip("stat_y:N", title="Stat B"),
                alt.Tooltip("corr:Q", title="Correlation", format=".2f"),
            ],
        )
        .properties(height=320)
    )


def scatter(df: pd.DataFrame, x_stat: str, y_stat: str) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_circle(opacity=0.65, size=80, color=ACCENT)
        .encode(
            x=alt.X(f"{x_stat}:Q", title=PRETTY_NAMES[x_stat]),
            y=alt.Y(f"{y_stat}:Q", title=PRETTY_NAMES[y_stat]),
            tooltip=[
                "player:N", "team:N", "season:N",
                alt.Tooltip(f"{x_stat}:Q", title=PRETTY_NAMES[x_stat], format=".2f"),
                alt.Tooltip(f"{y_stat}:Q", title=PRETTY_NAMES[y_stat], format=".2f"),
            ],
        )
        .interactive()
        .properties(height=360)
    )


def comparison_bars(compare_df: pd.DataFrame) -> alt.Chart:
    """Grouped bar chart comparing two players' standardized stats."""
    return (
        alt.Chart(compare_df)
        .mark_bar()
        .encode(
            y=alt.Y("stat:N", title="", sort=None),
            x=alt.X("z_score:Q", title="Standardized value (league average = 0)"),
            color=alt.Color(
                "player:N",
                title="Player",
                scale=alt.Scale(range=[BRAND["gold"], BRAND["teal"]]),
            ),
            yOffset="player:N",
            tooltip=["player:N", "stat:N", alt.Tooltip("z_score:Q", format=".2f")],
        )
        .properties(height=280)
    )
