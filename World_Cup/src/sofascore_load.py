"""Load SofaScore advanced stats for model features (WC finals + WC Qual)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

from . import load_data as ld

ROOT = Path(__file__).resolve().parent.parent
SOFASCORE_DIR = ROOT / "data" / "sofascore"
QUAL_CSV = SOFASCORE_DIR / "team_wc_qual_stats.csv"
HISTORICAL_DIR = SOFASCORE_DIR / "historical"

def _num(row: pd.Series, key: str) -> float:
    if key not in row.index:
        return float("nan")
    return float(pd.to_numeric(row[key], errors="coerce"))


def _stats_from_csv_row(row: pd.Series, aliases: Dict[str, str]) -> Dict[str, float]:
    team = ld.normalize_team(str(row["team"]), aliases)
    return {
        "team": team,
        "avg_possession": _num(row, "avg_possession"),
        "pass_completion_pct": _num(row, "pass_completion_pct"),
        "shots_on_target_pct": _num(row, "shots_on_target_pct"),
        "set_piece_success_rate": _num(row, "set_piece_success_rate"),
    }


@lru_cache(maxsize=1)
def _load_qual_stats_by_team() -> Dict[str, Dict[str, float]]:
    if not QUAL_CSV.is_file():
        return {}
    df = pd.read_csv(QUAL_CSV)
    if df.empty or "team" not in df.columns:
        return {}
    aliases = ld.load_aliases()
    out: Dict[str, Dict[str, float]] = {}
    for _, row in df.iterrows():
        stats = _stats_from_csv_row(row, aliases)
        out[stats["team"]] = stats
    return out


@lru_cache(maxsize=1)
def _load_historical_wc_by_year() -> Dict[int, Dict[str, Dict[str, float]]]:
    """year -> {canonical_team -> stat dict} from team_wc_stats_{year}.csv."""
    if not HISTORICAL_DIR.is_dir():
        return {}
    aliases = ld.load_aliases()
    by_year: Dict[int, Dict[str, Dict[str, float]]] = {}
    for path in sorted(HISTORICAL_DIR.glob("team_wc_stats_*.csv")):
        suffix = path.stem.replace("team_wc_stats_", "")
        if not suffix.isdigit():
            continue
        year = int(suffix)
        df = pd.read_csv(path)
        if df.empty or "team" not in df.columns:
            continue
        teams: Dict[str, Dict[str, float]] = {}
        for _, row in df.iterrows():
            stats = _stats_from_csv_row(row, aliases)
            teams[stats["team"]] = stats
        by_year[year] = teams
    return by_year


def available_historical_years() -> Tuple[int, ...]:
    return tuple(sorted(_load_historical_wc_by_year().keys()))


def sofascore_data_available() -> bool:
    return QUAL_CSV.is_file() or bool(_load_historical_wc_by_year())


def lookup_advanced_features(team: str, year: int) -> Dict[str, float]:
    """
    Advanced style stats from SofaScore.

    - year >= 2026: WC Qual aggregates (team_wc_qual_stats.csv)
    - year < 2026: FIFA World Cup finals for that year (historical/team_wc_stats_{year}.csv)
    Missing values are left as NaN; features._impute_features fills them with a
    below-minimum penalty instead of the year mean.
    """
    team = ld.normalize_team(team)
    stats: Optional[Dict[str, float]] = None
    source = float("nan")

    if year >= 2026:
        stats = _load_qual_stats_by_team().get(team)
        if stats is not None:
            source = 2026.0
    else:
        stats = _load_historical_wc_by_year().get(year, {}).get(team)
        if stats is not None:
            source = float(year)

    if stats is None:
        return {
            "last12mo_avg_possession": float("nan"),
            "last12mo_pass_completion_pct": float("nan"),
            "last12mo_set_piece_success_rate": float("nan"),
            "last12mo_shots_on_target_pct": float("nan"),
            "advanced_stats_source": float("nan"),
        }

    return {
        "last12mo_avg_possession": stats["avg_possession"],
        "last12mo_pass_completion_pct": stats["pass_completion_pct"],
        "last12mo_set_piece_success_rate": stats["set_piece_success_rate"],
        "last12mo_shots_on_target_pct": stats["shots_on_target_pct"],
        "advanced_stats_source": source,
    }


def sofascore_csv_available() -> bool:
    return QUAL_CSV.is_file()


def lookup_sofascore_features(team: str) -> Dict[str, float]:
    return lookup_advanced_features(team, 2026)


def has_sofascore_advanced_stats(team: str) -> bool:
    row = _load_qual_stats_by_team().get(ld.normalize_team(team))
    if not row:
        return False
    poss = row.get("avg_possession", float("nan"))
    return poss == poss
