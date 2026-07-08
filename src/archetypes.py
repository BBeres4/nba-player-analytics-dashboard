"""Clusters players into 10 labeled "archetypes" based on their stat profile.

This is the same rule-based labeling approach as the original app (each
cluster is matched to the archetype whose scoring rule it maximizes), just
pulled into its own module and cached so it isn't recomputed on every
sidebar interaction.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from src.config import FEATURES

N_ARCHETYPES = 10

# (role name, scoring rule) — each rule picks out the remaining cluster
# that best matches that archetype's defining stat pattern. Order matters:
# more distinctive archetypes are claimed first so common ones don't
# accidentally "steal" a cluster that fits a rarer archetype better.
_ROLE_RULES = [
    ("Primary Creator", lambda p: p["usage_rate"] + p["pts"] + p["ast"]),
    ("Playmaker", lambda p: p["ast"] + 0.25 * p["usage_rate"]),
    ("Shot Creator", lambda p: p["pts"] + 0.25 * p["usage_rate"]),
    ("Off-Ball Scorer", lambda p: p["pts"] + p["ts_pct"] - 0.6 * p["usage_rate"]),
    ("Efficient Finisher", lambda p: 1.5 * p["ts_pct"] - 0.5 * p["usage_rate"] + 0.2 * p["pts"]),
    ("Rebounder / Hustle Big", lambda p: 1.5 * p["reb"] + 0.2 * p["per"] - 0.2 * p["pts"]),
    ("Defensive Anchor", lambda p: 1.2 * p["per"] - 0.6 * p["pts"] - 0.4 * p["usage_rate"]),
    ("3&D Wing", lambda p: -0.8 * p["usage_rate"] + 0.8 * p["ts_pct"] + 0.6 * p["per"]),
    ("Two-Way Wing", lambda p: 0.6 * p["pts"] + 0.6 * p["reb"] + 0.6 * p["ast"] + 0.6 * p["per"]),
    # The last remaining cluster always becomes "Energy / Bench Role".
]


def _pick_best_cluster(cluster_z: pd.DataFrame, remaining: set[int], score_fn) -> int:
    best_cluster, best_score = None, None
    for cluster_id in remaining:
        score = score_fn(cluster_z.loc[cluster_id])
        if best_score is None or score > best_score:
            best_score, best_cluster = score, cluster_id
    remaining.remove(best_cluster)
    return best_cluster


@st.cache_data(show_spinner="Clustering players into archetypes…")
def build_archetypes(ref: pd.DataFrame) -> pd.DataFrame:
    """Cluster player-season averages into 10 labeled archetypes.

    Returns a dataframe indexed by player with their feature averages,
    assigned cluster/role, and a 2D PCA "style map" position.
    """
    x = ref.groupby("player")[FEATURES].mean()

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)

    kmeans = KMeans(n_clusters=N_ARCHETYPES, random_state=42, n_init=10)
    x["cluster"] = kmeans.fit_predict(x_scaled).astype(int)

    z = pd.DataFrame(scaler.transform(x[FEATURES]), index=x.index, columns=FEATURES)
    cluster_z = z.join(x["cluster"]).groupby("cluster")[FEATURES].mean()

    remaining = set(cluster_z.index.tolist())
    cluster_to_role: dict[int, str] = {}

    for role, score_fn in _ROLE_RULES:
        cluster_id = _pick_best_cluster(cluster_z, remaining, score_fn)
        cluster_to_role[cluster_id] = role

    last_cluster = remaining.pop()
    cluster_to_role[last_cluster] = "Energy / Bench Role"

    x["role"] = x["cluster"].map(cluster_to_role)

    style_map_2d = PCA(n_components=2, random_state=42).fit_transform(x_scaled)
    x["pca1"], x["pca2"] = style_map_2d[:, 0], style_map_2d[:, 1]

    return x
