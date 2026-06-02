from __future__ import annotations

from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split

from .features import MatchupFeaturesConfig, build_matchup_frame


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "archive 2"
MODELS_DIR = BASE_DIR / "models"


def _load_historical_matchups(years: Tuple[int, ...]) -> pd.DataFrame:
    """
    Load tournament matchups and resumes for the given years and build
    matchup-level features.
    """
    matchups = pd.read_csv(DATA_DIR / "Tournament Matchups.csv")
    resumes = pd.read_csv(DATA_DIR / "Resumes.csv")

    mask = matchups["YEAR"].isin(years) & (matchups["CURRENT ROUND"] == 64)
    matchups_round1 = matchups.loc[mask].copy()

    feats = build_matchup_frame(matchups_round1, resumes, MatchupFeaturesConfig())
    return feats


def train_logistic_regression(output_path: Path | None = None) -> Tuple[LogisticRegression, float, float]:
    """
    Train a baseline logistic regression model to predict whether team_a wins.

    Since we do not have game-level outcomes directly in this Kaggle bundle,
    we approximate labels using seed-based historical championship probabilities
    as a proxy target for demonstration purposes.

    Returns
    -------
    model, accuracy, log_loss
    """
    feats = _load_historical_matchups(years=(2010, 2011, 2012, 2013, 2014, 2015))

    # Synthetic target:
    # y = 1 if team_a is the better seed, 0 otherwise.
    # To get both classes, also include the mirrored perspective.
    feats = feats.dropna()
    y_primary = (feats["seed_a"] < feats["seed_b"]).astype(int)

    feats_mirror = feats.copy()
    feats_mirror[["seed_a", "seed_b"]] = feats_mirror[["seed_b", "seed_a"]].to_numpy()
    for col in ["RESUME_diff", "ELO_diff", "B POWER_diff", "R SCORE_diff"]:
        if col in feats_mirror.columns:
            feats_mirror[col] = -feats_mirror[col]
    y_mirror = (feats_mirror["seed_a"] < feats_mirror["seed_b"]).astype(int)

    feats_all = pd.concat([feats, feats_mirror], ignore_index=True)
    y = pd.concat([y_primary, y_mirror], ignore_index=True)

    feature_cols = [
        "seed_diff",
        "seed_abs_diff",
        "RESUME_diff",
        "ELO_diff",
        "B POWER_diff",
        "R SCORE_diff",
    ]
    feature_cols = [c for c in feature_cols if c in feats_all.columns]

    X = feats_all[feature_cols].to_numpy(dtype=float)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    ll = float(log_loss(y_test, y_prob))

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        output_path = MODELS_DIR / "round1_logit.pkl"
    joblib.dump({"model": clf, "feature_cols": feature_cols}, output_path)

    return clf, acc, ll


def load_trained_model(model_path: Path | None = None):
    if model_path is None:
        model_path = MODELS_DIR / "round1_logit.pkl"
    bundle = joblib.load(model_path)
    return bundle["model"], bundle["feature_cols"]


def predict_matchups(feats: pd.DataFrame, model_path: Path | None = None) -> pd.DataFrame:
    """
    Given a matchup-level feature frame, add model-based win probabilities.
    """
    model, feature_cols = load_trained_model(model_path)
    X = feats[feature_cols].to_numpy(dtype=float)
    probs = model.predict_proba(X)[:, 1]
    out = feats.copy()
    out["prob_team_a_wins_model"] = probs
    out["prob_team_b_wins_model"] = 1.0 - probs
    return out


if __name__ == "__main__":
    clf, acc, ll = train_logistic_regression()
    print(f"Baseline logistic regression trained. Accuracy={acc:.3f}, LogLoss={ll:.3f}")

