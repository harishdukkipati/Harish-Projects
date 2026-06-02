from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "archive 2"


@dataclass
class TitleFeatureConfig:
    year: int = 2026
    # Relative weights for different signal groups (must sum to something > 0; we normalise later)
    w_current_rating: float = 0.35
    w_seed_profile: float = 0.15
    w_seed_upset_profile: float = 0.10
    w_program_history: float = 0.20
    w_preseason: float = 0.10
    w_conference: float = 0.10


def _z(series: pd.Series) -> pd.Series:
    """Standardise a numeric series; returns 0 if variance is 0."""
    s = pd.to_numeric(series, errors="coerce")
    m = float(s.mean())
    v = float(s.std())
    if not np.isfinite(v) or v == 0:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - m) / v


def load_teams_for_year(year: int) -> pd.DataFrame:
    """
    Base frame of all tournament teams for a given year from Resumes.csv.
    """
    resumes = pd.read_csv(DATA_DIR / "Resumes.csv")
    df = resumes[resumes["YEAR"] == year].copy()
    # Standardise key names
    df = df.rename(
        columns={
            "YEAR": "year",
            "TEAM NO": "team_no",
            "TEAM": "team",
            "SEED": "seed",
        }
    )
    return df


def build_title_feature_table(config: TitleFeatureConfig) -> pd.DataFrame:
    """
    Build a per-team feature table for a given year that combines:
    - current season efficiency / rating info
    - seed-level historical championship profile
    - program-level tournament history
    - preseason expectations
    - conference strength
    """
    year = config.year

    teams = load_teams_for_year(year)

    # --- Current rating: KenPom/Barttorvik style metrics per team ---
    kp_bart = pd.read_csv(DATA_DIR / "KenPom Barttorvik.csv")
    kp_bart = kp_bart.rename(
        columns={
            "YEAR": "year",
            "TEAM NO": "team_no",
            "TEAM": "team",
        }
    )
    kp_bart_y = kp_bart[kp_bart["year"] == year][
        ["year", "team_no", "CONF", "KADJ EM", "BARTHAG"]
    ].copy()

    # --- Seed profile: seed-level historical title probabilities ---
    seed_results = pd.read_csv(DATA_DIR / "Seed Results.csv")
    seed_results = seed_results.rename(columns={"SEED": "seed", "CHAMP%": "seed_champ_pct"})
    # Convert '80.70%' style strings to floats in [0,1]
    seed_results["seed_champ_pct"] = (
        seed_results["seed_champ_pct"]
        .astype(str)
        .str.rstrip("%")
        .astype(float)
        / 100.0
    )

    # --- Seed upset profile: how often each seed pulls upsets ---
    # Upset Seed Info has one row per upset: YEAR, CURRENT ROUND, SEED WON, SEED LOST, SEED DIFF
    upset_info = pd.read_csv(DATA_DIR / "Upset Seed Info.csv")
    upset_info = upset_info.rename(
        columns={"SEED WON": "seed_won", "SEED LOST": "seed_lost", "SEED DIFF": "seed_diff"}
    )
    # Focus mainly on first-round upsets as the most relevant for overall chaos
    upset_r1 = upset_info[upset_info["CURRENT ROUND"] == 64].copy()
    # Count how many first-round upsets each winning seed has historically
    upset_counts = (
        upset_r1.groupby("seed_won")
        .agg(upset_wins_64=("seed_won", "size"), avg_seed_diff=("seed_diff", "mean"))
        .reset_index()
        .rename(columns={"seed_won": "seed"})
    )

    # --- Program history: team-level results over all tournaments ---
    team_results = pd.read_csv(DATA_DIR / "Team Results.csv")
    team_results = team_results.rename(
        columns={
            "TEAM": "team",
            "WIN%": "program_win_pct",
            "F4%": "program_f4_pct",
            "CHAMP%": "program_champ_pct",
        }
    )
    # Normalise percentage strings
    for col in ["program_f4_pct", "program_champ_pct"]:
        if team_results[col].dtype == object:
            team_results[col] = (
                team_results[col].astype(str).str.rstrip("%").astype(float) / 100.0
            )

    # --- Preseason expectations ---
    kp_pre = pd.read_csv(DATA_DIR / "KenPom Preseason.csv")
    kp_pre = kp_pre.rename(
        columns={
            "YEAR": "year",
            "TEAM NO": "team_no",
            "TEAM": "team",
            "PRESEASON KADJ EM": "preseason_em",
        }
    )
    kp_pre_y = kp_pre[kp_pre["year"] == year][
        ["year", "team_no", "preseason_em"]
    ].copy()

    # --- Conference strength ---
    conf_stats = pd.read_csv(DATA_DIR / "Conference Stats.csv")
    conf_stats = conf_stats.rename(columns={"YEAR": "year"})
    conf_y = conf_stats[conf_stats["year"] == year][["year", "CONF", "BADJ EM"]].copy()
    conf_y = conf_y.rename(columns={"BADJ EM": "conf_em"})

    # Join everything to the teams frame
    df = teams.merge(
        kp_bart_y[["year", "team_no", "CONF", "KADJ EM", "BARTHAG"]],
        on=["year", "team_no"],
        how="left",
    )
    df = df.merge(
        seed_results[["seed", "seed_champ_pct"]],
        on="seed",
        how="left",
    )
    df = df.merge(
        upset_counts,
        on="seed",
        how="left",
    )
    df = df.merge(
        team_results[["team", "program_win_pct", "program_f4_pct", "program_champ_pct"]],
        on="team",
        how="left",
    )
    df = df.merge(
        kp_pre_y[["year", "team_no", "preseason_em"]],
        on=["year", "team_no"],
        how="left",
    )
    df = df.merge(
        conf_y,
        on=["year", "CONF"],
        how="left",
    )

    # Some teams may miss certain fields; fill with column means where reasonable
    for col in [
        "KADJ EM",
        "BARTHAG",
        "seed_champ_pct",
        "upset_wins_64",
        "avg_seed_diff",
        "program_win_pct",
        "program_f4_pct",
        "program_champ_pct",
        "preseason_em",
        "conf_em",
    ]:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce")
            df[col] = s.fillna(s.mean())

    # --- Build grouped signals ---
    # current season rating signal
    df["z_current"] = (
        0.7 * _z(df.get("KADJ EM", pd.Series(np.zeros(len(df)))))
        + 0.3 * _z(df.get("BARTHAG", pd.Series(np.zeros(len(df)))))
    )

    # seed profile signal (historical success of the seed)
    df["z_seed_profile"] = _z(df.get("seed_champ_pct", pd.Series(np.zeros(len(df)))))

    # seed upset signal (how much a seed tends to be on the winning side of upsets)
    # We treat "upset_wins_64" as a proxy for seeds that historically punch above their seed line.
    df["z_seed_upsets"] = (
        0.7 * _z(df.get("upset_wins_64", pd.Series(np.zeros(len(df)))))
        + 0.3 * _z(df.get("avg_seed_diff", pd.Series(np.zeros(len(df)))))
    )

    # program history signal
    df["z_program"] = (
        0.4 * _z(df.get("program_win_pct", pd.Series(np.zeros(len(df)))))
        + 0.3 * _z(df.get("program_f4_pct", pd.Series(np.zeros(len(df)))))
        + 0.3 * _z(df.get("program_champ_pct", pd.Series(np.zeros(len(df)))))
    )

    # preseason expectations
    df["z_preseason"] = _z(df.get("preseason_em", pd.Series(np.zeros(len(df)))))

    # conference strength
    df["z_conf"] = _z(df.get("conf_em", pd.Series(np.zeros(len(df)))))

    # Combine into a single title score
    w_total = (
        config.w_current_rating
        + config.w_seed_profile
        + config.w_seed_upset_profile
        + config.w_program_history
        + config.w_preseason
        + config.w_conference
    )
    df["title_score_raw"] = (
        config.w_current_rating * df["z_current"]
        + config.w_seed_profile * df["z_seed_profile"]
        + config.w_seed_upset_profile * df["z_seed_upsets"]
        + config.w_program_history * df["z_program"]
        + config.w_preseason * df["z_preseason"]
        + config.w_conference * df["z_conf"]
    ) / w_total

    return df


def compute_title_probabilities(config: TitleFeatureConfig) -> pd.DataFrame:
    """
    Convert title scores into probabilities for winning the championship
    in the given year using a softmax over all tournament teams.
    """
    df = build_title_feature_table(config)

    # Softmax with temperature to avoid absurdly spiky distributions.
    temperature = 1.2
    scores = df["title_score_raw"].to_numpy(dtype=float) / temperature
    # For numerical stability
    scores = scores - np.max(scores)
    exp_scores = np.exp(scores)
    probs = exp_scores / exp_scores.sum()

    df["title_prob"] = probs
    return df


def main() -> None:
    config = TitleFeatureConfig()
    df = compute_title_probabilities(config)

    out_cols: List[str] = [
        "team",
        "seed",
        "title_prob",
        "KADJ EM",
        "BARTHAG",
        "program_champ_pct",
        "seed_champ_pct",
        "preseason_em",
        "conf_em",
    ]
    # Keep only available columns
    out_cols = [c for c in out_cols if c in df.columns]

    df_sorted = df.sort_values("title_prob", ascending=False).reset_index(drop=True)
    pd.set_option("display.max_rows", None)
    pd.set_option("display.width", 160)
    print(df_sorted[out_cols])


if __name__ == "__main__":
    main()

