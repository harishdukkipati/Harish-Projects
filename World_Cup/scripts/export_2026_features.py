#!/usr/bin/env python3
"""Write data/processed/team_{year}_features.csv for inspection."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PHASE1 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHASE1))

from src.features import save_model_year_features, save_year_features  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--years",
        type=int,
        nargs="+",
        default=[2006, 2010, 2014, 2018, 2022, 2026],
        help="WC years to export (default: 2006 2010 2014 2018 2022 2026)",
    )
    ap.add_argument(
        "--model-only",
        action="store_true",
        help="Also write team_{year}_model_features.csv (FEATURE_COLS only)",
    )
    args = ap.parse_args()
    for year in args.years:
        path = save_year_features(year)
        print(f"Wrote {path}")
        if args.model_only or year == 2026:
            model_path = save_model_year_features(year)
            print(f"Wrote {model_path}")


if __name__ == "__main__":
    main()
