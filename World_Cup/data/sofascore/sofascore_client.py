"""HTTP client for SofaScore's public JSON API (browser impersonation via curl_cffi)."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import quote
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

API_BASE = "https://www.sofascore.com/api/v1"

# WC Qual competition name patterns (men's football).
_QUAL_RE = re.compile(r"world\s*cup\s*qual", re.I)
_FIFA_WC_RE = re.compile(r"fifa\s*world\s*cup", re.I)
_YOUTH_RE = re.compile(r"\bU\d{2}\b", re.I)
_WOMEN_RE = re.compile(r"\bwomen\b|\bf\b", re.I)
_SKIP_FALLBACK_RE = re.compile(
    r"friendly|olympic|fifa\s*series|youth|women|\bU\d{2}\b",
    re.I,
)

# Continental / competitive fallbacks when WC qual stats are sparse (higher = prefer).
_FALLBACK_TIERS: List[Tuple[re.Pattern[str], int]] = [
    (re.compile(r"africa\s*cup\s*of\s*nations(?!\s*qual)", re.I), 100),
    (re.compile(r"asian\s*cup(?!\s*qual)", re.I), 100),
    (re.compile(r"concacaf\s*gold\s*cup|^gold\s*cup", re.I), 100),
    (re.compile(r"copa\s*america", re.I), 100),
    (re.compile(r"uefa\s*euro|european\s*championship", re.I), 100),
    (re.compile(r"nations\s*league", re.I), 85),
    (re.compile(r"african\s*nations\s*championship", re.I), 70),
    (re.compile(r"arab\s*cup", re.I), 60),
    (re.compile(r"afc\s*asian\s*cup\s*qual", re.I), 55),
    (re.compile(r"afcon\s*qual|africa\s*cup\s*of\s*nations\s*qual", re.I), 50),
]

ADVANCED_STAT_KEYS = (
    "avg_possession",
    "pass_completion_pct",
    "shots_on_target_pct",
    "set_piece_success_rate",
)
CORE_ADVANCED_KEYS = ADVANCED_STAT_KEYS[:3]

# Search query overrides when canonical name does not match SofaScore.
SEARCH_QUERY_OVERRIDES: Dict[str, str] = {
    "United States": "USA",
    "South Korea": "Korea Republic",
    "Côte d'Ivoire": "Ivory Coast",
    "Côte d&#x27;Ivoire": "Ivory Coast",
    "Turkey": "Türkiye",
    "IR Iran": "Iran",
    "Czech Republic": "Czechia",
    "Bosnia and Herzegovina": "Bosnia-Herzegovina",
    "DR Congo": "Congo DR",
    "Ivory Coast": "Côte d'Ivoire",
}


@dataclass(frozen=True)
class SeasonCandidate:
    unique_tournament_id: int
    season_id: int
    competition: str
    season: str
    source: str  # wc_qual | fallback
    priority: int
    season_year: int
    has_event_player_statistics: bool


def _season_year_value(season: Dict[str, Any]) -> int:
    year = season.get("year")
    if year is None:
        return 0
    if isinstance(year, int):
        return year
    text = str(year)
    found = re.findall(r"\d{4}", text)
    if found:
        return int(found[-1])
    try:
        return int(text)
    except ValueError:
        return 0


def advanced_stats_core_count(adv: Dict[str, float]) -> int:
    """How many of possession / pass% / SOT% are present."""
    return sum(1 for k in CORE_ADVANCED_KEYS if adv.get(k) == adv.get(k))


def advanced_stats_full_count(adv: Dict[str, float]) -> int:
    return sum(1 for k in ADVANCED_STAT_KEYS if adv.get(k) == adv.get(k))


def has_core_advanced_stats(adv: Dict[str, float]) -> bool:
    return advanced_stats_core_count(adv) == len(CORE_ADVANCED_KEYS)


def _fallback_tier(tournament_name: str) -> int:
    for pattern, tier in _FALLBACK_TIERS:
        if pattern.search(tournament_name):
            return tier
    return 0


def _get_session():
    try:
        from curl_cffi import requests as curl_requests

        return curl_requests.Session(impersonate="chrome")
    except ImportError as e:
        raise ImportError(
            "curl_cffi is required for SofaScore (Akamai WAF). "
            "Install: pip install curl_cffi"
        ) from e


class SofascoreClient:
    def __init__(self, *, delay_sec: float = 0.6, timeout: float = 30.0) -> None:
        self._session = _get_session()
        self._delay = delay_sec
        self._timeout = timeout
        self._last_request = 0.0

    def get_json(self, path: str, *, cache_path: Optional[Path] = None) -> Dict[str, Any]:
        if cache_path is not None and cache_path.is_file():
            return json.loads(cache_path.read_text(encoding="utf-8"))

        elapsed = time.monotonic() - self._last_request
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)

        url = path if path.startswith("http") else f"{API_BASE}{path}"
        resp = self._session.get(url, timeout=self._timeout)
        self._last_request = time.monotonic()
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(f"SofaScore API error for {path}: {data.get('error')}")

        if cache_path is not None:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    def search_team_id(self, query: str) -> Tuple[int, str]:
        """Return (team_id, sofascore_name) for a men's national football team."""
        path = f"/search/all?q={quote(query)}"
        data = self.get_json(path)
        results = data.get("results") or []
        if not isinstance(results, list):
            raise ValueError(f"Unexpected search response for {query!r}")

        candidates: List[Tuple[int, str, int]] = []
        for item in results:
            if item.get("type") != "team":
                continue
            ent = item.get("entity") or {}
            name = str(ent.get("name") or "")
            if _YOUTH_RE.search(name) or _WOMEN_RE.search(name):
                continue
            sport = ent.get("sport") or {}
            if sport.get("slug") not in (None, "football"):
                continue
            if ent.get("gender") not in (None, "M"):
                continue
            if ent.get("national") is False:
                continue
            tid = ent.get("id")
            if tid is None:
                continue
            score = int(ent.get("userCount") or 0)
            candidates.append((int(tid), name, score))

        if not candidates:
            raise ValueError(f"No national football team found for search {query!r}")

        # Prefer exact name match (case-insensitive), else highest userCount.
        q_lower = query.lower()
        exact = [c for c in candidates if c[1].lower() == q_lower]
        pool = exact if exact else candidates
        pool.sort(key=lambda x: x[2], reverse=True)
        tid, name, _ = pool[0]
        return tid, name

    def standings_seasons(self, team_id: int, *, cache_path: Optional[Path] = None) -> Dict[str, Any]:
        return self.get_json(f"/team/{team_id}/standings/seasons", cache_path=cache_path)

    def pick_wc_qual_season(
        self, seasons_payload: Dict[str, Any], *, prefer_year: int = 2026
    ) -> Tuple[int, int, str, str]:
        """
        Return (unique_tournament_id, season_id, tournament_name, season_name).
        """
        rows = seasons_payload.get("uniqueTournamentSeasons") or []
        qual_rows = []
        for row in rows:
            ut = row.get("uniqueTournament") or {}
            name = str(ut.get("name") or "")
            if not _QUAL_RE.search(name):
                continue
            if _WOMEN_RE.search(name):
                continue
            qual_rows.append(row)

        if not qual_rows:
            raise ValueError("No World Cup Qualification tournament in standings/seasons")

        # If multiple qual comps (rare), prefer name with shortest extra text.
        qual_rows.sort(key=lambda r: len(str((r.get("uniqueTournament") or {}).get("name") or "")))

        row = qual_rows[0]
        ut = row["uniqueTournament"]
        utid = int(ut["id"])
        tname = str(ut.get("name") or "")

        season_list = row.get("seasons") or []
        if not season_list:
            raise ValueError(f"No seasons listed for {tname}")

        def season_key(s: Dict[str, Any]) -> Tuple[int, int]:
            year = s.get("year")
            try:
                y = int(year)
            except (TypeError, ValueError):
                y = 0
            name = str(s.get("name") or "")
            boost = 1 if str(prefer_year) in name or str(prefer_year) == str(year) else 0
            return (boost, y)

        season_list = sorted(season_list, key=season_key, reverse=True)
        season = season_list[0]
        sid = int(season["id"])
        sname = str(season.get("name") or season.get("year") or sid)
        return utid, sid, tname, sname

    def list_season_candidates(
        self, seasons_payload: Dict[str, Any], *, prefer_qual_year: int = 2026
    ) -> List[SeasonCandidate]:
        """
        WC qual first, then continental / Nations League fallbacks (newest season each).
        """
        out: List[SeasonCandidate] = []
        seen: set[Tuple[int, int]] = set()

        try:
            utid, sid, tname, sname = self.pick_wc_qual_season(
                seasons_payload, prefer_year=prefer_qual_year
            )
            key = (utid, sid)
            if key not in seen:
                seen.add(key)
                out.append(
                    SeasonCandidate(
                        unique_tournament_id=utid,
                        season_id=sid,
                        competition=tname,
                        season=sname,
                        source="wc_qual",
                        priority=200,
                        season_year=prefer_qual_year,
                        has_event_player_statistics=False,
                    )
                )
        except ValueError:
            pass

        rows = seasons_payload.get("uniqueTournamentSeasons") or []
        fallback_rows: List[SeasonCandidate] = []
        wc_final_rows: List[SeasonCandidate] = []

        def _append_candidate(
            target: List[SeasonCandidate],
            *,
            utid: int,
            sid: int,
            tname: str,
            sname: str,
            source: str,
            priority: int,
            season_year: int,
            has_eps: bool,
        ) -> None:
            key = (utid, sid)
            if key in seen:
                return
            seen.add(key)
            target.append(
                SeasonCandidate(
                    unique_tournament_id=utid,
                    season_id=sid,
                    competition=tname,
                    season=sname,
                    source=source,
                    priority=priority,
                    season_year=season_year,
                    has_event_player_statistics=has_eps,
                )
            )

        max_seasons_per_tournament = 5
        for row in rows:
            ut = row.get("uniqueTournament") or {}
            tname = str(ut.get("name") or "")
            if not tname:
                continue
            if _WOMEN_RE.search(tname) or _YOUTH_RE.search(tname):
                continue

            utid = int(ut["id"])
            has_eps = bool(ut.get("hasEventPlayerStatistics"))
            season_list = sorted(
                row.get("seasons") or [],
                key=_season_year_value,
                reverse=True,
            )
            if not season_list:
                continue

            if _FIFA_WC_RE.search(tname) and not _QUAL_RE.search(tname):
                for season in season_list:
                    sy = _season_year_value(season)
                    if sy < 1990 or sy > 2022:
                        continue
                    sid = int(season["id"])
                    sname = str(season.get("name") or season.get("year") or sid)
                    _append_candidate(
                        wc_final_rows,
                        utid=utid,
                        sid=sid,
                        tname=tname,
                        sname=sname,
                        source="wc_finals_fallback",
                        priority=20,
                        season_year=sy,
                        has_eps=has_eps,
                    )
                continue

            if _QUAL_RE.search(tname) or _SKIP_FALLBACK_RE.search(tname):
                continue

            tier = _fallback_tier(tname)
            if tier == 0 and not has_eps:
                continue
            if tier == 0:
                tier = 15

            for season in season_list[:max_seasons_per_tournament]:
                sid = int(season["id"])
                sname = str(season.get("name") or season.get("year") or sid)
                _append_candidate(
                    fallback_rows,
                    utid=utid,
                    sid=sid,
                    tname=tname,
                    sname=sname,
                    source="fallback",
                    priority=tier,
                    season_year=_season_year_value(season),
                    has_eps=has_eps,
                )

        fallback_rows.sort(key=lambda c: (-c.priority, -c.season_year))
        wc_final_rows.sort(key=lambda c: -c.season_year)
        out.extend(fallback_rows)
        out.extend(wc_final_rows)
        return out

    def fetch_best_advanced_stats(
        self,
        team_id: int,
        seasons_payload: Dict[str, Any],
        *,
        cache_dir: Optional[Path] = None,
        use_cache: bool = True,
        prefer_qual_year: int = 2026,
    ) -> Tuple[SeasonCandidate, Dict[str, float], Dict[str, Any]]:
        """
        Try WC qual, then fallback competitions until core advanced stats exist.
        Returns (chosen season, extracted stats, raw statistics dict).
        """
        candidates = self.list_season_candidates(
            seasons_payload, prefer_qual_year=prefer_qual_year
        )
        if not candidates:
            raise ValueError("No tournament seasons found for team")

        best: Optional[Tuple[SeasonCandidate, Dict[str, float], Dict[str, Any]]] = None
        best_core = -1

        for cand in candidates:
            stats_path = None
            if use_cache and cache_dir is not None:
                stats_path = cache_dir / f"stats_{cand.unique_tournament_id}_{cand.season_id}.json"
            try:
                stats = self.team_statistics_overall(
                    team_id,
                    cand.unique_tournament_id,
                    cand.season_id,
                    cache_path=stats_path if use_cache else None,
                )
            except Exception:
                continue
            adv = extract_advanced_stats(stats)
            core = advanced_stats_core_count(adv)
            if core > best_core:
                best = (cand, adv, stats)
                best_core = core
            if has_core_advanced_stats(adv):
                return cand, adv, stats

        if best is None:
            raise ValueError("No statistics available for any candidate competition")
        return best

    def pick_fifa_world_cup_season(
        self, seasons_payload: Dict[str, Any], *, wc_year: int
    ) -> Tuple[int, int, str, str]:
        """
        Return (unique_tournament_id, season_id, tournament_name, season_name)
        for a completed FIFA World Cup edition (e.g. 2022 -> season 41087).
        """
        rows = seasons_payload.get("uniqueTournamentSeasons") or []
        wc_rows = []
        for row in rows:
            ut = row.get("uniqueTournament") or {}
            name = str(ut.get("name") or "")
            if not _FIFA_WC_RE.search(name):
                continue
            if _QUAL_RE.search(name):
                continue
            if _WOMEN_RE.search(name):
                continue
            wc_rows.append(row)

        if not wc_rows:
            raise ValueError(
                f"No FIFA World Cup tournament in standings/seasons for wc_year={wc_year}"
            )

        wc_rows.sort(
            key=lambda r: len(str((r.get("uniqueTournament") or {}).get("name") or ""))
        )
        row = wc_rows[0]
        ut = row["uniqueTournament"]
        utid = int(ut["id"])
        tname = str(ut.get("name") or "")

        season_list = row.get("seasons") or []
        if not season_list:
            raise ValueError(f"No seasons listed for {tname}")

        year_str = str(wc_year)

        def season_key(s: Dict[str, Any]) -> Tuple[int, int, int]:
            name = str(s.get("name") or "")
            try:
                y = int(s.get("year"))
            except (TypeError, ValueError):
                y = 0
            exact_year = 2 if y == wc_year or year_str in name else 0
            # Prefer seasons at or before wc_year (avoid grabbing a future edition).
            not_future = 1 if y <= wc_year or y == 0 else 0
            return (exact_year, not_future, y)

        season_list = sorted(season_list, key=season_key, reverse=True)
        best = season_list[0]
        if season_key(best)[0] == 0:
            raise ValueError(
                f"No FIFA World Cup season matching {wc_year} under {tname!r}"
            )
        sid = int(best["id"])
        sname = str(best.get("name") or best.get("year") or sid)
        return utid, sid, tname, sname

    def team_statistics_overall(
        self,
        team_id: int,
        unique_tournament_id: int,
        season_id: int,
        *,
        cache_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        path = (
            f"/team/{team_id}/unique-tournament/{unique_tournament_id}"
            f"/season/{season_id}/statistics/overall"
        )
        data = self.get_json(path, cache_path=cache_path)
        stats = data.get("statistics")
        if not isinstance(stats, dict):
            raise ValueError(f"Missing statistics object for team {team_id}")
        return stats


def extract_advanced_stats(stats: Dict[str, Any]) -> Dict[str, float]:
    """Map SofaScore overall statistics dict to model advanced features."""

    def _f(key: str) -> float:
        v = stats.get(key)
        if v is None:
            return float("nan")
        try:
            return float(v)
        except (TypeError, ValueError):
            return float("nan")

    poss = _f("averageBallPossession")
    pass_pct = _f("accuratePassesPercentage")
    if pass_pct != pass_pct:  # nan
        acc = _f("accuratePasses")
        tot = _f("totalPasses")
        if tot and tot == tot and tot > 0:
            pass_pct = 100.0 * acc / tot

    shots = _f("shots")
    sot = _f("shotsOnTarget")
    sot_pct = float("nan")
    if shots == shots and shots > 0 and sot == sot:
        sot_pct = 100.0 * sot / shots

    # Rough set-piece proxy: goals from set plays vs attempts (often sparse).
    sp_goals = _f("penaltyGoals") + _f("freeKickGoals")
    sp_attempts = _f("penaltiesTaken") + _f("freeKickShots")
    set_piece = float("nan")
    if sp_attempts == sp_attempts and sp_attempts > 0 and sp_goals == sp_goals:
        set_piece = 100.0 * sp_goals / sp_attempts

    return {
        "avg_possession": poss,
        "pass_completion_pct": pass_pct,
        "shots_on_target_pct": sot_pct,
        "set_piece_success_rate": set_piece,
        "sofascore_shots": shots,
        "sofascore_shots_on_target": sot,
    }
