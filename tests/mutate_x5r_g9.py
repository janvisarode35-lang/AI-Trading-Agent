"""SPEC-P1.3.1 §7.3 and §7.5 mutation harness — evidence for STAGE-1-GAP-AUDIT §10 condition 12.

    py -3.11 tests/mutate_x5r_g9.py --must-fail tests/verify_p13_policy_diff.py
                                    --must-pass tests/verify_p13_config.py
    py -3.11 tests/mutate_x5r_g9.py --must-fail tests/verify_p13_policy_diff.py --negative-control
    py -3.11 tests/mutate_x5r_g9.py --sweep --must-fail tests/verify_p13_policy_diff.py
    py -3.11 tests/mutate_x5r_g9.py --sweep --must-fail tests/verify_p13_policy_diff.py --negative-control

A mutation is KILLED only if, in both `python` and `python -O`, the suite exits non-zero AND a
`FAILED` line names the expected pin with a message beginning `<RULE-ID>.<field>`. A suite exiting
non-zero is not evidence on its own: a fixture failure proves nothing.

`--negative-control` re-runs every mutation with the pins stubbed, and exits 0 only if every one
SURVIVED. That proves kills are attributed to pins and not to something incidental.

Each mutated policy must still LOAD. In the five-mutation run a policy that does not load is
[INVALID]. In the sweep it is simply not counted: that is what "Load" in §7.5's table counts.

The sweep runs only the pin tests (P13_PINS_ONLY), because attribution reads nothing else and
486 full runs in both modes would take hours. SPEC DEVIATION, recorded in the X1 notes.

Every run first requires the suites to pass on the unmutated repository, in both modes: a suite that
is already red kills every mutation and proves nothing. The sweep then requires the literal counts of
§7.5, because a harness that exits 0 with nothing tested is worse than no harness. #17's reviewed edit
changes these literals with the policy, as it does the pins.
"""
from __future__ import annotations

import argparse
import ast
import copy
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PIN_STUBS = ("_pin", "t_scope_and_mode_pinned_for_every_rule",
             "t_constitutional_set_is_exactly_the_table", "t_pinned_rule_set_is_exactly_the_file",
             "t_exemption_scope_is_pinned", "t_kill_scope_rules_are_pinned",
             "t_halt_entries_rules_are_pinned")
SCOPE_AND_MODE = "t_scope_and_mode_pinned_for_every_rule"
SCOPES = ("global", "strategy", "market", "instrument", "pool", "consolidated",
          "pool_and_consolidated")
ACTIONS = ("KILL", "DENY", "MODIFY", "ALLOW")
COMPARISONS = ("lte", "lt", "gte", "gt", "eq", "in", "not_in", "multiple_of", "exists")
#: §7.2's 20 constitutional rules. A literal, so the sweep cannot shrink with the file.
CONSTITUTIONAL = ("EXP-001", "EXP-002", "EXP-003", "EXP-004", "LOSS-001", "LOSS-002", "LOSS-003",
                  "LOSS-004", "SIZE-001", "LIQ-001", "RATE-001", "RATE-002", "STOP-001",
                  "EXEC-001", "DATA-001", "REGIME-001", "KILL-001", "AUDIT-001", "LLM-001",
                  "LLM-002")


SWEEP_GENERATED = 582
SWEEP_LOADABLE = 486


@dataclass(frozen=True)
class Mutation:
    rule: str
    field: str
    value: object

    @property
    def label(self) -> str:
        return f"{self.rule} {self.field} -> {self.value}"

    @property
    def expected(self) -> set[str]:
        pin = f"t_pin_{self.rule.replace('-', '_')}"
        if self.field in ("scope", "mode"):
            return {SCOPE_AND_MODE, pin} if self.rule in CONSTITUTIONAL else {SCOPE_AND_MODE}
        return {pin}


FIVE = (
    Mutation("EXP-002", "action", "ALLOW"),
    Mutation("LOSS-001", "mode", "monitor"),
    Mutation("LOSS-004", "threshold", 0.200),
    Mutation("EXEC-001", "allowed_values", ["LIMIT", "MARKET"]),
    Mutation("STOP-001", "comparison", "lte"),
)


def _base() -> dict:
    return yaml.safe_load((ROOT / "config" / "policy.yaml").read_text(encoding="utf-8"))


def _rule(doc: dict, rule_id: str) -> dict:
    for r in doc["rules"]:
        if r["id"] == rule_id:
            return r
    raise KeyError(rule_id)


def sweep_mutations() -> list[Mutation]:
    """§7.5's table: 582 generated, in the file's own rule order."""
    doc = _base()
    out: list[Mutation] = []
    for r in doc["rules"]:
        other = "monitor" if r["mode"] == "enforce" else "enforce"
        out.append(Mutation(r["id"], "mode", other))
        out.extend(Mutation(r["id"], "scope", s) for s in SCOPES if s != r["scope"])
    for rid in CONSTITUTIONAL:
        r = _rule(doc, rid)
        out.extend(Mutation(rid, "action", a) for a in ACTIONS if a != r["action"])
        out.extend(Mutation(rid, "comparison", c) for c in COMPARISONS if c != r["comparison"])
        if isinstance(r.get("threshold"), (int, float)) and not isinstance(r["threshold"], bool):
            t = r["threshold"]
            out.append(Mutation(rid, "threshold", t * 2))
            out.append(Mutation(rid, "threshold", t / 2))
    out.extend((
        Mutation("EXEC-001", "allowed_values", ["LIMIT", "MARKET"]),
        Mutation("KILL-001", "allowed_values", ["ARMED", "TRIPPED"]),
        Mutation("LLM-001", "allowed_values", [True]),
        Mutation("REGIME-001", "disallowed_values", ["BEAR"]),
        Mutation("EXEC-001", "allowed_values_emergency", ["LIMIT"]),
    ))
    return out


def stub_tests(source: str, names: Sequence[str]) -> str:
    """Replace the body of each named function with `return None`."""
    lines = source.split("\n")
    targets = [n for n in ast.parse(source).body
               if isinstance(n, ast.FunctionDef) and n.name in names]
    missing = set(names) - {n.name for n in targets}
    if missing:
        raise SystemExit(f"cannot stub, not found: {sorted(missing)}")
    for fn in sorted(targets, key=lambda n: n.lineno, reverse=True):
        lines[fn.body[0].lineno - 1:fn.end_lineno] = ["    return None"]
    return "\n".join(lines)


def _copy_repo(dst: Path, policy: dict, stub: Path | None, suite: str) -> None:
    for sub in ("src", "tests", "config"):
        shutil.copytree(ROOT / sub, dst / sub,
                        ignore=shutil.ignore_patterns("__pycache__", "_lint_probe_tmp"))
    (dst / "config" / "policy.yaml").write_text(
        yaml.safe_dump(policy, sort_keys=False, allow_unicode=True), encoding="utf-8")
    if stub is not None:
        shutil.copyfile(stub, dst / suite)


def _loads(dst: Path) -> bool:
    code = ("import sys; sys.path.insert(0, 'src'); from config import loader as L; "
            "L.PolicyLoader('config').load(require_signature=False)")
    return subprocess.run([sys.executable, "-c", code], cwd=dst, capture_output=True,
                          check=False).returncode == 0


def _env(pins_only: bool) -> dict[str, str]:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    env.pop("P13_PINS_ONLY", None)
    if pins_only:
        env["P13_PINS_ONLY"] = "1"
    return env


def _killed_in(dst: Path, suite: str, m: Mutation, optimise: bool, pins_only: bool) -> bool:
    cmd = [sys.executable] + (["-O"] if optimise else []) + [suite]
    r = subprocess.run(cmd, cwd=dst, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", check=False, env=_env(pins_only))
    if r.returncode == 0:
        return False
    prefix = f"{m.rule}.{m.field}"
    return any(line.startswith(f"FAILED {name}: {prefix}")
               for line in r.stdout.splitlines() for name in m.expected)


def _passes(dst: Path, suite: str, optimise: bool) -> bool:
    cmd = [sys.executable] + (["-O"] if optimise else []) + [suite]
    return subprocess.run(cmd, cwd=dst, capture_output=True, check=False,
                          env=_env(False)).returncode == 0


def baseline_is_green(suites: Sequence[str]) -> bool:
    """Every suite must pass, in both modes, before a mutation can mean anything."""
    ok = True
    for suite in suites:
        for optimise in (False, True):
            if not _passes(ROOT, suite, optimise):
                print(f"[BASELINE FAILED] {suite}{' -O' if optimise else ''}")
                ok = False
    return ok


def run_one(m: Mutation, args: argparse.Namespace, stub: Path | None) -> str:
    """One of KILLED, SURVIVED, INVALID, or FAILS-MUST-PASS."""
    doc = copy.deepcopy(_BASE)
    _rule(doc, m.rule)[m.field] = m.value
    with tempfile.TemporaryDirectory() as d:
        dst = Path(d)
        _copy_repo(dst, doc, stub, args.must_fail)
        if not _loads(dst):
            return "INVALID"
        for suite in args.must_pass:
            if not (_passes(dst, suite, False) and _passes(dst, suite, True)):
                return "FAILS-MUST-PASS"
        if all(_killed_in(dst, args.must_fail, m, o, args.sweep) for o in (False, True)):
            return "KILLED"
        return "SURVIVED"


_BASE = _base()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--must-fail", required=True)
    ap.add_argument("--must-pass", action="append", default=[])
    ap.add_argument("--negative-control", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    args = ap.parse_args()

    if not baseline_is_green([args.must_fail, *args.must_pass]):
        return 1
    mutations = sweep_mutations() if args.sweep else list(FIVE)
    with tempfile.TemporaryDirectory() as d:
        stub = None
        if args.negative_control:
            stub = Path(d) / "suite.py"
            source = (ROOT / args.must_fail).read_text(encoding="utf-8")
            stub.write_text(stub_tests(source, PIN_STUBS), encoding="utf-8")
        with ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as pool:
            results = list(pool.map(lambda m: run_one(m, args, stub), mutations))

    counts: dict[str, int] = {}
    for m, result in zip(mutations, results, strict=True):
        counts[result] = counts.get(result, 0) + 1
        quiet = args.sweep and result in ("INVALID", "SURVIVED" if args.negative_control else "KILLED")
        if not quiet:
            print(f"[{result}] {m.label}")
    print(f"generated {len(mutations)}, loadable {len(mutations) - counts.get('INVALID', 0)}: "
          f"{counts}")

    if counts.get("FAILS-MUST-PASS"):
        return 1
    if counts.get("INVALID") and not args.sweep:
        return 1
    loadable = len(mutations) - counts.get("INVALID", 0)
    if args.sweep and (len(mutations), loadable) != (SWEEP_GENERATED, SWEEP_LOADABLE):
        print(f"[COUNT] expected {SWEEP_GENERATED} generated and {SWEEP_LOADABLE} loadable (§7.5)")
        return 1
    wanted = "SURVIVED" if args.negative_control else "KILLED"
    return 0 if counts.get(wanted, 0) == loadable else 1


if __name__ == "__main__":
    sys.exit(main())
