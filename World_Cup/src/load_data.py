"""Load Kaggle CSVs, inputs JSON, and shared lookups."""
from __future__ import annotations

import html
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
KAGGLE = DATA / "kaggle" / "martj_dataset"
INPUTS = DATA / "inputs"
WC_TOURNAMENT = "FIFA World Cup"

WC_HOSTS: Dict[int, List[str]] = {
    1930: ["Uruguay"],
    1934: ["Italy"],
    1938: ["France"],
    1950: ["Brazil"],
    1954: ["Switzerland"],
    1958: ["Sweden"],
    1962: ["Chile"],
    1966: ["England"],
    1970: ["Mexico"],
    1974: ["Germany"],
    1978: ["Argentina"],
    1982: ["Spain"],
    1986: ["Mexico"],
    1990: ["Italy"],
    1994: ["United States"],
    1998: ["France"],
    2002: ["South Korea", "Japan"],
    2006: ["Germany"],
    2010: ["South Africa"],
    2014: ["Brazil"],
    2018: ["Russia"],
    2022: ["Qatar"],
    2026: ["United States", "Canada", "Mexico"],
}

CONFEDERATIONS = ("UEFA", "CONMEBOL", "CONCACAF", "CAF", "AFC", "OFC")


@lru_cache(maxsize=1)
def load_aliases() -> Dict[str, str]:
    path = INPUTS / "team_aliases.json"
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_team(name: str, aliases: Optional[Dict[str, str]] = None) -> str:
    aliases = aliases or load_aliases()
    name = html.unescape(str(name).strip())
    return aliases.get(name, name)


@lru_cache(maxsize=1)
def load_wc_participants() -> Dict[int, List[str]]:
    raw = json.loads((INPUTS / "wc_participants.json").read_text(encoding="utf-8"))
    return {int(y): list(teams) for y, teams in raw.items()}


@lru_cache(maxsize=1)
def load_wc_winners() -> Dict[int, str]:
    raw = json.loads((INPUTS / "wc_winners.json").read_text(encoding="utf-8"))
    return {int(y): str(w) for y, w in raw.items()}


@lru_cache(maxsize=1)
def load_wc_runner_ups() -> Dict[int, str]:
    """Runner-up = loser of the last WC match that year."""
    wc = load_wc_results()
    shootouts = load_shootouts()
    out: Dict[int, str] = {}
    for year, grp in wc.groupby("year"):
        final = grp.loc[grp["date"].idxmax()]
        h, a = str(final["home_team"]), str(final["away_team"])
        hs, aws = int(final["home_score"]), int(final["away_score"])
        if hs > aws:
            out[int(year)] = a
        elif aws > hs:
            out[int(year)] = h
        else:
            day = final["date"]
            so = shootouts[
                (shootouts["date"] == day)
                & (
                    ((shootouts["home_team"] == h) & (shootouts["away_team"] == a))
                    | ((shootouts["home_team"] == a) & (shootouts["away_team"] == h))
                )
            ]
            if len(so):
                winner = str(so.iloc[0]["winner"])
                out[int(year)] = a if winner == h else h
    return out


@lru_cache(maxsize=1)
def load_wc_start_dates() -> Dict[int, pd.Timestamp]:
    wc = load_wc_results()
    return {int(y): grp["date"].min() for y, grp in wc.groupby("year")}


@lru_cache(maxsize=1)
def load_all_results() -> pd.DataFrame:
    df = pd.read_csv(KAGGLE / "results.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "home_score", "away_score"])
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)
    if "neutral" in df.columns:
        df["neutral"] = df["neutral"].astype(str).str.upper().eq("TRUE")
    else:
        df["neutral"] = False
    return df


@lru_cache(maxsize=1)
def load_wc_results() -> pd.DataFrame:
    df = load_all_results()
    df = df[df["tournament"].astype(str).eq(WC_TOURNAMENT)].copy()
    df = df[df["date"].dt.year <= 2022]
    df["year"] = df["date"].dt.year.astype(int)
    return df


@lru_cache(maxsize=1)
def load_shootouts() -> pd.DataFrame:
    path = KAGGLE / "shootouts.csv"
    if not path.is_file():
        return pd.DataFrame(columns=["date", "home_team", "away_team", "winner"])
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


@lru_cache(maxsize=1)
def load_elo() -> pd.DataFrame:
    df = pd.read_csv(DATA / "kaggle" / "elo" / "eloratings.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed")
    df = df.dropna(subset=["date"])
    return df


@lru_cache(maxsize=1)
def load_fifa_rankings() -> pd.DataFrame:
    rank_dir = DATA / "kaggle" / "Rankings"
    files = sorted(rank_dir.glob("fifa_ranking-*.csv"))
    if not files:
        raise FileNotFoundError(f"No FIFA ranking CSVs in {rank_dir}")
    path = max(files, key=lambda p: p.stat().st_size)
    df = pd.read_csv(path)
    df["rank_date"] = pd.to_datetime(df["rank_date"], errors="coerce")
    df = df.dropna(subset=["rank_date"])
    return df


@lru_cache(maxsize=1)
def load_teams_2026() -> List[Tuple[str, Optional[int]]]:
    raw = json.loads((INPUTS / "teams_2026.json").read_text(encoding="utf-8"))
    return [(str(t["team"]), t.get("fifa_rank")) for t in raw.get("teams", [])]


def fifa_name_map() -> Dict[str, str]:
    """Map FIFA country_full -> martj-style via aliases."""
    aliases = load_aliases()
    df = load_fifa_rankings()
    m: Dict[str, str] = {}
    for name in df["country_full"].astype(str).unique():
        m[name] = normalize_team(name, aliases)
    return m
