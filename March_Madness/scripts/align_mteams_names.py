"""Rewrite team strings in CSVs to match MTeams.csv TeamName."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "data"
MAP = {
    "Iowa St.": "Iowa St",
    "Kennesaw St.": "Kennesaw",
    "McNeese St.": "McNeese St",
    "Michigan St.": "Michigan St",
    "North Carolina St.": "NC State",
    "North Dakota St.": "N Dakota St",
    "Ohio St.": "Ohio St",
    "Prairie View A&M": "Prairie View",
    "Queens": "Queens NC",
    "Saint Louis": "St Louis",
    "Saint Mary's": "St Mary's CA",
    "St. John's": "St John's",
    "Tennessee St.": "Tennessee St",
    "Utah St.": "Utah St",
    "Wright St.": "Wright St",
    "East Tennessee St.": "ETSU",
}


def patch_file(path: Path) -> int:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        rows = list(csv.reader(f))
    if not rows:
        return 0
    header = rows[0]
    idxs = [i for i, h in enumerate(header) if h in ("TEAM", "team")]
    if not idxs:
        return 0
    n = 0
    for row in rows[1:]:
        while len(row) < len(header):
            row.append("")
        for i in idxs:
            v = row[i]
            if v in MAP:
                row[i] = MAP[v]
                n += 1
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    return n


def main() -> None:
    total = 0
    for path in sorted(ROOT.rglob("*.csv")):
        try:
            c = patch_file(path)
        except Exception as e:
            print(path, e)
            continue
        if c:
            print(f"{path.relative_to(ROOT)}: {c} cells")
            total += c
    print(f"Total: {total}")


if __name__ == "__main__":
    main()
