#!/usr/bin/env python3
"""
Step 4: Scrape 2026 World Cup teams + FIFA ranks from worldpicks.vercel.app.

Usage:
  python scripts/scrape_2026_teams.py
  python scripts/scrape_2026_teams.py --url https://worldpicks.vercel.app/
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

import requests

DEFAULT_URL = "https://worldpicks.vercel.app/?ref=reddit_sportsanalytics"

PHASE1 = Path(__file__).resolve().parent.parent
OUT_PATH = PHASE1 / "data" / "inputs" / "teams_2026.json"

# worldpicks label -> martj / Kaggle canonical name
WORLD_PICKS_TO_CANONICAL: dict[str, str] = {
    "USA": "United States",
    "US": "United States",
    "Türkiye": "Turkey",
    "Turkey": "Turkey",
    "Czechia": "Czech Republic",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Bosnia and Herzegovina": "Bosnia and Herzegovina",
    "DR Congo": "DR Congo",
    "South Korea": "South Korea",
    "Korea Republic": "South Korea",
    "Curaçao": "Curaçao",
    "Curacao": "Curaçao",
}


def _canonical(name: str) -> str:
    name = html.unescape(name.strip())
    if name in WORLD_PICKS_TO_CANONICAL:
        return WORLD_PICKS_TO_CANONICAL[name]
    # Title-case ALL CAPS marquee names (BRAZIL -> Brazil)
    if name.isupper() and len(name) > 3:
        return name.title()
    return name


def _parse_teams(html: str) -> dict[str, dict]:
    """Return team -> {fifa_rank: int} (best rank seen if duplicate)."""
    teams: dict[str, dict] = {}

    # Next.js markup: <span class="...font-semibold...">Mexico</span>...Rank <!-- -->14
    rank_pat = re.compile(
        r'font-semibold[^>]*>([^<]+)</span><span class="mt-1 block font-mono[^"]*">'
        r"Rank\s*(?:<!--\s*-->)?\s*(\d+)",
        re.DOTALL,
    )
    for m in rank_pat.finditer(html):
        raw, rank = m.group(1).strip(), int(m.group(2))
        name = _canonical(raw)
        prev = teams.get(name, {}).get("fifa_rank")
        if prev is None or rank < prev:
            teams[name] = {"team": name, "fifa_rank": rank}

    # Marquee cards: FIFA #<!-- -->5 (team name often in nearby semibold span)
    fifa_pat = re.compile(
        r'font-semibold[^>]*>([^<]+)</span>[\s\S]{0,400}?FIFA\s*#\s*(?:<!--\s*-->)?\s*(\d+)',
        re.DOTALL,
    )
    for m in fifa_pat.finditer(html):
        raw, rank = m.group(1).strip(), int(m.group(2))
        name = _canonical(raw)
        prev = teams.get(name, {}).get("fifa_rank")
        if prev is None or rank < prev:
            teams[name] = {"team": name, "fifa_rank": rank}

    return teams


def scrape(url: str) -> dict:
    resp = requests.get(url, timeout=60, headers={"User-Agent": "WorldCupPhase1/1.0"})
    resp.raise_for_status()
    teams = _parse_teams(resp.text)
    if len(teams) < 40:
        raise RuntimeError(
            f"Only parsed {len(teams)} teams from {url}; page structure may have changed."
        )
    return {
        "year": 2026,
        "source": url,
        "teams": sorted(teams.values(), key=lambda t: t["fifa_rank"]),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args()

    payload = scrape(args.url)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}  ({len(payload['teams'])} teams)")


if __name__ == "__main__":
    main()
