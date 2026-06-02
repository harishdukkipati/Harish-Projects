from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from . import bracket_data as bd
from . import matchup_model as mm

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
HYBRID_DETERMINISTIC_FRACTION = 0.5

# Round name -> round_num for the model (64, 32, 16, 8, 4, 2)
_ROUND_NUM: Dict[str, int] = {
    "R64": 64,
    "R32": 32,
    "Sweet16": 16,
    "Elite8": 8,
    "Final4": 4,
    "Champ": 2,
}


def _load_2026_model_context() -> Dict[str, Any]:
    """Load trained model and 2026 data for matchup win probability."""
    clf, feature_cols = mm.get_trained_model_and_feature_cols()
    resumes_2026 = bd.load_resumes([2026])
    kp_2026 = bd.load_kenpom_barttorvik([2026])
    pre_2026 = bd.load_kenpom_preseason([2026])
    seed_results = bd.load_seed_results()
    # Precompute historical upset-count means once (avoid loading CSV in sim loop).
    uc = bd.load_upset_count()
    round_cols = {
        64: "FIRST ROUND",
        32: "SECOND ROUND",
        16: "SWEET 16",
        8: "ELITE 8",
        4: "FINAL 4",
    }
    season_upsets_round_means = {
        r: float(pd.to_numeric(uc[col], errors="coerce").mean())
        for r, col in round_cols.items()
        if col in uc.columns
    }
    season_upsets_total_mean = float(pd.to_numeric(uc["TOTAL"], errors="coerce").mean()) if "TOTAL" in uc.columns else 0.0
    return {
        "clf": clf,
        "feature_cols": feature_cols,
        "resumes_2026": resumes_2026,
        "kp_2026": kp_2026,
        "pre_2026": pre_2026,
        "seed_results": seed_results,
        "season_upsets_round_means": season_upsets_round_means,
        "season_upsets_total_mean": season_upsets_total_mean,
    }


def _p_team_a_wins(
    team_a: str,
    team_b: str,
    round_name: str,
    ctx: Dict[str, Any],
) -> float:
    """Probability that team_a wins (0..1). Uses model + 2026 data + H2H from game_logs."""
    round_num = _ROUND_NUM[round_name]
    x = mm.build_2026_feature_row(
        team_a,
        team_b,
        round_num,
        ctx["resumes_2026"],
        ctx["kp_2026"],
        ctx["pre_2026"],
        ctx["seed_results"],
        ctx["feature_cols"],
        season_upsets_round_means=ctx.get("season_upsets_round_means"),
        season_upsets_total_mean=ctx.get("season_upsets_total_mean"),
    )
    # Model class 1 = team_a wins
    return float(ctx["clf"].predict_proba(x.reshape(1, -1))[0, 1])


def _apply_temperature(p: float, temperature: float) -> float:
    """T>1 pulls probabilities toward 0.5, T<1 sharpens."""
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    if abs(temperature - 1.0) < 1e-12:
        return float(p)
    eps = 1e-9
    p = min(max(float(p), eps), 1.0 - eps)
    logit = math.log(p / (1.0 - p))
    scaled = logit / temperature
    return 1.0 / (1.0 + math.exp(-scaled))


def _pick_winner(
    team_a: str,
    team_b: str,
    round_name: str,
    ctx: Dict[str, Any],
    rng: np.random.Generator,
    *,
    temperature: float = 1.0,
    pure_stochastic: bool = False,
) -> Tuple[str, str]:
    """
    Pick one winner for a game using either pure stochastic or hybrid mode.

    Hybrid mode: each game has 50% chance to be deterministic (p>=0.5)
    and 50% chance to be sampled Bernoulli(p). Temperature is applied first.
    """
    p = _apply_temperature(_p_team_a_wins(team_a, team_b, round_name, ctx), temperature)
    use_deterministic = (not pure_stochastic) and (rng.random() < HYBRID_DETERMINISTIC_FRACTION)
    if use_deterministic:
        winner = team_a if p >= 0.5 else team_b
    else:
        winner = team_a if rng.random() < p else team_b
    loser = team_b if winner == team_a else team_a
    return winner, loser


def _load_2026_round1_matchups() -> pd.DataFrame:
    """
    Load projected 2026 round-of-64 matchups from archive 2 Tournament Matchups.csv.

    We assume the file has one row per team per game with:
        - YEAR
        - TEAM NO
        - TEAM
        - SEED
        - BY YEAR NO
        - CURRENT ROUND

    For CURRENT ROUND == 64, rows are ordered so that sorting by BY YEAR NO
    descending and pairing consecutive rows gives actual games.
    """
    path = DATA_DIR / "archive 2" / "Tournament Matchups.csv"
    matchups = pd.read_csv(path)
    m = matchups[(matchups["YEAR"] == 2026) & (matchups["CURRENT ROUND"] == 64)].copy()

    m = m.rename(
        columns={
            "YEAR": "year",
            "TEAM NO": "team_no",
            "TEAM": "team",
            "SEED": "seed",
            "BY YEAR NO": "by_year_no",
        }
    )
    m = m.sort_values(["year", "by_year_no"], ascending=[True, False]).reset_index(drop=True)
    # The 2026 projection includes First Four style play-in games, so CURRENT ROUND == 64
    # has 72 rows (36 games, 68 unique teams). We pair consecutive rows to get 36 games.
    #
    # In this projection, the 4 games that contain the First Four participants are:
    # Lehigh, SMU, UMBC, NC State. Removing those 4 games yields exactly 32 games
    # (64 teams) for the clean Round of 64.
    first_four_teams = frozenset({"Lehigh", "SMU", "UMBC", "NC State"})

    if len(m) % 2 != 0:
        raise ValueError(f"Expected an even number of rows for CURRENT ROUND 64, got {len(m)}")

    games: List[Dict[str, Any]] = []
    for i in range(0, len(m), 2):
        a = m.iloc[i]
        b = m.iloc[i + 1]
        ta = str(a["team"])
        tb = str(b["team"])
        if ta in first_four_teams or tb in first_four_teams:
            continue
        games.append(
            {
                "game_index": len(games),  # 0..31 after filtering (preserve order)
                "team_a": ta,
                "team_b": tb,
                "seed_a": int(a["seed"]),
                "seed_b": int(b["seed"]),
                "team_no_a": int(a["team_no"]),
                "team_no_b": int(b["team_no"]),
            }
        )

    if len(games) != 32:
        raise ValueError(f"Expected 32 R64 games after filtering First Four slots, got {len(games)}")

    return pd.DataFrame(games)


def _simulate_bracket(
    ctx: Dict[str, Any],
    round1_games: pd.DataFrame,
    n_sims: int = 10000,
) -> Dict[str, Dict[str, int]]:
    """
    Run Monte Carlo simulations of the full bracket using a fixed tree topology.

    Tree topology:
        - Round of 64: 32 games, indices 0..31 from round1_games
        - Round of 32: game i has children (2*i, 2*i + 1) from previous round
        - Sweet 16: same pattern, etc. through to championship.

    We track, for each round, how many times each team wins that round-game.
    """
    rng = np.random.default_rng(seed=42)

    # Predefine tree structure: list of rounds, each round is list of (left_idx, right_idx)
    rounds: List[List[Tuple[int, int]]] = []
    # Round of 64 has implicit child indices; we just keep placeholder pairs for alignment.
    r64_pairs = [(i, i) for i in range(len(round1_games))]
    rounds.append(r64_pairs)

    # Build higher rounds until only one game left.
    prev_size = len(round1_games)
    while prev_size > 1:
        this_round: List[Tuple[int, int]] = []
        for i in range(0, prev_size, 2):
            this_round.append((i, i + 1))
        rounds.append(this_round)
        prev_size = len(this_round)

    # stats[round_name][team] = wins in that round
    stats: Dict[str, Dict[str, int]] = {}
    round_names = ["R64", "R32", "Sweet16", "Elite8", "Final4", "Champ"]

    for rn in round_names:
        stats[rn] = {}

    # Simulation loop
    for _ in range(n_sims):
        # winners_by_round[r][g_idx] = team name that advances from that round game
        winners_by_round: List[List[str]] = []

        # Round of 64
        r64_winners: List[str] = []
        for _, g in round1_games.sort_values("game_index").iterrows():
            team_a = g["team_a"]
            team_b = g["team_b"]
            p = _p_team_a_wins(team_a, team_b, "R64", ctx)
            win_a = rng.random() < p
            winner = team_a if win_a else team_b
            r64_winners.append(winner)
            stats["R64"][winner] = stats["R64"].get(winner, 0) + 1
        winners_by_round.append(r64_winners)

        # Higher rounds
        prev_winners = r64_winners
        for round_idx in range(1, len(rounds)):
            games = rounds[round_idx]
            rn = round_names[round_idx]
            curr_winners = []
            for left_idx, right_idx in games:
                team_a = prev_winners[left_idx]
                team_b = prev_winners[right_idx]
                p = _p_team_a_wins(team_a, team_b, rn, ctx)
                win_a = rng.random() < p
                winner = team_a if win_a else team_b
                curr_winners.append(winner)

            winners_by_round.append(curr_winners)

            # Update stats
            if round_idx == 1:
                rn = "R32"
            elif round_idx == 2:
                rn = "Sweet16"
            elif round_idx == 3:
                rn = "Elite8"
            elif round_idx == 4:
                rn = "Final4"
            else:
                rn = "Champ"

            for w in curr_winners:
                stats[rn][w] = stats[rn].get(w, 0) + 1

            prev_winners = curr_winners

    return stats


def _deterministic_bracket(
    ctx: Dict[str, Any],
    round1_games: pd.DataFrame,
) -> Dict[str, List[Tuple[str, str, str]]]:
    """
    Build a single \"most likely\" bracket by taking the logistic favourite
    in each game, walking from round of 64 through the title.

    Returns a mapping from round name to a list of tuples:
        (winner, loser, matchup_string)
    """
    round_names = ["R64", "R32", "Sweet16", "Elite8", "Final4", "Champ"]

    bracket: Dict[str, List[Tuple[str, str, str]]] = {rn: [] for rn in round_names}

    # Round of 64
    r64_winners = []
    for _, g in round1_games.sort_values("game_index").iterrows():
        team_a = g["team_a"]
        team_b = g["team_b"]
        p = _p_team_a_wins(team_a, team_b, "R64", ctx)
        if p >= 0.5:
            winner, loser = team_a, team_b
        else:
            winner, loser = team_b, team_a
        r64_winners.append(winner)
        bracket["R64"].append((winner, loser, f"{team_a} vs {team_b}"))

    # Build higher rounds using the same binary tree topology as in simulations.
    prev_winners = r64_winners
    round_size = len(prev_winners)
    round_idx = 1
    while round_size > 1 and round_idx < len(round_names):
        curr_winners = []
        rn = round_names[round_idx]
        for i in range(0, round_size, 2):
            team_a = prev_winners[i]
            team_b = prev_winners[i + 1]
            p = _p_team_a_wins(team_a, team_b, rn, ctx)
            if p >= 0.5:
                winner, loser = team_a, team_b
            else:
                winner, loser = team_b, team_a
            curr_winners.append(winner)
            bracket[rn].append((winner, loser, f"{team_a} vs {team_b}"))

        prev_winners = curr_winners
        round_size = len(prev_winners)
        round_idx += 1

    return bracket


def simulate_full_bracket_cumulative(
    ctx: Dict[str, Any],
    round1_games: pd.DataFrame,
    *,
    n_sims: int = 5000,
    temperature: float = 1.0,
    pure_stochastic: bool = False,
    seed: int | None = None,
) -> Dict[str, Any]:
    """
    Simulate full 2026 bracket (R64->Champ) and return cumulative bracket by slot.

    For each fixed slot in each round, we count (winner, loser) outcomes over sims
    and choose the most common pair as the consensus for that slot.
    """
    if n_sims < 1:
        raise ValueError("n_sims must be >= 1")
    if temperature <= 0:
        raise ValueError("temperature must be positive")

    rng = np.random.default_rng(seed=seed)
    round_names = ["R64", "R32", "Sweet16", "Elite8", "Final4", "Champ"]

    sorted_round1 = round1_games.sort_values("game_index").reset_index(drop=True)

    # Number of game slots in each round: 32,16,8,4,2,1
    slot_counts: List[int] = []
    size = len(sorted_round1)
    while size >= 1:
        slot_counts.append(size)
        size //= 2
    if slot_counts != [32, 16, 8, 4, 2, 1]:
        raise ValueError(f"Unexpected bracket slot structure: {slot_counts}")

    # slot_outcomes[round_name][slot_idx][(winner, loser)] = count
    slot_outcomes: Dict[str, List[Dict[Tuple[str, str], int]]] = {}
    for rn, n_slots in zip(round_names, slot_counts):
        slot_outcomes[rn] = [dict() for _ in range(n_slots)]

    champ_counts: Dict[str, int] = {}

    for _ in range(n_sims):
        # Round of 64
        r64_winners: List[str] = []
        for slot_idx, g in sorted_round1.iterrows():
            team_a = str(g["team_a"])
            team_b = str(g["team_b"])
            winner, loser = _pick_winner(
                team_a,
                team_b,
                "R64",
                ctx,
                rng,
                temperature=temperature,
                pure_stochastic=pure_stochastic,
            )
            r64_winners.append(winner)
            counts = slot_outcomes["R64"][slot_idx]
            key = (winner, loser)
            counts[key] = counts.get(key, 0) + 1

        prev_winners = r64_winners
        for round_idx in range(1, len(round_names)):
            rn = round_names[round_idx]
            curr_winners: List[str] = []
            slot_idx = 0
            for i in range(0, len(prev_winners), 2):
                team_a = prev_winners[i]
                team_b = prev_winners[i + 1]
                winner, loser = _pick_winner(
                    team_a,
                    team_b,
                    rn,
                    ctx,
                    rng,
                    temperature=temperature,
                    pure_stochastic=pure_stochastic,
                )
                curr_winners.append(winner)
                counts = slot_outcomes[rn][slot_idx]
                key = (winner, loser)
                counts[key] = counts.get(key, 0) + 1
                slot_idx += 1
            prev_winners = curr_winners

        champion = prev_winners[0]
        champ_counts[champion] = champ_counts.get(champion, 0) + 1

    def _most_common_pair(counts: Dict[Tuple[str, str], int]) -> Tuple[str, str]:
        return sorted(counts.items(), key=lambda x: (-x[1], x[0][0], x[0][1]))[0][0]

    cumulative: Dict[str, List[List[str]]] = {}
    for rn in round_names:
        key = rn.lower() if rn != "Sweet16" else "sweet16"
        if rn == "Final4":
            key = "final4"
        if rn == "Champ":
            key = "championship"
        cumulative[key] = [list(_most_common_pair(c)) for c in slot_outcomes[rn]]

    champion_frequencies = [
        {"team": team, "count": cnt, "pct": float(cnt) / float(n_sims)}
        for team, cnt in sorted(champ_counts.items(), key=lambda x: (-x[1], x[0]))
    ]

    mode = "pure_stochastic" if pure_stochastic else "hybrid"
    return {
        "cumulative": cumulative,
        "championFrequencies": champion_frequencies,
        "meta": {
            "sims": int(n_sims),
            "temperature": float(temperature),
            "mode": mode,
        },
    }


def main(n_sims: int = 10000) -> None:
    """
    Entry point: train matchup model on historic data (CompactResults, Resumes,
    Seed Results, Upset Info, Preseason) + game_logs H2H for 2026; load bracket,
    run Monte Carlo sims, and print bracket-style prediction.
    """
    ctx = _load_2026_model_context()
    round1 = _load_2026_round1_matchups()

    stats = _simulate_bracket(ctx, round1, n_sims=n_sims)
    bracket = _deterministic_bracket(ctx, round1)

    # Pretty-print bracket in the requested narrative format
    print("=== Simulated title odds (top 10) ===")
    champ = stats["Champ"]
    total = float(n_sims)
    top_champ = sorted(champ.items(), key=lambda x: x[1], reverse=True)[:10]
    for team, cnt in top_champ:
        print(f"{team}: {cnt / total:.3%} title probability")

    def _print_round(rname: str, label: str) -> None:
        print(f"\n{label}:")
        for winner, loser, matchup in bracket[rname]:
            print(f"- {matchup}: {winner} over {loser}")

    _print_round("R64", "Round of 64")
    _print_round("R32", "Round of 32")
    _print_round("Sweet16", "Sweet 16")
    _print_round("Elite8", "Elite 8")
    _print_round("Final4", "Final Four")
    _print_round("Champ", "Championship Game")


if __name__ == "__main__":
    main()

