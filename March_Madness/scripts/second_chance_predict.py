#!/usr/bin/env python3
"""
Second Chance bracket: score Sweet 16 from JSON, then Elite 8 / Final 4 / Champ.

Default JSON: data/bracket_data/bracket.json (if present), else built-in slate.

Canonical team strings must match Resumes.csv "TEAM" in the JSON file; printing
uses DISPLAY_NAMES for friendlier labels (e.g. St.John's, Iowa State).

Default: each game independently picks mode with 50% probability — deterministic (adj P≥0.5)
or stochastic (Bernoulli sample). That choice is re-rolled every game, every sim.
  --pure-stochastic  Every game uses random sampling only (old behavior).
  --temperature T    T>1 pulls P toward 50% before the rule above (default 1.0).
  --sims N           Bracket runs (default 1). N>1 prints champion frequencies + example.
  --seed S           RNG seed (same seed → same draws).
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.bracket_sim import _load_2026_model_context, _p_team_a_wins  # noqa: E402

DEFAULT_JSON = ROOT / "data" / "bracket_data/bracket.json"

# Canonical names from archive 2/Resumes.csv (2026 rows)
DEFAULT_REGIONS: Dict[str, List[Tuple[str, str]]] = {
    "East": [("Duke", "St John's"), ("Michigan St", "Connecticut")],
    "South": [("Iowa", "Nebraska"), ("Illinois", "Houston")],
    "West": [("Arizona", "Arkansas"), ("Purdue", "Texas")],
    "Midwest": [("Michigan", "Alabama"), ("Tennessee", "Iowa St")],
}

REGION_ORDER = ("East", "South", "West", "Midwest")

DISPLAY_NAMES: Dict[str, str] = {
    "St John's": "St.John's",
    "Iowa St": "Iowa State",
}

# Per game, P(this game uses deterministic ≥0.5 pick); else Bernoulli(P(win)).
HYBRID_DETERMINISTIC_FRACTION = 0.5


def _disp(name: str) -> str:
    return DISPLAY_NAMES.get(name, name)


def _load_regions(path: Path | None) -> Dict[str, List[Tuple[str, str]]]:
    if path is None:
        return {k: [tuple(p) for p in v] for k, v in DEFAULT_REGIONS.items()}
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        print(
            f"Warning: {path} is empty; using built-in DEFAULT_REGIONS. "
            "Paste valid JSON or delete the file.",
            file=sys.stderr,
        )
        return {k: [tuple(p) for p in v] for k, v in DEFAULT_REGIONS.items()}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in {path}: {e}\n"
            "Fix the file or pass --json to a valid path."
        ) from e
    out: Dict[str, List[Tuple[str, str]]] = {}
    for reg in REGION_ORDER:
        games = data.get(reg) or data.get(reg.lower())
        if not games:
            raise ValueError(f"JSON missing region {reg!r} (list of [team_a, team_b] pairs)")
        out[reg] = [(str(a), str(b)) for a, b in games]
        if len(out[reg]) != 2:
            raise ValueError(f"Region {reg} must have exactly 2 Sweet 16 games, got {len(out[reg])}")
    return out


def _apply_temperature(p: float, temperature: float) -> float:
    """T>1 pulls probability toward 0.5; T=1 unchanged; 0<T<1 sharper."""
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    if abs(temperature - 1.0) < 1e-12:
        return float(p)
    eps = 1e-9
    p = min(max(float(p), eps), 1.0 - eps)
    logit = math.log(p / (1.0 - p))
    scaled = logit / temperature
    return 1.0 / (1.0 + math.exp(-scaled))


def _adjusted_p(ctx: Any, team_a: str, team_b: str, rnd: str, temperature: float) -> float:
    p = _p_team_a_wins(team_a, team_b, rnd, ctx)
    return _apply_temperature(p, temperature)


def _winner_loser(
    ctx: Any,
    team_a: str,
    team_b: str,
    rnd: str,
    rng: random.Random,
    *,
    temperature: float = 1.0,
    hybrid: bool = True,
) -> Tuple[str, str]:
    p = _adjusted_p(ctx, team_a, team_b, rnd, temperature)
    use_deterministic = hybrid and (rng.random() < HYBRID_DETERMINISTIC_FRACTION)
    if use_deterministic:
        w = team_a if p >= 0.5 else team_b
    else:
        w = team_a if rng.random() < p else team_b
    l = team_b if w == team_a else team_a
    return w, l


@dataclass
class BracketLines:
    sweet_lines: List[str]
    elite_lines: List[str]
    ff_line1: str
    ff_line2: str
    champ_line: str
    champion: str
    sweet_outcomes: List[Tuple[str, str]]
    elite_outcomes: List[Tuple[str, str]]
    ff_outcomes: List[Tuple[str, str]]
    champ_outcome: Tuple[str, str]


def _run_bracket(
    regions: Dict[str, List[Tuple[str, str]]],
    ctx: Any,
    rng: random.Random,
    *,
    temperature: float,
    hybrid: bool = True,
) -> BracketLines:
    sweet_winners: Dict[str, List[str]] = {r: [] for r in REGION_ORDER}
    sweet_lines: List[str] = []
    sweet_outcomes: List[Tuple[str, str]] = []

    for reg in REGION_ORDER:
        for team_a, team_b in regions[reg]:
            w, l = _winner_loser(
                ctx, team_a, team_b, "Sweet16", rng, temperature=temperature, hybrid=hybrid
            )
            sweet_winners[reg].append(w)
            sweet_outcomes.append((w, l))
            sweet_lines.append(f"{_disp(w)} over {_disp(l)}")

    elite_winners: Dict[str, str] = {}
    elite_lines: List[str] = []
    elite_outcomes: List[Tuple[str, str]] = []
    for reg in REGION_ORDER:
        w0, w1 = sweet_winners[reg]
        ew, el = _winner_loser(ctx, w0, w1, "Elite8", rng, temperature=temperature, hybrid=hybrid)
        elite_winners[reg] = ew
        elite_outcomes.append((ew, el))
        elite_lines.append(f"{_disp(ew)} over {_disp(el)}")

    e, s, w, m = [elite_winners[r] for r in REGION_ORDER]
    ff1_w, ff1_l = _winner_loser(ctx, e, s, "Final4", rng, temperature=temperature, hybrid=hybrid)
    ff2_w, ff2_l = _winner_loser(ctx, w, m, "Final4", rng, temperature=temperature, hybrid=hybrid)

    champ_w, champ_l = _winner_loser(
        ctx, ff1_w, ff2_w, "Champ", rng, temperature=temperature, hybrid=hybrid
    )

    ff_outcomes = [(ff1_w, ff1_l), (ff2_w, ff2_l)]
    champ_outcome = (champ_w, champ_l)
    return BracketLines(
        sweet_lines=sweet_lines,
        elite_lines=elite_lines,
        ff_line1=f"{_disp(ff1_w)} over {_disp(ff1_l)}",
        ff_line2=f"{_disp(ff2_w)} over {_disp(ff2_l)}",
        champ_line=f"{_disp(champ_w)} over {_disp(champ_l)}",
        champion=champ_w,
        sweet_outcomes=sweet_outcomes,
        elite_outcomes=elite_outcomes,
        ff_outcomes=ff_outcomes,
        champ_outcome=champ_outcome,
    )


def _print_bracket(lines: BracketLines) -> None:
    print("Sweet 16")
    for i, line in enumerate(lines.sweet_lines, start=1):
        print(f"{i}. {line}")
    print("\nElite 8:")
    for i, line in enumerate(lines.elite_lines, start=1):
        print(f"{i}. {line}")
    print("\nFinal Four")
    print(f"1. {lines.ff_line1}")
    print(f"2. {lines.ff_line2}")
    print("\nChampionship:")
    print(f"1. {lines.champ_line}")


def _resolve_json_path(explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit
    if DEFAULT_JSON.is_file():
        return DEFAULT_JSON
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description="Second Chance predictions (Sweet 16 -> Champ)")
    ap.add_argument(
        "--json",
        type=Path,
        default=None,
        help=f"Path to regions JSON; default {DEFAULT_JSON} if that file exists, else built-in slate",
    )
    ap.add_argument(
        "--verbose",
        action="store_true",
        help="Also print model win probabilities (raw and temperature-adjusted) for each game",
    )
    ap.add_argument(
        "--temperature",
        type=float,
        default=1.0,
        help=">1 softens win probs toward 50%% before picking (default 1.0 = model output)",
    )
    ap.add_argument(
        "--sims",
        type=int,
        default=1,
        help="Number of full bracket runs (default 1). N>1 prints champion frequencies.",
    )
    ap.add_argument(
        "--seed",
        type=int,
        default=None,
        help="RNG seed for sampling (reproducible brackets)",
    )
    ap.add_argument(
        "--pure-stochastic",
        action="store_true",
        help="Every game uses random sampling (no 50/50 mix with deterministic ≥0.5)",
    )
    args = ap.parse_args()

    if args.sims < 1:
        ap.error("--sims must be >= 1")
    if args.temperature <= 0:
        ap.error("--temperature must be positive")

    regions = _load_regions(_resolve_json_path(args.json))
    ctx = _load_2026_model_context()
    hybrid = not args.pure_stochastic

    if args.verbose and args.sims == 1:
        print(f"=== Sweet 16 win probabilities: raw → T={args.temperature:g} ===\n")
        for reg in REGION_ORDER:
            print(f"{reg}:")
            for team_a, team_b in regions[reg]:
                pr = _p_team_a_wins(team_a, team_b, "Sweet16", ctx)
                pa = _apply_temperature(pr, args.temperature)
                print(f"  {team_a} vs {team_b}: P({team_a} wins) raw={pr:.3f} adj={pa:.3f}")
        print()

    if args.sims == 1:
        rng = random.Random(args.seed) if args.seed is not None else random.Random()
        lines = _run_bracket(regions, ctx, rng, temperature=args.temperature, hybrid=hybrid)
        _print_bracket(lines)
        return

    master = random.Random(args.seed) if args.seed is not None else random.Random()
    sweet_counts: List[Counter[Tuple[str, str]]] = [Counter() for _ in range(8)]
    elite_counts: List[Counter[Tuple[str, str]]] = [Counter() for _ in range(4)]
    ff_counts: List[Counter[Tuple[str, str]]] = [Counter() for _ in range(2)]
    champ_counts: Counter[Tuple[str, str]] = Counter()

    for _ in range(args.sims):
        lines = _run_bracket(regions, ctx, master, temperature=args.temperature, hybrid=hybrid)
        for i, out in enumerate(lines.sweet_outcomes):
            sweet_counts[i][out] += 1
        for i, out in enumerate(lines.elite_outcomes):
            elite_counts[i][out] += 1
        for i, out in enumerate(lines.ff_outcomes):
            ff_counts[i][out] += 1
        champ_counts[lines.champ_outcome] += 1

    sweet_consensus = [c.most_common(1)[0][0] for c in sweet_counts]
    elite_consensus = [c.most_common(1)[0][0] for c in elite_counts]
    ff_consensus = [c.most_common(1)[0][0] for c in ff_counts]
    champ_consensus = champ_counts.most_common(1)[0][0]

    consensus = BracketLines(
        sweet_lines=[f"{_disp(w)} over {_disp(l)}" for w, l in sweet_consensus],
        elite_lines=[f"{_disp(w)} over {_disp(l)}" for w, l in elite_consensus],
        ff_line1=f"{_disp(ff_consensus[0][0])} over {_disp(ff_consensus[0][1])}",
        ff_line2=f"{_disp(ff_consensus[1][0])} over {_disp(ff_consensus[1][1])}",
        champ_line=f"{_disp(champ_consensus[0])} over {_disp(champ_consensus[1])}",
        champion=champ_consensus[0],
        sweet_outcomes=sweet_consensus,
        elite_outcomes=elite_consensus,
        ff_outcomes=ff_consensus,
        champ_outcome=champ_consensus,
    )

    print(f"=== Cumulative bracket from {args.sims} sims ===\n")
    _print_bracket(consensus)


if __name__ == "__main__":
    main()
