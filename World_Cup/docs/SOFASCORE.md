# SofaScore — WC Qual advanced stats (2026)

Pre-tournament **possession**, **pass completion**, **shots on target %**, and a rough **set-piece** proxy for World Cup teams, pulled from SofaScore’s public JSON API (same data as the website). This is the **only** source for the four advanced model features.

## Prerequisites

```bash
# From repo root
pip install curl_cffi pandas
```

`curl_cffi` impersonates Chrome so SofaScore’s Akamai WAF accepts requests. Plain `requests` often returns `{"error": ...}`.

## API flow (no browser automation)

For each national team:

| Step | Endpoint | Purpose |
|------|----------|---------|
| 1 | `GET /api/v1/search/all?q={name}` | Resolve `teamId` (men’s national football only) |
| 2 | `GET /api/v1/team/{teamId}/standings/seasons` | List competitions; pick **World Cup Qual** |
| 3 | `GET /api/v1/team/{teamId}/unique-tournament/{utId}/season/{sId}/statistics/overall` | Season aggregates |

Example stats URL (Brazil, CONMEBOL qual):

```text
https://www.sofascore.com/api/v1/team/4748/unique-tournament/295/season/53820/statistics/overall
```

Key JSON fields under `statistics`:

- `averageBallPossession` → `last12mo_avg_possession`
- `accuratePassesPercentage` (or `accuratePasses` / `totalPasses`) → pass completion
- `shotsOnTarget` / `shots` → SoT %
- `penaltyGoals` + `freeKickGoals` vs `penaltiesTaken` + `freeKickShots` → set-piece proxy (optional)

**Note:** These are **World Cup Qual campaign** aggregates, not calendar “last 12 months” across all internationals.

## Historical WC year (FIFA World Cup finals, not Qual)

Separate script for completed tournaments (e.g. Argentina 2022 → `unique-tournament/16/season/41087`):

```bash
cd World_Cup/data/sofascore

python fetch_sofascore_wc_year_stats.py --year 2018
python fetch_sofascore_wc_year_stats.py --year 2022 --teams Argentina Brazil
```

Writes `data/sofascore/historical/team_wc_stats_{year}.csv` using teams from `wc_participants.json` for that year.

## Fetch script (2026 — World Cup Qual)

```bash
cd World_Cup/data/sofascore

# All 48 teams from data/inputs/teams_2026.json (~30–60s with rate limit)
python fetch_sofascore_team_stats.py

# Subset / refresh
python fetch_sofascore_team_stats.py --teams Argentina Brazil England
python fetch_sofascore_team_stats.py --no-cache

# Slower requests if you hit rate limits
python fetch_sofascore_team_stats.py --delay 1.2
```

### Outputs

| Path | Description |
|------|-------------|
| `data/sofascore/team_wc_qual_stats.csv` | One row per team — model input |
| `data/sofascore/cache/team_ids.json` | Cached `team` → SofaScore `teamId` |
| `data/sofascore/cache/raw/{teamId}/` | Cached JSON per team |

Seeded IDs (skip search when known): Argentina `4819`, Brazil `4748`.

### Search name overrides

Some names differ on SofaScore (see `SEARCH_QUERY_OVERRIDES` in `sofascore_client.py`), e.g. `United States` → `USA`, `South Korea` → `Korea Republic`.

## Model integration

`src/features.py` → `sofascore.lookup_advanced_features(team, year)`:

| Year | SofaScore source |
|------|------------------|
| `< 2026` | `historical/team_wc_stats_{year}.csv` (FIFA World Cup finals) |
| `>= 2026` | `team_wc_qual_stats.csv` (WC Qual) |

**Imputation:** Any missing value in the four advanced columns is filled with the **mean of that column for the same `year`** (e.g. all 2018 teams share 2018 means). If a whole year lacks data for a column, the **global** mean for that column is used. No more `fillna(0)` on advanced stats.

Regenerate features after fetching:

```bash
cd World_Cup
python scripts/train_and_predict.py --save-features
```

## Modules

| File | Role |
|------|------|
| `data/sofascore/sofascore_client.py` | HTTP client, qual picker, stat extraction |
| `data/sofascore/fetch_sofascore_team_stats.py` | CLI: fetch all teams → CSV |
| `src/sofascore_load.py` | Load CSV into feature dict |
| `src/features.py` | Prefer SofaScore for 2026 advanced block |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ImportError: curl_cffi` | `pip install curl_cffi` |
| `No World Cup Qualification tournament` | Team may use a different qual label; check `standings/seasons` JSON in cache |
| `No national football team found` | Add a `SEARCH_QUERY_OVERRIDES` entry or fix `team_aliases.json` |
| HTTP 403 / `error` in JSON | Increase `--delay`; ensure `curl_cffi` is used |
| Wrong team (youth/club) | Script filters `national=true`, excludes `U20`/`U23` in name |

## Legal

SofaScore does not offer a public licensed API for third parties. This pipeline is for personal/research use; respect rate limits and their terms of service.
