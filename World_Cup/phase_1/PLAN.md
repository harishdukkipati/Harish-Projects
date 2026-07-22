# Phase 1 — Predict the 2026 World Cup Champion (only)

## Goal

Single output: ranked probabilities `P(team wins WC 2026)` for all 48 entrants. Top-1 = our predicted champion. **No bracket math, no group simulation, no per-match features.** Just team-level pre-tournament features.

## Why this is the right place to start

- Avoids the hardest variance source (penalty shootouts, group tiebreakers, Poisson sampling chains across 64 dependent matches).
- Reuses the exact mental model of `../../March_Madness/src/matchup_model.py`: build feature row, train logistic, `predict_proba` → winner. Just over **teams** instead of matchups.
- Feeds Phase 2 cleanly: the same per-team feature snapshots become priors / per-team strengths in the Poisson goals model later.

## Dataset shape

One row per **(team, World_Cup_year)** pair, label = 1 if that team won that WC, else 0.

- 22 World Cups (1930–2022); 16/24/32/48 teams per year
- Approx **528 rows total** across all WCs (sum of teams across years), **22 positives**, ~506 negatives
- For 2026 inference: **48 rows** (one per entrant), no labels — we predict probabilities and rank them

## Features per (team, year) row

All features must be computed **strictly before that year's WC kicks off** (no leakage).

### Strength & form (always available)

- `pre_wc_elo` — ELO rating on day before WC starts
- `pre_wc_fifa_rank` — FIFA rank monthly snapshot before WC (NaN before 1992)
- `last12mo_win_pct` — win rate in last 12 months of internationals
- `last12mo_goals_for_per_match`
- `last12mo_goals_against_per_match`
- `last12mo_goal_diff_per_match`
- `last12mo_matches_played` (rust / activity proxy)
- `days_since_last_match` (right before WC)

### Pedigree

- `prior_wc_titles` (cumulative)
- `prior_wc_finals` (cumulative)
- `prior_wc_semifinals` (cumulative)
- `prior_wc_appearances`
- `is_defending_champion` (binary)

### Context

- `is_host` (binary; for 2026: USA, Canada, Mexico = 1)
- `host_confederation_match` (binary; team's confederation == host's)
- `confederation` (one-hot: UEFA, CONMEBOL, CONCACAF, CAF, AFC, OFC)

### Advanced (SofaScore — WC Qual for 2026, WC finals for historical years)

- `last12mo_avg_possession`
- `last12mo_pass_completion_pct`
- `last12mo_set_piece_success_rate` (PK/FK proxy)
- `last12mo_shots_on_target_pct`

Missing values are filled with **per-year column means** (then global mean). See `docs/SOFASCORE.md` and `data/sofascore/`.

## Model (shipped)

**`RandomForestClassifier`** (`class_weight='balanced'`, 300 trees, `max_depth=10`):

- One row per (team, WC year); predict `P(champion)` and rank entrants.
- Features: Elo, `fifa_rank_score` (= 1 / FIFA rank), last-12-month form, SofaScore advanced stats, confederation one-hot.
- Pedigree / host flags are built for CSV export but **not** fed to the forest.
- Training window default: WC years **≥ 2006** (SofaScore advanced stats available).
- Sample weights: **recency** by default (half-life 8 years, ref 2022 — 2006 lightest, 2022 heaviest). Use `--equal-tournament-weights` for flat editions.

Gradient boosting was removed (unstable on the small 2018+2022 training window).

## Validation: leave-one-WC-out CV

For each held-out WC year:

- Train on the other 21 WCs.
- Predict probabilities for that year's entrants; rank.
- Record whether true champion was top-1 / top-3 / top-5.

Headline metrics:

- **Top-1 hit rate** across 22 WCs (chance baseline ≈ 1/24 ≈ 4%)
- **Top-3 hit rate** (chance ≈ 12.5%)
- **Log-loss** on the 22 winner labels with predicted prob
- **Mean rank of true champion** (lower = better)

Spot checks: 2022 should rank Argentina top-3, 2018 France top-3, 2014 Germany top-3.

## Skeleton

```
World_Cup/phase_1/
  PLAN.md                      # this file
  data/
    kaggle/                    # raw downloaded CSVs (4 datasets below)
    sofascore/                 # WC Qual + historical WC stats (see docs/SOFASCORE.md)
    processed/                 # team_year_features.csv, team_*_features.csv
    inputs/
      teams_2026.json          # 48-team slate scraped from worldpicks
      team_aliases.json        # name normalization
      wc_winners.json          # year -> champion (manual, 22 entries, source-of-truth)
      wc_participants.json     # year -> [teams] (derived from results)
  src/
    load_data.py               # loaders for Kaggle CSVs + alias mapping
    sofascore_load.py          # advanced stats from data/sofascore/*.csv
    features.py                # build per-(team,year) feature row, leak-free time slicing
    model.py                   # train + cross-validate; expose predict_winner(teams_2026)
  scripts/
    fetch_kaggle.py            # uses kaggle CLI / opendatasets to pull 4 datasets
    scrape_2026_teams.py       # pulls worldpicks slate -> teams_2026.json
    export_2026_features.py    # inspection CSVs for 2018 / 2022 / 2026
    train_and_predict.py       # main: trains, runs LOO-CV, prints ranked 2026 probabilities
  docs/
    README.md                  # how to run, expected outputs, validation results
```

## Kaggle datasets (download once into `data/kaggle/`)

- [`martj42/international-football-results-from-1872-to-2017`](https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017) — every international match 1872–2026 (results, neutral flag, tournament tag). Used for **last-12mo form** and to identify **WC participants and winners** directly.
- [`saifalnimri/international-football-elo-ratings`](https://www.kaggle.com/datasets/saifalnimri/international-football-elo-ratings) — daily ELO 1872–2025; **pre-WC ELO snapshot**.
- [`cashncarry/fifaworldranking`](https://www.kaggle.com/datasets/cashncarry/fifaworldranking) — monthly FIFA rank 1992–2024; **pre-WC rank snapshot** (NaN before 1992 is fine, model handles it).
- [`abecklas/fifa-world-cup`](https://www.kaggle.com/datasets/abecklas/fifa-world-cup) — World Cup matches/players 1930–2014; redundant with `martj42` for results but cleaner WC tagging + player rosters if we ever want squad-value features.

For advanced stats (possession, pass %, set-piece success), the source is **SofaScore** (`data/sofascore/fetch_sofascore_team_stats.py` for 2026 qual, `fetch_sofascore_wc_year_stats.py` for historical WC years). Requires `curl_cffi` (see repo `requirements.txt`).

## Honest accuracy expectation

With only **22 positive examples**, the model can't be magic. Realistic targets on leave-one-WC-out CV:

- **Top-1 champion hit:** ~5–7 of 22 (model gets it right when the favorite actually wins, e.g. 2014 Germany, 2010 Spain)
- **Top-3 hit:** ~13–17 of 22 (60–75%)
- **Top-5 hit:** ~17–20 of 22

Real WC winners aren't always pre-tournament #1 (e.g., 2018 France, 2002 Brazil), so even when top-1 is wrong, top-3/top-5 should be strong.

## Open questions / risks

- **Name normalization** across `martj42`, ELO, FIFA rank, SofaScore, worldpicks (Türkiye/Turkey, Czechia/Czech Republic, Curaçao/Curacao, West Germany / Germany pre-1990). Single `team_aliases.json` is the source of truth.
- **Pre-1992 rows lose `pre_wc_fifa_rank`**; handled via NaN → impute. Decide whether to keep them or drop pre-1992 entirely (lose 6 WCs, gain feature consistency).
- **Class imbalance (~4% positives)** — use `class_weight='balanced'` and report log-loss / mean-rank-of-true-champ instead of just accuracy.
- **Squad-value / player-injury features** are the obvious next upgrade but require Transfermarkt scraping; deferred.
