"""Head-to-head match model using the same FEATURE_COLS as the champion classifier."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from . import load_data as ld
from .features import (
    ADVANCED_COLS,
    DEFAULT_ADVANCED_WEIGHT,
    DEFAULT_FIFA_SCORE_WEIGHT,
    DEFAULT_HOST_WEIGHT,
    FEATURE_COLS,
    _conf_one_hot,
    _host_flags,
    _impute_features,
    _last12mo_form,
    _lookup_advanced_features,
    _pre_wc_elo,
    _pre_wc_fifa_rank,
    _team_confederation,
    _elo_lookup_index,
    fifa_rank_score,
)
from .model import apply_feature_weights

# Poisson scaling: map P(team_a wins) + goal rates → expected goals (keeps draws).
POISSON_BASE = 1.35


def _feature_year_for_cutoff(cutoff: pd.Timestamp) -> int:
    if cutoff >= pd.Timestamp("2026-06-11"):
        return 2026
    wc_starts = ld.load_wc_start_dates()
    prior = [y for y, start in wc_starts.items() if start < cutoff]
    return max(prior) if prior else 2022


def build_features_at(
    team: str,
    cutoff: pd.Timestamp,
    *,
    fifa_rank_override: Optional[float] = None,
    neutral_site: bool = True,
) -> Dict[str, object]:
    """Pre-match feature row aligned with FEATURE_COLS (no pedigree / label)."""
    aliases = ld.load_aliases()
    team = ld.normalize_team(team, aliases)
    feature_year = _feature_year_for_cutoff(cutoff)

    elo = ld.load_elo().copy()
    elo["team"] = elo["team"].astype(str).map(lambda x: ld.normalize_team(x, aliases))
    fifa = ld.load_fifa_rankings()
    fifa_map = ld.fifa_name_map()
    results = ld.load_all_results()
    results = results[results["date"] < cutoff].copy()
    for c in ("home_team", "away_team"):
        results[c] = results[c].astype(str).map(lambda x: ld.normalize_team(x, aliases))

    conf = _team_confederation(team, cutoff, fifa, fifa_map)
    fifa_rank = (
        fifa_rank_override
        if fifa_rank_override is not None
        else _pre_wc_fifa_rank(team, cutoff, fifa, fifa_map)
    )
    row: Dict[str, object] = {
        "team": team,
        "pre_wc_elo": _pre_wc_elo(team, cutoff, elo),
        "pre_wc_fifa_rank": fifa_rank,
        "fifa_rank_score": fifa_rank_score(fifa_rank),
    }
    row.update(_last12mo_form(team, cutoff, results, elo_lookup=_elo_lookup_index()))
    row.update(_lookup_advanced_features(team, feature_year))
    if neutral_site:
        row["is_host"] = 0.0
        row["host_confederation_match"] = 0.0
    else:
        row.update(_host_flags(team, feature_year, conf))
    row.update(_conf_one_hot(conf))
    return row


def _matchup_diff_row(
    feats_a: Dict[str, object],
    feats_b: Dict[str, object],
) -> np.ndarray:
    """Feature difference (team_a minus team_b) in FEATURE_COLS order."""
    diff = []
    for col in FEATURE_COLS:
        a = float(feats_a.get(col, np.nan))
        b = float(feats_b.get(col, np.nan))
        diff.append(a - b)
    return np.asarray(diff, dtype=float)


@lru_cache(maxsize=1)
def _teams_2026_fifa() -> Dict[str, float]:
    return {ld.normalize_team(t): float(r) for t, r in ld.load_teams_2026()}


def build_training_matchups(
    *,
    min_year: int = 2010,
    max_matches: int = 25_000,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build (X, y) for logistic match model from international results.
    y=1 if team_a (listed first / home) wins; draws excluded.
    """
    aliases = ld.load_aliases()
    results = ld.load_all_results().copy()
    results = results[results["date"].dt.year >= min_year]
    for c in ("home_team", "away_team"):
        results[c] = results[c].astype(str).map(lambda x: ld.normalize_team(x, aliases))
    results = results.sort_values("date")

    if len(results) > max_matches:
        results = results.iloc[-max_matches:]

    fifa_2026 = _teams_2026_fifa()
    rows_x: list[np.ndarray] = []
    rows_y: list[int] = []

    for _, g in results.iterrows():
        home = str(g["home_team"])
        away = str(g["away_team"])
        hs, as_ = int(g["home_score"]), int(g["away_score"])
        if hs == as_:
            continue
        cutoff = pd.Timestamp(g["date"])
        y = 1 if hs > as_ else 0
        fh = build_features_at(
            home,
            cutoff,
            fifa_rank_override=fifa_2026.get(home),
            neutral_site=False,
        )
        fa = build_features_at(
            away,
            cutoff,
            fifa_rank_override=fifa_2026.get(away),
            neutral_site=False,
        )
        rows_x.append(_matchup_diff_row(fh, fa))
        rows_y.append(y)

    if not rows_x:
        raise ValueError("No training matchups built")

    X = np.vstack(rows_x)
    y = np.asarray(rows_y, dtype=int)
    medians = np.nanmedian(X, axis=0)
    inds = np.where(np.isnan(X))
    X[inds] = np.take(medians, inds[1])
    return X, y


class MatchupModel:
    """Logistic model on weighted FEATURE_COLS diffs (team_a − team_b)."""

    def __init__(
        self,
        *,
        fifa_score_weight: float = DEFAULT_FIFA_SCORE_WEIGHT,
        host_weight: float = DEFAULT_HOST_WEIGHT,
        advanced_weight: float = DEFAULT_ADVANCED_WEIGHT,
        min_train_year: int = 2010,
        max_train_matches: int = 25_000,
    ) -> None:
        self.fifa_score_weight = fifa_score_weight
        self.host_weight = host_weight
        self.advanced_weight = advanced_weight
        self.min_train_year = min_train_year
        self.max_train_matches = max_train_matches
        self.clf = LogisticRegression(max_iter=2000, class_weight="balanced")
        self._fitted = False

    def fit(self) -> "MatchupModel":
        X, y = build_training_matchups(
            min_year=self.min_train_year,
            max_matches=self.max_train_matches,
        )
        X_w = apply_feature_weights(
            X,
            fifa_score_weight=self.fifa_score_weight,
            host_weight=self.host_weight,
            advanced_weight=self.advanced_weight,
        )
        self.clf.fit(X_w, y)
        self._fitted = True
        return self

    def p_team_a_wins(
        self,
        feats_a: np.ndarray,
        feats_b: np.ndarray,
    ) -> float:
        """Probability team_a beats team_b (excludes draw mass)."""
        if not self._fitted:
            self.fit()
        diff = np.asarray(feats_a, dtype=float) - np.asarray(feats_b, dtype=float)
        X_w = apply_feature_weights(
            diff.reshape(1, -1),
            fifa_score_weight=self.fifa_score_weight,
            host_weight=self.host_weight,
            advanced_weight=self.advanced_weight,
        )
        return float(self.clf.predict_proba(X_w)[0, 1])

    def expected_goals(
        self,
        feats_a: np.ndarray,
        feats_b: np.ndarray,
        *,
        p_win: Optional[float] = None,
    ) -> Tuple[float, float]:
        """
        Poisson expected goals from FEATURE_COLS (same columns as classifier).
        Uses goals-for/against per match + win probability for calibration.
        """
        idx = {c: i for i, c in enumerate(FEATURE_COLS)}
        gf_a = max(0.35, float(feats_a[idx["last12mo_goals_for_per_match"]]))
        ga_a = max(0.35, float(feats_a[idx["last12mo_goals_against_per_match"]]))
        gf_b = max(0.35, float(feats_b[idx["last12mo_goals_for_per_match"]]))
        ga_b = max(0.35, float(feats_b[idx["last12mo_goals_against_per_match"]]))
        p = p_win if p_win is not None else self.p_team_a_wins(feats_a, feats_b)
        # Symmetric lambdas: stronger attack vs weaker defense, tilt by matchup logit.
        tilt = 0.35 * (p - 0.5)
        lam_a = POISSON_BASE * (0.5 * (gf_a + ga_b)) * np.exp(tilt)
        lam_b = POISSON_BASE * (0.5 * (gf_b + ga_a)) * np.exp(-tilt)
        return max(0.2, float(lam_a)), max(0.2, float(lam_b))


def team_feature_matrix(feats_df: pd.DataFrame) -> Dict[str, np.ndarray]:
    """Imputed FEATURE_COLS vectors keyed by team name."""
    out: Dict[str, np.ndarray] = {}
    for _, row in feats_df.iterrows():
        out[str(row["team"])] = row[FEATURE_COLS].to_numpy(dtype=float)
    return out
