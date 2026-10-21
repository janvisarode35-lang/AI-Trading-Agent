---
id: SPEC-P1.3.1-POLICY-DIFF
version: 0.1
status: DRAFT
phase: P1.3.1 — Policy diff and the two-person rule over every field (closes X5R-G2, X5R-G9)
depends_on: [SPEC-P1.3-CONFIG v0.1, STAGE-1-GAP-AUDIT §9 (X5R-G2, X5R-G9), STAGE-1-GAP-AUDIT §10 (condition 12), tests/verify_p11_x5_conditions.py (require() pattern)]
produces: [src/config/policy_diff.py, fn.diff_policies, fn.assert_policy_change_authorised, fn.key_direction, class.PolicyDiff, class.PolicyChange, class.PolicyDiffError, enum.Direction, enum.ChangeKind, enum.KeyDirection, const.CONFIG_KEY_DIRECTIONS, const.RULE_FIELDS, const.LIQUIDATION_PATH_RULES, tests/verify_p13_policy_diff.py, tests/mutate_x5r_g9.py, AMENDMENT SPEC-P1.3 §5.3]
---

# SPEC-P1.3.1 — Policy diff, and the two-person rule over every field

> **In one line:** the change list is derived from the two documents, never supplied by the
> person asking for approval, and anything the diff cannot prove is a tightening needs two people.

## 0. What this closes, and the premise it corrects

**X5R-G2.** SPEC-P1.3 §5.3 classes a change by `loosens_for(LimitChange, Rule)`. That function
sees one field (a numeric threshold), and only when the caller builds the `LimitChange`. A changed
`action`, `mode`, `comparison` or `scope`, a deleted rule, or a lowered config key that a rule
reads were invisible to governance and fell to the zero-approval tightening path.

**X5R-G9.** Five single-field mutations loaded and passed every suite. They are now killed, and so
are all 264 loadable governed-field mutations of the 20 constitutional rules (§8).

**The premise this phase corrects.** ADR-09 row 3 says "tightening is always safe". It is false
for any rule that can stand between the book and an *exit*. Narrowing KILL-002's exemption list,
removing `MARKET` from EXEC-001's emergency set, raising HOLD-001's minimum hold, or cutting
RATE-001 to 1 order/min all make a rule act *more* often — and all can trap a position during a
kill-switch liquidation. Under §5.3 as frozen, a single operator could do any of them with zero
approvals. This phase classifies them UNDECIDABLE (§3.4). ADR-09 is not amended; §5.3 is narrowed,
which ADR-09 row 3 itself permits because a stricter control is a tightening of governance.

## 1. BLOCKING questions — and the defaults applied

| # | Question | Options | Default applied | What breaks if the default is wrong |
|---|---|---|---|---|
| **1** | How is direction judged? | (a) per-field heuristics; (b) **the rule's pass set**: the observed values for which it does not act | **(b)** `[DEFAULT-D1]` | Under (a), `eq 2.5 → lte 2.5` (STOP-001) is "comparison changed, threshold unchanged" and has no direction. Under (b) it is `{2.5} → (−∞, 2.5]`: the pass set grew, so it loosens. One algebra covers thresholds, comparisons, value sets and scope |
| **2** | What is diffed? | (a) the single `policy.yaml` file; (b) **the merged effective document per (market, environment) combination, as `PolicyLoader` hashes it** | **(b)** `[DEFAULT-D2]` | Under (a) a loosening placed in `policy.market.IN.yaml` is never seen. The approval for a change is the union over every combination that will be loaded |
| **3** | What does UNDECIDABLE cost? | (a) treated as NEUTRAL; (b) its own approval count; (c) **treated as LOOSENS** | **(c)** — required by the brief `[DEFAULT-D3]` | (a) makes every incomparable change free, which is exactly the hole X5R-G2 describes |
| **4** | Is a pass-set shrink on an exit-gating rule a tightening? | (a) yes, per ADR-09 row 3; (b) **no — UNDECIDABLE** | **(b)** `[DEFAULT-D4]` | Under (a) one operator can, with no approval, make kill-switch liquidation impossible. That is [CONST-7] defeated through the governance layer |
| **5** | Is a monitor rule's predicate classified? | (a) NEUTRAL, it does not bind; (b) **classified as if it bound** | **(b)** `[DEFAULT-D5]` | Under (a): loosen CASH-002 while in monitor (free), then promote to enforce (free, a tightening). Two free steps equal one unapproved loosening |
| **6** | Which version's governance sets the approval count? | (a) the new; (b) **the active (old)** | **(b)** `[DEFAULT-D6]` | Under (a) a version that lowers its own threshold approves itself. The validator forbids < 2 today, but that is a second control; this one must not depend on it |
| **7** | Default for a config key with no declared direction | (a) NEUTRAL; (b) **UNDECIDABLE** | **(b)** `[DEFAULT-D7]` | Under (a) every new key, and every key a rule reads by `threshold_ref`, is free to change. **Operational consequence, stated:** at team size 1, changing an unlisted key (e.g. `schedule.US.pipeline_utc`) is impossible until a second approver is enrolled (Q-P1.3-1). Adding the key to `CONFIG_KEY_DIRECTIONS` as NEUTRAL is a code change under `DEPLOY_CODE` (ADR-09 row 10) |
| **8** | Severity lowered | (a) NEUTRAL — §4.2 says severity is "only" alert routing; (b) **LOOSENS** | **(b)** `[DEFAULT-D8]` | Lowering LOSS-004 from CRITICAL to LOW changes no verdict but delays the human. An alert is a control |
| **9** | `authority` edited | (a) NEUTRAL text; (b) **UNDECIDABLE** | **(b)** `[DEFAULT-D9]` | Re-attributing a `[CONST]` rule to an ADR is the first step of moving it out of the constitutional approval regime |
| **10** | How are exit-gating rules identified? | (a) a new `applies_to` schema field; (b) **schema-derivable signals plus an explicit, test-pinned set** | **(b)** `[DEFAULT-D10]` | The schema has no field for it (F-5). (b) can miss a future rule that gates exits; `t_liquidation_path_set_is_pinned` makes the set a reviewed change, and (a) is recommended for SPEC-P1.3 v0.2 |

## 2. NON-BLOCKING details resolved

| # | Detail | Resolution |
|---|---|---|
| 1 | Float vs Decimal | YAML parses `0.050` as a float. Both sides are compared as `Decimal(str(v))`. `0.050 → 0.05` and `20 → 20.0` are NEUTRAL (same number) |
| 2 | Inclusive bounds | Intervals carry closedness. `lte t` is `(−∞, t]`, `lt t` is `(−∞, t)`, `eq t` is `{t}`. So `lte → lt` at the same `t` tightens; `eq → lte` loosens |
| 3 | Symbolic bounds | `threshold_input` / `threshold_ref` are opaque tokens. Comparable only to the *same* token: `lte settled_cash → lt settled_cash` tightens; `lte settled_cash → lte cash` is UNDECIDABLE |
| 4 | Order in sets | `inputs`, `exempts`, `allowed_values*`, `disallowed_values`, and set-valued config keys compare as sets. Reordering is not a change |
| 5 | Lists of mappings | `hitl.actions`, `latency.stages` flatten by index. Reordering rows is a change, and UNDECIDABLE |
| 6 | Absent vs `null` | Absent is `CONFIG_REMOVED`/`CONFIG_ADDED`. A value changed to `null` is a value change whose numeric check fails → UNDECIDABLE |
| 7 | Removed vs re-added rule | Ids are never reused (SPEC-P1.3 §2 row 1). EXP-001 removed and EXP-007 added at 8% is two changes, and the removal alone is LOOSENS |
| 8 | Approver identity | Same normalisation as §5.3: strip, lower-case, de-duplicate, drop empties. `["js", " JS"]` is one person |
| 9 | Empty diff | Zero changes → zero approvals. A re-signed identical document is not a policy change |
| 10 | Record order | Changes are sorted by `(path, field)`, so the record is byte-reproducible (the property §4.2 buys for evaluation order) |
| 11 | Interpreter | Every suite is run with and without `python -O` |

## 3. Classification rules

### 3.1 The principle

A rule's **pass set** is the set of observed values for which it does not act. For a rule whose
action is DENY, MODIFY or KILL:

| New pass set vs old | Direction | Why |
|---|---|---|
| equal | NEUTRAL | No observation changes outcome |
| strict subset | TIGHTENS | The rule now acts on everything it acted on before, and more |
| strict superset | LOOSENS | Something it used to stop, it now lets through |
| neither | UNDECIDABLE | Some observations newly pass and others newly fail. No ordering exists |

This is why a raised threshold loosens `lte` and tightens `gte`: `(−∞, 0.05] ⊂ (−∞, 0.08]` and
`[0.20, ∞) ⊃ [0.30, ∞)`. The existing `NotImplementedError` on `LimitChange.loosens` stays
correct — direction needs the comparison, and the diff is where both are known.

### 3.2 Per field, for a rule present in both versions

| Field | Rule | Reasoning |
|---|---|---|
| `comparison` + `threshold` + `threshold_ref` + `threshold_input` | **Judged jointly** as one predicate: interval containment for `lte lt gte gt eq` with comparable bounds; else UNDECIDABLE | They are one predicate. Judged separately, `eq 2.5 → lte 2.5` has an unchanged threshold and a directionless comparison change. A switch of threshold *source* (constant ↔ ref ↔ input) is UNDECIDABLE: a constant cannot be ordered against a reference statically |
| `action` | Lattice KILL > DENY > MODIFY > ALLOW. Up the lattice TIGHTENS, down LOOSENS | Same lattice as §4.1. DENY → ALLOW makes the rule incapable of binding |
| `mode` | enforce → monitor LOOSENS; monitor → enforce TIGHTENS | A monitor rule never binds (§4.3). Promotion is ADR-09 row 3's tightening (Q-P1.3-4) |
| `scope` | Coverage sets: `pool_and_consolidated = {pool, consolidated}`. Coverage shrink LOOSENS, growth TIGHTENS. Every other pair UNDECIDABLE | Only this family nests. `strategy → global` on RATE-002 counts a different population against the same number |
| `on_missing_input` | KILL > DENY. DENY → KILL TIGHTENS | An unknown input halting the book is the stronger response |
| `kill_scope` | GLOBAL > POOL. Appear/disappear UNDECIDABLE | |
| `severity` | CRITICAL > HIGH > MEDIUM > LOW. Down LOOSENS `[DEFAULT-D8]` | Alert routing is a control |
| `allowed_values` | Under `in` on both sides: the set *is* the pass set. Under any other comparison: UNDECIDABLE | `[LIMIT] → [LIMIT, MARKET]` grows the pass set: LOOSENS |
| `disallowed_values` | Under `not_in` on both sides: growth TIGHTENS. Else UNDECIDABLE | The deny-set is the complement of the pass set |
| `allowed_values_emergency` | Growth LOOSENS. **Shrink UNDECIDABLE** | Shrinking it blocks a risk-reducing action (§3.4) |
| `allowed_values_ref` | Any change UNDECIDABLE | Repointing a reference |
| `exempts` | Growth LOOSENS. **Shrink UNDECIDABLE** | Fewer exemptions re-subject kill-switch liquidation to settlement, PDT and rate rules (§3.4) |
| `inputs` | Superset TIGHTENS; subset LOOSENS; swap UNDECIDABLE | Each input is one fail-closed path ([CONST-6]); removing one means the gate can no longer see it go missing |
| `measurement.basis` / `.window` / `.timing` | Any change UNDECIDABLE | Not monotone in the threshold. A shorter `sessions:N` loss window reports a smaller loss; a longer `rolling_seconds` rate window counts more orders; a median window is neither |
| `modify.to` | Numeric, same `*_pct` target: higher LOOSENS, lower TIGHTENS. Symbolic or other numeric: UNDECIDABLE | EXP-006 trimming to 6% instead of 4% trims less. Symbolic targets' arithmetic lives in P2.9 |
| `modify.target`, `modify` appearing/disappearing | UNDECIDABLE | The MODIFY now changes a different quantity |
| `authority` | UNDECIDABLE `[DEFAULT-D9]` | |
| `description`, `notes` | NEUTRAL | Free text; no verdict changes |
| `id` | Not a field change | A different id is a removal plus an addition (§3.3) |

`t_every_rule_field_is_classified` asserts `RULE_FIELDS == set(Rule.model_fields)`, so a field
added to `Rule` without a classification fails CI rather than being silently ignored.

### 3.3 Rule addition and removal

| Change | Direction | Reasoning |
|---|---|---|
| Rule **removed** | LOOSENS | Whatever it bounded is now unbounded. The id is retired, never reused |
| Exemption-granting rule removed (KILL-002) | UNDECIDABLE | Re-subjects liquidation to seven rules |
| Rule added: enforced DENY/MODIFY/KILL | TIGHTENS | |
| Rule added: gates an exit (§3.4) | UNDECIDABLE | |
| Rule added: grants exemptions | LOOSENS | Regardless of mode — see F-3 |
| Rule added: monitor, or ALLOW without exemptions | NEUTRAL | Cannot bind |

### 3.4 Overlays: where a smaller pass set is not safer

After per-field classification, every TIGHTENS on the following rules becomes UNDECIDABLE:

| Rule set | Signal | Example |
|---|---|---|
| Exemption-granting rules | `exempts` non-empty (KILL-002 today) | Removing CASH-001 from the exemption |
| Exit-gating rules | `measurement.timing == "pre_exit"` (HOLD-001 today) | Minimum hold raised from 3 to 30 sessions |
| Liquidation-path rules | `LIQUIDATION_PATH_RULES` = RATE-001, RATE-002, DATA-001, LIQ-001: not exempted by KILL-002, with a tunable threshold | RATE-001 at 1/min; DATA-001 at 1 s denies liquidation on any quiet tape |

LOOSENS on those rules stays LOOSENS. A `mode` change on an exemption-granting rule is
UNDECIDABLE in both directions, because `PolicyGate` applies exemptions regardless of mode (F-3).

### 3.5 Non-rule configuration

Every leaf outside `rules` is classified by `CONFIG_KEY_DIRECTIONS`, an ordered table, first match
wins, ending in `** → UNDECIDABLE`. Kinds: `HIGHER_LOOSENS`, `LOWER_LOOSENS`, `TRUE_LOOSENS`,
`FALSE_LOOSENS`, `SET_GROW_LOOSENS`, `SET_SHRINK_LOOSENS`, `NEUTRAL`, `UNDECIDABLE`.

**Why config keys are in scope at all.** At least ten numbers that rules depend on live outside
`rules` (F-2), and UNIV-001/002 read config through `threshold_ref`. Lowering
`universe.US.min_price_usd` from `"5.00"` to `"1.00"` changes no rule text and loosens UNIV-001;
lowering `cost.assumed_round_trip_bps.US` loosens EDGE-001. Both are LOOSENS here.

| Key | Kind | Key | Kind |
|---|---|---|---|
| `metadata.**`, `policy_version` | NEUTRAL | `universe.*.min_*` | LOWER_LOOSENS |
| `governance.min_approvals_to_loosen` | LOWER_LOOSENS | `universe.*.max_instruments`, `enter_rank`, `exit_rank` | HIGHER_LOOSENS |
| `governance/hitl.risk_deny_override_permitted` | TRUE_LOOSENS | `decision.min_edge_multiple_of_cost` | LOWER_LOOSENS |
| `kill_switch.requires_human_to_re_enable` | FALSE_LOOSENS | `cost.assumed_round_trip_bps.*` | LOWER_LOOSENS |
| `kill_switch.auto_re_enable_permitted` | TRUE_LOOSENS | `cost.verified_monthly_usd.*`, `vm_`, `backup_`, `total_operating_is_complete` | NEUTRAL |
| `fx.system_may_convert`, `llm.may_receive_portfolio_state` | TRUE_LOOSENS | `instrument_allowlist.tradeable` | SET_GROW_LOOSENS |
| `risk_evaluation.*` | FALSE_LOOSENS | `instrument_allowlist.permanently_banned` | SET_SHRINK_LOOSENS |
| `llm.replay_requires_approval`, `replay_offpeak_only` | FALSE_LOOSENS | `latency.exit.stale_bar_critical_seconds` | HIGHER_LOOSENS |
| `llm.gate_width`, `max_concurrency`, `spend_alarm_*` | HIGHER_LOOSENS | `dr.rpo_state_seconds`, `dr.rto_*` | HIGHER_LOOSENS |
| `account.enforce_settled_cash`, `enforce_day_trades` | FALSE_LOOSENS | `storage.records_retention_years` | LOWER_LOOSENS |
| `account.pdt_equity_floor_usd` | LOWER_LOOSENS | `storage.disk_*_pct` | HIGHER_LOOSENS |
| `account.pdt_max_day_trades_5d` | HIGHER_LOOSENS | `promotion.min_*`, `shadow_min_sessions`, `dsr_threshold` | LOWER_LOOSENS |
| `portfolio.max_position_pct`, `forced_trim_pct` | HIGHER_LOOSENS | `holding.time_stop_sessions`, `hard_max_sessions` | HIGHER_LOOSENS |
| `portfolio.min_cash_pct` | LOWER_LOOSENS | `holding.time_stop_min_return_pct` | LOWER_LOOSENS |
| `turnover.*` | HIGHER_LOOSENS | **everything else** | **UNDECIDABLE** |

A removed key is LOOSENS (whatever read it now reads nothing); an added key is UNDECIDABLE;
NEUTRAL keys stay NEUTRAL when added or removed. A set key changed by both adding and removing
members is UNDECIDABLE. A type change (number → string, bool → int) is UNDECIDABLE.

## 4. Types

```python
class Direction(str, Enum):
    LOOSENS = "LOOSENS"; TIGHTENS = "TIGHTENS"; NEUTRAL = "NEUTRAL"; UNDECIDABLE = "UNDECIDABLE"

class ChangeKind(str, Enum):
    RULE_ADDED = "RULE_ADDED"; RULE_REMOVED = "RULE_REMOVED"; RULE_FIELD = "RULE_FIELD"
    CONFIG_ADDED = "CONFIG_ADDED"; CONFIG_REMOVED = "CONFIG_REMOVED"; CONFIG_VALUE = "CONFIG_VALUE"

class PolicyChange(BaseModel):            # frozen, extra="forbid"
    kind: ChangeKind
    path: str            # "rules.<ID>.<field>" | "rules.<ID>" | dotted config path; never empty
    rule_id: str | None  # set iff kind is RULE_*; matches ^[A-Z]{2,7}-\d{3}$
    field: str | None    # set iff kind is RULE_FIELD; "measurement.window", "modify.to", ...
    old: str | None      # canonical string; None = absent in the old version
    new: str | None      # canonical string; None = absent in the new version
    direction: Direction
    reason: str          # human-readable; written to the audit record verbatim
    # requires_two_person: direction in {LOOSENS, UNDECIDABLE}

class PolicyDiff(BaseModel):              # frozen, extra="forbid"
    old_version: str     # ^\d+\.\d+\.\d+$, from the validated old document
    new_version: str
    changes: tuple[PolicyChange, ...]   # sorted by (path, field); empty = no change
    # requires_two_person: any change requires it
```

Canonical strings: `Decimal` via `str`, floats via `str(Decimal(str(f)))`, enums by value, sets
sorted, mappings by sorted key. No timestamps and no units enter a `PolicyChange`: units belong
to the rule (`*_pct` is a fraction, SPEC-P1.3 §3.3), and the change record is time-free so the
same pair of versions always yields the same bytes.

## 5. AMENDMENT — SPEC-P1.3 §5.3, exact replacement text

Replace SPEC-P1.3 §5.3 from "**Direction is judged against the rule's comparison**" through the
end of the paragraph beginning "**Two distinct *identities***" with:

> **The change list is derived, never declared.** `assert_policy_change_authorised(old, new,
> approvers)` computes the change list itself with `diff_policies()` over the two **effective**
> (merged) documents, for every (market, environment) combination that will be loaded
> (SPEC-P1.3.1). A caller cannot omit a change by not mentioning it. `assert_change_authorised()`
> and `LimitChange` are superseded for authorisation and must not be called on the approval path.
>
> **Every field is classified** LOOSENS, TIGHTENS, NEUTRAL or UNDECIDABLE by the rules in
> SPEC-P1.3.1 §3: comparison and threshold judged jointly on the pass set; `action` on the
> KILL > DENY > MODIFY > ALLOW lattice; `mode` enforce → monitor is a loosening; `scope` by
> coverage; removing a rule is a loosening; and every leaf outside `rules` by
> `CONFIG_KEY_DIRECTIONS`.
>
> **The two-person rule applies to every LOOSENS and every UNDECIDABLE change.** UNDECIDABLE is
> treated as a loosening because a change that cannot be proven to tighten does not get the
> tightening path ([CONST-6]).
>
> **A smaller pass set is not a tightening on a rule that can block an exit.** On an
> exemption-granting rule, a `pre_exit` rule, or a rule in `LIQUIDATION_PATH_RULES`, a change
> that would otherwise tighten is UNDECIDABLE. "Tightening is always safe" (ADR-09 row 3) holds
> only for rules that cannot stand between the book and a risk-reducing exit.
>
> **The approval count is the active version's.** `min_approvals_to_loosen` is read from the
> version being replaced, never from the version being approved.
>
> **Two distinct *identities*, not two approvals.** Unchanged from v0.1: normalised and
> de-duplicated; `["js", "JS "]` is one person.

The table at the head of §5.3 gains one row:

| Direction | Approvals | Authority |
|---|---|---|
| **Undecidable** — the diff cannot prove the direction | **2 distinct identities** | SPEC-P1.3.1 §3, `[CONST-6]` |

## 6. Error paths

| Condition | Exception / outcome | Fail-closed behaviour |
|---|---|---|
| Old or new document fails `PolicyDocument` validation | `PolicyDiffError` (a `PolicyError`) | No change list exists; nothing is authorised. Raised by `assert_policy_change_authorised` too |
| A comparison bound is a token on one side and a number on the other | UNDECIDABLE | Two-person |
| Two different tokens | UNDECIDABLE | Two-person |
| A set-valued key is not a list on one side | UNDECIDABLE | Two-person |
| A numeric key becomes a non-number or `null` | UNDECIDABLE | Two-person |
| A config key with no table entry | UNDECIDABLE (`**` catch-all) | Two-person |
| A `Rule` field with no classification | Impossible at runtime: `t_every_rule_field_is_classified` fails CI first | — |
| Loosening/undecidable change with fewer distinct approvers than the **active** version requires | `PolicyGovernanceError` | Change refused |
| Any change set that is entirely TIGHTENS/NEUTRAL | Returns the `PolicyDiff` | Caller writes it to the audit trail before the version takes effect ([CONST-5]) |

## 7. Upstream defects found — required output

| # | Defect | Evidence (executed) | Consequence | Owner |
|---|---|---|---|---|
| **F-1** | `threshold_ref` is never validated, and 3 of 5 do not resolve. UNIV-001 references `universe.{market}.min_price`; the key is `min_price_usd`/`min_price_inr`. UNIV-002 references `min_market_cap`; the key is `min_market_cap_usd`/`_inr`. UNIV-003's "ref" is an expression, `max(...)`, not a key | Resolution check over `policy.yaml`: UNIV-001/002/003 DO NOT RESOLVE for US or IN; UNIV-004/005 resolve | Whatever P2.9 does with an unresolvable ref is unspecified. If it treats it as a missing input, UNIV-001..003 deny every instrument — safe, but an empty universe. If it does anything else it is inventing a threshold. **The diff cannot attribute a key change to these rules**, which is why config keys are classified directly (§3.5) | P1.3 v0.2: validate every `threshold_ref` resolves; split UNIV-003 into data |
| **F-2** | **STAGE-1-GAP-AUDIT §9 says no Block A number is "stated two ways". It is.** `portfolio.max_position_pct: 0.050` duplicates EXP-001; `forced_trim_pct` EXP-006; `min_cash_pct` PORT-001; `turnover.*` TURN-001/002; `holding.min_sessions/time_stop_sessions/hard_max_sessions` HOLD-001/002/003; `decision.min_edge_multiple_of_cost` EDGE-001; `account.pdt_max_day_trades_5d` CASH-002 | `portfolio.max_position_pct 0.05` and `EXP-001 0.05` read from the same load | The two copies can diverge in one signed version and nothing detects it. The diff governs both; it does not reconcile them | P1.3 v0.2: one copy, referenced by `threshold_ref` |
| **F-3** | `PolicyGate` applies an exemption whenever an ALLOW rule passes, **regardless of `mode`**. A monitor-mode KILL-002 still exempts | Set KILL-002 to `monitor`, fail CASH-001: verdict `ALLOW` | §4.3's "monitor does not bind" is false for exemptions. Mode changes on exemption rules are UNDECIDABLE here until fixed | P1.3 v0.2: `if passed and rule.binds and ...` in `PolicyGate.evaluate` |
| **F-4** | The signature covers the **merged** document. Any market, environment or override layer changes the signed hash | Base hash ≠ hash with a one-key `policy.market.IN.yaml` | One signature per (market, env, override) combination, not one per policy version. And the `operator_override` layer is not a runtime knob as §6 describes: changing it invalidates the signature, so the process does not start until it is re-signed | Q-P1.3.1-2 |
| **F-5** | No field says whether a rule applies to exits | Schema of `Rule` | `LIQUIDATION_PATH_RULES` has to be explicit (§3.4, `[DEFAULT-D10]`) | P1.3 v0.2: `applies_to: entry \| exit \| both` |
| **F-6** | `assert_change_authorised()` is still exported and still trusts a caller-supplied change list | `loader.py` §8 | The bypass X5R-G2 describes stays callable. This phase does not edit the FROZEN loader; the amendment forbids its use on the approval path | P6.2 / P6.4 must call `assert_policy_change_authorised`; remove in P1.3 v0.2 |
| **F-7** | ADR-09 row 3 "tightening is always safe" is false for exit-gating rules | §0, §3.4 | Narrowed here, in §5.3, without amending ADR-09 | Owner may wish to annotate ADR-09 row 3 |

## 8. Verification

All runs: Python 3.13.16, pydantic 2.13.5, PyYAML 6.0.3, cryptography 50.0.1. **Not run on 3.12**
(condition 15 stays open).

| Check | Result |
|---|---|
| `tests/verify_p13_policy_diff.py` on the real file | **55/55 PASS**, with and without `-O` |
| `tests/verify_p13_config.py` on the real file (unchanged) | 39/39 PASS |
| `tests/mutate_x5r_g9.py --must-fail tests/verify_p13_policy_diff.py` | **5/5 KILLED**, each under `-O`. Each mutated policy still loads, so each is a real, deployable mutation |
| Same five against `verify_p13_config.py` | 5/5 survive — X5R-G9 reproduced |
| Sweep: every alternative `action`/`mode`/`comparison`/`scope` value on each of the 20 constitutional rules | 360 mutations: 96 rejected by the loader; **264 loadable, 264 killed** by the new suite; the old suite killed 13 of the 264 |

Which tests kill each X5R-G9 mutation (under `-O`):

| Mutation | Failing tests |
|---|---|
| EXP-002 `action` → ALLOW | `t_pin_EXP_002`, `t_action_follows_the_lattice`, `t_x5r_g9_…` |
| LOSS-001 `mode` → monitor | `t_pin_LOSS_001`, `t_mode_enforce_to_monitor_loosens_and_back_tightens`, `t_x5r_g9_…` |
| LOSS-004 `threshold` → 20% | `t_pin_LOSS_004`, `t_threshold_direction_respects_comparison`, `t_x5r_g9_…` |
| EXEC-001 allows MARKET | `t_pin_EXEC_001`, `t_value_sets`, `t_x5r_g9_…` |
| STOP-001 `comparison` → lte | `t_pin_STOP_001`, `t_comparison_changes_by_pass_set`, `t_x5r_g9_…` |

The pins are the primary detector. The diff tests also fail on a mutated tree only because their
fixtures are read from the mutated file — that is incidental and is not counted as evidence.

**Pinned per constitutional rule** (20 rules: authority cites `[CONST…]` or `IMMUTABLE`):
`action`, `mode`, `comparison`, `scope`, `threshold`, `on_missing_input`, `kill_scope`,
`allowed_values`, `allowed_values_emergency`, `disallowed_values`, `measurement` (basis, window,
timing), `inputs`, absence of `threshold_ref`/`threshold_input`, and `binds`.
`t_constitutional_set_is_exactly_the_table` pins membership, so a rule cannot leave the set by an
`authority` edit and a new `[CONST]` rule cannot arrive unpinned.

**Not pinned, deliberately:** the 27 non-constitutional rules. A tightening of one needs zero
approvals by governance; a pin would turn it into a `DEPLOY_CODE` change. They are governed at
change time by the diff, not at test time by a table.

**Not verified here:** `tests/verify_p11_x5_conditions.py`, because `src/domain/models.py` was not
in the input. It fails identically mutated and unmutated, so it is not evidence either way.

## 9. Text for STAGE-1-GAP-AUDIT §10 — condition 12 to CLOSED

Replace the condition 12 row with:

| # | Condition | Gates | Severity | State |
|---|---|---|---|---|
| **12** | Pin `action`, `mode`, `comparison` and `scope` of the constitutional rules; define loosening for a non-threshold change (X5R-G2) | P2.9; any policy change | HIGH | **CLOSED** 2026-10-19 by SPEC-P1.3.1-POLICY-DIFF v0.1 — see evidence below |

Add below the table:

> **Condition 12 — closure evidence.** (1) `tests/verify_p13_policy_diff.py` pins 16 governed
> fields of each of the 20 constitutional rules and pins the membership of that set; it uses
> `require()` and passes 55/55 under both `python` and `python -O`. (2) The five X5R-G9 mutations
> each still load and are each killed under `-O` (`tests/mutate_x5r_g9.py --must-fail
> tests/verify_p13_policy_diff.py`, exit 0). (3) A sweep of every alternative `action`, `mode`,
> `comparison` and `scope` across the 20 rules produced 264 loadable mutations, all killed; the
> pre-existing suite killed 13. (4) `src/config/policy_diff.py` derives the complete change list
> between two policy versions and classifies every `Rule` field and every config leaf as
> LOOSENS / TIGHTENS / NEUTRAL / UNDECIDABLE; `t_every_rule_field_is_classified` makes an
> unclassified field a CI failure. (5) SPEC-P1.3 §5.3 is amended to apply the two-person rule
> to every LOOSENS and UNDECIDABLE change, with the approval count taken from the active version.
> **Residue carried, not closed:** F-1 to F-6 of SPEC-P1.3.1 §7 (P1.3 v0.2); Q-P1.3-1 (second
> approver); Python 3.12+ (condition 15); the X5 conditions suite was not re-run (domain models
> not in scope of this change).

And in §9, the sentence "A rule's `action`, `mode`, `comparison` and `scope` are not pinned" is
replaced by "Pinned by SPEC-P1.3.1 (condition 12, CLOSED)". The sentence "none stated two ways"
is replaced by "none stated two ways inside `rules`; ten are duplicated in non-rule config
(SPEC-P1.3.1 F-2)".

---

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | Direction is judged on the pass set; comparison and threshold jointly | One algebra covers thresholds, comparisons, value sets and scope. Separate judgement is how STOP-001 `eq → lte` slipped | Yes | **Critical** — a misclassified loosening takes the zero-approval path |
| 2 | UNDECIDABLE is a first-class outcome and costs two approvers | Required; [CONST-6] applied to governance | No | Low — the cost is friction, never a loss |
| 3 | Shrinks on exemption, `pre_exit` and liquidation-path rules are UNDECIDABLE, not TIGHTENS | A "tightening" there can trap a liquidation; ADR-09 row 3 does not hold for them | Yes | **Critical** if reversed — one operator could disable the exit path |
| 4 | The diff runs on merged effective documents, per (market, env) | Layer-only loosenings would otherwise be invisible | Yes | High |
| 5 | Monitor rules are classified as if they bound | Blocks the loosen-then-promote laundering path | Yes | High |
| 6 | Approval count comes from the active version | A version must not approve itself | No | High |
| 7 | Unlisted config keys default to UNDECIDABLE | Fail closed; a rule may read any key | Yes | Medium — operational friction at team size 1 |
| 8 | Pins cover the 20 constitutional rules, not all 47 | Pinning non-constitutional rules makes free tightenings into code deployments | Yes | Medium — non-constitutional rules rely on change-time diffing |
| 9 | `LIQUIDATION_PATH_RULES` is an explicit, test-pinned set | The schema has no `applies_to` (F-5) | Yes — replace with a schema field | High if a new exit-gating rule is not added |
| 10 | The FROZEN loader is not edited | Code under a frozen spec changes with a spec revision, not a side-patch | Yes | Low — F-3 and F-6 stay open until P1.3 v0.2 |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|---|---|---|---|
| 1 | `[DEFAULT-D1]` P2.9's evaluator implements `passed = observed <comparison> threshold` | P2.9 is unwritten; SPEC-P1.3 §3.2 implies it | P2.9's evaluator, against `t_threshold_direction_respects_comparison` | Every pass-set classification inverts |
| 2 | `[DEFAULT-D10]` RATE-001/002, DATA-001, LIQ-001 are the only tunable rules that bind against liquidation | KILL-002's notes say EXP-*, LOSS-*, INST-001 cannot bind against a reduction; that depends on P2.9 | P2.9: run a liquidation order through every rule | A missed rule's tightening is free and can slow an exit |
| 3 | EXP-*/LOSS-* cannot bind against a sell | KILL-002 notes | Same | Same |
| 4 | Severity lowered is a loosening `[DEFAULT-D8]` | Alerting is a control in practice | Owner | Some severity edits need two people unnecessarily |
| 5 | `[DEFAULT-D2]` every (market, env) combination that will run is enumerable at approval time | `TRADING_ENV` and markets are a small fixed set | P6.4 deployment manifest | A combination missed at approval runs unapproved |
| 6 | Directions in `CONFIG_KEY_DIRECTIONS` are as tabulated — e.g. lowering `pdt_equity_floor_usd` restricts fewer accounts | Reading of ADR-13 Chain D / PDT rule; the floor itself is unverified (condition 16) | Broker PDT documentation | One key misclassified |

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|---|---|---|---|
| **Q-P1.3.1-1** | Who is the second approver? (carries Q-P1.3-1) | Owner | Enrol a second Ed25519 identity in Vault | Every LOOSENS **and every UNDECIDABLE** change — wider than before; includes edits to any unlisted config key |
| **Q-P1.3.1-2** | One signature per (market, env, override) combination, or sign the base layer and hash layers separately? (F-4) | Owner + P6.4 | SPEC-P1.3 §5.2 vs §6; `PolicyLoader.load()` signs `content_hash(merged)` | P6.4 deployment; any use of `operator_override` |
| **Q-P1.3.1-3** | How should P2.9 treat an unresolvable `threshold_ref` (F-1)? | P2.9 author | UNIV-001/002/003 refs vs `universe.*` keys | **P2.9** |
| **Q-P1.3.1-4** | Add `applies_to` to `Rule` (F-5)? | P1.3 v0.2 | `Rule` schema | Nothing today; replaces `LIQUIDATION_PATH_RULES` |
| **Q-P1.3.1-5** | Does the liquidation path go through `PolicyGate` at all, or straight to the broker? | P2.10 | P2.10 kill-switch liquidation design | If it bypasses the gate, §3.4's liquidation overlay is unneeded — and KILL-002 is dead |
| Q15 *(carried)* | Suites on Python 3.12+ | CI | `python3.12 -O tests/verify_p13_policy_diff.py` | All |

## CONTRACTS EXPORTED

| Name | Kind | Signature or schema | Consumers |
|---|---|---|---|
| `diff_policies` | function | `(old_raw: Mapping, new_raw: Mapping) -> PolicyDiff`; raises `PolicyDiffError` | P6.2, P6.4 |
| `assert_policy_change_authorised` | function | `(old_raw, new_raw, approver_ids: Sequence[str]) -> PolicyDiff`; raises `PolicyGovernanceError` / `PolicyDiffError` | **P6.2, P6.4 — the only approval path** |
| `PolicyDiff` | model | `old_version, new_version, changes`; `.requires_two_person`, `.by_direction()`, `.for_rule()` | P6.2, P1.4 (audit record of the approval) |
| `PolicyChange` | model | §4 | P1.4 |
| `PolicyDiffError` | exception | subclass of `PolicyError` | P6.2 |
| `Direction`, `ChangeKind`, `KeyDirection` | enums | §4, §3.5 | P6.2, P1.4 |
| `CONFIG_KEY_DIRECTIONS` | constant | ordered `(pattern, KeyDirection)`; last entry `("**", UNDECIDABLE)` | P6.2; any phase adding a config key |
| `RULE_FIELDS` | constant | equals `set(Rule.model_fields)` | CI |
| `LIQUIDATION_PATH_RULES` | constant | `{"RATE-001","RATE-002","DATA-001","LIQ-001"}` | P2.10 |
| `key_direction` | function | `(path: str) -> KeyDirection` | P6.2 |
| `tests/verify_p13_policy_diff.py` | test suite | 55 checks, `require()` only | **CI**, run with and without `-O` |
| `tests/mutate_x5r_g9.py` | test harness | `[--must-fail SUITE ...] [SUITE ...]` → exit 0 iff every mutation loads and is killed | CI, gap audits |

**END OF SPEC-P1.3.1-POLICY-DIFF v0.1**
