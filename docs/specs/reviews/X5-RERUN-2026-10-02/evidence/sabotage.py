import shutil, subprocess, sys, pathlib, re
S = pathlib.Path(sys.argv[1]); base = S / "copy"; work = S / "sab"
SUITES = ["verify_p11_invariants","verify_p11_p12_contract","verify_p11_x2_regressions","verify_p11_x5_conditions","verify_p13_config","verify_p14_audit"]
MUT = [
 ("M01 regime UNKNOWN permits entries", "src/domain/models.py", "return self.label is not RegimeLabel.UNKNOWN", "return True"),
 ("M02 unreconciled position does not block", "src/domain/models.py", "return self.state is PositionState.UNRECONCILED", "return False"),
 ("M03 HALTED instrument tradeable (status check dropped)", "src/domain/models.py", "            and self.status is InstrumentStatus.ACTIVE\n", ""),
 ("M04 symbol mapping valid_to made inclusive", "src/domain/models.py", "(self.valid_to is None or on < self.valid_to)", "(self.valid_to is None or on <= self.valid_to)"),
 ("M05 non-final bar feeds a signal", "src/domain/models.py", "        if not self.is_final:\n            raise StaleDataError(", "        if False:\n            raise StaleDataError("),
 ("M06 money rounding half-even", "src/domain/models.py", "MONEY_ROUNDING: Final[str] = decimal.ROUND_HALF_UP", "MONEY_ROUNDING: Final[str] = decimal.ROUND_HALF_EVEN"),
 ("M07 settlement_date precedes trading_date allowed", "src/domain/models.py", "if self.settlement_date < self.trading_date:", "if False:"),
 ("M08 session open>=close allowed", "src/domain/models.py", "if self.regular_open_utc >= self.regular_close_utc:", "if False:"),
 ("M09 split without ratio allowed", "src/domain/models.py", "if self.action_type in needs_ratio and self.ratio is None:", "if False:"),
 ("M10 fundamentals disseminated before filed allowed", "src/domain/models.py", "if self.disseminated_at < self.filed_at:", "if False:"),
 ("M11 nth_prior_session off by one", "src/domain/models.py", "return self._sequenced[i - n]", "return self._sequenced[i - n + 1 if n else i]"),
 ("M12 loosening direction inverted for LTE", "src/config/loader.py", "        return change.new_value > change.old_value", "        return change.new_value < change.old_value"),
 ("M13 fail-open on_missing_input accepted", "src/config/loader.py", "if self.on_missing_input not in (RuleAction.DENY, RuleAction.KILL):", "if False:"),
 ("M14 chain deep content check disabled", "src/audit/chain.py", "if deep and not e.verify_self():", "if False:"),
 ("M15 is_effectful always False", "src/audit/events.py", "return EVENT_REGISTRY[self.event_type].is_effectful", "return False"),
 ("M16 Anchor.to_payload drops anchor_hash", "src/audit/chain.py", '            "anchor_hash": self.anchor_hash,\n', ""),
 ("M17 resolve_symbol returns first hit on ambiguity", "src/domain/models.py", 'raise AmbiguousSymbolError(f"{len(hits)} symbols for {instrument_id} on {on}")', "pass"),
 ("M18 delisted instrument without delisted_on allowed", "src/domain/models.py", "if self.status is InstrumentStatus.DELISTED and self.delisted_on is None:", "if False:"),
]
for name, path, old, new in MUT:
    if work.exists(): shutil.rmtree(work)
    shutil.copytree(base, work, ignore=shutil.ignore_patterns("__pycache__"))
    p = work / path; s = p.read_text(encoding="utf-8")
    if s.count(old) != 1:
        print(f"{name}: MUTATION NOT APPLIED (matches={s.count(old)})"); continue
    p.write_text(s.replace(old, new), encoding="utf-8")
    res = []
    for mode in ([], ["-O"]):
        failed = []
        for t in SUITES:
            r = subprocess.run(["py", "-3.11", *mode, f"tests/{t}.py"], cwd=work, capture_output=True, text=True)
            if r.returncode != 0:
                n = len(re.findall(r"^FAILED", r.stdout, re.M))
                failed.append(f"{t.replace('verify_','')}({n or 'exit'+str(r.returncode)})")
        res.append(", ".join(failed) or "ALL GREEN - NOT DETECTED")
    print(f"{name}\n    normal: {res[0]}\n    -O    : {res[1]}")
shutil.rmtree(work)
