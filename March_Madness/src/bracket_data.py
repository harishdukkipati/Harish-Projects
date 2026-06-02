"""
Load and join all data needed for bracket simulation: historic results,
team names, seeds, resumes, ratings, preseason, seed/upset stats, and game logs.
Uses MTeams TeamID (Kaggle) for CompactResults; joins to archive2 by team name.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ARCHIVE = DATA_DIR / "archive 2"
HISTORIC = DATA_DIR / "historic_data"
BRACKET_DATA = DATA_DIR / "bracket_data"


def load_mteams_id_to_name() -> pd.Series:
    """TeamID (Kaggle/MTeams) -> TeamName. One-to-one."""
    path = BRACKET_DATA / "MTeams.csv"
    df = pd.read_csv(path)
    df = df.astype({"TeamID": int})
    return df.set_index("TeamID")["TeamName"].squeeze()


def load_tourney_seeds(seasons: List[int] | None = None) -> pd.DataFrame:
    """MNCAATourneySeeds: Season, Seed (W01), TeamID -> add seed_num 1-16."""
    path = BRACKET_DATA / "MNCAATourneySeeds.csv"
    df = pd.read_csv(path)
    df = df.rename(columns={"Season": "season"})
    # Seed is like W01, X02 -> extract number
    df["seed_num"] = df["Seed"].astype(str).str.extract(r"(\d+)", expand=False).astype(int)
    if seasons is not None:
        df = df[df["season"].isin(seasons)]
    return df


def load_regular_season_compact_results(seasons: List[int] | None = None) -> pd.DataFrame:
    """MRegularSeasonCompactResults: Season, DayNum, WTeamID, LTeamID, WScore, LScore."""
    path = HISTORIC / "MRegularSeasonCompactResults.csv"
    df = pd.read_csv(path)
    df = df.rename(columns={"Season": "season", "DayNum": "day_num"})
    if seasons is not None:
        df = df[df["season"].isin(seasons)]
    return df


def load_raw_tourney_compact_games(seasons: List[int] | None = None) -> pd.DataFrame:
    """MNCAATourneyCompactResults with season/day_num only (no round inference)."""
    path = HISTORIC / "MNCAATourneyCompactResults.csv"
    df = pd.read_csv(path)
    df = df.rename(columns={"Season": "season", "DayNum": "day_num"})
    if seasons is not None:
        df = df[df["season"].isin(seasons)]
    return df


def build_h2h_prior_index(seasons: List[int] | None = None) -> Dict[Tuple[int, int, int], List[Tuple[int, int, int, int]]]:
    """
    All regular-season + NCAA tournament games (same season), keyed by
    (season, min_id, max_id). Each value is a list of (day_num, WTeamID, WScore, LScore)
    sorted by day_num within the pair.

    Used to compute head-to-head prior to a given tournament game (day_num < game day).
    """
    reg = load_regular_season_compact_results(seasons)
    tr = load_raw_tourney_compact_games(seasons)
    cols = ["season", "day_num", "WTeamID", "LTeamID", "WScore", "LScore"]
    all_g = pd.concat([reg[cols], tr[cols]], ignore_index=True)
    all_g['id_lo'] = all_g[["WTeamID", "LTeamID"]].min(axis=1)
    all_g['id_hi'] = all_g[["WTeamID", "LTeamID"]].max(axis=1)
    all_g = all_g.sort_values(["season", "id_lo", "id_hi", "day_num"])
    index: Dict[Tuple[int, int, int], List[Tuple[int, int, int, int]]] = {}
    for (season, lo, hi), g in all_g.groupby(["season", "id_lo", "id_hi"], sort=False):
        idx = (int(season), int(lo), int(hi))
        index[idx] = [
            (int(r["day_num"]), int(r["WTeamID"]), int(r["WScore"]), int(r["LScore"]))
            for _, r in g.iterrows()
        ]
    return index


def build_team_season_form_index(
    seasons: List[int] | None = None,
) -> Dict[Tuple[int, int], List[Tuple[int, int, int, int]]]:
    """
    (season, team_id) -> chronological list of (day_num, pts_for, pts_against, win_bool).
    Built from regular season + NCAA tournament compact games.
    """
    reg = load_regular_season_compact_results(seasons)
    tr = load_raw_tourney_compact_games(seasons)
    cols = ["season", "day_num", "WTeamID", "LTeamID", "WScore", "LScore"]
    all_g = pd.concat([reg[cols], tr[cols]], ignore_index=True)
    raw: Dict[Tuple[int, int], List[Tuple[int, int, int, int]]] = defaultdict(list)
    for _, r in all_g.iterrows():
        s = int(r["season"])
        d = int(r["day_num"])
        wid, lid = int(r["WTeamID"]), int(r["LTeamID"])
        ws, ls = int(r["WScore"]), int(r["LScore"])
        raw[(s, wid)].append((d, ws, ls, 1))
        raw[(s, lid)].append((d, ls, ws, 0))
    return {k: sorted(v, key=lambda x: x[0]) for k, v in raw.items()}


def recent_form_last_n(
    index: Dict[Tuple[int, int], List[Tuple[int, int, int, int]]],
    season: int,
    team_id: int,
    before_day: int,
    n: int = 10,
) -> Tuple[float, float]:
    """
    Win rate and mean scoring margin (pts_for - pts_against) over the last n games
    strictly before before_day. Fewer than n games uses all available; none -> (0.5, 0.0).
    """
    key = (season, team_id)
    games = index.get(key, [])
    prior = [g for g in games if g[0] < before_day]
    last = prior[-n:] if len(prior) >= n else prior
    if not last:
        return 0.5, 0.0
    wins = sum(g[3] for g in last)
    margins = [g[1] - g[2] for g in last]
    return wins / len(last), float(sum(margins) / len(margins))


def build_team_form_index_2026_from_logs() -> Dict[str, List[Tuple[int, int, int]]]:
    """
    team name -> chronological list of (pts_for, pts_against, win) from game_logs_2026.
    Sorted by parsed date then row order.
    """
    gl = load_game_logs_2026()
    if gl.empty:
        return {}
    gl = gl.copy()
    gl["_dt"] = pd.to_datetime(gl["date"], errors="coerce")
    gl["_row"] = range(len(gl))
    gl = gl.sort_values(["team", "_dt", "_row"], na_position="last")
    out: Dict[str, List[Tuple[int, int, int]]] = {}
    for team, g in gl.groupby("team", sort=False):
        seq: List[Tuple[int, int, int]] = []
        for _, r in g.iterrows():
            pf = int(r["team_score"])
            pa = int(r["opp_score"])
            win = 1 if bool(r["is_win"]) else 0
            seq.append((pf, pa, win))
        out[str(team)] = seq
    return out


def recent_form_last_n_2026(
    index: Dict[str, List[Tuple[int, int, int]]],
    team: str,
    n: int = 10,
) -> Tuple[float, float]:
    """Last n games in 2026 logs by date (season to date). No games -> (0.5, 0.0)."""
    games = index.get(team, [])
    if not games:
        return 0.5, 0.0
    last = games[-n:] if len(games) >= n else games
    wins = sum(g[2] for g in last)
    margins = [g[0] - g[1] for g in last]
    return wins / len(last), float(sum(margins) / len(margins))


DEFAULT_SWEET16_PATH_JSON = BRACKET_DATA / "sweet16_path_wins_2026.json"

# Common alternate spellings -> exact TEAM string in Resumes.csv
RESUME_TEAM_ALIASES: Dict[str, str] = {
    "long island": "LIU Brooklyn",
    "liu brooklyn": "LIU Brooklyn",
    "long island university": "LIU Brooklyn",
    "saint louis university": "St Louis",
    "st louis university": "St Louis",
    "st. louis": "St Louis",
    "st louis": "St Louis",
    "tennesee st.": "Tennessee St",
    "tennessee st.": "Tennessee St",
    "tennesse st": "Tennessee St",
    "queens": "Queens NC",
    "miami": "Miami FL",
    "miami (oh)": "Miami OH",
    "miami (ohio)": "Miami OH",
    "miami oh": "Miami OH",
    "north dakota st": "N Dakota St",
    "north dakota state": "N Dakota St",
    "ohio state": "Ohio St",
    "michigan state": "Michigan St",
    "iowa state": "Iowa St",
    "texas a&m": "Texas A&M",
    "texas am": "Texas A&M",
}


def normalize_resume_team_name(name: str, valid_teams: set[str] | None = None) -> str:
    """
    Map user/JSON team string to Resumes.csv TEAM if possible.
    """
    raw = str(name).strip()
    if not raw:
        return raw
    if valid_teams is not None:
        if raw in valid_teams:
            return raw
        lower_map = {t.lower(): t for t in valid_teams}
        if raw.lower() in lower_map:
            return lower_map[raw.lower()]
    if raw in RESUME_TEAM_ALIASES.values():
        return raw
    key = raw.lower().replace("  ", " ")
    if key in RESUME_TEAM_ALIASES:
        cand = RESUME_TEAM_ALIASES[key]
        if valid_teams is None or cand in valid_teams:
            return cand
    return raw


def load_sweet16_path_wins_2026(
    path: Path | None = None,
    valid_teams: set[str] | None = None,
) -> Dict[str, List[str]]:
    """
    Optional JSON: { "Duke": ["Siena", "Ohio St"], ... } opponent names as in Resumes.csv.
    Opponent strings are normalized via RESUME_TEAM_ALIASES when valid_teams is provided (2026).
    """
    p = path or DEFAULT_SWEET16_PATH_JSON
    if not p.is_file():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    out: Dict[str, List[str]] = {}
    for k, v in data.items():
        team_key = str(k).strip()
        if valid_teams is not None:
            team_key = normalize_resume_team_name(team_key, valid_teams)
        beaten = [normalize_resume_team_name(str(x), valid_teams) for x in v]
        out[team_key] = beaten
    return out


def path_beaten_strength(
    team: str,
    beaten: List[str],
    team_seed: Dict[str, float],
    valid_teams: set[str] | None = None,
) -> float:
    """
    Mean of (17 - opponent_seed) for beaten opponents (higher = beat stronger seeds).
    Missing opponent seed skipped; empty -> 0.0.
    """
    if not beaten:
        return 0.0
    vals: List[float] = []
    for opp in beaten:
        name = normalize_resume_team_name(str(opp), valid_teams)
        sd = team_seed.get(name, team_seed.get(opp))
        if sd is not None and pd.notna(sd):
            vals.append(17.0 - float(sd))
    return float(sum(vals) / len(vals)) if vals else 0.0


def h2h_prior_stats(
    index: Dict[Tuple[int, int, int], List[Tuple[int, int, int, int]]],
    season: int,
    team_a_id: int,
    team_b_id: int,
    before_day: int,
) -> Tuple[float, float]:
    """
    From team_a's perspective (prior to this tournament game only):
    return (win_rate, mean_point_diff) where point_diff = team_a_pts - team_b_pts per game.
    No prior games -> (0.5, 0.0).
    """
    if team_a_id == team_b_id:
        return 0.5, 0.0
    lo, hi = sorted([team_a_id, team_b_id])
    key = (season, lo, hi)
    games = index.get(key, [])
    prior = [g for g in games if g[0] < before_day]
    if not prior:
        return 0.5, 0.0
    wins = 0
    diffs: List[float] = []
    for _day_num, w_id, w_score, l_score in prior:
        if w_id == team_a_id:
            wins += 1
            diffs.append(float(w_score - l_score))
        else:
            diffs.append(float(l_score - w_score))
    return wins / len(prior), float(sum(diffs) / len(diffs))


def load_compact_results(seasons: List[int] | None = None) -> pd.DataFrame:
    """MNCAATourneyCompactResults with round inferred. Adds WTeamName, LTeamName, round_num."""
    path = HISTORIC / "MNCAATourneyCompactResults.csv"
    df = pd.read_csv(path)
    df = df.rename(columns={"Season": "season", "DayNum": "day_num"})
    if seasons is not None:
        df = df[df["season"].isin(seasons)]
    id2name = load_mteams_id_to_name()
    df["WTeamName"] = df["WTeamID"].map(id2name)
    df["LTeamName"] = df["LTeamID"].map(id2name)

    # Infer round: per season, order by day_num; first 32 = 64, next 16 = 32, next 8 = 16, next 4 = 8, next 2 = 4, next 1 = 2
    round_by_idx = [64] * 32 + [32] * 16 + [16] * 8 + [8] * 4 + [4] * 2 + [2] * 1
    df = df.sort_values(["season", "day_num"]).reset_index(drop=True)
    idx_in_season = df.groupby("season").cumcount()
    df["round_num"] = idx_in_season.map(lambda i: round_by_idx[i] if i < len(round_by_idx) else 64)
    return df


def load_resumes(years: List[int] | None = None) -> pd.DataFrame:
    """Resumes.csv: YEAR, TEAM NO, TEAM, SEED, RESUME, ELO, B POWER, R SCORE (if present)."""
    path = ARCHIVE / "Resumes.csv"
    df = pd.read_csv(path)
    df = df.rename(columns={"YEAR": "year", "TEAM NO": "team_no", "TEAM": "team", "SEED": "seed"})
    cols = ["year", "team_no", "team", "seed"]
    for c in ["RESUME", "ELO", "B POWER", "R SCORE"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            cols.append(c)
    df = df[[c for c in cols if c in df.columns]]
    if years is not None:
        df = df[df["year"].isin(years)]
    return df


def load_kenpom_barttorvik(years: List[int] | None = None) -> pd.DataFrame:
    """KenPom Barttorvik: year, team, KADJ EM, BARTHAG."""
    path = ARCHIVE / "KenPom Barttorvik.csv"
    df = pd.read_csv(path)
    df = df.rename(columns={"YEAR": "year", "TEAM": "team", "TEAM NO": "team_no"})
    for c in ["KADJ EM", "BARTHAG"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    keep = ["year", "team", "team_no"] + [c for c in ["KADJ EM", "BARTHAG"] if c in df.columns]
    df = df[[c for c in keep if c in df.columns]]
    if years is not None:
        df = df[df["year"].isin(years)]
    return df


def load_kenpom_preseason(years: List[int] | None = None) -> pd.DataFrame:
    """KenPom Preseason: year, team, PRESEASON KADJ EM (and rank if present)."""
    path = ARCHIVE / "KenPom Preseason.csv"
    df = pd.read_csv(path)
    df = df.rename(columns={"YEAR": "year", "TEAM": "team", "TEAM NO": "team_no"})
    em_col = "PRESEASON KADJ EM" if "PRESEASON KADJ EM" in df.columns else None
    rank_col = "PRESEASON KADJ EM RANK" if "PRESEASON KADJ EM RANK" in df.columns else None
    if em_col:
        df[em_col] = pd.to_numeric(df[em_col], errors="coerce")
    keep = ["year", "team", "team_no"]
    if em_col:
        keep.append(em_col)
    if rank_col and rank_col in df.columns:
        df[rank_col] = pd.to_numeric(df[rank_col], errors="coerce")
        keep.append(rank_col)
    df = df[[c for c in keep if c in df.columns]]
    if years is not None:
        df = df[df["year"].isin(years)]
    return df


def load_seed_results() -> pd.DataFrame:
    """Seed Results.csv: SEED, WIN%, CHAMP% etc. Parsed to numeric."""
    path = ARCHIVE / "Seed Results.csv"
    df = pd.read_csv(path)
    df = df.rename(columns={"SEED": "seed"})
    if "CHAMP%" in df.columns:
        df["seed_champ_pct"] = (
            df["CHAMP%"].astype(str).str.rstrip("%").astype(float) / 100.0
        )
    if "WIN%" in df.columns:
        df["seed_win_pct"] = (
            df["WIN%"].astype(str).str.rstrip("%").astype(float) / 100.0
        )
    return df


def load_upset_seed_info() -> pd.DataFrame:
    """Upset Seed Info: YEAR, CURRENT ROUND, SEED WON, SEED LOST, SEED DIFF."""
    path = ARCHIVE / "Upset Seed Info.csv"
    df = pd.read_csv(path)
    df = df.rename(columns={
        "YEAR": "year",
        "CURRENT ROUND": "round_num",
        "SEED WON": "seed_won",
        "SEED LOST": "seed_lost",
        "SEED DIFF": "seed_diff",
    })
    return df


def load_upset_count() -> pd.DataFrame:
    """
    Upset Count.csv: YEAR and number of upsets by round.

    Columns are: YEAR, FIRST ROUND, SECOND ROUND, SWEET 16, ELITE 8, FINAL 4, TOTAL
    """
    path = ARCHIVE / "Upset Count.csv"
    df = pd.read_csv(path)
    df = df.rename(columns={"YEAR": "year"})
    for c in ["FIRST ROUND", "SECOND ROUND", "SWEET 16", "ELITE 8", "FINAL 4", "TOTAL"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def load_game_logs_2026() -> pd.DataFrame:
    """game_logs_2026.csv: season, team, opponent, is_win, team_score, opp_score."""
    path = DATA_DIR / "game_logs_2026.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df = df[df["season"] == 2026].copy()
    df["is_win"] = df["is_win"].map({True: 1, False: 0, "True": 1, "False": 0})
    return df


def build_h2h_2026_summaries() -> Dict[Tuple[str, str], Tuple[float, float]]:
    """
    From game_logs_2026: for each sorted name pair (t1, t2), (P(t1 wins), mean(t1_pts - t2_pts))
    across unique games (deduped by date + pair). Empty if no logs.
    """
    gl = load_game_logs_2026()
    if gl.empty:
        return {}
    from collections import defaultdict

    pair_games: Dict[Tuple[str, str], List[Tuple[float, bool]]] = defaultdict(list)
    seen_gids: set = set()
    for _, r in gl.iterrows():
        t, o = str(r["team"]), str(r["opponent"])
        if t == o:
            continue
        gid = (tuple(sorted([t, o])), str(r["date"]))
        if gid in seen_gids:
            continue
        seen_gids.add(gid)
        t1, t2 = sorted([t, o])
        if t == t1:
            diff_lo = float(r["team_score"]) - float(r["opp_score"])
            win_lo = bool(r["is_win"])
        else:
            diff_lo = float(r["opp_score"]) - float(r["team_score"])
            win_lo = not bool(r["is_win"])
        pair_games[(t1, t2)].append((diff_lo, win_lo))
    out: Dict[Tuple[str, str], Tuple[float, float]] = {}
    for k, games in pair_games.items():
        diffs = [g[0] for g in games]
        wins_lo = sum(1 for g in games if g[1])
        n = len(games)
        out[k] = (wins_lo / n if n else 0.5, float(sum(diffs) / n) if n else 0.0)
    return out


def h2h_stats_2026_for_teams(
    team_a: str,
    team_b: str,
    summaries: Dict[Tuple[str, str], Tuple[float, float]],
) -> Tuple[float, float]:
    """(P(team_a wins), mean(team_a_pts - team_b_pts)) from 2026 game logs."""
    if team_a == team_b:
        return 0.5, 0.0
    t1, t2 = sorted([team_a, team_b])
    key = (t1, t2)
    if key not in summaries:
        return 0.5, 0.0
    p_lo, md_lo = summaries[key]
    if team_a == t1:
        return p_lo, md_lo
    return 1.0 - p_lo, -md_lo


def build_h2h_win_pct_2026() -> Dict[Tuple[str, str], float]:
    """
    For each sorted name pair, P(alphabetically-first team wins).
    Delegates to build_h2h_2026_summaries (deduped games).
    """
    summ = build_h2h_2026_summaries()
    return {k: v[0] for k, v in summ.items()}
