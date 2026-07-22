"""Build per-(team, year) feature rows for champion prediction."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from . import load_data as ld
from . import sofascore_load as sofascore

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"

FEATURE_COLS = [
    "pre_wc_elo",
    "fifa_rank_score",
    "last12mo_avg_opponent_elo",
    "last12mo_win_pct",
    "last12mo_goals_for_per_match",
    "last12mo_goals_against_per_match",
    "last12mo_goal_diff_per_match",
    "last12mo_matches_played",
    "days_since_last_match",
    "last12mo_avg_possession",
    "last12mo_pass_completion_pct",
    "last12mo_set_piece_success_rate",
    "last12mo_shots_on_target_pct",
    "is_host",
] + [f"conf_{c}" for c in ld.CONFEDERATIONS]

BINARY_FEATURE_COLS = ["is_host"]

CONTEXT_COLS = ["host_confederation_match"]

PEDIGREE_COLS = [
    "prior_wc_titles",
    "prior_wc_finals",
    "prior_wc_semifinals",
    "prior_wc_appearances",
    "is_defending_champion",
]

STRENGTH_FORM_COLS = [
    "pre_wc_elo",
    "pre_wc_fifa_rank",
    "fifa_rank_score",
    "last12mo_win_pct",
    "last12mo_avg_opponent_elo",
    "last12mo_goals_for_per_match",
    "last12mo_goals_against_per_match",
    "last12mo_goal_diff_per_match",
    "last12mo_matches_played",
    "days_since_last_match",
]

DEFAULT_ELO = 1500.0

ADVANCED_COLS = [
    "last12mo_avg_possession",
    "last12mo_pass_completion_pct",
    "last12mo_set_piece_success_rate",
    "last12mo_shots_on_target_pct",
]

CONF_COLS = [f"conf_{c}" for c in ld.CONFEDERATIONS]

DEFAULT_FIFA_SCORE_WEIGHT = 4.0
DEFAULT_FIFA_RANK_WEIGHT = DEFAULT_FIFA_SCORE_WEIGHT
DEFAULT_HOST_WEIGHT = 0.25
DEFAULT_ADVANCED_WEIGHT = 0.5


def fifa_rank_score(rank: float) -> float:
    """Higher is better: 1 / rank (rank 1 → 1.0, rank 10 → 0.1)."""
    if rank is None or rank != rank or rank <= 0:
        return float("nan")
    return 1.0 / float(rank)


def feature_weight_vector(
    *,
    fifa_score_weight: float = DEFAULT_FIFA_SCORE_WEIGHT,
    fifa_rank_weight: Optional[float] = None,
    host_weight: float = DEFAULT_HOST_WEIGHT,
    advanced_weight: float = DEFAULT_ADVANCED_WEIGHT,
) -> np.ndarray:
    """Per-column multipliers aligned with FEATURE_COLS."""
    if fifa_rank_weight is not None:
        fifa_score_weight = fifa_rank_weight
    w = np.ones(len(FEATURE_COLS), dtype=float)
    if fifa_score_weight != 1.0 and "fifa_rank_score" in FEATURE_COLS:
        w[FEATURE_COLS.index("fifa_rank_score")] = float(fifa_score_weight)
    if host_weight != 1.0 and "is_host" in FEATURE_COLS:
        w[FEATURE_COLS.index("is_host")] = float(host_weight)
    if advanced_weight != 1.0:
        for col in ADVANCED_COLS:
            if col in FEATURE_COLS:
                w[FEATURE_COLS.index(col)] = float(advanced_weight)
    return w


def _pre_wc_elo(team: str, cutoff: pd.Timestamp, elo: pd.DataFrame) -> float:
    sub = elo[(elo["team"] == team) & (elo["date"] < cutoff)]
    if sub.empty:
        return np.nan
    return float(sub.iloc[-1]["rating"])


def _pre_wc_fifa_rank(
    team: str, cutoff: pd.Timestamp, fifa: pd.DataFrame, fifa_map: Dict[str, str]
) -> float:
    inv = {v: k for k, v in fifa_map.items()}
    fifa_name = inv.get(team)
    if fifa_name is None:
        sub = fifa[fifa["country_full"].astype(str).map(fifa_map) == team]
    else:
        sub = fifa[fifa["country_full"] == fifa_name]
    sub = sub[sub["rank_date"] < cutoff]
    if sub.empty:
        return np.nan
    row = sub.sort_values("rank_date").iloc[-1]
    return float(row["rank"])


def _team_confederation(
    team: str, cutoff: pd.Timestamp, fifa: pd.DataFrame, fifa_map: Dict[str, str]
) -> Optional[str]:
    inv = {v: k for k, v in fifa_map.items()}
    fifa_name = inv.get(team)
    if fifa_name is None:
        sub = fifa[fifa["country_full"].astype(str).map(fifa_map) == team]
    else:
        sub = fifa[fifa["country_full"] == fifa_name]
    sub = sub[sub["rank_date"] < cutoff]
    if sub.empty:
        return None
    conf = str(sub.sort_values("rank_date").iloc[-1]["confederation"])
    return conf if conf in ld.CONFEDERATIONS else None


@lru_cache(maxsize=1)
def _elo_lookup_index() -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """Canonical team -> (sorted dates, ratings) for as-of lookups."""
    aliases = ld.load_aliases()
    elo = ld.load_elo().copy()
    elo["team"] = elo["team"].astype(str).map(lambda x: ld.normalize_team(x, aliases))
    out: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}
    for team, grp in elo.groupby("team", sort=False):
        g = grp.sort_values("date")
        out[str(team)] = (
            g["date"].to_numpy(dtype="datetime64[ns]"),
            g["rating"].to_numpy(dtype=float),
        )
    return out


def _elo_at(lookup: Dict[str, Tuple[np.ndarray, np.ndarray]], team: str, when: pd.Timestamp) -> float:
    entry = lookup.get(team)
    if entry is None:
        return DEFAULT_ELO
    dates, ratings = entry
    idx = int(np.searchsorted(dates, when.to_datetime64(), side="right") - 1)
    if idx < 0:
        return DEFAULT_ELO
    return float(ratings[idx])


def _empty_form() -> Dict[str, float]:
    return {
        "last12mo_win_pct": np.nan,
        "last12mo_avg_opponent_elo": np.nan,
        "last12mo_goals_for_per_match": np.nan,
        "last12mo_goals_against_per_match": np.nan,
        "last12mo_goal_diff_per_match": np.nan,
        "last12mo_matches_played": 0.0,
        "days_since_last_match": np.nan,
    }


def _last12mo_form(
    team: str,
    cutoff: pd.Timestamp,
    results: pd.DataFrame,
    *,
    elo_lookup: Optional[Dict[str, Tuple[np.ndarray, np.ndarray]]] = None,
) -> Dict[str, float]:
    start = cutoff - pd.DateOffset(months=12)
    games = results[
        (results["date"] >= start)
        & (results["date"] < cutoff)
        & ((results["home_team"] == team) | (results["away_team"] == team))
    ]
    if games.empty:
        return _empty_form()

    lookup = elo_lookup if elo_lookup is not None else _elo_lookup_index()
    gf, ga, wins = [], [], []
    opp_elos: List[float] = []

    for _, g in games.iterrows():
        home = g["home_team"] == team
        opp = str(g["away_team"] if home else g["home_team"])
        goals_for = int(g["home_score"] if home else g["away_score"])
        goals_against = int(g["away_score"] if home else g["home_score"])
        won = int(
            (home and g["home_score"] > g["away_score"])
            or (not home and g["away_score"] > g["home_score"])
        )

        gf.append(goals_for)
        ga.append(goals_against)
        wins.append(won)
        opp_elos.append(_elo_at(lookup, opp, pd.Timestamp(g["date"])))

    n = len(gf)
    last_date = games["date"].max()
    days = (cutoff - last_date).days
    return {
        "last12mo_win_pct": sum(wins) / n,
        "last12mo_avg_opponent_elo": float(np.mean(opp_elos)),
        "last12mo_goals_for_per_match": sum(gf) / n,
        "last12mo_goals_against_per_match": sum(ga) / n,
        "last12mo_goal_diff_per_match": (sum(gf) - sum(ga)) / n,
        "last12mo_matches_played": float(n),
        "days_since_last_match": float(days),
    }


def _pedigree(
    team: str, year: int, winners: Dict[int, str], runners: Dict[int, str], participants: Dict[int, List[str]]
) -> Dict[str, float]:
    titles = sum(1 for y, w in winners.items() if y < year and w == team)
    finals = sum(
        1
        for y in winners
        if y < year and (winners[y] == team or runners.get(y) == team)
    )
    apps = sum(1 for y, teams in participants.items() if y < year and team in teams)
    prev_champ = winners.get(year - 1)
    return {
        "prior_wc_titles": float(titles),
        "prior_wc_finals": float(finals),
        "prior_wc_semifinals": float(finals),
        "prior_wc_appearances": float(apps),
        "is_defending_champion": 1.0 if prev_champ == team else 0.0,
    }


def _host_flags(
    team: str, year: int, conf: Optional[str]
) -> Dict[str, float]:
    aliases = ld.load_aliases()
    hosts = [
        ld.normalize_team(h, aliases) for h in ld.WC_HOSTS.get(year, [])
    ]
    is_host = 1.0 if team in hosts else 0.0
    host_confs: List[Optional[str]] = []
    fifa = ld.load_fifa_rankings()
    fifa_map = ld.fifa_name_map()
    wc_starts = ld.load_wc_start_dates()
    cutoff = wc_starts.get(year, pd.Timestamp(f"{year}-06-01"))
    for h in hosts:
        host_confs.append(_team_confederation(h, cutoff, fifa, fifa_map))
    host_conf_match = 0.0
    if conf and host_confs:
        host_conf_match = 1.0 if conf in {c for c in host_confs if c} else 0.0
    return {"is_host": is_host, "host_confederation_match": host_conf_match}


def _conf_one_hot(conf: Optional[str]) -> Dict[str, float]:
    return {f"conf_{c}": 1.0 if conf == c else 0.0 for c in ld.CONFEDERATIONS}


def _lookup_advanced_features(team: str, year: int) -> Dict[str, float]:
    """
    Advanced stats from SofaScore (WC finals by year, WC Qual for 2026+).
    Missing values stay NaN until _impute_features applies a penalty fill.
    """
    return sofascore.lookup_advanced_features(team, year)


def build_row(
    team: str,
    year: int,
    *,
    label: Optional[int] = None,
    fifa_rank_override: Optional[float] = None,
) -> Dict[str, object]:
    aliases = ld.load_aliases()
    team = ld.normalize_team(team, aliases)
    winners = ld.load_wc_winners()
    runners = ld.load_wc_runner_ups()
    participants = ld.load_wc_participants()
    wc_starts = ld.load_wc_start_dates()
    cutoff = wc_starts.get(year, pd.Timestamp(f"{year}-06-01"))
    if year == 2026:
        cutoff = pd.Timestamp("2026-06-11")

    elo = ld.load_elo().copy()
    elo["team"] = elo["team"].astype(str).map(lambda x: ld.normalize_team(x, aliases))
    fifa = ld.load_fifa_rankings()
    fifa_map = ld.fifa_name_map()
    results = ld.load_all_results()
    results = results[results["date"] < cutoff].copy()
    for c in ("home_team", "away_team"):
        results[c] = results[c].astype(str).map(lambda x: ld.normalize_team(x, aliases))

    conf = _team_confederation(team, cutoff, fifa, fifa_map)
    fifa_rank = (
        fifa_rank_override
        if fifa_rank_override is not None
        else _pre_wc_fifa_rank(team, cutoff, fifa, fifa_map)
    )
    row: Dict[str, object] = {
        "team": team,
        "year": year,
        "pre_wc_elo": _pre_wc_elo(team, cutoff, elo),
        "pre_wc_fifa_rank": fifa_rank,
        "fifa_rank_score": fifa_rank_score(fifa_rank),
    }
    row.update(_last12mo_form(team, cutoff, results, elo_lookup=_elo_lookup_index()))
    row.update(_pedigree(team, year, winners, runners, participants))
    row.update(_lookup_advanced_features(team, year))
    row.update(_host_flags(team, year, conf))
    row.update(_conf_one_hot(conf))
    if label is not None:
        row["label"] = label
    return row


def build_training_frame() -> pd.DataFrame:
    winners = ld.load_wc_winners()
    participants = ld.load_wc_participants()
    rows: List[Dict[str, object]] = []
    for year, teams in sorted(participants.items()):
        champ = winners.get(year)
        for team in teams:
            team = ld.normalize_team(team)
            rows.append(
                build_row(team, year, label=1 if team == champ else 0)
            )
    df = pd.DataFrame(rows)
    return _impute_features(df)


def build_2026_frame() -> pd.DataFrame:
    return build_year_features_export(2026, model_only=True)


def _rows_for_year(year: int) -> List[Dict[str, object]]:
    if year == 2026:
        rows: List[Dict[str, object]] = []
        for team, fifa_rank in ld.load_teams_2026():
            rank_val = float(fifa_rank) if fifa_rank is not None else np.nan
            rows.append(build_row(team, year, fifa_rank_override=rank_val))
        return rows

    winners = ld.load_wc_winners()
    participants = ld.load_wc_participants()
    teams = participants.get(year, [])
    if not teams:
        raise ValueError(f"No WC participants for year {year}")
    champ = winners.get(year)
    rows = []
    for team in teams:
        team = ld.normalize_team(team)
        label = 1 if champ and team == champ else 0
        rows.append(build_row(team, year, label=label))
    return rows


def build_year_features_export(year: int, *, model_only: bool = False) -> pd.DataFrame:
    """
    Per-team feature table for inspection (2026, 2018, 2022, etc.).

    model_only=False: raw SofaScore advanced stats, imputed model values, source
    flags, strength/form, confederation, pedigree (and label for historical WCs).
    model_only=True: same columns as the classifier (FEATURE_COLS + team/year).
    """
    raw = pd.DataFrame(_rows_for_year(year))

    if model_only:
        out = raw.copy()
        for c in FEATURE_COLS:
            if c not in out.columns:
                out[c] = np.nan
        return _impute_features(out)[["team", "year"] + FEATURE_COLS]

    for c in ADVANCED_COLS:
        raw[f"raw_{c}"] = raw[c]
    raw["has_sofascore_advanced"] = raw["advanced_stats_source"].notna()

    model_df = _impute_features(raw.copy())
    for c in ADVANCED_COLS:
        raw[c] = model_df[c]
        raw[f"advanced_imputed_{c}"] = raw[f"raw_{c}"].isna()

    raw["advanced_any_imputed"] = raw[[f"advanced_imputed_{c}" for c in ADVANCED_COLS]].any(axis=1)

    front = [
        "team",
        "year",
        "advanced_stats_source",
        "has_sofascore_advanced",
        "advanced_any_imputed",
    ]
    raw_block = [f"raw_{c}" for c in ADVANCED_COLS]
    model_block = ADVANCED_COLS + [f"advanced_imputed_{c}" for c in ADVANCED_COLS]
    strength = [c for c in STRENGTH_FORM_COLS if c in raw.columns]
    conf = [c for c in CONF_COLS if c in raw.columns]
    context = [c for c in CONTEXT_COLS if c in raw.columns]
    pedigree = [c for c in PEDIGREE_COLS if c in raw.columns]
    model_feature_order = [c for c in FEATURE_COLS if c in raw.columns]

    cols = front + raw_block + model_block + strength + conf + context + pedigree + [
        c
        for c in model_feature_order
        if c not in front + raw_block + model_block + strength + conf + context + pedigree
    ]
    cols = [c for c in cols if c in raw.columns]
    if "label" in raw.columns:
        cols = cols + ["label"]
    cols = list(dict.fromkeys(c for c in cols if c in raw.columns))
    out = raw[cols].sort_values(["pre_wc_fifa_rank", "team"], na_position="last")
    return out.reset_index(drop=True)


def build_2026_features_export(*, model_only: bool = False) -> pd.DataFrame:
    return build_year_features_export(2026, model_only=model_only)


def _penalize_missing_advanced(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """
    Fill missing SofaScore advanced stats with a value below the observed minimum
    (per column, within this frame). Sklearn RF needs finite inputs; this penalizes
    missing data instead of imputing the year mean.
    """
    out = df.copy()
    for col in cols:
        if col not in out.columns:
            continue
        s = pd.to_numeric(out[col], errors="coerce")
        if s.notna().any():
            fill = float(s.min()) - 1.0
        else:
            fill = 0.0
        out[col] = s.fillna(fill)
    return out


def _impute_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in FEATURE_COLS:
        if c not in out.columns:
            out[c] = np.nan
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out = _penalize_missing_advanced(out, ADVANCED_COLS)
    for c in PEDIGREE_COLS:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0.0)
    for c in BINARY_FEATURE_COLS:
        if c in FEATURE_COLS:
            out[c] = out[c].fillna(0.0)
    for c in FEATURE_COLS:
        if c not in ADVANCED_COLS and c not in BINARY_FEATURE_COLS:
            out[c] = out[c].fillna(out[c].median())
    return out


def save_training_frame(path: Optional[Path] = None) -> Path:
    path = path or PROCESSED / "team_year_features.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    build_training_frame().to_csv(path, index=False)
    return path


def save_year_features(year: int, path: Optional[Path] = None) -> Path:
    path = path or PROCESSED / f"team_{year}_features.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    build_year_features_export(year, model_only=False).to_csv(path, index=False)
    return path


def save_model_year_features(year: int, path: Optional[Path] = None) -> Path:
    """team + FEATURE_COLS only — what train_and_predict.py actually uses."""
    path = path or PROCESSED / f"team_{year}_model_features.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    build_year_features_export(year, model_only=True).to_csv(path, index=False)
    return path


def save_2026_features(path: Optional[Path] = None) -> Path:
    return save_year_features(2026, path=path)


def save_2026_model_features(path: Optional[Path] = None) -> Path:
    return save_model_year_features(2026, path=path)
