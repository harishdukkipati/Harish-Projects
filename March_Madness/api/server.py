from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src import bracket_sim as bs


class SimRequest(BaseModel):
    sims: int = Field(default=5000, ge=1, le=20000)
    temperature: float = Field(default=1.0, gt=0.0, le=3.0)
    pure_stochastic: bool = False
    seed: Optional[int] = None


app = FastAPI(title="March Madness API", version="1.0.0")
_CTX: Dict[str, Any] | None = None
_R64: pd.DataFrame | None = None


def _warm_context() -> None:
    global _CTX, _R64
    if _CTX is None:
        _CTX = bs._load_2026_model_context()
    if _R64 is None:
        _R64 = bs._load_2026_round1_matchups()


@app.on_event("startup")
def _startup() -> None:
    _warm_context()


@app.get("/health")
def health() -> Dict[str, bool]:
    return {"ok": True}


@app.get("/matchups/r64")
def get_r64_matchups() -> Dict[str, List[Dict[str, Any]]]:
    _warm_context()
    assert _R64 is not None
    cols = ["game_index", "team_a", "team_b", "seed_a", "seed_b", "team_no_a", "team_no_b"]
    out = _R64[cols].sort_values("game_index").to_dict(orient="records")
    return {"matchups": out}


@app.post("/simulate")
def simulate(req: SimRequest) -> Dict[str, Any]:
    _warm_context()
    assert _CTX is not None and _R64 is not None
    try:
        return bs.simulate_full_bracket_cumulative(
            _CTX,
            _R64,
            n_sims=req.sims,
            temperature=req.temperature,
            pure_stochastic=req.pure_stochastic,
            seed=req.seed,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
