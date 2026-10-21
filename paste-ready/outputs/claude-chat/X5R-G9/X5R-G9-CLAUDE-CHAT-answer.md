Before writing a line, one challenge to the brief: you've asked me to treat "tightening" as the safe direction, but three rules in the frozen file show that a tighter policy is not always a safer one. I'll build the diff function, check that every mutation is actually caught, and set out that problem in the spec.

Green on the real file, with and without `-O`. Now the acceptance check — each mutation against both suites:

Now verifying the upstream defects I intend to report, rather than asserting them from reading:

All four defects confirmed by execution. Writing the spec amendment now.

Your brief takes "tightening is always safe" (ADR-09 row 3) as a given, and that is the assumption I'd challenge first. For any rule that can sit between the book and an exit, a smaller pass set traps positions instead of protecting them. Under the frozen §5.3, one operator with zero approvals could:
- narrow KILL-002's exemption list,
- remove `MARKET` from EXEC-001's emergency order types,
- raise HOLD-001's minimum hold, or
- set RATE-001 to 1 order/min.

The diff classifies all of these as UNDECIDABLE, which means two approvers. The spec amendment states this and the tests pin it.

**Acceptance results**
- [Certain] All five X5R-G9 mutations still load as valid policy, and each is caught by the new suite under `python -O`. `verify_p13_config.py` misses all five, which reproduces the audit finding.
- [Certain] I also tried every alternative `action`, `mode`, `comparison` and `scope` value on all 20 constitutional rules. That gave 264 mutations that load: the new suite catches all 264, the old suite caught 13.
- [Certain] The new suite passes 55/55 on the real file, with and without `-O`. A test fails if any field of `Rule` has no classification. The spec includes the §5.3 replacement text and the exact text to move condition 12 to CLOSED.

**Design choices you should check**
- [Likely] Direction is judged on the rule's pass set, with comparison and threshold treated as one predicate. That is what catches STOP-001 `eq → lte`: the threshold doesn't move, but the pass set grows.
- [Likely] The diff covers config keys outside `rules` too. Ten rule numbers are duplicated there, and lowering `universe.US.min_price_usd` loosens UNIV-001 without touching any rule text.
- [Certain] The approval count comes from the version currently in force, never the one being approved.
- [Likely] Any config key without a declared direction defaults to UNDECIDABLE. At team size 1, that makes even editing `schedule.US.pipeline_utc` impossible until a second approver is enrolled.

**Upstream defects (all confirmed by running code)**
- [Certain] Three of the five `threshold_ref` values don't resolve to any key. UNIV-001 points at `min_price`, but the key is `min_price_usd`. UNIV-002 has the same problem, and UNIV-003's reference is an expression rather than a key. P2.9 has nothing defined for this case.
- [Certain] The gap audit says no constitutional number is stated two ways, but `portfolio.max_position_pct` duplicates EXP-001.
- [Certain] A KILL-002 switched to monitor mode still grants its exemptions, because `PolicyGate` ignores mode for exemptions.
- [Certain] The signature covers the merged document, so any market or override layer invalidates it. `operator_override` is therefore not the runtime knob that §6 describes.
- [Guessing] My exit-path set (RATE-001/002, DATA-001, LIQ-001) assumes liquidation orders pass through `PolicyGate` and that P2.9 evaluates rules the way §3.2 implies. If P2.10 sends liquidation straight to the broker, that set is unnecessary, and so is KILL-002.

**Not verified**
- Python 3.12. Everything here ran on 3.13.
- `verify_p11_x5_conditions.py`, because `src/domain/models.py` wasn't in the paste. That suite fails with or without mutations, so it's not evidence either way.
- I left the FROZEN `loader.py` unedited, so `assert_change_authorised` still accepts a change list supplied by the caller. The amendment forbids using it for approval, but the bypass stays callable until P1.3 v0.2.