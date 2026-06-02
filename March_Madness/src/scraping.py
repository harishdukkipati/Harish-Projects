from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Schedule page: id is the only thing that changes (defaults to current season).
ESPN_SCHEDULE_URL = "https://www.espn.com/mens-college-basketball/team/schedule/_/id/{team_id}"


@dataclass
class EspnTeamStatsConfig:
    """
    Configuration for scraping ESPN team stats.
    """

    base_url: str = "https://www.espn.com/mens-college-basketball/team/stats/_/id/{team_id}"


def _normalize_opponent(raw: str) -> str:
    """Strip 'vs'/'@', leading rank number, trailing '*'. e.g. 'vsNorth Florida' -> 'North Florida', 'vs13Arizona*' -> 'Arizona'."""
    if not raw:
        return ""
    s = raw.strip()
    s = re.sub(r"^(vs|@)\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^\d+\s*", "", s)
    s = s.rstrip("*").strip()
    return s


def fetch_html(url: str, *, timeout: float = 10.0) -> BeautifulSoup:
    """
    Download a single HTML page and parse it into a BeautifulSoup object.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MarchMadnessBot/0.1; +https://example.com/bot)"
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def parse_espn_schedule_page(
    soup: BeautifulSoup,
    team_name: str,
    espn_team_id: int,
    season: int,
    debug: bool = False,
) -> List[Dict]:
    """
    Parse an ESPN team schedule page and return a list of game rows
    (regular season). Table columns are DATE, OPPONENT, RESULT, W-L (CONF), ...
    """
    rows_out: List[Dict] = []
    # Result pattern: "W 75-60", "W78-76", "L 82-81" (with or without space; score can be in link)
    result_re = re.compile(r"^\s*(W|L)\s*(?:\[)?(\d+)-(\d+)(?:\])?\s*$", re.IGNORECASE)

    tables = soup.find_all("table")
    if debug:
        print(f"    [DEBUG] {team_name}: found {len(tables)} <table> elements")

    for ti, table in enumerate(tables):
        all_rows = table.find_all("tr")
        if not all_rows:
            continue
        # ESPN uses one table: first row is "Postseason", then that section's header/data,
        # then "Regular Season" and that section's header (DATE, OPPONENT, RESULT, ...) and data.
        # Find the row that has RESULT in it (the Regular Season header), not the first row.
        header_row = None
        header_idx = None
        for ri, tr in enumerate(all_rows):
            cells = tr.find_all(["th", "td"])
            headers = [c.get_text(strip=True).upper() for c in cells]
            if "RESULT" in headers:
                header_row = tr
                header_idx = ri
                break
        if not header_row or "RESULT" not in [c.get_text(strip=True).upper() for c in header_row.find_all(["th", "td"])]:
            if debug and ti < 2:
                print(f"    [DEBUG] table {ti}: no row with RESULT in headers")
            continue
        headers = [c.get_text(strip=True).upper() for c in header_row.find_all(["th", "td"])]
        if debug:
            print(f"    [DEBUG] table {ti}: found RESULT header at row {header_idx}, headers = {headers}")
        idx_date = headers.index("DATE") if "DATE" in headers else 0
        idx_opp = headers.index("OPPONENT") if "OPPONENT" in headers else 1
        idx_result = headers.index("RESULT")
        body_rows = all_rows[header_idx + 1:]
        if debug:
            print(f"    [DEBUG] table {ti} (Regular Season): {len(body_rows)} body rows, idx_date={idx_date} idx_opp={idx_opp} idx_result={idx_result}")
        for ri, tr in enumerate(body_rows):
            tds = tr.find_all("td")
            if len(tds) <= max(idx_date, idx_opp, idx_result):
                if debug and ri < 2:
                    print(f"    [DEBUG]   row {ri}: only {len(tds)} tds, need > {max(idx_date, idx_opp, idx_result)}")
                continue
            date_cell = tds[idx_date].get_text(strip=True)
            result_cell = tds[idx_result].get_text(strip=True)
            if debug and ri < 3:
                all_cells = [td.get_text(strip=True)[:40] for td in tds]
                print(f"    [DEBUG]   row {ri}: date={date_cell!r} result_cell={result_cell!r} | all_cells={all_cells}")
            # Skip postseason row (time like "2:50 PM") or empty
            if not result_cell:
                continue
            if ":" in result_cell and ("AM" in result_cell or "PM" in result_cell):
                continue
            match = result_re.match(result_cell)
            if debug and ri < 3:
                print(f"    [DEBUG]   row {ri}: result_re.match({result_cell!r}) = {match}")
            if not match:
                continue
            w_or_l, team_score_s, opp_score_s = match.group(1), match.group(2), match.group(3)
            try:
                team_score = int(team_score_s)
                opp_score = int(opp_score_s)
            except ValueError:
                continue
            is_win = w_or_l.upper() == "W"
            opponent_name = tds[idx_opp].get_text(strip=True)
            # If opponent cell is empty, try team link in row
            if not opponent_name:
                for a in tr.find_all("a", href=True):
                    if "/team/" in a.get("href", ""):
                        t = a.get_text(strip=True)
                        if t and not re.match(r"^\d+-\d+$", t):
                            opponent_name = t
                            break
            opponent_name = _normalize_opponent(opponent_name or "")
            result_str = f"{w_or_l} {team_score}-{opp_score}"
            rows_out.append({
                "season": season,
                "team": team_name,
                "espn_team_id": espn_team_id,
                "date": date_cell,
                "opponent": opponent_name,
                "result": result_str,
                "team_score": team_score,
                "opp_score": opp_score,
                "is_win": is_win,
            })
    return rows_out


def scrape_all_game_logs(
    team_ids_csv_path: str | Path,
    output_csv_path: str | Path,
    season: int = 2026,
    delay_seconds: float = 1.0,
    max_teams: int | None = None,
    debug: bool = False,
) -> pd.DataFrame:
    """
    Load team -> ESPN ID mapping from CSV, fetch each team's schedule page,
    parse game logs, and save to a single CSV. Polite delay between requests.
    If max_teams is set, only process that many teams (for debugging).
    """
    path = Path(team_ids_csv_path)
    mapping = pd.read_csv(path)
    if "team" not in mapping.columns or "espn_team_id" not in mapping.columns:
        raise ValueError(f"{path} must have columns 'team' and 'espn_team_id'")

    if max_teams is not None:
        mapping = mapping.head(max_teams)
        print(f"  [DEBUG] Limiting to first {max_teams} teams: {list(mapping['team'])}")

    all_games: List[Dict] = []
    for _, row in mapping.iterrows():
        team_name = str(row["team"]).strip()
        espn_id = int(row["espn_team_id"])
        url = ESPN_SCHEDULE_URL.format(team_id=espn_id)
        if debug:
            print(f"  [DEBUG] Fetching {url}")
        try:
            soup = fetch_html(url)
            if debug:
                print(f"  [DEBUG] Response length: {len(soup.get_text())} chars")
            games = parse_espn_schedule_page(soup, team_name, espn_id, season, debug=debug)
            all_games.extend(games)
            print(f"  {team_name}: {len(games)} games")
        except Exception as e:
            print(f"  {team_name}: failed ({e})")
            if debug:
                import traceback
                traceback.print_exc()
        time.sleep(delay_seconds)

    df = pd.DataFrame(all_games)
    out = Path(output_csv_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return df


def parse_espn_team_totals(soup: BeautifulSoup) -> Dict[str, float]:
    """
    Very small proof-of-concept parser that looks for a basic
    team totals table and extracts a handful of standard stats.

    This is intentionally conservative and may need adjustment
    once you pick specific ESPN pages to rely on.
    """
    tables = soup.find_all("table")
    if not tables:
        return {}

    # Heuristic: pick the first table and treat the last row as team totals.
    table = tables[0]
    rows = table.find_all("tr")
    if len(rows) < 2:
        return {}

    header_cells = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
    last_row_cells = [td.get_text(strip=True) for td in rows[-1].find_all("td")]

    stats = {}
    for col, val in zip(header_cells, last_row_cells):
        try:
            # Attempt to parse numeric values; silently skip non-numeric.
            stats[col] = float(val)
        except ValueError:
            continue

    return stats


def scrape_one_team_espn(team_id: int, config: EspnTeamStatsConfig | None = None) -> pd.DataFrame:
    """
    Proof-of-concept: scrape one team's ESPN stats page and return a
    one-row DataFrame of numeric totals.
    """
    if config is None:
        config = EspnTeamStatsConfig()

    url = config.base_url.format(team_id=team_id)
    soup = fetch_html(url)
    stats = parse_espn_team_totals(soup)

    if not stats:
        return pd.DataFrame()

    df = pd.DataFrame([stats])
    df.insert(0, "espn_team_id", team_id)
    return df


def scrape_many_teams_espn(team_ids: Iterable[int], config: EspnTeamStatsConfig | None = None) -> pd.DataFrame:
    """
    Scale scraping to multiple teams. This is a very light wrapper that
    loops over team_ids and concatenates results.
    """
    frames: List[pd.DataFrame] = []
    for tid in team_ids:
        try:
            df = scrape_one_team_espn(tid, config=config)
            if not df.empty:
                frames.append(df)
        except Exception:
            # Fail soft for now; you can add logging if desired.
            continue

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    print("Scraping 2026 game logs for all teams ...")
    df = scrape_all_game_logs(
        team_ids_csv_path=base / "data" / "team_espn_ids.csv",
        output_csv_path=base / "data" / "game_logs_2026.csv",
        season=2026,
        delay_seconds=1.0,
    )
    print(f"Done. Saved {len(df)} rows to data/game_logs_2026.csv")

