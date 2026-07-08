"""User-weighted custom player ranking."""

from __future__ import annotations

import pandas as pd

CUSTOM_RANK_STATS = ["per", "ts_pct", "pts"]


def custom_rank(df: pd.DataFrame, w_per: float, w_ts: float, w_pts: float) -> pd.DataFrame:
    """Combine standardized stats into a single score, weighted by the user.

    Standardizing first (z-scores) means the weights control *importance*
    rather than being dominated by whichever stat happens to have the
    largest raw numbers.
    """
    z = (df[CUSTOM_RANK_STATS] - df[CUSTOM_RANK_STATS].mean()) / df[CUSTOM_RANK_STATS].std()
    score = z["per"] * w_per + z["ts_pct"] * w_ts + z["pts"] * w_pts

    out = df[["player", "team", "season"]].copy()
    out["score"] = score
    return out
