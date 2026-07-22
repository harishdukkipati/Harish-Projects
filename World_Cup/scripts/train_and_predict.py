#!/usr/bin/env python3
"""
Step 5: Build features, leave-one-WC-out CV (Random Forest), rank 2026 teams.

Usage (from phase_1):
  ../../venv/bin/python scripts/train_and_predict.py
  ../../venv/bin/python scripts/train_and_predict.py --save-features

From scripts/ directory:
  python3 train_and_predict.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PHASE1 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHASE1))

from src.features import (  # noqa: E402
    DEFAULT_ADVANCED_WEIGHT,
    DEFAULT_FIFA_SCORE_WEIGHT,
    DEFAULT_HOST_WEIGHT,
    build_2026_frame,
    build_training_frame,
    save_training_frame,
)
from src.model import (  # noqa: E402
    DEFAULT_MIN_YEAR,
    DEFAULT_RECENCY_HALF_LIFE,
    describe_tournament_weights,
    normalize_top_n_probs,
    predict_teams,
    run_cv,
    train_full,
)

TOP_N_DISPLAY = 32


def _print_cv(res) -> None:
    print(f"\n=== RandomForest — leave-one-WC-out CV ({res.n_folds} folds) ===")
    print(f"  Top-1 champion: {res.top1_hits}/{res.n_folds} ({100*res.top1_hits/res.n_folds:.1f}%)")
    print(f"  Top-3 champion: {res.top3_hits}/{res.n_folds} ({100*res.top3_hits/res.n_folds:.1f}%)")
    print(f"  Top-5 champion: {res.top5_hits}/{res.n_folds} ({100*res.top5_hits/res.n_folds:.1f}%)")
    print(f"  Mean rank of true champion: {res.mean_champion_rank:.2f}")
    print(f"  Mean log-loss: {res.mean_log_loss:.4f}")
    print("  Recent folds:")
    for d in res.fold_details[-5:]:
        print(
            f"    {d['year']}: champ={d['champion']} rank={d['champion_rank']}  "
            f"top3={[t['team'] for t in d['top3']]}"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--save-features", action="store_true", help="Write data/processed/team_year_features.csv")
    ap.add_argument(
        "--recency-half-life",
        type=float,
        default=DEFAULT_RECENCY_HALF_LIFE,
        metavar="YEARS",
        help=f"Up-weight recent WCs: weight halves every N years (ref 2022). "
        f"Default {DEFAULT_RECENCY_HALF_LIFE:g} (2006 lightest → 2022 heaviest).",
    )
    ap.add_argument(
        "--equal-tournament-weights",
        action="store_true",
        help="Equal total weight per WC edition (disables recency weighting).",
    )
    ap.add_argument(
        "--uniform-row-weights",
        action="store_true",
        help="One weight per row (no per-tournament normalization). "
        "Differs from default only if editions have different team counts.",
    )
    ap.add_argument(
        "--min-year",
        type=int,
        default=DEFAULT_MIN_YEAR,
        help=f"Drop WC editions before this year (default {DEFAULT_MIN_YEAR}: 2006–2022).",
    )
    ap.add_argument(
        "--fifa-score-weight",
        "--fifa-rank-weight",
        type=float,
        default=DEFAULT_FIFA_SCORE_WEIGHT,
        dest="fifa_score_weight",
        help=f"Emphasize fifa_rank_score (=1/rank) in the model (default {DEFAULT_FIFA_SCORE_WEIGHT:g}).",
    )
    ap.add_argument(
        "--host-weight",
        type=float,
        default=DEFAULT_HOST_WEIGHT,
        help=f"Emphasize is_host in the model (default {DEFAULT_HOST_WEIGHT:g}).",
    )
    ap.add_argument(
        "--advanced-weight",
        type=float,
        default=DEFAULT_ADVANCED_WEIGHT,
        help=f"Emphasize SofaScore advanced stats (default {DEFAULT_ADVANCED_WEIGHT:g}).",
    )
    args = ap.parse_args()

    half_life = None if args.equal_tournament_weights else args.recency_half_life
    equal_tournament = not args.uniform_row_weights
    min_year = args.min_year
    fifa_score_weight = args.fifa_score_weight
    host_weight = args.host_weight
    advanced_weight = args.advanced_weight

    print("Building training features (1930–2022)...")
    train_df = build_training_frame()
    print(f"  {len(train_df)} rows, {int(train_df['label'].sum())} champions")
    print(
        "  Model: RandomForest (class_weight=balanced) — strength/form + opponent Elo SOS + advanced + host + confederation"
    )
    print("  Excluded from features: WC pedigree, defending-champion flags")
    print(f"  Training window: year >= {min_year}")
    print(f"  fifa_rank_score (= 1 / FIFA rank), feature weight {fifa_score_weight:g}x")
    print(f"  is_host, feature weight {host_weight:g}x")
    print(f"  SofaScore advanced cols, feature weight {advanced_weight:g}x")

    train_slice = train_df[train_df["year"] >= min_year] if min_year else train_df
    if half_life is not None:
        print(f"  Sample weights: recency half-life={half_life:g} years (ref=2022)")
    elif equal_tournament:
        print("  Sample weights: equal per WC edition (no recency bias)")
    else:
        print("  Sample weights: uniform per team row")
    wtab = describe_tournament_weights(
        train_slice,
        half_life_years=half_life,
        equal_tournament_years=equal_tournament,
    )
    for _, r in wtab.iterrows():
        print(f"    {int(r['year'])}: relative tournament weight ~{r['tournament_weight_sum']:.2f}")

    if args.save_features:
        path = save_training_frame()
        print(f"  Saved {path}")

    kw = dict(
        half_life_years=half_life,
        min_year=min_year,
        equal_tournament_years=equal_tournament,
        fifa_score_weight=fifa_score_weight,
        host_weight=host_weight,
        advanced_weight=advanced_weight,
    )
    cv = run_cv(train_df, **kw)
    _print_cv(cv)

    print("\nTraining Random Forest on all historical WCs in window...")
    model = train_full(train_df, **kw)

    print("Building 2026 features...")
    pred_2026 = build_2026_frame()
    ranked = predict_teams(
        model,
        pred_2026,
        fifa_score_weight=fifa_score_weight,
        host_weight=host_weight,
        advanced_weight=advanced_weight,
    )
    ranked = normalize_top_n_probs(ranked, top_n=TOP_N_DISPLAY)
    top32 = ranked.head(TOP_N_DISPLAY)

    print("\n=== 2026 World Cup champion pick (random_forest) ===")
    top = ranked.iloc[0]
    print(
        f"  Predicted champion: {top['team']}  "
        f"(win share={top['pred_prob']:.4f} among top {TOP_N_DISPLAY})"
    )
    print(f"\n  Top {TOP_N_DISPLAY} (normalized win shares, sum = {top32['pred_prob'].sum():.4f}):")
    for _, row in top32.iterrows():
        print(f"    {int(row['rank']):2d}. {row['team']:<22s}  {row['pred_prob']:.4f}")


if __name__ == "__main__":
    main()
