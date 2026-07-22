# Phase 1 data pipeline (steps 0–4)

## Step 0 — Kaggle CSVs (manual)

Place files under `data/kaggle/` (already done).

## Steps 1–2 — Historical WC participants & winners

```bash
cd World_Cup/phase_1
../../venv/bin/python scripts/build_wc_inputs.py
```

Writes:

- `data/inputs/wc_participants.json` — unique teams per WC year (1930–2022) from `martj_dataset/results.csv`
- `data/inputs/wc_winners.json` — champion per year (last WC match; shootouts for drawn finals)

## Step 4 — 2026 team slate

```bash
../../venv/bin/python scripts/scrape_2026_teams.py
```

Writes `data/inputs/teams_2026.json` (48 teams + FIFA rank) from [worldpicks.vercel.app](https://worldpicks.vercel.app/).

## Step 3 — Name aliases

```bash
../../venv/bin/python scripts/build_team_aliases.py
```

Writes `data/inputs/team_aliases.json` from `former_names.csv` + static worldpicks→martj mappings.

Run **after** steps 1–2 and 4.

## Step 5 — Features + Random Forest

```bash
../../venv/bin/python scripts/train_and_predict.py --save-features
../../venv/bin/python scripts/export_2026_features.py   # optional: team_2018/2022/2026_features.csv
```

Writes `data/processed/team_year_features.csv`, prints leave-one-WC-out CV (default: 2006–2022, recency-weighted), then top-15 2026 rankings.

Modules: `src/load_data.py`, `src/features.py`, `src/model.py`.

## SofaScore — advanced stats (possession, passing, shooting)

```bash
cd World_Cup/phase_1/data/sofascore
../../../venv/bin/python fetch_sofascore_team_stats.py
```

See **`docs/SOFASCORE.md`**.

- **2026:** `fetch_sofascore_team_stats.py` → `team_wc_qual_stats.csv`
- **Historical WCs:** `fetch_sofascore_wc_year_stats.py --year 2018` (etc.) → `historical/team_wc_stats_{year}.csv`

`src/sofascore_load.py` feeds `src/features.py` for model training and inference.
