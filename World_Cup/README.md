# World Cup Predictor

Predicts the 2026 World Cup **champion** — a ranked probability `P(team wins WC 2026)` for all 48 entrants, no bracket simulation. A per-team-per-tournament classifier trained on 1930–2022 World Cup winners and pre-tournament features (ELO, FIFA rank, recent form, pedigree).

See [`phase_1/PLAN.md`](phase_1/PLAN.md) for the full methodology and [`phase_1/docs/`](phase_1/docs) for the data pipeline, feature list, and model notes.

## Result

Top of the final probability ranking (2026 slate): Spain, France, Argentina, England as the top 4 — matching the actual semifinal field, with Spain predicted (and confirmed) champion.

## Running it

```bash
cd phase_1
python scripts/build_wc_inputs.py
python scripts/scrape_2026_teams.py
python scripts/build_team_aliases.py
python scripts/train_and_predict.py --save-features
```

See [`phase_1/docs/DATA_PIPELINE.md`](phase_1/docs/DATA_PIPELINE.md) for what each step writes.
