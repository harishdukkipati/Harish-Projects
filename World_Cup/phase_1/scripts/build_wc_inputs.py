#!/usr/bin/env python3
"""
Step 1–2: Build wc_participants.json and wc_winners.json from Kaggle martj CSVs.

Usage (from repo root or phase_1):
  python scripts/build_wc_inputs.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

PHASE1 = Path(__file__).resolve().parent.parent
DATA = PHASE1 / "data"
KAGGLE = DATA / "kaggle" / "martj_dataset"
INPUTS = DATA / "inputs"
WC_TOURNAMENT = "FIFA World Cup"


def _load_results() -> pd.DataFrame:
    path = KAGGLE / "results.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}")
    df = pd.read_csv(path)
    mask = df["tournament"].astype(str).eq(WC_TOURNAMENT)
    df = df.loc[mask].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.dropna(subset=["home_score", "away_score"])
    df["year"] = df["date"].dt.year.astype(int)
    # martj may list future 2026 fixtures without results; training uses 1930–2022
    df = df[df["year"] <= 2022]
    return df


def _load_shootouts() -> pd.DataFrame:
    path = KAGGLE / "shootouts.csv"
    if not path.is_file():
        return pd.DataFrame(columns=["date", "home_team", "away_team", "winner"])
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def build_participants(wc: pd.DataFrame) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for year, grp in wc.groupby("year", sort=True):
        teams = set(grp["home_team"].astype(str)) | set(grp["away_team"].astype(str))
        out[str(int(year))] = sorted(teams)
    return out


def _winner_from_final_row(row: pd.Series, shootouts: pd.DataFrame) -> str:
    home, away = str(row["home_team"]), str(row["away_team"])
    hs, aws = int(row["home_score"]), int(row["away_score"])
    if hs > aws:
        return home
    if aws > hs:
        return away
    day = row["date"]
    so = shootouts[
        (shootouts["date"] == day)
        & (
            ((shootouts["home_team"] == home) & (shootouts["away_team"] == away))
            | ((shootouts["home_team"] == away) & (shootouts["away_team"] == home))
        )
    ]
    if len(so):
        return str(so.iloc[0]["winner"])
    raise ValueError(f"No shootout row for drawn final on {day.date()}: {home} vs {away}")


def build_winners(wc: pd.DataFrame, shootouts: pd.DataFrame) -> dict[str, str]:
    out: dict[str, str] = {}
    for year, grp in wc.groupby("year", sort=True):
        final = grp.loc[grp["date"].idxmax()]
        out[str(int(year))] = _winner_from_final_row(final, shootouts)
    return out


def main() -> None:
    INPUTS.mkdir(parents=True, exist_ok=True)
    wc = _load_results()
    shootouts = _load_shootouts()

    participants = build_participants(wc)
    winners = build_winners(wc, shootouts)

    part_path = INPUTS / "wc_participants.json"
    win_path = INPUTS / "wc_winners.json"
    part_path.write_text(json.dumps(participants, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    win_path.write_text(json.dumps(winners, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Wrote {part_path}  ({len(participants)} tournaments)")
    print(f"Wrote {win_path}  ({len(winners)} champions)")
    print("Sample winners:", {k: winners[k] for k in sorted(winners, key=int)[-5:]})


if __name__ == "__main__":
    main()
