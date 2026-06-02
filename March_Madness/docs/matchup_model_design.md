# Matchup model design (training + simulation)

## Goal
Predict \(P(\text{team\_a wins})\) for any tournament matchup using:
- historic NCAA tournament game outcomes (`MNCAATourneyCompactResults.csv`)
- team strength / resume signals (`Resumes.csv`, `KenPom Barttorvik.csv`, `KenPom Preseason.csv`)
- seed priors (`Seed Results.csv`)
- seed-pair upset tendencies (`Upset Seed Info.csv`)
- season-level chaos (`Upset Count.csv`)
- 2026 head-to-head from actual played games (`game_logs_2026.csv`) when available

The probability is used inside `src/bracket_sim.py` to simulate bracket paths.

## Target label
We train a binary classifier on historic games.

- **`label = 1`**: `team_a` won the game  
- **`label = 0`**: `team_a` lost the game

At prediction time, we call `predict_proba(...)[1]` to get **\(P(label=1)\)**, i.e. **\(P(\text{team\_a wins})\)**.

## Training dataset construction
Training rows come from `data/historic_data/MNCAATourneyCompactResults.csv` (seasons 2008–2025).

Pipeline:
1. Read compact results (winner/loser team IDs).
2. Map Kaggle `TeamID` → `TeamName` using `data/bracket_data/MTeams.csv`.
3. Infer tournament `round_num` by sorting by `DayNum` within season and assigning:
   - 32 games → 64
   - 16 games → 32
   - 8 games → 16
   - 4 games → 8
   - 2 games → 4
   - 1 game → 2
4. Join per-team signals by `(year, team name)` from archive2:
   - `Resumes.csv`: `RESUME`, `ELO`, `B POWER`, `R SCORE`, and `seed`
   - `KenPom Barttorvik.csv`: `KADJ EM`, `BARTHAG`
   - `KenPom Preseason.csv`: `PRESEASON KADJ EM`
5. Join seed priors from `Seed Results.csv` by `seed` (`seed_champ_pct`).
6. Add upset features:
   - **Pairwise upset rate** \(P(\text{seed\_hi beats seed\_lo} \mid \text{round})\) from `Upset Seed Info.csv` divided by the number of historical games between those seed pairs (denominator computed from compact results + `MNCAATourneySeeds.csv`).
   - **Season-level upset counts** from `Upset Count.csv` for that season and round, plus total upsets.
7. Add a mirrored training row for each game by swapping `team_a`/`team_b` and setting `label=0`.

## Features
Features are built in `src/matchup_model.py` and used in a single `LogisticRegression`.

### Identifiers (for export/debugging)
- `season`
- `team_a`, `team_b`
- `seed_a`, `seed_b`
- `round_num`

### Model features (numeric)
- `seed_diff`: `seed_a - seed_b`
- `resume_diff`: `RESUME_b - RESUME_a` (positive means team_a has the better resume rank)
- `elo_diff`, `b_power_diff`, `r_score_diff`
- `kadj_em_diff`, `bart_diff`
- `preseason_em_diff`
- `seed_champ_pct_diff`: `seed_champ_pct_a - seed_champ_pct_b`
- `seed_a_upset_rate_vs_seed_b`:
  - if `seed_a > seed_b`, uses the historical upset rate for `(round_num, seed_a, seed_b)`
  - if `seed_a < seed_b`, uses `1 - upset_rate(round_num, seed_b, seed_a)`
- `season_upsets_round`, `season_upsets_total` from `Upset Count.csv`
- `h2h_win_pct`, `h2h_point_diff`:
  - **Training (historic tournaments):** from `MRegularSeasonCompactResults.csv` + `MNCAATourneyCompactResults.csv`: all games in that season **before** the tournament game’s `DayNum` between the two teams. Win rate is from `team_a`’s perspective; point diff is mean(`team_a` points − `team_b` points) over those games. If they never met, `(0.5, 0)`.
  - **2026 inference:** from `data/game_logs_2026.csv` (deduped by date + pair); same semantics.
- `last10_win_pct_diff`, `last10_margin_diff`: **team_a** minus **team_b** on win rate and mean scoring margin over each team’s **last 10 games** before this game’s `DayNum` (regular season + earlier NCAA games that season). **2026:** last 10 rows per team in `game_logs_2026` sorted by date.
- `path_beaten_strength_diff`: **team_a − team_b** on mean(`17 − opponent_seed`) for opponents eliminated in **R64 and R32 only** (first two NCAA rounds). **Training:** computed from `MNCAATourneyCompactResults` + `MNCAATourneySeeds` (actual winners/losers before each game day). **2026 inference:** from `data/bracket_data/sweet16_path_wins_2026.json` (16 teams → two opponent names each, Resumes `TEAM` spelling). Aliases like “Long Island” → `LIU Brooklyn` are applied in `bracket_data.normalize_resume_team_name`. Logistic regression learns whether a **higher** path score correlates with winning (typically positive if tougher paths predict better teams).

## Exported training CSV
Run:

```bash
python3 scripts/export_matchup_training_df.py
```

Output:
- `data/derived/matchup_training_df_2008_2025.csv`

This CSV contains **all engineered feature columns plus `label`**, and is the “combined dataset” the model trains on.

## Simulation usage
`src/bracket_sim.py`:
1. Trains one model on 2008–2025.
2. Builds 2026 matchup feature rows (adds `h2h_win_pct` when available).
3. Uses the model’s `predict_proba` to simulate each game outcome in a Monte Carlo bracket run.

