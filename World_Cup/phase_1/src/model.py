"""Train / evaluate RandomForest champion classifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss

from .features import (
    DEFAULT_ADVANCED_WEIGHT,
    DEFAULT_FIFA_SCORE_WEIGHT,
    DEFAULT_HOST_WEIGHT,
    FEATURE_COLS,
    feature_weight_vector,
)

MODEL_NAME = "random_forest"

# Training window: SofaScore historical CSVs from 2006 onward.
DEFAULT_MIN_YEAR = 2006
# Recency: weight halves every N years before ref 2022 (2006 < 2010 < … < 2022).
DEFAULT_RECENCY_HALF_LIFE = 8.0


def recency_sample_weights(
    years: np.ndarray,
    *,
    reference_year: int = 2022,
    half_life_years: float = 12.0,
) -> np.ndarray:
    """
    Exponential decay by WC year: weight = 0.5^((ref_year - year) / half_life).
    Normalized to mean 1 so overall loss scale stays comparable.
    """
    if half_life_years <= 0:
        raise ValueError("half_life_years must be positive")
    years_f = np.asarray(years, dtype=float)
    age = np.maximum(0.0, reference_year - years_f)
    w = np.power(0.5, age / half_life_years)
    return w / float(w.mean())


def equal_tournament_year_weights(years: np.ndarray) -> np.ndarray:
    """
    Each WC edition contributes equal total weight (1 / n_teams_that_year per row).
    Use when comparing tournaments without favoring more recent years.
    """
    years_arr = np.asarray(years)
    _, inv = np.unique(years_arr, return_inverse=True)
    counts = np.bincount(inv)
    w = 1.0 / counts[inv].astype(float)
    return w / float(w.mean())


def feature_matrix(df: pd.DataFrame) -> np.ndarray:
    """Model inputs (fifa_rank_score = 1 / FIFA rank)."""
    return df[FEATURE_COLS].to_numpy(dtype=float)


def apply_feature_weights(
    X: np.ndarray,
    *,
    fifa_score_weight: float = DEFAULT_FIFA_SCORE_WEIGHT,
    fifa_rank_weight: Optional[float] = None,
    host_weight: float = DEFAULT_HOST_WEIGHT,
    advanced_weight: float = DEFAULT_ADVANCED_WEIGHT,
) -> np.ndarray:
    if fifa_rank_weight is not None:
        fifa_score_weight = fifa_rank_weight
    w = feature_weight_vector(
        fifa_score_weight=fifa_score_weight,
        fifa_rank_weight=fifa_rank_weight,
        host_weight=host_weight,
        advanced_weight=advanced_weight,
    )
    return np.asarray(X, dtype=float) * w


def weights_for_frame(
    df: pd.DataFrame,
    *,
    half_life_years: Optional[float] = DEFAULT_RECENCY_HALF_LIFE,
    reference_year: int = 2022,
    min_year: Optional[int] = DEFAULT_MIN_YEAR,
    equal_tournament_years: bool = True,
) -> Tuple[pd.DataFrame, Optional[np.ndarray]]:
    """
    Optionally drop old years; return (filtered_df, sample_weight or None).

    Default: recency weights (half-life DEFAULT_RECENCY_HALF_LIFE, ref 2022).
    Pass half_life_years=None for equal weight per WC edition instead.
    """
    out = df
    if min_year is not None:
        out = out[out["year"] >= min_year].copy()
    if half_life_years is not None:
        w = recency_sample_weights(
            out["year"].to_numpy(),
            reference_year=reference_year,
            half_life_years=half_life_years,
        )
        return out, w
    if equal_tournament_years:
        w = equal_tournament_year_weights(out["year"].to_numpy())
        return out, w
    return out, None


@dataclass
class CVResult:
    model_name: str
    top1_hits: int
    top3_hits: int
    top5_hits: int
    n_folds: int
    mean_champion_rank: float
    mean_log_loss: float
    fold_details: List[Dict[str, object]]


def _make_model() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )


def _fit_model(
    X: np.ndarray,
    y: np.ndarray,
    sample_weight: Optional[np.ndarray] = None,
    *,
    fifa_score_weight: float = DEFAULT_FIFA_SCORE_WEIGHT,
    fifa_rank_weight: Optional[float] = None,
    host_weight: float = DEFAULT_HOST_WEIGHT,
    advanced_weight: float = DEFAULT_ADVANCED_WEIGHT,
) -> RandomForestClassifier:
    X_w = apply_feature_weights(
        X,
        fifa_score_weight=fifa_score_weight,
        fifa_rank_weight=fifa_rank_weight,
        host_weight=host_weight,
        advanced_weight=advanced_weight,
    )
    clf = _make_model()
    clf.fit(X_w, y, sample_weight=sample_weight)
    return clf


def _predict_proba(
    model: RandomForestClassifier,
    X: np.ndarray,
    *,
    fifa_score_weight: float = DEFAULT_FIFA_SCORE_WEIGHT,
    fifa_rank_weight: Optional[float] = None,
    host_weight: float = DEFAULT_HOST_WEIGHT,
    advanced_weight: float = DEFAULT_ADVANCED_WEIGHT,
) -> np.ndarray:
    X_w = apply_feature_weights(
        X,
        fifa_score_weight=fifa_score_weight,
        fifa_rank_weight=fifa_rank_weight,
        host_weight=host_weight,
        advanced_weight=advanced_weight,
    )
    return model.predict_proba(X_w)[:, 1]


def leave_one_wc_out_cv(
    df: pd.DataFrame,
    *,
    half_life_years: Optional[float] = DEFAULT_RECENCY_HALF_LIFE,
    min_year: Optional[int] = DEFAULT_MIN_YEAR,
    equal_tournament_years: bool = True,
    fifa_score_weight: float = DEFAULT_FIFA_SCORE_WEIGHT,
    fifa_rank_weight: Optional[float] = None,
    host_weight: float = DEFAULT_HOST_WEIGHT,
    advanced_weight: float = DEFAULT_ADVANCED_WEIGHT,
) -> CVResult:
    if fifa_rank_weight is not None:
        fifa_score_weight = fifa_rank_weight
    train_df, _ = weights_for_frame(
        df,
        half_life_years=half_life_years,
        min_year=min_year,
        equal_tournament_years=equal_tournament_years,
    )
    years = sorted(train_df["year"].unique())

    top1 = top3 = top5 = 0
    ranks: List[float] = []
    losses: List[float] = []
    details: List[Dict[str, object]] = []

    for test_year in years:
        train_mask = train_df["year"] != test_year
        test_mask = train_df["year"] == test_year
        train_part = train_df.loc[train_mask]
        X_train = feature_matrix(train_part)
        y_train = train_part["label"].to_numpy(dtype=int)
        sw_train = None
        if half_life_years is not None:
            sw_train = recency_sample_weights(
                train_part["year"].to_numpy(),
                half_life_years=half_life_years,
            )
        elif equal_tournament_years and len(train_part) > 0:
            sw_train = equal_tournament_year_weights(train_part["year"].to_numpy())
        test_df = train_df.loc[test_mask].copy()

        model = _fit_model(
            X_train,
            y_train,
            sample_weight=sw_train,
            fifa_score_weight=fifa_score_weight,
            host_weight=host_weight,
            advanced_weight=advanced_weight,
        )
        probs = _predict_proba(
            model,
            feature_matrix(test_df),
            fifa_score_weight=fifa_score_weight,
            host_weight=host_weight,
            advanced_weight=advanced_weight,
        )
        test_df = test_df.assign(pred_prob=probs)
        test_df = test_df.sort_values("pred_prob", ascending=False)

        champ_row = test_df[test_df["label"] == 1]
        if champ_row.empty:
            continue
        champ = champ_row.iloc[0]
        champ_team = champ["team"]
        rank = int(test_df.reset_index(drop=True).index[test_df["team"] == champ_team][0]) + 1
        ranks.append(rank)

        if rank == 1:
            top1 += 1
        if rank <= 3:
            top3 += 1
        if rank <= 5:
            top5 += 1

        y_test = test_df["label"].to_numpy(dtype=int)
        p_test = np.clip(test_df["pred_prob"].to_numpy(dtype=float), 1e-6, 1 - 1e-6)
        losses.append(log_loss(y_test, p_test, labels=[0, 1]))

        details.append(
            {
                "year": int(test_year),
                "champion": champ_team,
                "champion_rank": rank,
                "top3": test_df.head(3)[["team", "pred_prob"]].to_dict("records"),
            }
        )

    n = len(details)
    return CVResult(
        model_name=MODEL_NAME,
        top1_hits=top1,
        top3_hits=top3,
        top5_hits=top5,
        n_folds=n,
        mean_champion_rank=float(np.mean(ranks)) if ranks else float("nan"),
        mean_log_loss=float(np.mean(losses)) if losses else float("nan"),
        fold_details=details,
    )


def train_full(
    df: pd.DataFrame,
    *,
    half_life_years: Optional[float] = DEFAULT_RECENCY_HALF_LIFE,
    min_year: Optional[int] = DEFAULT_MIN_YEAR,
    equal_tournament_years: bool = True,
    fifa_score_weight: float = DEFAULT_FIFA_SCORE_WEIGHT,
    fifa_rank_weight: Optional[float] = None,
    host_weight: float = DEFAULT_HOST_WEIGHT,
    advanced_weight: float = DEFAULT_ADVANCED_WEIGHT,
) -> RandomForestClassifier:
    if fifa_rank_weight is not None:
        fifa_score_weight = fifa_rank_weight
    train_df, w = weights_for_frame(
        df,
        half_life_years=half_life_years,
        min_year=min_year,
        equal_tournament_years=equal_tournament_years,
    )
    X = feature_matrix(train_df)
    y = train_df["label"].to_numpy(dtype=int)
    return _fit_model(
        X,
        y,
        sample_weight=w,
        fifa_score_weight=fifa_score_weight,
        host_weight=host_weight,
        advanced_weight=advanced_weight,
    )


def predict_teams(
    model: RandomForestClassifier,
    df: pd.DataFrame,
    *,
    year: int = 2026,
    fifa_score_weight: float = DEFAULT_FIFA_SCORE_WEIGHT,
    fifa_rank_weight: Optional[float] = None,
    host_weight: float = DEFAULT_HOST_WEIGHT,
    advanced_weight: float = DEFAULT_ADVANCED_WEIGHT,
) -> pd.DataFrame:
    if fifa_rank_weight is not None:
        fifa_score_weight = fifa_rank_weight
    X = feature_matrix(df)
    probs = _predict_proba(
        model,
        X,
        fifa_score_weight=fifa_score_weight,
        fifa_rank_weight=fifa_rank_weight,
        host_weight=host_weight,
        advanced_weight=advanced_weight,
    )
    out = df[["team", "year"]].copy()
    out["raw_prob"] = probs
    out["pred_prob"] = probs
    out = out.sort_values("pred_prob", ascending=False).reset_index(drop=True)
    out["rank"] = np.arange(1, len(out) + 1)
    return out


def normalize_top_n_probs(ranked: pd.DataFrame, top_n: int = 32) -> pd.DataFrame:
    """
    Renormalize raw RF scores so pred_prob over the top_n rows sums to 1.
    Keeps raw_prob unchanged; overwrites pred_prob on those rows only.
    """
    out = ranked.copy()
    if "raw_prob" not in out.columns:
        out["raw_prob"] = out["pred_prob"].astype(float)
    n = min(top_n, len(out))
    idx = out.index[:n]
    total = float(out.loc[idx, "raw_prob"].sum())
    if total > 0:
        out.loc[idx, "pred_prob"] = out.loc[idx, "raw_prob"] / total
    return out


def run_cv(
    train_df: pd.DataFrame,
    *,
    half_life_years: Optional[float] = DEFAULT_RECENCY_HALF_LIFE,
    min_year: Optional[int] = DEFAULT_MIN_YEAR,
    equal_tournament_years: bool = True,
    fifa_score_weight: float = DEFAULT_FIFA_SCORE_WEIGHT,
    fifa_rank_weight: Optional[float] = None,
    host_weight: float = DEFAULT_HOST_WEIGHT,
    advanced_weight: float = DEFAULT_ADVANCED_WEIGHT,
) -> CVResult:
    """Leave-one-WC-out CV for the Random Forest model."""
    return leave_one_wc_out_cv(
        train_df,
        half_life_years=half_life_years,
        min_year=min_year,
        equal_tournament_years=equal_tournament_years,
        fifa_score_weight=fifa_score_weight,
        fifa_rank_weight=fifa_rank_weight,
        host_weight=host_weight,
        advanced_weight=advanced_weight,
    )


def describe_tournament_weights(
    df: pd.DataFrame,
    *,
    half_life_years: Optional[float] = DEFAULT_RECENCY_HALF_LIFE,
    equal_tournament_years: bool = True,
) -> pd.DataFrame:
    """Per-WC-year total sample weight (sum over teams in that edition)."""
    _, w = weights_for_frame(
        df,
        min_year=None,
        half_life_years=half_life_years,
        equal_tournament_years=equal_tournament_years,
    )
    if w is None:
        w = np.ones(len(df), dtype=float)
    tmp = df[["year"]].copy()
    tmp["row_weight"] = w
    return (
        tmp.groupby("year", as_index=False)["row_weight"]
        .sum()
        .rename(columns={"row_weight": "tournament_weight_sum"})
        .sort_values("year")
    )


def describe_recency_weights(
    df: pd.DataFrame,
    *,
    half_life_years: float = 1.5,
    reference_year: int = 2022,
) -> pd.DataFrame:
    """Per-WC-year total weight (all teams in that tournament)."""
    w = recency_sample_weights(
        df["year"].to_numpy(), reference_year=reference_year, half_life_years=half_life_years
    )
    tmp = df[["year"]].copy()
    tmp["row_weight"] = w
    return (
        tmp.groupby("year", as_index=False)["row_weight"]
        .sum()
        .rename(columns={"row_weight": "tournament_weight_sum"})
        .sort_values("year")
    )
