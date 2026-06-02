#!/usr/bin/env python3
"""
Write training rows to CSVs for Sweet 16, Elite 8, Final Four, and Championship only.

Output: data/derived/by_round/
  matchup_training_round_16.csv
  matchup_training_round_8.csv
  matchup_training_round_4.csv
  matchup_training_round_2.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.matchup_model import export_training_df_by_round  # noqa: E402


def main() -> None:
    out_dir = ROOT / "data" / "derived" / "by_round"
    paths = export_training_df_by_round(out_dir)
    for p in paths:
        print(f"Wrote {p}")


if __name__ == "__main__":
    main()
