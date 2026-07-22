#!/usr/bin/env python3
"""
Fetch pre-tournament advanced stats for 2026 World Cup teams from SofaScore.

Uses the same JSON endpoints as the website (no browser automation):
  1. GET /search/all?q={name}           -> teamId
  2. GET /team/{teamId}/standings/seasons -> World Cup Qual tournament + season ids
  3. GET /team/{teamId}/unique-tournament/{utId}/season/{sId}/statistics/overall

Example:

  cd World_Cup/phase_1/data/sofascore
  ../../venv/bin/python fetch_sofascore_team_stats.py
  ../../venv/bin/python fetch_sofascore_team_stats.py --teams Argentina Brazil
  ../../venv/bin/python fetch_sofascore_team_stats.py --no-cache

Requires: pip install curl_cffi pandas
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from sofascore_client import (
    ADVANCED_STAT_KEYS,
    CORE_ADVANCED_KEYS,
    SEARCH_QUERY_OVERRIDES,
    SofascoreClient,
    advanced_stats_full_count,
    has_core_advanced_stats,
)

_SOFA_DIR = Path(__file__).resolve().parent
_PHASE1 = _SOFA_DIR.parent.parent
_DEFAULT_TEAMS_JSON = _PHASE1 / "data" / "inputs" / "teams_2026.json"
_CACHE = _SOFA_DIR / "cache"
_OUT_CSV = _SOFA_DIR / "team_wc_qual_stats.csv"
_TEAM_IDS_JSON = _SOFA_DIR / "cache" / "team_ids.json"

# Verified men's national team ids (skip search when present).
_SEED_TEAM_IDS: Dict[str, int] = {
    "Argentina": 4819,
    "Brazil": 4748,
}


def _phase1_on_path() -> None:
    root = str(_PHASE1)
    if root not in sys.path:
        sys.path.insert(0, root)


def _load_teams(path: Path) -> List[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    names = []
    for t in data.get("teams", []):
        raw = t.get("team")
        if raw:
            names.append(html.unescape(str(raw)))
    return names


def _load_team_id_cache() -> Dict[str, int]:
    if not _TEAM_IDS_JSON.is_file():
        return dict(_SEED_TEAM_IDS)
    cached = json.loads(_TEAM_IDS_JSON.read_text(encoding="utf-8"))
    out = dict(_SEED_TEAM_IDS)
    out.update({k: int(v) for k, v in cached.items()})
    return out


def _save_team_id_cache(cache: Dict[str, int]) -> None:
    _TEAM_IDS_JSON.parent.mkdir(parents=True, exist_ok=True)
    _TEAM_IDS_JSON.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")


def _search_query(canonical: str, aliases: Dict[str, str]) -> str:
    if canonical in SEARCH_QUERY_OVERRIDES:
        return SEARCH_QUERY_OVERRIDES[canonical]
    for alias, target in aliases.items():
        if target == canonical and alias in SEARCH_QUERY_OVERRIDES:
            return SEARCH_QUERY_OVERRIDES[alias]
    return canonical


def fetch_team_row(
    client: SofascoreClient,
    canonical: str,
    *,
    team_id: Optional[int],
    use_cache: bool,
    prefer_year: int,
) -> Dict[str, Any]:
    _phase1_on_path()
    from src import load_data as ld  # noqa: WPS433

    aliases = ld.load_aliases()
    canon = ld.normalize_team(canonical, aliases)
    search_q = _search_query(canon, aliases)

    sofascore_name = ""
    if team_id is None:
        team_id, sofascore_name = client.search_team_id(search_q)
    else:
        sofascore_name = search_q

    cache_dir = _CACHE / "raw" / str(team_id)
    seasons_path = cache_dir / "standings_seasons.json" if use_cache else None
    seasons_data = client.standings_seasons(
        team_id, cache_path=seasons_path if use_cache else None
    )
    cand, adv, _stats = client.fetch_best_advanced_stats(
        team_id,
        seasons_data,
        cache_dir=cache_dir,
        use_cache=use_cache,
        prefer_qual_year=prefer_year,
    )

    return {
        "team": canon,
        "sofascore_team_id": team_id,
        "sofascore_team_name": sofascore_name,
        "unique_tournament_id": cand.unique_tournament_id,
        "season_id": cand.season_id,
        "competition": cand.competition,
        "season": cand.season,
        "stats_source": cand.source,
        **adv,
    }


def _print_missing_report(df: pd.DataFrame) -> None:
    """Summarize missing advanced stat columns after fetch."""
    n = len(df)
    print("\n=== Advanced stats missing-column report ===")
    print(f"Teams fetched: {n}")
    if n == 0:
        return

    for col in ADVANCED_STAT_KEYS:
        missing = df[col].isna().sum()
        print(f"  missing {col}: {missing}/{n}")

    core_missing = df.apply(
        lambda r: not has_core_advanced_stats(
            {k: r.get(k, float("nan")) for k in ADVANCED_STAT_KEYS}
        ),
        axis=1,
    )
    full_missing = df.apply(
        lambda r: advanced_stats_full_count(
            {k: r.get(k, float("nan")) for k in ADVANCED_STAT_KEYS}
        )
        < len(ADVANCED_STAT_KEYS),
        axis=1,
    )
    print(f"  missing any core ({', '.join(CORE_ADVANCED_KEYS)}): {int(core_missing.sum())}/{n}")
    print(f"  missing any of 4 advanced cols: {int(full_missing.sum())}/{n}")

    if "stats_source" in df.columns:
        print("\n  stats_source breakdown:")
        for src, grp in df.groupby("stats_source", dropna=False):
            ok = int((~grp.apply(
                lambda r: not has_core_advanced_stats(
                    {k: r.get(k, float("nan")) for k in ADVANCED_STAT_KEYS}
                ),
                axis=1,
            )).sum())
            print(f"    {src}: {len(grp)} teams ({ok} with full core stats)")

    bad = df[core_missing][["team", "stats_source", "competition"] + list(ADVANCED_STAT_KEYS)]
    if not bad.empty:
        print("\n  Teams still missing core advanced stats:")
        for _, row in bad.iterrows():
            miss_cols = [k for k in ADVANCED_STAT_KEYS if pd.isna(row.get(k))]
            print(
                f"    {row['team']}: source={row.get('stats_source')} "
                f"comp={row.get('competition')} missing={miss_cols}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch SofaScore WC Qual team statistics")
    parser.add_argument(
        "--teams-json",
        type=Path,
        default=_DEFAULT_TEAMS_JSON,
        help="JSON with 2026 WC teams (default: data/inputs/teams_2026.json)",
    )
    parser.add_argument(
        "--teams",
        nargs="*",
        help="Only fetch these team names (default: all in teams-json)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=_OUT_CSV,
        help="Output CSV path",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore/write through JSON cache under cache/raw/",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.6,
        help="Seconds between API requests (default: 0.6)",
    )
    parser.add_argument(
        "--prefer-year",
        type=int,
        default=2026,
        help="Prefer WC qual season matching this year (default: 2026)",
    )
    args = parser.parse_args()

    all_teams = _load_teams(args.teams_json)
    targets = args.teams if args.teams else all_teams
    use_cache = not args.no_cache
    client = SofascoreClient(delay_sec=args.delay)
    id_cache = _load_team_id_cache()

    rows: List[Dict[str, Any]] = []
    failed: List[str] = []

    for name in targets:
        _phase1_on_path()
        from src import load_data as ld  # noqa: WPS433

        canon = ld.normalize_team(name)
        tid = id_cache.get(canon)
        try:
            row = fetch_team_row(
                client,
                name,
                team_id=tid,
                use_cache=use_cache,
                prefer_year=args.prefer_year,
            )
            rows.append(row)
            id_cache[canon] = int(row["sofascore_team_id"])
            poss = row["avg_possession"]
            poss_s = f"poss={poss:.1f}" if poss == poss else "poss=?"
            src = row.get("stats_source", "?")
            print(
                f"  OK {canon}: team_id={row['sofascore_team_id']} "
                f"[{src}] {row['competition']} ({row['season_id']}) {poss_s}"
            )
        except Exception as e:
            failed.append(f"{canon}: {e}")
            print(f"  FAIL {canon}: {e}")

    _save_team_id_cache(id_cache)

    if rows:
        df_new = pd.DataFrame(rows)
        if args.out.is_file() and args.teams:
            existing = pd.read_csv(args.out)
            if "team" in existing.columns:
                fetched = set(df_new["team"].astype(str))
                existing = existing[~existing["team"].astype(str).isin(fetched)]
                df = pd.concat([existing, df_new], ignore_index=True)
            else:
                df = df_new
        else:
            df = df_new
        args.out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.out, index=False)
        print(f"\nWrote {args.out} ({len(df)} teams)")
        _print_missing_report(df)

    if failed:
        print(f"\n{len(failed)} failed:", file=sys.stderr)
        for msg in failed:
            print(f"  - {msg}", file=sys.stderr)
        sys.exit(1 if not rows else 0)


if __name__ == "__main__":
    main()
