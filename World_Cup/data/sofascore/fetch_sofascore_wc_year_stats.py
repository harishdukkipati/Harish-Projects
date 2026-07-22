#!/usr/bin/env python3
"""
Fetch SofaScore advanced stats for a **completed FIFA World Cup** edition.

Uses the "FIFA World Cup" competition (not World Cup Qual), e.g. Argentina 2022:
  /team/4819/unique-tournament/16/season/41087/statistics/overall

Flow per team:
  1. GET /search/all?q={name}  -> teamId
  2. GET /team/{teamId}/standings/seasons  -> pick FIFA World Cup + season for --year
  3. GET .../statistics/overall  -> possession, pass %, SoT %, set-piece proxy

Example:

  cd World_Cup/data/sofascore
  python3 fetch_sofascore_wc_year_stats.py --year 2018
  python3 fetch_sofascore_wc_year_stats.py --year 2022 --teams Argentina Brazil
  python3 fetch_sofascore_wc_year_stats.py --year 2018 --no-cache

Teams default to wc_participants.json for that year. Output:
  data/sofascore/historical/team_wc_stats_{year}.csv

Requires: pip install curl_cffi pandas
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from sofascore_client import SofascoreClient, extract_advanced_stats
from fetch_sofascore_team_stats import (
    _load_team_id_cache,
    _root_on_path,
    _save_team_id_cache,
    _search_query,
)

_SOFA_DIR = Path(__file__).resolve().parent
_ROOT = _SOFA_DIR.parent.parent
_PARTICIPANTS_JSON = _ROOT / "data" / "inputs" / "wc_participants.json"
_HISTORICAL_DIR = _SOFA_DIR / "historical"


def _load_participants_for_year(year: int) -> List[str]:
    data = json.loads(_PARTICIPANTS_JSON.read_text(encoding="utf-8"))
    key = str(year)
    if key not in data:
        raise KeyError(
            f"No teams for year {year} in {_PARTICIPANTS_JSON.name}. "
            f"Available years include: {sorted(data.keys())[-5:]}"
        )
    return list(data[key])


def fetch_team_row_for_wc_year(
    client: SofascoreClient,
    team_name: str,
    *,
    wc_year: int,
    team_id: Optional[int],
    use_cache: bool,
) -> Dict[str, Any]:
    _root_on_path()
    from src import load_data as ld

    aliases = ld.load_aliases()
    canon = ld.normalize_team(team_name, aliases)
    search_q = _search_query(canon, aliases)

    if team_id is None:
        team_id, sofascore_name = client.search_team_id(search_q)
    else:
        sofascore_name = search_q

    cache_dir = _SOFA_DIR / "cache" / "raw" / str(team_id)
    seasons_path = cache_dir / "standings_seasons.json" if use_cache else None
    seasons_data = client.standings_seasons(
        team_id, cache_path=seasons_path if use_cache else None
    )
    utid, sid, tname, sname = client.pick_fifa_world_cup_season(
        seasons_data, wc_year=wc_year
    )

    stats_path = (
        cache_dir / f"stats_wc_{wc_year}_{utid}_{sid}.json" if use_cache else None
    )
    stats = client.team_statistics_overall(
        team_id, utid, sid, cache_path=stats_path if use_cache else None
    )
    adv = extract_advanced_stats(stats)

    return {
        "team": canon,
        "wc_year": wc_year,
        "sofascore_team_id": team_id,
        "sofascore_team_name": sofascore_name,
        "unique_tournament_id": utid,
        "season_id": sid,
        "competition": tname,
        "season": sname,
        **adv,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch SofaScore FIFA World Cup tournament stats for one WC year"
    )
    parser.add_argument(
        "--year",
        type=int,
        required=True,
        metavar="YYYY",
        help="World Cup year to fetch (e.g. 2018, 2022)",
    )
    parser.add_argument(
        "--teams",
        nargs="*",
        help="Subset of teams (default: all participants that year)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output CSV (default: historical/team_wc_stats_{year}.csv)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass JSON cache under cache/raw/",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.6,
        help="Seconds between API requests (default: 0.6)",
    )
    args = parser.parse_args()

    wc_year = args.year
    out_path = args.out or (_HISTORICAL_DIR / f"team_wc_stats_{wc_year}.csv")
    targets = args.teams if args.teams else _load_participants_for_year(wc_year)
    use_cache = not args.no_cache

    client = SofascoreClient(delay_sec=args.delay)
    id_cache = _load_team_id_cache()

    rows: List[Dict[str, Any]] = []
    failed: List[str] = []

    print(f"Fetching FIFA World Cup SofaScore stats for WC {wc_year} ({len(targets)} teams)")

    for name in targets:
        _root_on_path()
        from src import load_data as ld

        canon = ld.normalize_team(name)
        tid = id_cache.get(canon)
        try:
            row = fetch_team_row_for_wc_year(
                client,
                name,
                wc_year=wc_year,
                team_id=tid,
                use_cache=use_cache,
            )
            rows.append(row)
            id_cache[canon] = int(row["sofascore_team_id"])
            poss = row["avg_possession"]
            poss_s = f"poss={poss:.1f}" if poss == poss else "poss=?"
            print(
                f"  OK {canon}: team_id={row['sofascore_team_id']} "
                f"{row['competition']} season={row['season_id']} {poss_s}"
            )
        except Exception as e:
            failed.append(f"{canon}: {e}")
            print(f"  FAIL {canon}: {e}")

    _save_team_id_cache(id_cache)

    if rows:
        df = pd.DataFrame(rows)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)
        print(f"\nWrote {out_path} ({len(df)} teams)")
        print(
            f"  with_possession={df['avg_possession'].notna().sum()}  "
            f"with_sot_pct={df['shots_on_target_pct'].notna().sum()}"
        )

    if failed:
        print(f"\n{len(failed)} failed:", file=sys.stderr)
        for msg in failed:
            print(f"  - {msg}", file=sys.stderr)
        sys.exit(1 if not rows else 0)


if __name__ == "__main__":
    main()
