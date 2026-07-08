"""Render functions for each tab in the app.

Each function takes whatever data/state it needs and draws its tab's
content. Keeping these out of app.py makes the entry point read like a
table of contents instead of a 700-line script.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src import archetypes as arch_mod
from src import charts
from src.config import FEATURES, PRETTY_NAMES
from src.scoring import custom_rank
from src.theme import card_close, card_open, muted

# ============================================================ OVERVIEW ====
def render_overview(df: pd.DataFrame) -> None:
    st.subheader("Overview")
    muted("Start here: a simple top list, then a distribution chart to see what's normal vs. rare.")
    st.write("")

    if df.empty:
        st.info("No players match the current filters.")
        return

    st.markdown("**Top Players by Overall Impact (PER demo)**")
    st.caption("Use the sidebar filters to narrow this down.")

    top = (
        df.sort_values("per", ascending=False)
        .loc[:, ["player", "team", "season", "games", "pts", "reb", "ast", "ts_pct", "usage_rate", "per"]]
        .head(20)
    )

    st.dataframe(
        top.style.format({
            "pts": "{:.1f}", "reb": "{:.1f}", "ast": "{:.1f}",
            "ts_pct": "{:.3f}", "usage_rate": "{:.1f}", "per": "{:.2f}",
        }),
        use_container_width=True,
    )
    st.download_button(
        "⬇️ Download this table as CSV",
        top.to_csv(index=False).encode("utf-8"),
        file_name="nba_top_players.csv",
        mime="text/csv",
    )

    st.write("")
    st.markdown("**How are players distributed?**")
    metric = st.selectbox(
        "Pick a metric to see its distribution",
        FEATURES,
        format_func=lambda m: PRETTY_NAMES[m],
    )
    st.altair_chart(charts.histogram(df, metric), use_container_width=True)
    muted("Tip: a long tail means a small number of players are extreme outliers.")


# ============================================================== PLAYER ====
def render_player(base: pd.DataFrame, player: str) -> None:
    st.subheader("Player Snapshot")
    muted("Pick a player in the sidebar to see their latest season, trend, and closest statistical peers.")
    st.write("")

    if player == "All":
        st.info("Select a player from the sidebar to view details.")
        return

    pdata = base[base["player"] == player].sort_values("season")
    latest = pdata.iloc[-1]

    card_open()
    st.markdown(f"### {player}")
    muted(f"{latest['team']} · Season {latest['season']}")
    a, b, c, d = st.columns(4)
    a.metric("PER (demo)", f"{latest['per']:.2f}")
    b.metric("TS% (efficiency)", f"{latest['ts_pct']:.3f}")
    c.metric("Usage (involvement)", f"{latest['usage_rate']:.1f}")
    d.metric("Games", f"{latest['games']:.0f}")
    card_close()
    st.write("")

    st.caption("Trend chart: see whether the player improved, declined, or stayed consistent across seasons.")
    trend = pdata[["season", "per", "ts_pct", "usage_rate"]].melt(
        "season", var_name="metric", value_name="value"
    )
    trend["metric"] = trend["metric"].map({
        "per": PRETTY_NAMES["per"],
        "ts_pct": PRETTY_NAMES["ts_pct"],
        "usage_rate": PRETTY_NAMES["usage_rate"],
    })
    st.altair_chart(charts.trend_line(trend), use_container_width=True)

    st.write("")
    st.subheader("Closest Statistical Peers")
    st.caption("Players with the most similar overall stat profile (standardized distance).")

    similar = _find_similar_players(base, player)
    if similar is not None and not similar.empty:
        st.dataframe(similar, use_container_width=True)
    else:
        st.info("Not enough data to find comparable players yet.")


def _find_similar_players(base: pd.DataFrame, player: str, top_n: int = 8) -> pd.DataFrame | None:
    """Nearest neighbors in standardized stat-space (simple Euclidean distance)."""
    x = base.groupby("player")[FEATURES].mean()
    if player not in x.index or len(x) < 2:
        return None

    z = (x - x.mean()) / x.std()
    target = z.loc[player]
    distance = ((z - target) ** 2).sum(axis=1).pow(0.5).drop(index=player, errors="ignore")

    return distance.sort_values().head(top_n).rename("distance").reset_index()


# ============================================================= COMPARE ====
def render_compare(base: pd.DataFrame, players: list[str]) -> None:
    st.subheader("Compare Two Players")
    muted("Pick any two players to see how their stat profiles differ, relative to the league average.")
    st.write("")

    if len(players) < 2:
        st.info("Not enough players in the dataset to compare.")
        return

    left, right = st.columns(2)
    with left:
        player_a = st.selectbox("Player A", players, index=0, key="cmp_a")
    with right:
        player_b = st.selectbox("Player B", players, index=min(1, len(players) - 1), key="cmp_b")

    if player_a == player_b:
        st.warning("Pick two different players to compare.")
        return

    x = base.groupby("player")[FEATURES].mean()
    if player_a not in x.index or player_b not in x.index:
        st.info("Not enough games for one of these players yet.")
        return

    z = (x - x.mean()) / x.std()

    compare_df = pd.concat([
        z.loc[player_a].rename("z_score").reset_index().assign(player=player_a),
        z.loc[player_b].rename("z_score").reset_index().assign(player=player_b),
    ]).rename(columns={"index": "stat"})
    compare_df["stat"] = compare_df["stat"].map(PRETTY_NAMES)

    card_open()
    a, b = st.columns(2)
    a.metric(f"{player_a} · PER (demo)", f"{x.loc[player_a, 'per']:.2f}")
    b.metric(f"{player_b} · PER (demo)", f"{x.loc[player_b, 'per']:.2f}")
    card_close()
    st.write("")

    st.caption("Bars show each stat as standard deviations above (+) or below (−) the league average.")
    st.altair_chart(charts.comparison_bars(compare_df), use_container_width=True)

    st.write("")
    st.markdown("**Career averages, side by side**")
    raw_compare = x.loc[[player_a, player_b], FEATURES].round(2).rename(columns=PRETTY_NAMES)
    st.dataframe(raw_compare, use_container_width=True)


# ============================================================ TEAM HUB ====
def render_team_hub(base: pd.DataFrame, teams: list[str], min_games: int) -> None:
    st.subheader("Team Hub")
    muted("Pick a team to see a roster summary (per-player averages).")
    st.write("")

    team_pick = st.selectbox("Team", teams)
    tdf = base[(base["team"] == team_pick) & (base["games"] >= min_games)]

    card_open()
    a, b = st.columns(2)
    a.metric("Players", int(tdf["player"].nunique()))
    b.metric("Avg PER (demo)", f"{tdf['per'].mean():.2f}" if not tdf.empty else "—")
    card_close()
    st.write("")

    if tdf.empty:
        st.info("No players meet the games minimum for this team — try lowering it in the sidebar.")
        return

    st.caption("Roster table = each player's average stats (filtered by minimum games).")
    roster = (
        tdf.groupby("player", as_index=False)[["pts", "reb", "ast", "per"]]
        .mean()
        .sort_values("per", ascending=False)
        .round(2)
        .rename(columns={"pts": "PTS", "reb": "REB", "ast": "AST", "per": "PER (demo)"})
    )
    st.dataframe(roster, use_container_width=True)


# ============================================================ RANKINGS ====
def render_rankings(base: pd.DataFrame, min_games: int) -> None:
    st.subheader("Custom Ranking")
    muted('Build your own definition of "best player" by weighting the stats you care about.')
    st.write("")

    card_open()
    st.markdown(
        "**How it works:** you choose how important each stat is, we standardize every player "
        "against the league average, then combine the stats into one score. Higher score = better "
        "by *your* definition."
    )
    card_close()
    st.write("")

    w_per = st.slider("PER weight (overall impact)", 0.0, 3.0, 1.5)
    st.caption("Higher = you care more about overall box-score impact.")
    w_ts = st.slider("TS% weight (efficiency)", 0.0, 3.0, 1.0)
    st.caption("Higher = you care more about efficient scoring.")
    w_pts = st.slider("PTS weight (scoring volume)", 0.0, 3.0, 0.5)
    st.caption("Higher = you care more about players who score a lot.")

    ref = base[base["games"] >= min_games]
    if ref.empty:
        st.info("No players meet the games minimum — try lowering it in the sidebar.")
        return

    ranked = (
        custom_rank(ref, w_per, w_ts, w_pts)
        .groupby("player", as_index=False)["score"]
        .mean()
        .sort_values("score", ascending=False)
        .head(25)
        .round(3)
    )

    st.subheader("Top Players by Your Score")
    st.caption("This list updates instantly when you change the weights.")
    st.dataframe(ranked, use_container_width=True)
    st.download_button(
        "⬇️ Download this ranking as CSV",
        ranked.to_csv(index=False).encode("utf-8"),
        file_name="nba_custom_ranking.csv",
        mime="text/csv",
    )


# ========================================================== ARCHETYPES ====
def render_archetypes(base: pd.DataFrame, min_games: int) -> None:
    st.subheader("Player Archetypes (10 Types)")
    muted('Archetypes are player "types" found by clustering similar stat profiles together.')
    st.write("")

    card_open()
    st.markdown(
        "**How to use this tab:** the map groups similar players close together, color shows the "
        "archetype, and the dropdown below lets you see who belongs to each type."
    )
    card_close()
    st.write("")

    st.info(
        "This dataset doesn't include 3-point tracking or advanced defensive metrics, "
        "so some archetype names are best-effort."
    )

    ref = base[base["games"] >= min_games].copy()
    if ref["player"].nunique() < arch_mod.N_ARCHETYPES:
        st.warning("Not enough players meet the games minimum to build 10 archetypes — try lowering it.")
        return

    x = arch_mod.build_archetypes(ref)

    card_open()
    m1, m2, m3 = st.columns(3)
    m1.metric("Players clustered", int(x.shape[0]))
    m2.metric("Archetypes", arch_mod.N_ARCHETYPES)
    m3.metric("Unique labels", int(x["role"].nunique()))
    card_close()
    st.write("")

    st.caption("Map tip: closer dots = more similar stat profiles. Hover a dot to see the player name.")
    st.altair_chart(charts.style_map(x), use_container_width=True)

    st.subheader("Archetype Profiles (Average Stats)")
    st.caption("Average stats per archetype, so you can compare types.")
    role_profile = (
        x.reset_index()
        .groupby("role")[FEATURES]
        .mean()
        .round(2)
        .sort_values("per", ascending=False)
        .rename(columns=PRETTY_NAMES)
    )
    st.dataframe(role_profile, use_container_width=True)

    st.subheader("Players in Each Archetype")
    role_pick = st.selectbox("Pick an archetype", sorted(x["role"].unique()), key="role_pick")
    players_df = x.reset_index()
    players_in_role = (
        players_df.loc[players_df["role"] == role_pick, ["player"] + FEATURES]
        .sort_values("per", ascending=False)
        .head(30)
        .round(2)
        .rename(columns=PRETTY_NAMES)
    )
    st.dataframe(players_in_role, use_container_width=True)


# ============================================================= INSIGHTS ====
def render_insights(df: pd.DataFrame) -> None:
    st.markdown("### Insights")
    muted("Simple patterns: which stats move together. A starting point for exploring the data.")
    st.write("")

    if df.empty:
        st.info("No players match the current filters.")
        return

    cols = FEATURES

    card_open()
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown("**🗺 Heatmap**")
        muted("Darker = stronger link.")
    with s2:
        st.markdown("**💡 Takeaways**")
        muted("Top relationships explained.")
    with s3:
        st.markdown("**🔎 Scatter**")
        muted("Pick two stats and see players.")
    card_close()
    st.write("")

    card_open()
    a, b, c, d = st.columns(4)
    a.metric("Players in view", int(df["player"].nunique()))
    b.metric("Avg PTS", f"{df['pts'].mean():.1f}")
    c.metric("Avg TS%", f"{df['ts_pct'].mean():.3f}")
    d.metric("Avg PER (demo)", f"{df['per'].mean():.2f}")
    card_close()
    st.write("")

    st.subheader("Correlation Heatmap")
    st.caption("Correlation ranges from -1 to +1. Near 0 means there isn't a clear pattern.")

    corr = df[cols].corr()
    corr_long = (
        corr.reset_index()
        .melt(id_vars="index", var_name="stat_y", value_name="corr")
        .rename(columns={"index": "stat_x"})
    )
    st.altair_chart(charts.correlation_heatmap(corr_long, cols), use_container_width=True)

    st.subheader("Key Takeaways")
    st.caption("The strongest relationships in the current view.")

    pairs = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            pairs.append((cols[i], cols[j], float(corr.loc[cols[i], cols[j]])))

    pairs_df = (
        pd.DataFrame(pairs, columns=["stat_a", "stat_b", "corr"])
        .assign(abs_corr=lambda d: d["corr"].abs())
        .sort_values("abs_corr", ascending=False)
        .head(6)
        .drop(columns="abs_corr")
    )

    def strength_label(v: float) -> str:
        av = abs(v)
        if av >= 0.70:
            return "Strong"
        if av >= 0.40:
            return "Moderate"
        return "Weak"

    takeaways = pairs_df.copy()
    takeaways["Relationship"] = takeaways.apply(
        lambda r: f"{PRETTY_NAMES[r['stat_a']]} ↔ {PRETTY_NAMES[r['stat_b']]}", axis=1
    )
    takeaways["Insight"] = takeaways.apply(
        lambda r: f"{strength_label(r['corr'])} link — these usually move together."
        if r["corr"] > 0
        else f"{strength_label(r['corr'])} link — one tends to rise as the other falls.",
        axis=1,
    )
    takeaways = takeaways[["Relationship", "corr", "Insight"]]
    st.dataframe(takeaways.style.format({"corr": "{:.2f}"}), use_container_width=True)

    st.subheader("Explore a Relationship")
    st.caption("Pick two stats. Each dot is a player-season row. Hover a dot to see who it is.")

    left, right = st.columns(2)
    with left:
        x_stat = st.selectbox("X-axis", cols, index=0, format_func=lambda x: PRETTY_NAMES[x])
    with right:
        y_stat = st.selectbox("Y-axis", cols, index=5, format_func=lambda x: PRETTY_NAMES[x])

    st.altair_chart(charts.scatter(df, x_stat, y_stat), use_container_width=True)

    card_open("teal")
    st.markdown(
        "**Simple interpretation:** positive correlation means players high in one stat are often "
        "high in the other; negative means one tends to fall as the other rises; near zero means no "
        "strong pattern. Correlation shows a pattern, not a reason."
    )
    card_close()
