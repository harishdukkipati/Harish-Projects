"""
Build training data from historic tournament results and archive2/seed data,
train one logistic model for P(team_a wins), and expose predict_proba for bracket_sim.
Includes 2026 game-log H2H win% when the two teams played.
Tune FEATURE_COEF_MULTIPLIERS / LOGISTIC_REG_C. Huge multipliers on coef_ amplify fit noise (looks like overfitting);
smaller C = stronger L2 before those tweaks.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from . import bracket_data as bd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ARCHIVE = DATA_DIR / "archive 2"

# Lazy cache for 2026 H2H summaries from game_logs (pair -> stats)
_h2h_2026_summaries: Dict[Tuple[str, str], Tuple[float, float]] | None = None
_form_2026_index: Dict[str, List[Tuple[int, int, int]]] | None = None


def _get_h2h_2026_summaries() -> Dict[Tuple[str, str], Tuple[float, float]]:
    global _h2h_2026_summaries
    if _h2h_2026_summaries is None:
        _h2h_2026_summaries = bd.build_h2h_2026_summaries()
    return _h2h_2026_summaries


def _get_form_2026_index() -> Dict[str, List[Tuple[int, int, int]]]:
    global _form_2026_index
    if _form_2026_index is None:
        _form_2026_index = bd.build_team_form_index_2026_from_logs()
    return _form_2026_index

# Feature columns used by the model (order matters for predict)
FEATURE_COLS = [
    "seed_diff",           # seed_a - seed_b (negative = team_a better)
    "round_num",           # 64, 32, 16, 8, 4, 2
    "resume_diff",         # RESUME rank: lower is better, so we use -rank or rank_b - rank_a
    "elo_diff",
    "b_power_diff",
    "r_score_diff",
    "kadj_em_diff",
    "bart_diff",
    "preseason_em_diff",
    "seed_champ_pct_diff", # from Seed Results
    "seed_a_upset_rate_vs_seed_b",  # from Upset Seed Info (pairwise by round, smoothed)
    "season_upsets_round",          # from Upset Count (season-level, by round)
    "season_upsets_total",          # from Upset Count (season-level total)
    "h2h_win_pct",         # prior season H2H win rate (team_a); 2026 from game_logs
    "h2h_point_diff",      # mean(team_a_pts - team_b_pts) in prior meetings; 0 if none
    "last10_win_pct_diff",   # team_a minus team_b win% in last 10 games before game day
    "last10_margin_diff",    # team_a minus team_b mean margin in those games
    "path_beaten_strength_diff",  # team_a - team_b: mean(17-opp_seed) for R64+R32 victims (historic) or JSON (2026)
]

# After LogisticRegression.fit, coef[j] *= boost * dampen (default 1.0 each if column omitted).
# Upset rate ×7; non-KenPom ×2; KenPom diffs + season_upsets_* ×1 (omitted).
FEATURE_COEF_MULTIPLIERS: Dict[str, float] = {
    "seed_a_upset_rate_vs_seed_b": 7.0,
    "seed_diff": 2.0,
    "round_num": 2.0,
    "resume_diff": 2.0,
    "elo_diff": 2.0,
    "b_power_diff": 2.0,
    "r_score_diff": 2.0,
    "seed_champ_pct_diff": 2.0,
    "h2h_win_pct": 2.0,
    "h2h_point_diff": 2.0,
    "last10_win_pct_diff": 2.0,
    "last10_margin_diff": 2.0,
    "path_beaten_strength_diff": 2.0,
}

# sklearn: smaller C = stronger L2 penalty (shrink weights before FEATURE_COEF_MULTIPLIERS).
LOGISTIC_REG_C = 0.45

FEATURE_COEF_DAMPEN: Dict[str, float] = {}


def _build_upset_rate_map(seasons: List[int]) -> Dict[Tuple[int, int, int], float]:
    """Training only: historic pairwise upset rates from compact + Upset Seed Info."""
    compact = bd.load_compact_results(seasons)
    seeds_df = bd.load_tourney_seeds(seasons)
    upset_seed = bd.load_upset_seed_info()
    seed_map = (
        seeds_df[["season", "TeamID", "seed_num"]]
        .rename(columns={"TeamID": "team_id"})
        .copy()
    )
    c = compact[["season", "round_num", "WTeamID", "LTeamID"]].copy()
    c = c.merge(seed_map, left_on=["season", "WTeamID"], right_on=["season", "team_id"], how="left")
    c = c.rename(columns={"seed_num": "w_seed"}).drop(columns=["team_id"])
    c = c.merge(seed_map, left_on=["season", "LTeamID"], right_on=["season", "team_id"], how="left")
    c = c.rename(columns={"seed_num": "l_seed"}).drop(columns=["team_id"])
    c = c.dropna(subset=["w_seed", "l_seed"])
    c["w_seed"] = c["w_seed"].astype(int)
    c["l_seed"] = c["l_seed"].astype(int)
    c["seed_hi"] = c[["w_seed", "l_seed"]].max(axis=1)
    c["seed_lo"] = c[["w_seed", "l_seed"]].min(axis=1)
    denom = (
        c.groupby(["round_num", "seed_hi", "seed_lo"])
        .size()
        .rename("n_games")
        .reset_index()
    )
    up = upset_seed.copy()
    up["seed_won"] = pd.to_numeric(up["seed_won"], errors="coerce")
    up["seed_lost"] = pd.to_numeric(up["seed_lost"], errors="coerce")
    up["round_num"] = pd.to_numeric(up["round_num"], errors="coerce")
    up = up.dropna(subset=["seed_won", "seed_lost", "round_num"])
    up["seed_won"] = up["seed_won"].astype(int)
    up["seed_lost"] = up["seed_lost"].astype(int)
    up["round_num"] = up["round_num"].astype(int)
    num = (
        up.groupby(["round_num", "seed_won", "seed_lost"])
        .size()
        .rename("n_upsets")
        .reset_index()
        .rename(columns={"seed_won": "seed_hi", "seed_lost": "seed_lo"})
    )
    upset_rates = denom.merge(num, on=["round_num", "seed_hi", "seed_lo"], how="left")
    upset_rates["n_upsets"] = upset_rates["n_upsets"].fillna(0.0)
    alpha, beta = 1.0, 8.0
    upset_rates["upset_rate"] = (upset_rates["n_upsets"] + alpha) / (upset_rates["n_games"] + alpha + beta)
    return {
        (int(r["round_num"]), int(r["seed_hi"]), int(r["seed_lo"])): float(r["upset_rate"])
        for _, r in upset_rates.iterrows()
    }


def _lookup_seed_a_upset_rate(
    upset_rate_map: Dict[Tuple[int, int, int], float],
    seed_a: int,
    seed_b: int,
    round_num: int,
) -> float:
    """Training rows only: P(seed_a seed beats seed_b) from historic underdog-win rates."""
    if seed_a == seed_b:
        return 0.5
    if seed_a > seed_b:
        return float(upset_rate_map.get((int(round_num), int(seed_a), int(seed_b)), 0.5))
    return 1.0 - float(upset_rate_map.get((int(round_num), int(seed_b), int(seed_a)), 0.5))


def _apply_feature_coef_multipliers(clf: LogisticRegression, use_cols: List[str]) -> None:
    w = clf.coef_
    for j, col in enumerate(use_cols):
        w[0, j] *= float(FEATURE_COEF_MULTIPLIERS.get(col, 1.0))
        w[0, j] *= float(FEATURE_COEF_DAMPEN.get(col, 1.0))


def _seed_for_team_in_season(seeds_df: pd.DataFrame, season: int, team_id: int) -> float:
    """Return seed number (1-16) for that team in that season. NaN if missing."""
    sub = seeds_df[(seeds_df["season"] == season) & (seeds_df["TeamID"] == team_id)]
    if len(sub) == 0:
        return np.nan
    return float(sub["seed_num"].iloc[0])


def _build_tourney_wins_index(compact_df: pd.DataFrame) -> Dict[Tuple[int, int], List[Tuple[int, int, int]]]:
    """(season, WTeamID) -> sorted [(day_num, round_num, LTeamID), ...]."""
    idx: Dict[Tuple[int, int], List[Tuple[int, int, int]]] = defaultdict(list)
    for _, r in compact_df.iterrows():
        idx[(int(r["season"]), int(r["WTeamID"]))].append(
            (int(r["day_num"]), int(r["round_num"]), int(r["LTeamID"]))
        )
    return {k: sorted(v, key=lambda x: x[0]) for k, v in idx.items()}


def _tourney_path_strength_r64_r32(
    wins_index: Dict[Tuple[int, int], List[Tuple[int, int, int]]],
    season: int,
    team_id: int,
    before_day: int,
    seeds_df: pd.DataFrame,
) -> float:
    """
    Mean(17 - loser_seed) for this team's wins in R64 and R32 before before_day.
    Same scale as path_beaten_strength from JSON (higher = beat better seeds).
    """
    games = wins_index.get((season, team_id), [])
    use = [g for g in games if g[0] < before_day and g[1] in (64, 32)]
    if not use:
        return 0.0
    vals: List[float] = []
    for _d, _r, lid in use:
        ls = _seed_for_team_in_season(seeds_df, season, lid)
        if pd.notna(ls):
            vals.append(17.0 - float(ls))
    return float(sum(vals) / len(vals)) if vals else 0.0


def build_training_df(seasons: List[int]) -> pd.DataFrame:
    """
    Build one row per game (plus mirror) with features and label.
    label = 1 means team_a (first team) won.
    Uses only seasons where we have Resumes/KenPom (archive2 has 2008+).
    """
    compact = bd.load_compact_results(seasons)
    seeds_df = bd.load_tourney_seeds(seasons)
    resumes = bd.load_resumes(seasons)
    kp = bd.load_kenpom_barttorvik(seasons)
    pre = bd.load_kenpom_preseason(seasons)
    seed_results = bd.load_seed_results()
    upset_count = bd.load_upset_count()
    upset_rate_map = _build_upset_rate_map(seasons)

    # Resumes: prefer numeric columns that exist
    resume_num = ["RESUME", "ELO", "B POWER", "R SCORE"]
    resume_num = [c for c in resume_num if c in resumes.columns]
    kp_cols = [c for c in ["KADJ EM", "BARTHAG"] if c in kp.columns]
    pre_em = "PRESEASON KADJ EM" if "PRESEASON KADJ EM" in pre.columns else None

    # Upset Count season-level map (year -> counts)
    upset_count = upset_count.copy()
    upset_count["year"] = pd.to_numeric(upset_count["year"], errors="coerce")
    upset_count = upset_count.dropna(subset=["year"])
    upset_count["year"] = upset_count["year"].astype(int)
    upset_count_map = {int(r["year"]): r for _, r in upset_count.iterrows()}

    def season_upset_features(year: int, round_num: int) -> Tuple[float, float]:
        # round mapping from Upset Count columns
        col = {64: "FIRST ROUND", 32: "SECOND ROUND", 16: "SWEET 16", 8: "ELITE 8", 4: "FINAL 4"}.get(round_num)
        if year in upset_count_map and col and col in upset_count_map[year]:
            ur = float(upset_count_map[year][col])
            ut = float(upset_count_map[year].get("TOTAL", 0.0))
            return ur, ut
        # fallback: mean across known years
        known = [y for y in upset_count_map.keys()]
        if not known or not col:
            return 0.0, 0.0
        ur = float(pd.to_numeric(upset_count[col], errors="coerce").mean()) if col in upset_count.columns else 0.0
        ut = float(pd.to_numeric(upset_count["TOTAL"], errors="coerce").mean()) if "TOTAL" in upset_count.columns else 0.0
        return ur, ut

    h2h_index = bd.build_h2h_prior_index(seasons)
    form_index = bd.build_team_season_form_index(seasons)
    tourney_wins_index = _build_tourney_wins_index(compact)

    rows = []
    for _, row in compact.iterrows():
        season = int(row["season"])
        day_num = int(row["day_num"])
        w_id = int(row["WTeamID"])
        l_id = int(row["LTeamID"])
        w_name = row["WTeamName"]
        l_name = row["LTeamName"]
        round_num = int(row["round_num"])

        if pd.isna(w_name) or pd.isna(l_name):
            continue

        w_seed = _seed_for_team_in_season(seeds_df, season, w_id)
        l_seed = _seed_for_team_in_season(seeds_df, season, l_id)
        if pd.isna(w_seed) or pd.isna(l_seed):
            continue

        # Resumes for this year
        res_y = resumes[resumes["year"] == season]
        w_res = res_y[res_y["team"] == w_name]
        l_res = res_y[res_y["team"] == l_name]
        kp_y = kp[kp["year"] == season]
        pre_y = pre[pre["year"] == season] if pre_em else pd.DataFrame()
        w_kp = kp_y[kp_y["team"] == w_name].iloc[0] if len(kp_y[kp_y["team"] == w_name]) else None
        l_kp = kp_y[kp_y["team"] == l_name].iloc[0] if len(kp_y[kp_y["team"] == l_name]) else None
        w_pre = pre_y[pre_y["team"] == w_name].iloc[0] if pre_em and len(pre_y) and len(pre_y[pre_y["team"] == w_name]) else None
        l_pre = pre_y[pre_y["team"] == l_name].iloc[0] if pre_em and len(pre_y) and len(pre_y[pre_y["team"] == l_name]) else None

        def get_res_vals(rf, name):
            if rf is None or len(rf) == 0:
                return {c: np.nan for c in resume_num}
            r = rf[rf["team"] == name]
            if len(r) == 0:
                return {c: np.nan for c in resume_num}
            r = r.iloc[0]
            return {c: r[c] for c in resume_num if c in r.index}

        w_res_vals = get_res_vals(res_y, w_name)
        l_res_vals = get_res_vals(res_y, l_name)

        seed_champ = seed_results.set_index("seed")["seed_champ_pct"].to_dict() if "seed_champ_pct" in seed_results.columns else {}
        w_champ = seed_champ.get(int(w_seed), np.nan)
        l_champ = seed_champ.get(int(l_seed), np.nan)

        def feat_row(
            team_a_name,
            team_b_name,
            seed_a,
            seed_b,
            res_a,
            res_b,
            kp_a,
            kp_b,
            pre_a,
            pre_b,
            champ_a,
            champ_b,
            h2h_wp,
            h2h_pd,
            l10_wp_diff,
            l10_m_diff,
            path_str_diff,
            label,
        ):
            seed_diff = float(seed_a - seed_b)
            resume_diff = (res_b.get("RESUME", np.nan) - res_a.get("RESUME", np.nan)) if "RESUME" in resume_num else np.nan  # higher rank number = worse, so res_b - res_a: positive if a better
            elo_diff = (res_a.get("ELO", np.nan) - res_b.get("ELO", np.nan)) if "ELO" in res_a else np.nan
            b_power_diff = (res_a.get("B POWER", np.nan) - res_b.get("B POWER", np.nan)) if "B POWER" in res_a else np.nan
            r_score_diff = (res_a.get("R SCORE", np.nan) - res_b.get("R SCORE", np.nan)) if "R SCORE" in res_a else np.nan
            kadj_em_diff = (float(kp_a["KADJ EM"]) - float(kp_b["KADJ EM"])) if kp_a is not None and kp_b is not None and "KADJ EM" in kp_cols else np.nan
            bart_diff = (float(kp_a["BARTHAG"]) - float(kp_b["BARTHAG"])) if kp_a is not None and kp_b is not None and "BARTHAG" in kp_cols else np.nan
            pre_diff = (float(pre_a[pre_em]) - float(pre_b[pre_em])) if pre_em and pre_a is not None and pre_b is not None else np.nan
            champ_diff = (champ_a - champ_b) if not (np.isnan(champ_a) or np.isnan(champ_b)) else np.nan
            upset_rate = _lookup_seed_a_upset_rate(upset_rate_map, int(seed_a), int(seed_b), int(round_num))
            season_up_r, season_up_t = season_upset_features(season, int(round_num))
            return {
                "season": season,
                "team_a": team_a_name,
                "team_b": team_b_name,
                "seed_a": float(seed_a),
                "seed_b": float(seed_b),
                "seed_diff": seed_diff,
                "round_num": float(round_num),
                "resume_diff": resume_diff,
                "elo_diff": elo_diff,
                "b_power_diff": b_power_diff,
                "r_score_diff": r_score_diff,
                "kadj_em_diff": kadj_em_diff,
                "bart_diff": bart_diff,
                "preseason_em_diff": pre_diff,
                "seed_champ_pct_diff": champ_diff,
                "seed_a_upset_rate_vs_seed_b": upset_rate,
                "season_upsets_round": season_up_r,
                "season_upsets_total": season_up_t,
                "h2h_win_pct": h2h_wp,
                "h2h_point_diff": h2h_pd,
                "last10_win_pct_diff": l10_wp_diff,
                "last10_margin_diff": l10_m_diff,
                "path_beaten_strength_diff": path_str_diff,
                "label": label,
            }

        hw, hd = bd.h2h_prior_stats(h2h_index, season, w_id, l_id, day_num)
        rw, rm = bd.recent_form_last_n(form_index, season, w_id, day_num, 10)
        lw, lm = bd.recent_form_last_n(form_index, season, l_id, day_num, 10)
        pw = _tourney_path_strength_r64_r32(tourney_wins_index, season, w_id, day_num, seeds_df)
        pl = _tourney_path_strength_r64_r32(tourney_wins_index, season, l_id, day_num, seeds_df)
        # Winner = team_a, loser = team_b -> label 1
        r1 = feat_row(
            w_name,
            l_name,
            w_seed,
            l_seed,
            w_res_vals,
            l_res_vals,
            w_kp,
            l_kp,
            w_pre,
            l_pre,
            w_champ,
            l_champ,
            hw,
            hd,
            rw - lw,
            rm - lm,
            pw - pl,
            1,
        )
        rows.append(r1)
        # Mirror: loser = team_a, winner = team_b -> label 0 (same feature logic, swapped names)
        hw2, hd2 = bd.h2h_prior_stats(h2h_index, season, l_id, w_id, day_num)
        r2 = feat_row(
            l_name,
            w_name,
            l_seed,
            w_seed,
            l_res_vals,
            w_res_vals,
            l_kp,
            w_kp,
            l_pre,
            w_pre,
            l_champ,
            w_champ,
            hw2,
            hd2,
            lw - rw,
            lm - rm,
            pl - pw,
            0,
        )
        rows.append(r2)

    df = pd.DataFrame(rows)
    return df


def train_model(
    seasons: List[int] | None = None, max_iter: int = 2000
) -> Tuple[LogisticRegression, List[str]]:
    """Train on historic games. Returns (model, feature_cols_in_order)."""
    if seasons is None:
        seasons = list(range(2008, 2026))
    train_df = build_training_df(seasons)
    use_cols = [c for c in FEATURE_COLS if c in train_df.columns]
    train_df = train_df.dropna(subset=["seed_diff", "round_num"], how="all")
    for c in use_cols:
        train_df[c] = train_df[c].fillna(0)
    X = train_df[use_cols].to_numpy(dtype=float)
    y = train_df["label"].to_numpy(dtype=int)
    clf = LogisticRegression(C=LOGISTIC_REG_C, max_iter=max_iter)
    clf.fit(X, y)
    _apply_feature_coef_multipliers(clf, use_cols)
    return clf, use_cols


def export_training_df(output_csv: Path | str, seasons: List[int] | None = None) -> Path:
    """
    Build the full training DataFrame and save it to CSV so you can inspect:
      - identifiers (season, team_a, team_b, seed_a, seed_b, round_num)
      - all feature columns
      - label (target)
    """
    if seasons is None:
        seasons = list(range(2008, 2026))
    df = build_training_df(seasons)
    out = Path(output_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return out


def export_training_df_by_round(
    output_dir: Path | str,
    seasons: List[int] | None = None,
    round_nums: List[int] | None = None,
) -> List[Path]:
    """
    Split build_training_df rows into CSVs per round. Filename: matchup_training_round_{n}.csv
    Default round_nums: Sweet 16 (16), Elite 8 (8), Final Four (4), Championship (2).
    """
    if seasons is None:
        seasons = list(range(2008, 2026))
    if round_nums is None:
        round_nums = [16, 8, 4, 2]
    df = build_training_df(seasons)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []
    for r_int in sorted(set(int(r) for r in round_nums)):
        sub = df[df["round_num"] == float(r_int)]
        path = out_dir / f"matchup_training_round_{r_int}.csv"
        sub.to_csv(path, index=False)
        paths.append(path)
    return paths


def build_2026_feature_row(
    team_a: str,
    team_b: str,
    round_num: int,
    resumes_2026: pd.DataFrame,
    kp_2026: pd.DataFrame,
    pre_2026: pd.DataFrame,
    seed_results: pd.DataFrame,
    feature_cols: List[str] | None = None,
    season_upsets_round_means: Dict[int, float] | None = None,
    season_upsets_total_mean: float | None = None,
) -> np.ndarray:
    """
    One row of features for (team_a, team_b) at round_num for 2026.
    H2H win% and point differential come from game_logs_2026 (see build_h2h_2026_summaries).
    If feature_cols is provided, return only those in that order (for model.predict).
    """
    if feature_cols is None:
        feature_cols = FEATURE_COLS
    res_a = resumes_2026[resumes_2026["team"] == team_a]
    res_b = resumes_2026[resumes_2026["team"] == team_b]
    kp_a = kp_2026[kp_2026["team"] == team_a]
    kp_b = kp_2026[kp_2026["team"] == team_b]
    pre_a = pre_2026[pre_2026["team"] == team_a]
    pre_b = pre_2026[pre_2026["team"] == team_b]

    seed_a = float(res_a["seed"].iloc[0]) if len(res_a) else 8.0
    seed_b = float(res_b["seed"].iloc[0]) if len(res_b) else 8.0
    seed_diff = seed_a - seed_b

    resume_diff = np.nan
    if len(res_a) and len(res_b) and "RESUME" in res_a.columns:
        resume_diff = float(res_b["RESUME"].iloc[0]) - float(res_a["RESUME"].iloc[0])
    elo_diff = (float(res_a["ELO"].iloc[0]) - float(res_b["ELO"].iloc[0])) if len(res_a) and len(res_b) and "ELO" in res_a.columns else 0.0
    b_power_diff = (float(res_a["B POWER"].iloc[0]) - float(res_b["B POWER"].iloc[0])) if len(res_a) and len(res_b) and "B POWER" in res_a.columns else 0.0
    r_score_diff = (float(res_a["R SCORE"].iloc[0]) - float(res_b["R SCORE"].iloc[0])) if len(res_a) and len(res_b) and "R SCORE" in res_a.columns else 0.0

    kadj_em_diff = (float(kp_a["KADJ EM"].iloc[0]) - float(kp_b["KADJ EM"].iloc[0])) if len(kp_a) and len(kp_b) else 0.0
    bart_diff = (float(kp_a["BARTHAG"].iloc[0]) - float(kp_b["BARTHAG"].iloc[0])) if len(kp_a) and len(kp_b) else 0.0

    pre_em = "PRESEASON KADJ EM" if "PRESEASON KADJ EM" in pre_2026.columns else None
    preseason_em_diff = (float(pre_a[pre_em].iloc[0]) - float(pre_b[pre_em].iloc[0])) if pre_em and len(pre_a) and len(pre_b) else 0.0

    champ = seed_results.set_index("seed")["seed_champ_pct"].to_dict() if "seed_champ_pct" in seed_results.columns else {}
    champ_a = champ.get(int(seed_a), 0.0)
    champ_b = champ.get(int(seed_b), 0.0)
    seed_champ_pct_diff = champ_a - champ_b

    # 2026: no pairwise upset prior in features (neutral); training still uses historic upset rates per game.
    seed_a_upset_rate_vs_seed_b = 0.5
    if season_upsets_round_means is not None and season_upsets_total_mean is not None:
        season_upsets_round = season_upsets_round_means.get(round_num, 0.0)
        season_upsets_total = season_upsets_total_mean
    else:
        uc = bd.load_upset_count()
        col = {64: "FIRST ROUND", 32: "SECOND ROUND", 16: "SWEET 16", 8: "ELITE 8", 4: "FINAL 4"}.get(round_num)
        season_upsets_round = float(pd.to_numeric(uc[col], errors="coerce").mean()) if (col and col in uc.columns) else 0.0
        season_upsets_total = float(pd.to_numeric(uc["TOTAL"], errors="coerce").mean()) if ("TOTAL" in uc.columns) else 0.0

    summaries = _get_h2h_2026_summaries()
    h2h_win_pct, h2h_point_diff = bd.h2h_stats_2026_for_teams(team_a, team_b, summaries)

    form_idx = _get_form_2026_index()
    aw, am = bd.recent_form_last_n_2026(form_idx, team_a, 10)
    bw, bm = bd.recent_form_last_n_2026(form_idx, team_b, 10)
    last10_win_pct_diff = aw - bw
    last10_margin_diff = am - bm

    valid_teams = set(resumes_2026["team"].astype(str).unique()) if len(resumes_2026) else set()
    path_map = bd.load_sweet16_path_wins_2026(valid_teams=valid_teams if valid_teams else None)
    team_seed = (
        resumes_2026.set_index("team")["seed"].astype(float).to_dict()
        if len(resumes_2026) and "team" in resumes_2026.columns and "seed" in resumes_2026.columns
        else {}
    )
    ta = bd.normalize_resume_team_name(team_a, valid_teams if valid_teams else None)
    tb = bd.normalize_resume_team_name(team_b, valid_teams if valid_teams else None)
    pa = bd.path_beaten_strength(ta, path_map.get(ta, []), team_seed, valid_teams=valid_teams if valid_teams else None)
    pb = bd.path_beaten_strength(tb, path_map.get(tb, []), team_seed, valid_teams=valid_teams if valid_teams else None)
    path_beaten_strength_diff = pa - pb

    values = {
        "seed_diff": seed_diff,
        "round_num": float(round_num),
        "resume_diff": resume_diff if np.isfinite(resume_diff) else 0.0,
        "elo_diff": elo_diff,
        "b_power_diff": b_power_diff,
        "r_score_diff": r_score_diff,
        "kadj_em_diff": kadj_em_diff,
        "bart_diff": bart_diff,
        "preseason_em_diff": preseason_em_diff,
        "seed_champ_pct_diff": seed_champ_pct_diff,
        "seed_a_upset_rate_vs_seed_b": seed_a_upset_rate_vs_seed_b,
        "season_upsets_round": season_upsets_round,
        "season_upsets_total": season_upsets_total,
        "h2h_win_pct": h2h_win_pct,
        "h2h_point_diff": h2h_point_diff,
        "last10_win_pct_diff": last10_win_pct_diff,
        "last10_margin_diff": last10_margin_diff,
        "path_beaten_strength_diff": path_beaten_strength_diff,
    }
    return np.array([values[c] for c in feature_cols], dtype=float)


def get_trained_model_and_feature_cols() -> Tuple[LogisticRegression, List[str]]:
    """Train once and return (model, feature column names in order)."""
    return train_model()
