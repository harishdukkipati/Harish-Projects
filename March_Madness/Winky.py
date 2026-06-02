from pathlib import Path

import pandas as pd

from March_Madness.src.features import MatchupFeaturesConfig, build_matchup_frame
from March_Madness.src.model import predict_matchups


DATA_DIR = Path(__file__).resolve().parent / "data" / "archive 2"


def load_round1_matchups_with_features(year: int = 2026) -> pd.DataFrame:
    """
    Load round-of-64 tournament matchups for a given year, join in resume / rating
    data, and build matchup-level features ready for the trained logistic model.
    """
    matchups = pd.read_csv(DATA_DIR / "Tournament Matchups.csv")
    resumes = pd.read_csv(DATA_DIR / "Resumes.csv")

    mask = (matchups["YEAR"] == year) & (matchups["CURRENT ROUND"] == 64)
    matchups_year = matchups.loc[mask].copy()

    feats = build_matchup_frame(matchups_year, resumes, MatchupFeaturesConfig())
    return feats


def main() -> None:
    """
    End-to-end: load 2026 round-of-64 matchups, build features, apply the
    trained logistic regression model, and print win probabilities.
    """
    feats = load_round1_matchups_with_features(year=2026)
    preds = predict_matchups(feats)

    preds = preds.sort_values("game_index")

    pd.set_option("display.max_rows", None)
    pd.set_option("display.width", 140)

    print(
        preds[
            [
                "game_index",
                "team_a",
                "seed_a",
                "team_b",
                "seed_b",
                "prob_team_a_wins_model",
                "prob_team_b_wins_model",
            ]
        ]
    )


if __name__ == "__main__":
    main()
