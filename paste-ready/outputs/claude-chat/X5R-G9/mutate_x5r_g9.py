"""X5R-G9 mutation harness — evidence for STAGE-1-GAP-AUDIT §10 condition 12.

Applies each of the five single-field mutations that X5R-G9 found passing every suite to a
throwaway copy of the repository, then runs each named suite against that copy.

    python tests/mutate_x5r_g9.py tests/verify_p13_config.py tests/verify_p13_policy_diff.py

Exit 0 only if, for every mutation:
  - the mutated policy still LOADS (so the mutation is a real, deployable policy, not one the
    validator already rejects), and
  - at least one of the suites given with --must-fail FAILS on it.

Every suite is also run with `python -O`, because a check that only holds without -O is a
check that a production interpreter strips (X5 GAP-2).
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _rule(doc: dict, rule_id: str) -> dict:
    for r in doc["rules"]:
        if r["id"] == rule_id:
            return r
    raise KeyError(rule_id)


def _m_exp002_allow(doc: dict) -> None:
    _rule(doc, "EXP-002")["action"] = "ALLOW"


def _m_loss001_monitor(doc: dict) -> None:
    _rule(doc, "LOSS-001")["mode"] = "monitor"


def _m_loss004_20pct(doc: dict) -> None:
    _rule(doc, "LOSS-004")["threshold"] = 0.200


def _m_exec001_market(doc: dict) -> None:
    _rule(doc, "EXEC-001")["allowed_values"] = ["LIMIT", "MARKET"]


def _m_stop001_lte(doc: dict) -> None:
    _rule(doc, "STOP-001")["comparison"] = "lte"


MUTATIONS: dict[str, Callable[[dict], None]] = {
    "EXP-002 action -> ALLOW": _m_exp002_allow,
    "LOSS-001 mode -> monitor": _m_loss001_monitor,
    "LOSS-004 threshold -> 20%": _m_loss004_20pct,
    "EXEC-001 allows MARKET": _m_exec001_market,
    "STOP-001 comparison -> lte": _m_stop001_lte,
}


def mutated_policy(name: str) -> dict:
    doc = yaml.safe_load((ROOT / "config" / "policy.yaml").read_text(encoding="utf-8"))
    MUTATIONS[name](doc)
    return doc


def _copy_repo(dst: Path, policy: dict) -> None:
    for sub in ("src", "tests", "config"):
        shutil.copytree(ROOT / sub, dst / sub,
                        ignore=shutil.ignore_patterns("__pycache__", "_lint_probe_tmp"))
    (dst / "config" / "policy.yaml").write_text(
        yaml.safe_dump(policy, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _loads(dst: Path) -> bool:
    code = ("import sys; sys.path.insert(0, 'src'); from config import loader as L; "
            "L.PolicyLoader('config').load(require_signature=False)")
    return subprocess.run([sys.executable, "-c", code], cwd=dst,
                          capture_output=True).returncode == 0


def _suite_fails(dst: Path, suite: str, optimise: bool) -> bool:
    cmd = [sys.executable] + (["-O"] if optimise else []) + [suite]
    return subprocess.run(cmd, cwd=dst, capture_output=True).returncode != 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--must-fail", nargs="*", default=[],
                    help="suites of which at least one must fail on every mutation")
    ap.add_argument("suites", nargs="*", help="suites to report on")
    args = ap.parse_args()
    suites = list(dict.fromkeys(args.suites + args.must_fail))

    ok = True
    for name in MUTATIONS:
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d)
            _copy_repo(dst, mutated_policy(name))
            if not _loads(dst):
                print(f"[INVALID]  {name}: mutated policy does not load - not a real mutation")
                ok = False
                continue
            caught_by = []
            for s in suites:
                plain, opt = _suite_fails(dst, s, False), _suite_fails(dst, s, True)
                tag = "FAILS" if plain and opt else ("FAILS-ONLY-WITHOUT-O" if plain else "passes")
                print(f"  {name:32s} {s:42s} {tag}")
                if plain and opt and s in args.must_fail:
                    caught_by.append(s)
            if args.must_fail and not caught_by:
                print(f"[SURVIVED] {name}")
                ok = False
            elif args.must_fail:
                print(f"[KILLED]   {name}  by {', '.join(caught_by)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
