from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd


@dataclass
class MatchupFeaturesConfig:
    """
    Configuration for building matchup-level features.
    """

    rating_cols: List[str] = None

    def __post_init__(self) -> None:
        if self.rating_cols is None:
            # Columns that often exist in the resumes file and behave like strength ratings.
            self.rating_cols = ["RESUME", "ELO", "B POWER", "R SCORE"]


def build_matchup_frame(
    matchups: pd.DataFrame, resumes: pd.DataFrame, config: MatchupFeaturesConfig | None = None
) -> pd.DataFrame:
    """
    Convert raw tournament matchups + team resumes into one-row-per-game
    features suitable for classification models.

    Parameters
    ----------
    matchups:
        DataFrame like `Tournament Matchups.csv` filtered to a specific year
        and round, one row per team with columns including:
        - YEAR
        - TEAM NO
        - TEAM
        - SEED
        - BY YEAR NO
        - CURRENT ROUND

    resumes:
        DataFrame like `Resumes.csv` with at least:
        - YEAR
        - TEAM NO
        - TEAM
        - SEED
        - RESUME, ELO, B POWER, R SCORE (or a subset of these).

    Returns
    -------
    DataFrame where each row represents a single game, with columns:
        - year
        - team_a, seed_a, team_b, seed_b
        - various feature columns such as seed_diff, rating diffs, etc.
    """
    if config is None:
        config = MatchupFeaturesConfig()

    # Standardize column names for safer joins
    m = matchups.rename(
        columns={
            "YEAR": "year",
            "TEAM NO": "team_no",
            "TEAM": "team",
            "SEED": "seed",
            "BY YEAR NO": "by_year_no",
        }
    ).copy()

    r = resumes.rename(
        columns={
            "YEAR": "year",
            "TEAM NO": "team_no",
            "TEAM": "team",
            "SEED": "seed",
        }
    ).copy()

    # Attach resume / rating information to each team in the matchup table
    # using (year, team_no) which is stable across files.
    r_key_cols = ["year", "team_no"]
    m_key_cols = ["year", "team_no"]

    join_cols = r_key_cols.copy()
    augmented = m.merge(
        r[r_key_cols + config.rating_cols],
        how="left",
        left_on=m_key_cols,
        right_on=join_cols,
        suffixes=("", "_r"),
    )

    # Order so that adjacent rows form actual games (the CSV is structured this way)
    augmented = augmented.sort_values(["year", "by_year_no"], ascending=[True, False]).reset_index(drop=True)

    # Pair teams into games
    if len(augmented) % 2 != 0:
        raise ValueError(f"Expected an even number of rows when forming matchups, got {len(augmented)}")

    games = []
    for i in range(0, len(augmented), 2):
        a = augmented.iloc[i]
        b = augmented.iloc[i + 1]

        row = {
            "year": int(a["year"]),
            "game_index": i // 2 + 1,
            "team_a": a["team"],
            "seed_a": int(a["seed"]),
            "team_b": b["team"],
            "seed_b": int(b["seed"]),
        }

        # Seed-derived features
        row["seed_diff"] = row["seed_a"] - row["seed_b"]  # positive --> team_a is higher seed number (worse seed)
        row["seed_abs_diff"] = abs(row["seed_diff"])

        # Rating-derived features from the resumes file (diffs and sums)
        for col in config.rating_cols:
            if col not in augmented.columns:
                continue
            val_a = a[col]
            val_b = b[col]
            row[f"{col}_a"] = val_a
            row[f"{col}_b"] = val_b
            # Differences: team_a minus team_b
            row[f"{col}_diff"] = val_a - val_b

        games.append(row)

    return pd.DataFrame(games)

