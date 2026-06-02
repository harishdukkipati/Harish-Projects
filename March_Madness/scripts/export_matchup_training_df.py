#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.matchup_model import export_training_df  # noqa: E402


def main() -> None:
    out = ROOT / "data" / "derived" / "matchup_training_df_2008_2025.csv"
    export_training_df(out)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

