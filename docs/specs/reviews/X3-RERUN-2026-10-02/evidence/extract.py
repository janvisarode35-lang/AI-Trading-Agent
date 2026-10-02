"""X3 re-run: extract the four standard tables from the four Stage 1 specs.

Read-only on the repository. Splits markdown rows on unescaped pipes that are
outside backtick code spans, so `US` \\| `IN` stays one cell.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]  # repository root (path made relative for publication)
SPECS = {
    "P1.1": "docs/specs/SPEC-P1.1-DOMAIN.md",
    "P1.2": "docs/specs/SPEC-P1.2-STORAGE.md",
    "P1.3": "docs/specs/SPEC-P1.3-CONFIG.md",
    "P1.4": "docs/specs/SPEC-P1.4-AUDIT.md",
}
SECTIONS = ["DECISIONS MADE", "ASSUMPTIONS", "OPEN QUESTIONS", "CONTRACTS EXPORTED"]


def split_row(line: str) -> list[str]:
    cells, cur, in_code, i = [], [], False, 0
    s = line.strip()
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
            cur.append(ch)
        elif ch == "|" and not in_code:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    cells.append("".join(cur).strip())
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def tables(path: Path) -> dict[str, list[list[str]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: dict[str, list[list[str]]] = {}
    current = None
    for ln in lines:
        m = re.match(r"^## (.+?)\s*$", ln)
        if m:
            current = m.group(1) if m.group(1) in SECTIONS else None
            if current:
                out[current] = []
            continue
        if current and ln.startswith("|"):
            cells = split_row(ln)
            if all(re.fullmatch(r":?-+:?", c) for c in cells):
                continue
            out[current].append(cells)
    for k in out:
        out[k] = out[k][1:]  # drop header row
    return out


def header(path: Path) -> dict[str, str]:
    h = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---"
    for ln in lines[1:]:
        if ln == "---":
            break
        k, _, v = ln.partition(":")
        h[k.strip()] = v.strip()
    return h


def main() -> None:
    result = {}
    for key, rel in SPECS.items():
        p = REPO / rel
        result[key] = {"header": header(p), "tables": tables(p)}
    out = Path(sys.argv[1])
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    for key, v in result.items():
        h = v["header"]
        prod = [x.strip() for x in h["produces"].strip("[]").split(",")]
        print(f"{key}: version={h['version']} status={h['status']} produces={len(prod)}")
        print(f"   depends_on={h['depends_on']}")
        for s in SECTIONS:
            rows = v["tables"].get(s, [])
            widths = sorted({len(r) for r in rows})
            print(f"   {s}: {len(rows)} rows, cell-count set {widths}")


if __name__ == "__main__":
    main()
