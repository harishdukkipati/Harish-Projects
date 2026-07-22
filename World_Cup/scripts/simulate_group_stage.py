#!/usr/bin/env python3
"""
Monte Carlo simulation of 2026 WC group stage (round-robin within each group).

Uses the same FEATURE_COLS and feature weights as the champion Random Forest
(via a logistic matchup model trained on historical international results).

Each group: 4 teams play 6 matches (every pair once). Group winner = most points,
then GD, GF, head-to-head among tied teams.

Usage (from World_Cup):
  python scripts/simulate_group_stage.py
  python scripts/simulate_group_stage.py --sims 100000 --seed 42
"""
from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import load_data as ld
from src.features import (
    DEFAULT_ADVANCED_WEIGHT,
    DEFAULT_FIFA_SCORE_WEIGHT,
    DEFAULT_HOST_WEIGHT,
    build_2026_frame,
)
from src.matchup import MatchupModel, team_feature_matrix

GROUPS_JSON = ROOT / "data" / "inputs" / "wc_2026_groups.json"
OUT_MD = ROOT / "docs" / "GROUP_STAGE_SIMULATION.md"
OUT_JSON = ROOT / "data" / "processed" / "group_stage_sim_results.json"

DEFAULT_SIMS = 50_000


def _normalize(name: str) -> str:
    aliases = ld.load_aliases()
    return ld.normalize_team(name, aliases)


def _load_groups(path: Path) -> Dict[str, List[str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    groups = raw["groups"]
    return {g: [_normalize(t) for t in teams] for g, teams in groups.items()}


def _record_result(
    standings: Dict[str, Dict[str, int]],
    team: str,
    gf: int,
    ga: int,
) -> None:
    s = standings[team]
    s["gf"] += gf
    s["ga"] += ga
    if gf > ga:
        s["pts"] += 3
        s["w"] += 1
    elif gf == ga:
        s["pts"] += 1
        s["d"] += 1
    else:
        s["l"] += 1


def _h2h_subset(
    teams: List[str],
    results: List[Tuple[str, str, int, int]],
) -> Dict[str, Dict[str, int]]:
    """Mini-table for tied teams from pairwise results."""
    sub = {t: {"pts": 0, "gd": 0, "gf": 0} for t in teams}
    tset = set(teams)
    for a, b, ga, gb in results:
        if a not in tset or b not in tset:
            continue
        for team, gf, ga_opp in ((a, ga, gb), (b, gb, ga)):
            sub[team]["gf"] += gf
            sub[team]["gd"] += gf - ga_opp
            if gf > ga_opp:
                sub[team]["pts"] += 3
            elif gf == ga_opp:
                sub[team]["pts"] += 1
    return sub


def _rank_group(
    teams: List[str],
    standings: Dict[str, Dict[str, int]],
    match_results: List[Tuple[str, str, int, int]],
) -> List[str]:
    """Return teams sorted best-first (group winner first)."""

    def sort_key(team: str) -> Tuple:
        s = standings[team]
        gd = s["gf"] - s["ga"]
        return (-s["pts"], -gd, -s["gf"], team)

    ranked = sorted(teams, key=sort_key, reverse=False)
    top = ranked[0]
    tied = [
        t
        for t in teams
        if (
            standings[t]["pts"] == standings[top]["pts"]
            and (standings[t]["gf"] - standings[t]["ga"])
            == (standings[top]["gf"] - standings[top]["ga"])
            and standings[t]["gf"] == standings[top]["gf"]
        )
    ]
    if len(tied) <= 1:
        return ranked

    h2h = _h2h_subset(tied, match_results)
    tied_sorted = sorted(
        tied,
        key=lambda t: (-h2h[t]["pts"], -h2h[t]["gd"], -h2h[t]["gf"], t),
    )
    rest = [t for t in ranked if t not in tied]
    return tied_sorted + rest


def _simulate_match(
    rng: np.random.Generator,
    team_a: str,
    team_b: str,
    feat_vecs: Dict[str, np.ndarray],
    model: MatchupModel,
) -> Tuple[int, int]:
    fa = feat_vecs[team_a]
    fb = feat_vecs[team_b]
    p_win = model.p_team_a_wins(fa, fb)
    lam_a, lam_b = model.expected_goals(fa, fb, p_win=p_win)
    ga = int(rng.poisson(lam_a))
    gb = int(rng.poisson(lam_b))
    return ga, gb


def _simulate_one_group(
    teams: List[str],
    feat_vecs: Dict[str, np.ndarray],
    model: MatchupModel,
    rng: np.random.Generator,
) -> List[str]:
    standings = {t: {"pts": 0, "gf": 0, "ga": 0, "w": 0, "d": 0, "l": 0} for t in teams}
    results: List[Tuple[str, str, int, int]] = []
    for a, b in combinations(teams, 2):
        ga, gb = _simulate_match(rng, a, b, feat_vecs, model)
        results.append((a, b, ga, gb))
        _record_result(standings, a, ga, gb)
        _record_result(standings, b, gb, ga)
    return _rank_group(teams, standings, results)


def simulate_all_groups(
    groups: Dict[str, List[str]],
    feat_vecs: Dict[str, np.ndarray],
    model: MatchupModel,
    *,
    n_sims: int,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    win_counts: Dict[str, Dict[str, int]] = {g: {t: 0 for t in teams} for g, teams in groups.items()}
    top2_counts: Dict[str, Dict[str, int]] = {g: {t: 0 for t in teams} for g, teams in groups.items()}

    for _ in range(n_sims):
        for g, teams in groups.items():
            ranked = _simulate_one_group(teams, feat_vecs, model, rng)
            win_counts[g][ranked[0]] += 1
            for t in ranked[:2]:
                top2_counts[g][t] += 1

    rows = []
    for g, teams in groups.items():
        for t in teams:
            rows.append(
                {
                    "group": g,
                    "team": t,
                    "group_wins": win_counts[g][t],
                    "p_win_group": win_counts[g][t] / n_sims,
                    "p_top2": top2_counts[g][t] / n_sims,
                }
            )
    return pd.DataFrame(rows).sort_values(["group", "p_win_group"], ascending=[True, False])


def _write_markdown(
    df: pd.DataFrame,
    groups: Dict[str, List[str]],
    *,
    n_sims: int,
    seed: int,
    fifa_score_weight: float,
    host_weight: float,
    advanced_weight: float,
) -> str:
    lines = [
        "# 2026 World Cup — Group stage simulation",
        "",
        "Monte Carlo simulation of the **group stage only** (round-robin: each team plays",
        "the other three in its group). **Not** knockout/bracket prediction.",
        "",
        "## Method",
        "",
        f"- **Simulations:** {n_sims:,} independent group-stage draws",
        f"- **Random seed:** {seed}",
        "- **Feature set:** same `FEATURE_COLS` as the champion Random Forest",
        "  (Elo, FIFA rank score, last-12mo form, SofaScore advanced stats, confederation)",
        f"- **Feature weights:** fifa_rank_score ×{fifa_score_weight:g}, "
        f"host ×{host_weight:g}, advanced ×{advanced_weight:g}",
        "- **Match model:** logistic regression on weighted feature diffs (team A − team B)",
        "  trained on international results since 2010; Poisson goals calibrated from",
        "  the same features (goals for/against per match + win probability)",
        "- **Points:** 3 win / 1 draw / 0 loss",
        "- **Group winner tiebreak:** points → goal difference → goals scored → head-to-head",
        "  among tied teams",
        "- **Advancement:** top 2 per group (`p_top2`) — 48-team format (2026)",
        "",
        "Groups defined in `data/inputs/wc_2026_groups.json`.",
        "",
        "> **Disclaimer:** Statistical model, not betting advice.",
        "",
        "---",
        "",
    ]

    for g in sorted(groups.keys()):
        sub = df[df["group"] == g].sort_values("p_win_group", ascending=False)
        lines.append(f"## Group {g}")
        lines.append("")
        lines.append("| Team | P(win group) | P(finish top 2) |")
        lines.append("|------|-------------:|----------------:|")
        for _, row in sub.iterrows():
            lines.append(
                f"| {row['team']} | {100 * row['p_win_group']:.1f}% | {100 * row['p_top2']:.1f}% |"
            )
        fav = sub.iloc[0]
        lines.append("")
        lines.append(
            f"**Favorite to win group {g}:** {fav['team']} ({100 * fav['p_win_group']:.1f}%)"
        )
        lines.append("")

    if "C" in groups:
        sub = df[df["group"] == "C"].sort_values("p_win_group", ascending=False)
        lines.append("---")
        lines.append("")
        lines.append("## Group C snapshot (Brazil · Morocco · Haiti · Scotland)")
        lines.append("")
        for _, row in sub.iterrows():
            lines.append(
                f"- **{row['team']}:** {100 * row['p_win_group']:.1f}% win group, "
                f"{100 * row['p_top2']:.1f}% top 2"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Simulate 2026 WC group stage")
    ap.add_argument("--sims", type=int, default=DEFAULT_SIMS)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--groups-json", type=Path, default=GROUPS_JSON)
    ap.add_argument("--out-md", type=Path, default=OUT_MD)
    ap.add_argument("--out-json", type=Path, default=OUT_JSON)
    ap.add_argument(
        "--fifa-score-weight",
        type=float,
        default=DEFAULT_FIFA_SCORE_WEIGHT,
        help=f"Emphasize fifa_rank_score (default {DEFAULT_FIFA_SCORE_WEIGHT:g}).",
    )
    ap.add_argument(
        "--host-weight",
        type=float,
        default=DEFAULT_HOST_WEIGHT,
        help=f"Host feature weight (default {DEFAULT_HOST_WEIGHT:g}).",
    )
    ap.add_argument(
        "--advanced-weight",
        type=float,
        default=DEFAULT_ADVANCED_WEIGHT,
        help=f"SofaScore advanced stat weight (default {DEFAULT_ADVANCED_WEIGHT:g}).",
    )
    ap.add_argument(
        "--min-train-year",
        type=int,
        default=2010,
        help="Earliest year for matchup model training data.",
    )
    args = ap.parse_args()

    groups = _load_groups(args.groups_json)
    feats = build_2026_frame()
    feat_vecs = team_feature_matrix(feats)

    missing = []
    for g, teams in groups.items():
        for t in teams:
            if t not in feat_vecs:
                missing.append(f"{g}:{t}")
    if missing:
        print("WARNING: missing feature rows for:", ", ".join(missing), file=sys.stderr)

    print("Training matchup model on historical international results...", flush=True)
    model = MatchupModel(
        fifa_score_weight=args.fifa_score_weight,
        host_weight=args.host_weight,
        advanced_weight=args.advanced_weight,
        min_train_year=args.min_train_year,
    )
    model.fit()
    print("Matchup model ready.", flush=True)

    df = simulate_all_groups(
        groups,
        feat_vecs,
        model,
        n_sims=args.sims,
        seed=args.seed,
    )

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "n_sims": args.sims,
        "seed": args.seed,
        "fifa_score_weight": args.fifa_score_weight,
        "host_weight": args.host_weight,
        "advanced_weight": args.advanced_weight,
        "feature_cols": "same as champion RF (FEATURE_COLS)",
        "groups": groups,
        "results": df.to_dict(orient="records"),
    }
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md = _write_markdown(
        df,
        groups,
        n_sims=args.sims,
        seed=args.seed,
        fifa_score_weight=args.fifa_score_weight,
        host_weight=args.host_weight,
        advanced_weight=args.advanced_weight,
    )
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(md, encoding="utf-8")

    print(f"Wrote {args.out_json}")
    print(f"Wrote {args.out_md}")
    print(f"\nGroup winners (P win group), {args.sims:,} sims:")
    for g in sorted(groups.keys()):
        sub = df[df["group"] == g].sort_values("p_win_group", ascending=False)
        top = sub.iloc[0]
        print(f"  Group {g}: {top['team']} ({100 * top['p_win_group']:.1f}%)")


if __name__ == "__main__":
    main()
