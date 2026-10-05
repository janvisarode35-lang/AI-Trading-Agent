# X5 — GAP AUDIT, Stage 1 re-run — full report

| | |
|---|---|
| Template | `docs/PROMPT-PACK.md`, "X5 — Gap Audit", all five PRODUCE items |
| Run on | 2026-10-02, in its own conversation |
| Commit | `3cd91a0`, branch `main`, working tree clean at start and at end |
| Required by | `STAGE-1-FREEZE.md` §11.6 step 5 |
| Repository changes | **None.** Nothing edited, staged, committed or pushed |
| Development database | `ai-trading-tsdb` not connected to, not modified |
| Not opened | `AI-Trading-Agent-stage1-review-drafts` — not opened, not listed, not read |

> **Publication note, 2026-10-02.** This is the report as produced by the read-only re-run, published
> on the Owner's instruction. Only this note was added. `STAGE-1-GAP-AUDIT.proposed.diff` is kept as
> the reviewed artifact; it is applied to `STAGE-1-GAP-AUDIT.md` in the record commit that follows
> this folder's publication, so it no longer applies to the tree after that commit. "Repository
> changes: None" and "Not applied" below describe the re-run itself.

**Reading this report.** Finding ids use the prefix `X5R-`. `X5R-G` is a gap, `X5R-E` is an error
in the existing audit (`STAGE-1-GAP-AUDIT.md`, taken at `605ff40`), `X5R-X` is a point where I
differ from the X3 re-run. X3's ids (`X3R-…`) are quoted as it wrote them.

---

## 0. Summary

### 0.1 Verdict

# GO WITH CONDITIONS

Stated bluntly: **no Stage 2 phase may start today.** Two entry conditions are open (E-1, E-2 in
§5). Once they are met, P2.1 may start as a specification phase. **P2.1 code may not write an
audit event** until condition 9 is closed, and it may not land until condition 11 is closed.

Not GO: the entry gate in the record is wrong, one spec is not re-frozen, and the code P2.1 will
build on is the least tested code in the stage.

Not NO GO: every Block A number is in the policy with the right value, all nine suites pass, the
re-opened spec matches its migration, conditions 1, 2, 5, 6 and 7 are closed and I verified each
by breaking the code, and nothing I found is a defect that the v0.1 → v0.5 change introduced.

### 0.2 The eight conditions of the existing audit, as measured today

| # | Condition | Existing audit says | Measured at `3cd91a0` |
|---|---|---|---|
| 1 | Test the exposure and valuation cluster | CLOSED | **CLOSED — verified.** 7 of 7 mutations detected, both Python modes |
| 2 | Test the kill-switch and regime gates | CLOSED | **CLOSED — verified.** 3 of 3 mutations detected, both modes |
| 3 | Close Q-P1.1-1 and test `settlement_date_for` | OPEN | **OPEN.** But the two halves differ: the question is external; the test is not blocked by it (X5R-E6) |
| 4 | Close Q-P1.1-6 | OPEN | **OPEN, and cannot be closed before P2.1.** The spec says it is answered by a measurement taken during P2.1 |
| 5 | Convert the harnesses off bare `assert` | PARTIAL | **CLOSED.** 0 bare `assert` in all six harnesses; 18 of 18 detected mutations fail identically under `-O`. Its replacement risk is condition 11 |
| 6 | Test `loosens` and `assert_no_env_risk_reads` | CLOSED | **CLOSED — verified.** Mutations C9 and M12 detected, both modes; `t_c6_…` pins that the bare `loosens` property refuses to guess |
| 7 | Close Q-P1.2-6's five runtime assertions | OPEN | **CLOSED, with one answer being "no".** The suite exists, passes 36 of 36 on a fresh database, and fails under 7 of 8 sabotages. Assertion 1 does not hold: that is Finding A, open and accepted |
| 8 | Resolve C-1, C-2, C-5 | OPEN | **OPEN and larger.** C-1 is 4 instances, not 2. C-2 is in all four specs. C-5 was never true and is withdrawn |

### 0.3 What the existing audit got wrong

| Id | Existing audit | Found |
|---|---|---|
| X5R-E1 | §1.2 line coverage 64.0 / 83.1 / 61.5 / 67.0 % | Statement coverage is 89.4 / 98.8 / 94.5 / 91.3 %. The old denominator counted docstring lines. The function counts (60, 11, 14, 20; 6 never executed) reproduce exactly |
| X5R-E2 | §2.2: corporate actions, halts, and timezone/DST/half-day each "✓ test … OK" | None of the three has a test. `CorporateAction` is never constructed by any test. No test uses a `HALTED` instrument, a `HALF_DAY` session or a DST pair. Mutations M03, M08 and M09 pass every suite |
| X5R-E3 | §3: "No behavioural contradiction was found between any spec and its code"; C-3 "NONE" | X3R-M1, X3R-M2 and X3R-M3. I reproduced all three. All existed at `605ff40` |
| X5R-E4 | §3 C-5: order rates "appear only in `config/policy.yaml`, in no spec prose" | SPEC-P1.3 line 348: "20 orders/min global, 10 per strategy" |
| X5R-E5 | §5: P2.1 "does not consume any of the untested exposure functions", so it "may proceed now" | True of the exposure functions. But P2.1 is the phase that constructs `CorporateAction`, `SuccessorLink`, `Trade`, `FundamentalsSnapshot` and the calendar — the models no test builds |
| X5R-E6 | Condition 3: testing `settlement_date_for` is "blocked on an external fact" | The function returns a stored date. It asserts no cycle. It can be tested today |
| X5R-E7 | §1 is titled "Three-tick matrix" | It maps 13 numbers to a rule and a value. It has no test column, and it does not cover "every capability, control, and number" as X5 item 1 requires. §1 below is that matrix |
| X5R-E8 | §1.1 row "risk per trade 1% — RISK rule §515" | The rule is `SIZE-001`. Block A's "limit orders default, market only for emergency exit" (`EXEC-001`) is missing from the table |
| X5R-E9 | Header `depends_on … SPEC-P1.2-STORAGE v0.1` | v0.5 |

### 0.4 Where I differ from the X3 re-run

I tested X3's findings as claims. **Confirmed by my own measurement:** X3R-M1 (5 envelope fields
with no column), X3R-M2 (132 numeric leaves: 104 `int`, 28 `float`; `NonCanonicalPayloadError`),
X3R-M3, X3R-M4, X3R-C1 (4 instances), X3R-C2, X3R-C5, X3R-C6, X3R-C7 (240 `CHECK (`, 3 `EXCLUDE`,
6 `SECURITY DEFINER`), X3R-C13, X3R-E5, X3R-G1, `A-14`, and the counts 118 / 32 / 32.

| Id | X3 re-run says | Found |
|---|---|---|
| X5R-X1 | X3R-G2, G3, G4, G6, G8 are gaps "not recorded anywhere" | They are in no Stage 0 or Stage 1 spec, which is what X3 searched. **The prompt pack schedules all five**: P2.10 (lines 749–750), P3.3 (858), P4.1 (923), P6.3 (1272), P5.1 (1094). They are deferred work with an owner, not lost requirements. **Only X3R-G1, earnings blackout, appears nowhere** — 0 mentions in the pack, in all seven specs, in the policy and in the code |
| X5R-X2 | 28 triggers against 27 — "Reasoned from the script, NOT VERIFIED by execution" | **Verified by execution.** `pg_trigger` 28, `information_schema.triggers` 27; the one not listed is `audit_log_no_truncate` |
| X5R-X3 | §5.4: P2.1 is blocked by `Q-P1.2-7` | Agreed for code that writes an audit event. I add what X3 did not say: **no phase owns the audit writer** (X5R-G3), so the first writer has nothing to implement from |
| X5R-X4 | §6.2: "anomaly detection — Later, P2.2" | Agreed, and the pack schedules it (line 479). Zero mentions in any Stage 0 or Stage 1 spec, the same position as G2–G8 |

I did not re-derive X3's 70-row matrix or its seven-way contract comparison row by row. Where I
cite an X3 finding I did not reproduce, §6 says so.

### 0.5 NOT VERIFIED

| Item | State |
|---|---|
| Behaviour on Python 3.12 or later | **NOT VERIFIED.** Block A fixes "Python 3.12+". Only Python 3.11.9 has the dependencies on this host; 3.13 and 3.14 have no `pydantic`. Every Python result here is on 3.11.9 |
| `mypy --strict` clean (X1 rule) | **NOT VERIFIED.** `mypy` is not installed |
| Whether SPEC-P1.3 and SPEC-P1.4 ever had an X2 review (F-2, G-3) | **NOT VERIFIED.** The string "X2" appears 0 times in SPEC-P1.3 and once, unrelated, in SPEC-P1.4. `docs/specs/reviews/` holds one folder, the X3 re-run |
| The contents of `ai-trading-tsdb` | **NOT VERIFIED.** Not connected to. "No production audit history" rests on the repository: no deploy tree, and CI tears its database down |
| The PDT floor of 25,000 | **NOT VERIFIED.** No source consulted |
| X3R-M5, M6, M7; X3R-C8 to C12; X3R-G5, G7 | Not reproduced. Quoted as X3's |
| N-6, N-7, N-8 of the second X2 | The record does not say what they are |
| A collision in the database preimage | Reasoned, not executed. See X5R-G9 |

---

## 1. Item 1 — requirement coverage matrix: spec · code · test

### 1.1 Method

Every capability, control and number in `master-research-summary.md` that Stage 1 could carry,
plus Block A's hard numbers. Three columns:

- **Spec** — a Stage 1 spec states it, with the place.
- **Code** — a Stage 1 artifact carries it: a type, a rule, DDL.
- **Test** — a test fails when it is broken. I did not accept "a test mentions it". Where I broke
  the code and ran the suites, the mutation id is given (§7.3). `✓` means detected. `✗` means the
  suites stayed green. `◐` means part is pinned and part is not.

Three ticks are required. Anything with fewer is a gap.

### 1.2 Block A hard numbers — 13 lines of Block A, plus fail-closed

The value is pinned by `t_const_thresholds_match_the_constitution` for 12 rule ids. **Nothing pins
a constitutional rule's `action`, `mode`, `comparison` or `scope`**, except the `KILL` action of
`LOSS-003` and `LOSS-004`.

| Block A | Spec | Code (`policy.yaml`) | Test | Ticks |
|---|---|---|---|---|
| position ≤ 5% NAV | P1.3 §10 | `EXP-001` `0.050` lte DENY | ✓ value (P01), ✓ comparison (P02) | 3 |
| sector ≤ 20% NAV | P1.3 §10 | `EXP-002` `0.200` lte DENY | ✓ value; **✗ action** — `DENY → ALLOW` passes (P03) | ◐ |
| gross ≤ 2× | P1.3 §10 | `EXP-003` `2.0` | ✓ value | 3 |
| net ≤ 1× | P1.3 §10 | `EXP-004` `1.0` | ✓ value | 3 |
| daily loss ≤ 2% | P1.3 §10 | `LOSS-001` `0.020` | ✓ value; **✗ mode** — `enforce → monitor` passes (P04) | ◐ |
| weekly loss ≤ 5% | P1.3 §10 | `LOSS-002` `0.050` | ✓ value | 3 |
| drawdown ≤ 10%, trips kill | P1.3 §10 | `LOSS-003` pool, `LOSS-004` consolidated, both KILL | ✓ `LOSS-003` value and action (P06); **✗ `LOSS-004` value** — 10% → 20% passes (P05) | ◐ |
| risk per trade 1% | P1.3 §10 | `SIZE-001` `0.010` MODIFY | ✓ value | 3 |
| liquidity 1% ADDV | P1.3 §10 | `LIQ-001` `0.010` MODIFY | ✓ value; ✓ action, rejected by the loader (P10) | 3 |
| ≤ 20 orders/min global | P1.3 §10, line 348 | `RATE-001` `20` | ✓ value; **✗ scope** — `global → strategy` passes (P09) | ◐ |
| ≤ 10 per strategy | P1.3 §10, line 348 | `RATE-002` `10` | ✓ value | 3 |
| stop = entry − 2.5 × ATR(14) | P1.3 §10; P1.1 §8.1 | `STOP-001` `2.5` eq | ✓ value; **✗ comparison** — `eq → lte` passes (P08) | ◐ |
| limit default, market for emergency exit only | P1.3 §10 | `EXEC-001` `allowed_values: [LIMIT]` | **✗** — adding `MARKET` passes (P07) | **2** |
| fail-closed on missing input | P1.3 §4.3 | 47 rules: 44 DENY, 3 KILL | ✓ (M13) | 3 |

**No constitutional number is stated two ways.** I agree with both earlier records on that. All
47 rules load; the inventory is 45 enforce and 2 monitor; 37 DENY, 6 MODIFY, 3 KILL, 1 ALLOW.

### 1.3 Capabilities and controls that Stage 1 carries

| Requirement (RS §) | Spec | Code | Test | Ticks |
|---|---|---|---|---|
| Two markets, nothing US-only (§4, Block A 10) | P1.1 §2 | `Market`, `Exchange`, `PoolId`, `Currency` | ✓ `t_india_requires_lot_size`, `t_pool_segregation`, `t_muhurat_excluded`, `t_fx_*` | 3 |
| Universe filters, US (§4) | P1.3 | `universe.US`, `UNIV-*` | **✗** — `min_price_usd` 5.00 → 0.50 passes (P12) | **2** |
| Universe price floor, India ₹100 (§4) | P1.3 says the summary gives none | `min_price_inr: "50.00"` | ✗ | **contradiction** (X3R-C5, confirmed) |
| BUY / HOLD / SELL / NO-TRADE (§4) | P1.1 §7 | `DecisionAction`, `SignalDirection` | ✓ `t_no_sell_short`, `t_llm_cannot_emit_signal` | 3 |
| Thesis with invalidation conditions (§4) | P1.1 §7.4 | `Thesis`, `InvalidationCondition`; trigger `thesis_must_be_falsifiable` | ◐ model tested; the trigger is in no suite | ◐ |
| Risk engine overrides; DENY is final (§1, §19) | P1.1 §8.2 | `RiskVerdict`, `Decision`; `CHECK (risk_decision = 'ALLOW')` | ✓ `t_risk_deny_is_final`, `t_no_override_parameters`; check 7.3 (D2) | 3 |
| LLM never sizes or executes (§9) | P1.1 §7.4 | `Thesis` has no size field | ✓ `t_thesis_has_no_size_fields` | 3 |
| Kill switch needs a human to re-enable (§11) | P1.1 §11.3 | `KILL_SWITCH_TRANSITIONS`, `KILL-001` | ✓ `t_kill_switch`; **✗ `KILL-001` mode** (P13) | ◐ |
| **Earnings blackout** (§4, §6 Phase 8) | **none** | **none** | **none** | **0** |
| Duplicate-order protection (§4) | P1.1; P1.4 §7 | `client_order_id`; `UNIQUE (account_id, client_order_id)`; `recover_incomplete_intents` | ◐ recovery tested (3 tests); the `UNIQUE` is in no suite | ◐ |
| Unique strategy id per order (§2, §16) | P1.1 line 1191; P1.2 | `Order.strategy_id` min length 1; `order_intent.strategy_id NOT NULL` | ◐ used as a fixture value; no test omits it | ◐ |
| Append-only audit, hash chain (§14) | P1.2 §9; P1.4 §6 | deny triggers; `audit_chain_assign`; `chain.py` | ✓ M14, D9, checks 7.1a–7.1h | 3 — with Finding A open and X3R-M1 |
| Decisions reproducible (§1) | P1.4 §5 | `ReproducibilityBundle`, `replay_run` | ✓ in memory; **no column stores the bundle** (X3R-M1) | ◐ |
| Write-before-act (Block A 5) | P1.4 §7 | `write_before_act` | ✓ `t_audit_failure_means_the_action_does_not_happen`; **✗ `is_effectful`** (M15) | ◐ |
| Effective config dump to the audit log (P1.3 prompt) | P1.3 §9 | `audit_payload()` | **✗ — and it cannot be written** (X3R-M2, confirmed) | **contradiction** |
| UTC at rest, naive rejected | P1.1 §4 | `UtcDatetime`; GUC pins | ✓ two tests; checks 7.7, 7.8 | 3 |
| DST and half-days | P1.1 lines 321–324 | `SessionType.HALF_DAY`; explicit UTC instants | **✗** — no `HALF_DAY` row, no DST pair; open ≥ close passes (M08) | **2** |
| Corporate actions | P1.1 §5 | `CorporateAction`, `SuccessorLink`; table | **✗** — never constructed; a split with no ratio passes (M09) | **2** |
| Symbol identity, ticker change, reuse | P1.1 §5 | `SymbolMapping`, `resolve_instrument`; `EXCLUDE` | ◐ ✓ reuse, ambiguity, check 7.2 (D1); **✗** `valid_to` boundary (M04), **✗** `resolve_symbol` (M17) | ◐ |
| Halted, suspended, delisted names | P1.1; `INST-001` | `InstrumentStatus`, `is_tradeable_v1` | **✗** — a `HALTED` name is tradeable with every suite green (M03); `delisted_on` check (M18) | **2** |
| Partial fills | P1.1 dust rule | `Order.is_complete`; deferred trigger | ✓ C7; check 7.5 (D4b, D5) | 3 |
| Restart and recovery | P1.4 §7 | `recover_incomplete_intents` | ✓ three tests. Executed; not mutation-tested | 3 |
| Settlement date | P1.1; Q-P1.1-1 open | `settlement_date_for` | **✗** — never executed; `settlement_date < trading_date` passes (M07) | **1** |
| No look-ahead (§13) | P1.2 §3 | six as-of functions; grants | ◐ check 7.4 probes one table (D3 ✓, D8 ✗); **no suite calls an as-of function**; `feature_timestamp` never executed | ◐ |
| Survivorship-free data (§13) | P1.2 §5.4 | `delisted_on`, `final_price` | **✗** (M18) | **2** |
| Wash sales (§16) | P1.1 §9.1 | `Lot` wash fields | ✓ `t_wash_sale_india_blocked`, `t_lot_basis_exact` | 3 |
| PDT (§16) | P1.1 §9.4 | `CASH-002` monitor; floor `25000` | **✗** — floor 25,000 → 1 passes (P11); the number is unverified | **2** |
| Secrets in Vault, no risk number from the environment (§15) | P1.3 §7, §8 | `VaultRef`, lint, `infra_env` | ✓ C9, C10 | 3 |
| Limits changed only with two approvers | P1.3 §5.3 | `assert_change_authorised` | ◐ ✓ for a threshold (M12); **undefined for mode, action, comparison** (X5R-G2) | ◐ |
| Fresh data, fail-closed (§11) | P1.1 §6.7; `DATA-001` | `StalenessPolicy`; 600 s | ◐ ✓ bar finality (M05); **✗** threshold, 600 → 86,400 passes (P14) | ◐ |
| Money is Decimal, half-up | P1.1 §3 | `Money`, `Price`, `Quantity` | ✓ M06 | 3 |

### 1.4 Requirements owned by a later phase

Not Stage 1 gaps. Each has fewer than three ticks because it is not built yet. I checked that the
prompt pack names an owner for each.

| Requirement | Owner in the pack | In a Stage 0 or 1 spec? |
|---|---|---|
| Ingestion, validation, anomaly detection | P2.1, P2.2 | no |
| Scanner, scoring, regime, decision, sizing | P2.3 to P2.8 | Stage 0 decisions only |
| Risk engine evaluation of the 47 rules | P2.9 | rules only |
| Kill triggers: volatility > 3σ, API failure > 5 retries, agent loop > 10, data quality | P2.10, lines 749–750 | no |
| Retry with backoff; broker abstraction | P3.1 | Stage 0 |
| Trailing stop | P3.3, line 858 | **no type for it in P1.1** |
| Exit hierarchy | P3.4, lines 877–883 | **no type for it in P1.1** |
| Sanitiser, origin tags | P4.1, line 923 | no |
| Backtest, walk-forward, Monte Carlo | P5.1, line 1094 | walk-forward `CHECK` only |
| Monitoring, alerting, VaR | P6.1 | no |
| Secret rotation, static IP | P6.2 | partly |
| Best execution | P6.3, line 1272 | no |

### 1.5 Totals

Of 45 Stage 1 rows (14 + 31): **19 have three ticks. 15 are partial. 8 have two ticks or one.
2 are contradictions. 1 has none** (earnings blackout).

---

## 2. Item 2 — silent gaps

### 2.1 The six areas X5 names

| Area | Spec | Code | Test | Verdict |
|---|---|---|---|---|
| Timezone | ✓ | ✓ | ✓ | **OK** |
| DST and half-days | ✓ | ✓ type only | ✗ | **GAP.** The spec's two edge-case rows have no test. P2.1's calendar loader is where a DST error would enter, and nothing checks what it produces |
| Corporate actions | ✓ | ✓ | ✗ | **GAP.** Only the type parser is tested. The model and its three validators have never run |
| Halts | ✓ | ✓ | ✗ | **GAP.** The existing audit counted the kill switch's `POOL_HALTED` as a halt test. An instrument halt is a different thing and is untested |
| Partial fills | ✓ | ✓ | ✓ | **OK** |
| Restarts | ✓ | ✓ | ✓ in memory | **OK for Stage 1.** No database-backed recovery exists yet |
| Second market | ✓ | ✓ | ✓ | **OK**, with the ₹50 / ₹100 contradiction and Q-P1.1-2 open |

### 2.2 Gaps found by this run

**X5R-G1 — HIGH — the code P2.1 builds on is the least tested code in Stage 1.** Six models are
never constructed by any test: `CorporateAction`, `SuccessorLink`, `Trade`,
`FundamentalsSnapshot`, `Candidate`, `Score`. Four validators have never run. Ten of eighteen
single-line mutations in `src/` pass every suite, in both Python modes: M03 halted name tradeable,
M04 `valid_to` inclusive, M07 settlement before trade date, M08 session open ≥ close, M09 split
without a ratio, M10 fundamentals disseminated before filed, M15 `is_effectful` false, M16 anchor
hash dropped, M17 ambiguous symbol not raised, M18 delisted without a date. Eight of the ten are
in types P2.1 constructs. Belongs to Stage 1: X1 requires "every non-trivial branch gets a test in
the same drop".

**X5R-G2 — HIGH — the two-person rule covers a threshold and nothing else.** `LimitChange` holds
two decimals. Demoting a rule to `monitor`, changing its `action` to `ALLOW`, or flipping its
`comparison` disables a constitutional limit and leaves its threshold untouched. SPEC-P1.3 §5.3
does not say whether those are a loosening. No function derives the change list from two policy
versions; the caller supplies it. P03 and P04 show such a file loads and passes every suite.
Belongs to Stage 1: the P1.3 prompt asks "who may change what".

**X5R-G3 — HIGH — nobody owns the audit writer.** SPEC-P1.4's CONTRACTS table names a "P1.2
writer" as a consumer twice. No spec defines it and no phase prompt owns it. Nothing in `src/`
opens a database connection. Combined with X3R-M1, the first phase to emit an event must invent
the mapping from an 18-field envelope to a 13-column table.

**X5R-G4 — MEDIUM — the tests are run by hand, on a Python the constitution excludes.**
`ci-migration.yml` applies the migration and runs no suite, and it triggers only on four paths.
All results in every record are from Python 3.11.9. `mypy` has never been run here.

**X5R-G5 — MEDIUM — earnings blackout** (X3R-G1, confirmed and narrowed). The only requirement in
the research summary with no spec, no rule, no code, no test and no owner in the pack.

**X5R-G6 — MEDIUM — the kill-trigger list is contradicted before it is specified.** The research
summary §11 and the pack's P2.10 prompt (line 749) both list daily loss > 2% and weekly loss > 5%
as automatic kill triggers. `LOSS-001` and `LOSS-002` are `DENY`. Block A names only drawdown.
No decision records which is right.

**X5R-G7 — LOW — check 7.4 probes one table of 37.** `GRANT SELECT ON trading.bar_daily TO
backtest_ro` leaves the suite at 36 of 36 (D8). The real grants are correct: I measured 0 of 37
base tables readable by `backtest_ro`.

**X5R-G8 — LOW — sizing and exits emit no audit event.** `Producer` has `P2.8_SIZER` and
`P3.4_EXIT`; the registry gives neither an event type.

**X5R-G9 — LOW — the database preimage has no field separators.** `seq::text || event_type`
is ambiguous if an event type begins with a digit, and `event_type` is constrained only to be
non-empty. Registry names never begin with a digit. Reasoned, **not executed**.

**X5R-G10 — LOW — one test asserts wall-clock time.** `t_f6_lookup_is_fast_and_correct` failed
under my tracer on timing alone. It will fail on a slow host.

Carried and still open: `DECISIONS.md` is absent (pack appendix; §11.6 step 6). N-1 to N-9 and
X2-4/a to /f are as the record leaves them.

---

## 3. Item 3 — contradictions across all documents

| # | Contradiction | Source A | Source B | State |
|---|---|---|---|---|
| C-1 | `depends_on` drift | P1.2 → P1.1 v0.1; P1.3 → P1.1 v0.2, P1.2 v0.1; P1.4 → P1.2 v0.1 | P1.1 is v0.3; P1.2 is v0.5 | **OPEN, 4 instances** (was 2). Read from the four headers |
| C-2 | `produces:` headers | P1.1 names 4 things that do not exist; P1.2 omits `verify_audit_chain`, `account`, `run_context`; P1.3 omits 3; P1.4 omits 6 | the CONTRACTS tables and the code | **OPEN, all four specs** (was P1.4 only) |
| C-3 | Duplicate contract name | `canonical_bytes` in P1.3: accepts numbers | `canonical_bytes` in P1.4: raises on them | **OPEN** (was "NONE"). Reproduced |
| C-4 | Block A number stated two ways | — | — | **NONE.** 12 thresholds and the order-type rule checked |
| C-5 | Order rates in no spec prose | — | SPEC-P1.3 line 348 | **WITHDRAWN.** Never true |
| C-6 | One event, two hashes (X3R-M1) | P1.4: 15 keys as canonical JSON; 18-field envelope | P1.2: 11 columns concatenated; 13 columns; the trigger overwrites `payload_hash` | **OPEN, HIGH.** 5 fields have no column, measured |
| C-7 | Config dump rejected (X3R-M2) | P1.3 `audit_payload()`: 132 JSON numbers | P1.4 §6.2 rule 4: no JSON numbers | **OPEN, HIGH.** Reproduced |
| C-8 | SPEC-P1.2 status (X3R-C14) | header `status: FROZEN` | same header: "NOT re-frozen" | **OPEN, MEDIUM** |
| C-9 | India price floor (X3R-C5) | research summary line 118: ₹100 | `policy.yaml` line 117: `"50.00"`; P1.3 says the summary gives none | **OPEN, MEDIUM** |
| C-10 | Staleness (X3R-C6) | research summary §8: 5 s | `DATA-001`: 600 s | **OPEN, LOW.** No decision found |
| C-11 | Kill triggers (X5R-G6) | research summary §11, pack line 749: daily and weekly loss trip the switch | `LOSS-001`, `LOSS-002`: `DENY` | **OPEN, MEDIUM** |
| C-12 | Risk verdict shape (X3R-C9) | P1.1: `ALLOW` / `DENY` | P1.3: four actions | **OPEN, MEDIUM.** `RiskDecision` and `RuleAction` members confirmed |
| C-13 | `Q-P1.2-6` row | SPEC-P1.2: "the DDL is unexecuted" | executed here: exit 0, 37 / 8 / 3 / 27 | **OPEN, LOW**, stale row |
| C-14 | Finding A wording | §11.5, migration comment: "no supported mechanism exists" | §11.11: a mechanism was measured | **OPEN.** Left as written by Owner decision; listed so it is not lost |
| C-15 | The entry gate | §9: "Blocking open questions for P2.1: NONE" | §12.6: `Q-P1.2-7` blocks P2.1 | **OPEN.** §12 supersedes §9 "where they differ"; the gate table itself is unedited |
| C-16 | This audit against itself | §2.2 "OK" for three areas; §3 "no behavioural contradiction" | §2.1 and C-6, C-7 above | X5R-E2, X5R-E3 |

Not contradictions: 28 triggers against 27 (X5R-X2). X3R-C7, C8, C10, C11, C12 and C13 are X3's
and stand as it wrote them; I reproduced C7 and C13 only.

---

## 4. Item 4 — assumption ledger, by impact

32 rows in the four ASSUMPTIONS tables (13, 8, 6, 5), counted. X3 found 30 distinct; not
re-derived. "Verified" means verified by something in this repository or by this run.

| Rank | Assumption | Verified? | Risk if false |
|---|---|---|---|
| 1 | `[CONST-2]` is enforced structurally at the `Decision` constructor | **YES** in Stage 1's scope — two tests, and the database `CHECK` under sabotage D2 | `[CONST-1]` is decorative |
| 2 | Off-VM anchor storage is write-once with separate credentials | **NO** — Q-P1.4-1. **RISK** | The only answer to Finding A's residual. Until it exists a forged append under replica role is undetectable |
| 3 | No production audit history exists | **PARTLY** — no deploy tree; CI tears down. Dev database not inspected. **In no ASSUMPTIONS table** | v0.5 invalidated every earlier hash on this basis |
| 4 | US and India settlement are both T+1 | **NO** — Q-P1.1-1, Q-P1.1-2. **RISK** for P2.9 | `settled_cash` sizing is wrong |
| 5 | PDT is a margin-account rule with a 25,000 floor | **NO.** **RISK.** In no ASSUMPTIONS table and absent from the STAGE-0 register (0 mentions in `STAGE-0-FREEZE.md`) | An unverified regulatory number in a frozen spec, and unpinned by any test |
| 6 | Mean audit row ~1,000 B; 15,000 events per session | **NO** — Q15. **RISK** | The disk model breaks near 10× |
| 7 | Round-trip cost 25 bps US, 90 bps India | **NO** — Q13. **RISK** | Every edge estimate; `EDGE-001` |
| 8 | The suites behave the same on Python 3.12+ | **NO.** New in this run | Every "PASSED" in the record is on 3.11 |
| 9 | The off-VM WAL receiver fits the 5 s exit budget | **NO** — Q-P1.2-2 | RPO 0 and the exit budget cannot both hold |
| 10 | A second approver exists | **NO** — Q-P1.3-1 | No limit can be raised at team size 1. Safe, but it is a standing constraint |
| 11 | India price floor ₹50 | **Contradicted** by the research summary | India universe selection. Unfunded |
| 12 | 600 s staleness is the right bound | **NO** — no authority recorded | Stale data admitted, or fresh data refused |
| 13 | `Price` at 6 dp is enough | **NO** — measured during P2.1 (Q-P1.1-6) | Silent truncation |
| 14 | No natural-person data enters the log | NO | Erasure law against an immutable log |
| 15 | Compression 15× and 4× | NO | Disk; 4× headroom at 8× |
| 16–32 | The rest | mixed | Local and recoverable |

Items 2, 4, 5, 6 and 7 are unverified and each feeds a capacity decision, a sizing rule or a
regulatory control. Item 5 is the one I would escalate first: it is a number from a regulation,
nobody is assigned to check it, and the test suite does not notice if it changes.

---

## 5. Item 5 — readiness verdict for Stage 2

# GO WITH CONDITIONS

### 5.1 Entry conditions — before any Stage 2 phase starts

| # | Condition | Why |
|---|---|---|
| **E-1** | Finish §11.6 steps 6 and 7: create `DECISIONS.md`; resolve SPEC-P1.2's status (X3R-C14); re-freeze | Pack rule 3: a code phase may cite only a `FROZEN` spec. The appendix: freezing means merged, gap-audited, and blocking questions closed |
| **E-2** | Rewrite the Stage 2 entry gate so it names its blockers | §9 still says nothing blocks P2.1. Freezing over X3R-M1 and X3R-M2 is defensible only if the gate names them |

### 5.2 Conditions, each tied to the phase it gates

| # | Condition | Gates | Severity | State |
|---|---|---|---|---|
| 1 | Test the exposure and valuation cluster | P2.8, P2.9 | — | **CLOSED**, verified |
| 2 | Test the kill-switch and regime gates | P2.10 | — | **CLOSED**, verified |
| 3 | Close Q-P1.1-1. Separately, test `settlement_date_for` and the settlement-date validator now | P2.9 | BLOCKER for P2.9 | **OPEN** |
| 4 | Close Q-P1.1-6 by the measurement P2.1 takes | P2.2 | BLOCKER for P2.2 | **OPEN** — a P2.1 deliverable, not a precondition |
| 5 | Convert the harnesses off bare `assert` | all | — | **CLOSED** |
| 6 | Test `loosens` and `assert_no_env_risk_reads` | P6.2 | — | **CLOSED**, verified |
| 7 | Q-P1.2-6's five runtime assertions | P6.4 | — | **CLOSED.** Residue: update the stale row; widen check 7.4 (X5R-G7); N-9 |
| 8 | Documentary: C-1, C-2, C-13 and the stale text in X2-4/a | — | LOW | **OPEN**, larger |
| **9** | Decide `Q-P1.2-7` / X3R-M1, widened to `reproducibility`, **and name the owner of the audit writer** (X5R-G3) | **P2.1 code that writes an audit event**; P2.3, P2.5, P2.6, P2.7, P2.9 | **BLOCKER** | OPEN |
| **10** | Decide X3R-M2: which of P1.3's payload or P1.4's no-numbers rule changes | The first run that writes `EFFECTIVE_CONFIG_RENDERED` | **BLOCKER** for that run | OPEN |
| **11** | Tests for the types P2.1 constructs (X5R-G1): corporate actions, successor links, trades, fundamentals, session ordering and settlement, a half-day row, a DST pair, the `valid_to` boundary, `resolve_symbol`, halted and delisted status | **P2.1 code drop** | **HIGH** | OPEN. May be done in parallel with the P2.1 spec |
| **12** | Pin `action`, `mode`, `comparison` and `scope` of the constitutional rules in a test, including `LOSS-004` and `EXEC-001`; define loosening for a non-threshold change (X5R-G2) | P2.9; any policy change | **HIGH** | OPEN |
| **13** | Before P2.9: ratify `A-14`; state how a `PolicyVerdict` becomes a `RiskVerdict` (X3R-Q3); decide earnings blackout (X5R-G5) | P2.9 | BLOCKER for P2.9 | OPEN |
| **14** | Before P2.10: decide whether daily and weekly loss trip the switch (X5R-G6) | P2.10 | BLOCKER for P2.10 | OPEN |
| **15** | Run the suites in CI, on Python 3.12+ (X5R-G4) | all | MEDIUM | OPEN |
| **16** | Verify the PDT floor and register it | P3.2, P6.3 | MEDIUM | OPEN |
| — | Finding A | P6.2, P6.4 | HIGH | **OPEN, accepted.** Remediation E deferred. Not a Stage 2 entry condition; its only mitigation is assumption 2 above |

### 5.3 What may proceed

- **Nothing in Stage 2, until E-1 and E-2.**
- After them: **the P2.1 specification.** No open question blocks writing it.
- **P2.1 code** that parses and validates into the domain types, once condition 11 is closed.
- **P2.1 code that writes an audit event**: not until condition 9.

---

## 6. What changed since the existing audit, and what did not

`git diff --stat 605ff40..3cd91a0`: 17 files, 4,585 insertions, 240 deletions, six commits.
`src/` and `config/` are unchanged: `git diff 605ff40..3cd91a0 -- src config` is empty. The ten
artifact hashes over the git blob at `3cd91a0` equal the ones in STAGE-1-FREEZE §12.2.

So every coverage figure and every mutation result against `src/` describes the code as it was at
`605ff40` as well. X5R-E2, E3, E4 and E5 were wrong when written.

What the commits since then did change: the migration and SPEC-P1.2 (v0.1 → v0.5), one new
Python harness, one new shell suite, and four harnesses moved off bare `assert`.

---

## 7. Evidence

### 7.1 Environment

- Windows 11, Git Bash. Python 3.11.9, pydantic 2.13.5, PyYAML 6.0.3, cryptography 46.0.7.
- Isolated copy: `git archive 3cd91a0 | tar -x` into the session scratch folder, outside the
  repository. Every import, suite and mutation ran there or in a copy of it.
- Database: a throwaway container `x5run-tsdb` from `timescale/timescaledb:2.29.2-pg16`, compose
  project `x5run`, its own volume, port 55434, started with the Owner's approval given in this
  conversation. Removed with its volume afterwards. `ai-trading-tsdb` and `x2run-tsdb` were
  running throughout and were not touched.
- `git status --porcelain=v1 --untracked-files=all` on the repository: empty at the start and at
  the end. `git rev-parse --short HEAD`: `3cd91a0` both times.

### 7.2 Baseline

| Command | Exit | Result |
|---|---|---|
| `py -3.11 tests/verify_p11_invariants.py`, and with `-O` | 0, 0 | PASSED 42; 42 |
| `py -3.11 tests/verify_p11_p12_contract.py`, and with `-O` | 0, 0 | 21 pairs ALIGNED; ALIGNED |
| `py -3.11 tests/verify_p11_x2_regressions.py`, and with `-O` | 0, 0 | PASSED 21; 21 |
| `py -3.11 tests/verify_p11_x5_conditions.py`, and with `-O` | 0, 0 | PASSED 12; 12 |
| `py -3.11 tests/verify_p13_config.py`, and with `-O` | 0, 0 | PASSED 39; 39 |
| `py -3.11 tests/verify_p14_audit.py`, and with `-O` | 0, 0 | PASSED 36; 36 |
| `bash scripts/apply-migration.sh` | 0 | 37 tables, 8 hypertables, 3 continuous aggregates, 27 triggers; 3 extensions in `extensions` |
| `bash tests/verify_p12_migration_rerun.sh` | 0 | PASSED 6, FAILED 0 |
| `bash tests/verify_p12_cagg_immutability.sh` | 0 | PASSED 6, FAILED 0 |
| `bash tests/verify_p12_runtime_behaviours.sh` | 0 | PASSED 36, FAILED 0 |

Bare `assert` statements, counted from the syntax tree: 0 in each of the six harnesses and 0 in
each of the four source modules. At `605ff40`, by text match: 56, 0, 37, 56, 62.

### 7.3 Coverage — `evidence/cov_run.py`, `evidence/cov_report.py`

`sys.settrace` over all six harnesses. The denominator is the set of lines that carry bytecode
(`co_lines()`), so docstrings are excluded. A function counts as executed if a line of its body
ran. `timeit.timeit` was replaced by a single call inside the tracer, because the tracer's
overhead failed one wall-clock test (X5R-G10) before it reached the code under it.

| Module | Statement coverage | Public functions never executed | Existing audit |
|---|---|---|---|
| `src/domain/models.py` | 1,372 / 1,535 = **89.4%** | **3 / 60** | 64.0%; 3 / 60 |
| `src/audit/events.py` | 423 / 428 = **98.8%** | **1 / 11** | 83.1%; 1 / 11 |
| `src/audit/chain.py` | 225 / 238 = **94.5%** | **2 / 14** | 61.5%; 2 / 14 |
| `src/config/loader.py` | 545 / 597 = **91.3%** | **0 / 20** | 67.0%; 0 / 20 |
| Total | | **6 / 105** | 6 |

The six: `settlement_date_for`, `resolve_symbol`, `feature_timestamp`, `is_effectful`, `link`,
`to_payload`. Private validators never executed: `SuccessorLink._positive`,
`CorporateAction._check`, `FundamentalsSnapshot._check`, `Candidate._non_empty`.

Models never constructed (`evidence/inst_run.py`, which wraps `BaseModel.__init__` and
`model_validate`): 6 of 35 concrete models in `models.py`; 0 of 3 in `events.py`; 0 of 11 in
`loader.py`.

**Coverage is not the finding.** 89% of statements run and ten mutations in that code still pass.

### 7.4 Mutations — `evidence/sabotage.py`, `sabotage2.py`, `sab_policy.py`

Each mutation is one change in a fresh copy, then all six suites, normal and `-O`.

| Set | Mutations | Detected | Not detected |
|---|---|---|---|
| Source, general (M01–M18) | 18 | 8 — M01, M02, M05, M06, M11, M12, M13, M14 | **10** — M03, M04, M07, M08, M09, M10, M15, M16, M17, M18 |
| Source, conditions 1, 2, 6 (C1–C10) | 10 | **10** | 0 |
| Policy file (P01–P14), `-O` only | 14 | 4 — P01, P02 (indirectly, through the loosening tests), P06, P10 | **10** — P03, P04, P05, P07, P08, P09, P11, P12, P13, P14 |
| Database (D1–D9) | 8 effective | 7 — D1, D2, D3, D4b, D5, D7, D9 | **1** — D8 |

Every detected source mutation was detected identically in both modes: 18 of 18. That is the
evidence for condition 5.

D4 was not applied: PostgreSQL refuses `ALTER CONSTRAINT` on a constraint trigger; D4b recreates
it `NOT DEFERRABLE`. D6, `DISABLE TRIGGER` on a database with no chunks, changed nothing — new
chunks receive an enabled copy — so it is not counted; on a populated database the same statement
is detected (34 passed, 2 failed).

Policy mutations P04 and P13 change `mode`; P03 changes `action`. The loader accepted all three.

### 7.5 Condition 7 — the five assertions of Q-P1.2-6

| Assertion | Check | Fresh database | Under sabotage |
|---|---|---|---|
| 1. `ENABLE ALWAYS` fires under replica role | 7.1b, inverted | **Does not hold.** Chunk triggers are `O` (8 of 8 measured). Finding A | Not sabotaged: the check pins a defect. Normal-mode protection (7.1a): D9, 34 passed, 2 failed |
| 2. `EXCLUDE` rejects an overlapping mapping | 7.2 | PASS | D1: 35 / 1 |
| 3. `decision` rejects `DENY` | 7.3 | PASS | D2: 35 / 1 |
| 4. `backtest_ro` denied on a base table | 7.4 | PASS; 0 of 37 readable | D3: 35 / 1. **D8: 36 / 0** |
| 5. Overfill trigger fires at commit | 7.5 | PASS | D4b: 35 / 1. D5: 34 / 2 |

### 7.6 Claims tested from the X3 re-run — `evidence/claims.py`

`audit_payload()` into `canonical_json()`: `NonCanonicalPayloadError` at `$.rule_count`; 132
numeric leaves. Both `canonical_bytes`: outputs as X3 quotes them. `AuditEnvelope.model_fields`
minus the 13 `audit_log` columns: `canonical_schema`, `causation_id`, `input_hash`,
`reproducibility`, `schema_version`. Registry: 42 types, 25 effectful, 6 reproducible;
`P2.1_INGEST` produces three; `P2.8_SIZER` and `P3.4_EXIT` produce none.

Text search across the seven specs, the policy, the four modules and the migration: `blackout`
0, `earnings` 0, `monte carlo` 0, `best execution` 0, `origin tag` 0, `3σ` 0, `agent loop` 0,
`anomal` 0. Across `docs/PROMPT-PACK.md`: `blackout` 0; every other term at least 1.

### 7.7 Files in this folder

| File | What it is |
|---|---|
| `X5-report.md` | This report |
| `STAGE-1-GAP-AUDIT.proposed.diff` | Appends a dated re-run section. Existing sections untouched. **Not applied** |
| `evidence/*.py` | The scripts that produced §7.3 to §7.6 |
| `evidence/mut2.txt` | The ten condition mutations |
| `evidence/db_*.log`, `evidence/sab_db*.log` | Output of the database runs |

### 7.8 The proposed diff

Generated with `git diff` in a throwaway repository holding the file exactly as
`git show 3cd91a0:docs/specs/STAGE-1-GAP-AUDIT.md` returns it. Its `index` line names blob
`a76b9d7`, which is the blob the repository holds at `3cd91a0`.

| Check, run in the repository | Result |
|---|---|
| `git apply --check --verbose STAGE-1-GAP-AUDIT.proposed.diff` | `Checking patch docs/specs/STAGE-1-GAP-AUDIT.md...` — exit 0 |
| `git apply --check --cached` | exit 0 |
| `git apply --check --whitespace=error-all` | exit 0 |
| `git apply --stat` | 157 insertions, 0 deletions |

One hunk, starting at line 273. It adds lines after the last existing line and removes none.
Sections 1 to 5 and the four standard tables are untouched. The file's header (`version`,
`depends_on`) is left alone; `depends_on` still names SPEC-P1.2 v0.1 (X5R-E9).

**The diff was not applied.** After the checks: `git status --porcelain=v1 --untracked-files=all`
returned nothing, `git rev-parse --short HEAD` returned `3cd91a0`, and `git diff --stat` returned
nothing.

The file has CRLF line endings in this working tree and LF in git (`core.autocrlf=true`).
`git apply` handled that in the check. A tool other than git may not.
