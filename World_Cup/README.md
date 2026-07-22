# World Cup Predictor

Predicts the 2026 World Cup **champion**: a ranked `P(team wins WC 2026)` for all 48 entrants, trained on 94 years of World Cup history. No bracket simulation — one number per team, ranked.

## Result

For the actual 2026 tournament, the model's top 4 by predicted win probability were **Spain, France, Argentina, England** — exactly the four teams that reached the semifinals, with **Spain** as the top overall pick and eventual champion.

Full ranked output (top 32 of 48 entrants, probabilities renormalized to sum to 100% over this slice):

| # | Team | Share | # | Team | Share |
|---|------|------:|---|------|------:|
| 1 | Spain | 14.78% | 17 | Algeria | 0.98% |
| 2 | France | 11.75% | 18 | Mexico | 0.68% |
| 3 | Argentina | 10.87% | 19 | Egypt | 0.67% |
| 4 | England | 10.38% | 20 | South Africa | 0.67% |
| 5 | Portugal | 6.20% | 21 | South Korea | 0.66% |
| 6 | Germany | 5.52% | 22 | Iraq | 0.46% |
| 7 | Netherlands | 5.28% | 23 | United States | 0.46% |
| 8 | Austria | 5.20% | 24 | Turkey | 0.45% |
| 9 | Belgium | 4.30% | 25 | Bosnia and Herzegovina | 0.35% |
| 10 | Croatia | 4.17% | 26 | Brazil | 0.33% |
| 11 | Norway | 3.90% | 27 | Uruguay | 0.33% |
| 12 | Colombia | 3.63% | 28 | Iran | 0.23% |
| 13 | Switzerland | 2.90% | 29 | Australia | 0.23% |
| 14 | Ivory Coast | 1.79% | 30 | Canada | 0.23% |
| 15 | Morocco | 1.36% | 31 | Senegal | 0.12% |
| 16 | Panama | 1.00% | 32 | Czech Republic | 0.12% |

## How it works

Four stages, each a script in [`scripts/`](scripts):

1. **Historical inputs** ([`build_wc_inputs.py`](scripts/build_wc_inputs.py)) — derives every WC's participant list and champion (1930–2022) from the Kaggle results dataset.
2. **2026 slate** ([`scrape_2026_teams.py`](scripts/scrape_2026_teams.py)) — scrapes the 48 qualified teams + FIFA rank from worldpicks.
3. **Name aliasing** ([`build_team_aliases.py`](scripts/build_team_aliases.py)) — reconciles team names across four different data sources (e.g. Türkiye/Turkey, Czechia/Czech Republic, West Germany → Germany).
4. **Features + model** ([`train_and_predict.py`](scripts/train_and_predict.py)) — builds one feature row per (team, WC year), trains the classifier, cross-validates it, and ranks the 2026 slate.

See [`docs/DATA_PIPELINE.md`](docs/DATA_PIPELINE.md) for exact commands and file outputs.

### Training data

One row per **(team, World Cup year)** pair, label `1` if that team won that tournament, `0` otherwise — roughly 528 rows spanning 1930–2022, of which only **22 are positive** (one champion per tournament). All features for a given row are computed **strictly before that tournament kicked off**, so the model never sees information a bettor wouldn't have had at the time.

### Features (16 columns fed to the model)

| Group | Features |
|---|---|
| Strength | `pre_wc_elo`, `fifa_rank_score` (= 1 / FIFA rank) |
| Recent form (trailing 12 months) | win %, goals for/against per match, goal differential, matches played, days since last match, average opponent Elo (strength of schedule) |
| Advanced stats (SofaScore) | possession, pass completion %, shots-on-target %, set-piece success rate |
| Context | `is_host`, confederation (one-hot: UEFA, CONMEBOL, CONCACAF, CAF, AFC, OFC) |

Two things are computed but deliberately **excluded** from the model: WC pedigree (prior titles/finals/appearances) and defending-champion status. With only 22 positive examples, letting the model key off "this team has won before" collapses into a self-fulfilling loop toward historically dominant teams rather than reflecting each team's actual current strength — this is called out explicitly in [`docs/decision_tree_vs_ensemble.md`](docs/decision_tree_vs_ensemble.md).

Missing SofaScore data is filled with a value *below* the observed minimum for that column, rather than the mean — a missing stat is treated as a penalty, not a neutral placeholder. See [`docs/FEATURES.md`](docs/FEATURES.md) for the full column-by-column reference.

## The model: Random Forest

### Why not a single decision tree

A decision tree predicts by asking a sequence of yes/no questions about a team's features (e.g. *"Is Elo > 1850? → Does it have a prior title? → Is it hosting?"*) until it lands in one leaf, where `P(win)` is just the win rate of training rows in that leaf.

The problem: with only 22 championship examples, one tree happily memorizes noise — a branch might exist purely because it perfectly separates "Germany 2014" from everything else, which is a coincidence, not a pattern. That tree looks great on the data it was trained on and falls apart on a held-out tournament.

### Why a forest fixes it

A random forest trains many trees (300 here), each on a random bootstrap sample of the training rows and a random subset of features at each split, then **averages** their predicted probabilities. Any one tree's overfit quirk gets diluted out by the other 299 trees that didn't see that same quirk — variance goes down without needing more data. This is the classic bagging (bootstrap aggregating) argument, and it's the reason the shipped model is a forest rather than one tree. A walk-through with toy trees and diagrams is in [`docs/decision_tree_vs_ensemble.md`](docs/decision_tree_vs_ensemble.md).

### Configuration ([`src/model.py`](src/model.py))

```python
RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    min_samples_leaf=2,
    class_weight="balanced",   # 22 positives vs ~500 negatives
    random_state=42,
)
```

- **Training window:** WC years ≥ 2006 (the first year the SofaScore advanced stats exist).
- **Sample weighting:** recency-weighted by default — each row's weight decays with an 8-year half-life referenced to 2022, so 2022 counts most and 2006 least. (`--equal-tournament-weights` disables this and weights every WC edition equally instead.)
- **Feature weighting:** `fifa_rank_score` is up-weighted 4x (FIFA rank is a strong, low-noise prior), `is_host` is down-weighted to 0.25x (host advantage is real but shouldn't dominate), and the four SofaScore advanced stats are weighted 0.5x each (noisier, more incomplete coverage).
- Gradient boosting was tried and dropped — it was unstable on this small a positive-class window.

## Validation: leave-one-World-Cup-out cross-validation

Standard k-fold CV would leak information (rows from the same tournament aren't independent — exactly one team wins). Instead, for each of the 22 historical WCs: train on the other 21, predict + rank that year's entrants, and check whether the actual champion landed in the top 1 / top 3 / top 5 of the model's ranking. Metrics tracked: top-1/3/5 hit rate, mean rank of the true champion, and log-loss.

## Bonus: group-stage simulation

[`simulate_group_stage.py`](scripts/simulate_group_stage.py) runs a 10,000-trial Monte Carlo simulation of just the group stage (not the bracket) using the same feature set, with a logistic-regression-on-feature-diffs match model and Poisson-distributed goals. Output: each team's `P(win group)` and `P(finish top 2)` for all 12 groups — see [`docs/GROUP_STAGE_SIMULATION.md`](docs/GROUP_STAGE_SIMULATION.md).

## Running it

```bash
python scripts/build_wc_inputs.py
python scripts/scrape_2026_teams.py
python scripts/build_team_aliases.py
python scripts/train_and_predict.py --save-features
```

See [`docs/DATA_PIPELINE.md`](docs/DATA_PIPELINE.md) for what each step writes and [`docs/SOFASCORE.md`](docs/SOFASCORE.md) for pulling the advanced-stats data.

## Docs

- [`PLAN.md`](PLAN.md) — original design doc: data sources, full feature list, honest accuracy expectations
- [`docs/FEATURES.md`](docs/FEATURES.md) — every feature column, in detail
- [`docs/decision_tree_vs_ensemble.md`](docs/decision_tree_vs_ensemble.md) — single tree vs. forest, with diagrams
- [`docs/DATA_PIPELINE.md`](docs/DATA_PIPELINE.md) — pipeline steps and outputs
- [`docs/SOFASCORE.md`](docs/SOFASCORE.md) — advanced-stats scraper
- [`docs/GROUP_STAGE_SIMULATION.md`](docs/GROUP_STAGE_SIMULATION.md) — group-stage Monte Carlo results
