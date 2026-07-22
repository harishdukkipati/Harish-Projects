#!/usr/bin/env python3
"""
Step 3: Build team_aliases.json from former_names.csv, FIFA name fixes, and worldpicks vs martj.

Run after build_wc_inputs.py and scrape_2026_teams.py.

Usage:
  python scripts/build_team_aliases.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "data" / "inputs"
KAGGLE = ROOT / "data" / "kaggle" / "martj_dataset"

STATIC_ALIASES: dict[str, str] = {
    "Germany FR": "Germany",
    "FRG": "Germany",
    "TCH": "Czechoslovakia",
    "USA": "United States",
    "US": "United States",
    "Türkiye": "Turkey",
    "Czechia": "Czech Republic",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Korea Republic": "South Korea",
    "Republic of Korea": "South Korea",
    "Curacao": "Curaçao",
    "Iran": "Iran",
    "Cape Verde": "Cape Verde",
    "DR Congo": "DR Congo",
    "Congo DR": "DR Congo",
    "Congo-Kinshasa": "DR Congo",
    "Zaïre": "DR Congo",
    "Zaire": "DR Congo",
}


def _load_former_names() -> dict[str, str]:
    path = KAGGLE / "former_names.csv"
    if not path.is_file():
        return {}
    df = pd.read_csv(path)
    aliases: dict[str, str] = {}
    for _, row in df.iterrows():
        current = str(row["current"]).strip()
        former = str(row["former"]).strip()
        if former and current:
            aliases[former] = current
    return aliases


def _martj_team_set() -> set[str]:
    part_path = INPUTS / "wc_participants.json"
    if not part_path.is_file():
        return set()
    data = json.loads(part_path.read_text(encoding="utf-8"))
    teams: set[str] = set()
    for lst in data.values():
        teams.update(lst)
    return teams


def _worldpicks_teams() -> list[str]:
    path = INPUTS / "teams_2026.json"
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [t["team"] for t in data.get("teams", [])]


def main() -> None:
    aliases: dict[str, str] = {}
    aliases.update(_load_former_names())
    aliases.update(STATIC_ALIASES)

    martj = _martj_team_set()
    for wp_name in _worldpicks_teams():
        if martj and wp_name not in martj:
            for candidate in [wp_name, STATIC_ALIASES.get(wp_name, wp_name)]:
                if candidate in martj:
                    if candidate != wp_name:
                        aliases[wp_name] = candidate
                    break

    out_path = INPUTS / "team_aliases.json"
    INPUTS.mkdir(parents=True, exist_ok=True)
    sorted_aliases = dict(sorted(aliases.items(), key=lambda x: x[0].lower()))
    out_path.write_text(
        json.dumps(sorted_aliases, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {out_path}  ({len(sorted_aliases)} alias entries)")


if __name__ == "__main__":
    main()
