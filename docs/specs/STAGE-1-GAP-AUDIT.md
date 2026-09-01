---
id: STAGE-1-GAP-AUDIT
version: 1.0
status: ACTIVE
phase: Stage 1 — SPECIFY, closure (template X5 — GAP AUDIT)
depends_on: [STAGE-1-FREEZE v1.0, STAGE-1-MERGE-CHANGES v1.0, SPEC-P1.1-DOMAIN v0.3, SPEC-P1.2-STORAGE v0.1, SPEC-P1.3-CONFIG v0.1, SPEC-P1.4-AUDIT v0.1, master-research-summary.md]
produces: [GAP-AUDIT-P1, THREE-TICK-MATRIX-P1, SILENT-GAP-REGISTER-P1, STAGE-2-READINESS-VERDICT]
---

# STAGE 1 GAP AUDIT (X5)

**Run at:** 2026-08-31 (UTC) · **HEAD:** `605ff40`

X5's instruction is "be blunt; a green audit that misses a gap is worse than useless". This audit
is not green. It is **GO WITH CONDITIONS**, and the conditions are specific.

Method note: every number below was **measured**, not estimated. Coverage comes from the stdlib
`trace` module (no new dependency, per Block A), running the full harness suite and recording
which lines actually executed.

---

## 1. Three-tick matrix — spec · code · test

### 1.1 Constitutional numbers — 13 of 13 PASS

Every hard risk number in Block A was traced to its enforcing rule in `config/policy.yaml` and
its value compared.

| Block A number | Rule | policy.yaml | Verdict |
|---|---|---|---|
| position ≤ 5% NAV | EXP-001 | `0.050` | OK |
| sector ≤ 20% NAV | EXP-002 | `20%` | OK |
| gross ≤ 2x equity | EXP-003 | `2.0` | OK |
| net ≤ 1x equity | EXP-004 | `1.0` | OK |
| daily loss ≤ 2% | LOSS-001 | `0.020`, basis `nav_at_session_start` | OK |
| weekly loss ≤ 5% | LOSS-002 | `0.050`, basis `nav_at_week_start` | OK |
| max drawdown ≤ 10% | LOSS-003 | `10%`, trips kill switch | OK |
| risk per trade 1% | RISK rule §515 | `1% of pool NAV` | OK |
| liquidity ≤ 1% ADDV | LIQ-001 | `1%` of 20-session **median** ADDV | OK |
| ≤ 20 orders/min global | RATE | `20` | OK |
| ≤ 10 orders/min per strategy | RATE | `10` | OK |
| stop = entry − 2.5 × ATR(14) | STOP | `2.5` | OK |
| fail-closed on missing input | all 47 rules | 44 `DENY`, 3 `KILL` | OK |

**No constitutional number is stated two ways anywhere in the repository.** This is the strongest
result in the audit.

### 1.2 Measured test coverage — the weakest result

| Module | Lines executed | Coverage | Public functions never executed |
|---|---|---|---|
| `src/domain/models.py` | 1342 / 2144 | **62.6%** | **14 / 60** |
| `src/audit/events.py` | 423 / 509 | **83.1%** | 1 / 11 |
| `src/audit/chain.py` | 225 / 366 | **61.5%** | 2 / 14 |
| `src/config/loader.py` | 539 / 814 | **66.2%** | 2 / 20 |

The line-coverage denominator counts every non-blank non-comment line, including docstring
bodies, so true statement coverage is somewhat higher than shown. The **function** column is
exact: a function counts as exercised only if at least one line in its body ran.

---

## 2. Silent gaps

### 2.1 GAP-1 — nineteen public functions are specified, implemented, and never executed

X5 requires three ticks. These have two. They are not obscure helpers; they cluster on
exposure, valuation, kill-switch gating and change authorisation.

| Function | Location | What it guards | Why it matters |
|---|---|---|---|
| `gross_notional` | models.py:2189 | Gross exposure | Feeds **EXP-003/004**. The number the risk engine compares against 2x/1x is computed here |
| `market_value` | models.py:2408 | Position valuation | Feeds every exposure and P&L figure |
| `fifo_lots` | models.py:2413 | FIFO cost basis | **Wash-sale and tax correctness** (Block A invariant 9) |
| `quantity` | models.py:2389 | Position size | Feeds sizing and EXP-001 |
| `blocks_new_entries` | models.py:2422 | **Kill-switch gating** | Invariant 7. Whether a tripped switch actually stops entries |
| `permits_new_entries` | models.py:2674 | Regime gating | Fail-closed on `RegimeLabel.UNKNOWN` |
| `has_unreconciled` | models.py:2449 | Reconciliation state | Whether an unreconciled position blocks trading |
| `open_positions` | models.py:2446 | Portfolio enumeration | Input to sector and count limits |
| `settlement_date_for` | models.py:1226 | Settlement date | Tied to **Q-P1.1-1**, which blocks P2.9 |
| `resolve_symbol` | models.py:1357 | Symbol resolution | Ticker changes, corporate actions |
| `feature_timestamp` | models.py:1594 | Feature timing | **Look-ahead bias surface** |
| `remaining` / `is_complete` | models.py:2150/2153 | Order completion | The dust-remainder rule at SPEC-P1.1 §267 |
| `dedupe_key` | models.py:2192 | Fill dedupe | Brokers re-send fills on reconnect (P1.2 §901) |
| `is_effectful` | events.py:697 | Effectful-event classification | Drives **write-before-act** (invariant 5) |
| `link` / `to_payload` | chain.py:71/194 | Chain linking | Audit chain construction |
| `loosens` | loader.py:615 | Whether a change **loosens** a limit | Triggers the **two-person rule** (§5.3) |
| `assert_no_env_risk_reads` | loader.py:1040 | Risk-numbers-from-env lint | Block A: risk numbers are never set by the AI |

`lint_no_env_risk_reads` (the inner function) *is* tested; its raising wrapper is not.

**Blunt reading:** the audit trail and the policy DSL are well tested. The **portfolio and
exposure layer is not**. Every function that computes a number the risk engine will compare
against a constitutional limit is currently unexercised.

### 2.2 Areas X5 names explicitly — checked individually

| Area | Spec | Code | Test | Verdict |
|---|---|---|---|---|
| Timezone / DST / half-day | ✓ P1.1, P1.2 | ✓ `_require_utc` rejects naive | ✓ `verify_p11_invariants` | **OK** |
| Corporate actions | ✓ | ✓ `CorporateAction`, `successor_link` | ✓ | OK, but `resolve_symbol` untested (GAP-1) |
| Halts | ✓ P1.1, P1.2, P1.3 | ✓ `InstrumentStatus.HALTED`, `POOL_HALTED` | ✓ kill-switch transitions tested | **OK** |
| Partial fills | ✓ P1.1 §267 dust rule | ✓ `PARTIALLY_FILLED` + state machine | ~ `t_f1_basis_after_partial_consumption` | **PARTIAL** — the dust rule itself (`is_complete`) is untested |
| Restarts / recovery | ✓ | ✓ `recover_incomplete_intents` | ✓ `verify_p14_audit` | **OK** |
| Second market (India) | ✓ | ✓ `universe.IN` fully parameterised, `IN_POOL`, INR | ✓ | **OK** — no US-only leakage found |

### 2.3 GAP-2 — `-O` makes the harness vacuous (carried as B-5)

Every Python harness except one test uses bare `assert`. Under `python -O` those are stripped,
so the reported "PASSED 42 / 39 / 36" in optimised mode verifies almost nothing. Only
`t_m2_allocate_postcondition_survives_dash_O` uses explicit raises.

### 2.4 GAP-3 — `Q-P1.2-6`'s five runtime assertions remain untested

`ENABLE ALWAYS` triggers under `session_replication_role='replica'`; `EXCLUDE` rejecting an
overlapping symbol mapping; `decision` rejecting a `DENY` verdict; `backtest_ro` denied on a base
table; the overfill trigger on a deferred commit. The migration now executes (B-1), so these are
cheap to close. Blocks **P6.4**.

---

## 3. Contradictions across all documents

| # | Contradiction | State |
|---|---|---|
| C-1 | `depends_on` version drift: P1.2→v0.1, P1.3→v0.2, P1.4→v0.3 of SPEC-P1.1-DOMAIN (current v0.3) | **OPEN**, documentary only |
| C-2 | Six contracts in `src/audit/` and P1.4's table absent from its `produces:` header | **OPEN**, documentary only |
| C-3 | Duplicate contract names across specs | **NONE** — 118 checked |
| C-4 | Constitutional numbers stated two ways | **NONE** — 13 checked |
| C-5 | `20 orders/min` and `10/min per strategy` appear **only** in `config/policy.yaml`, in no spec prose | **OPEN** — correctly implemented, undocumented outside the policy file |

No behavioural contradiction was found between any spec and its code.

---

## 4. Assumption ledger, by impact, unverified flagged as risk

| Rank | Assumption | Verified? | Risk if false |
|---|---|---|---|
| 1 | Mean `audit_log` row ~1,000 B | **NO** — measurement-by-design Q15 | P0.3 §9.4 storage model. Survives 5×, breaks ~10× |
| 2 | 15,000 audit events/session | **NO** — `[DEFAULT-B4]` | Same model |
| 3 | Round-trip cost 25 bps US / 90 bps India | **NO** — Q13, needs ≥200 live fills | Every backtest edge estimate |
| 4 | PDT equity floor 25,000 | **NO** — `ASSUMPTION [VERIFY-P0.2]`, and **not in the STAGE-0 carried-forward register** | A regulatory number, unverified, inside a FROZEN spec |
| 5 | `min_price_inr` 50.00 | **NO** — Q-P1.3-2 | India universe selection. Unfunded, so latent |
| 6 | TimescaleDB compression ratio on audit trail | **NO** | Storage projection |
| 7 | Remaining 26 of 32 | mixed | Local, recoverable |

**Risk flag:** items 1–4 are unverified and all four feed either a capacity decision or a
regulatory control. Item 4 is the one I would escalate: a FROZEN spec carries an unverified
regulatory threshold that no register tracks.

---

## 5. Readiness verdict

# GO WITH CONDITIONS

**P2.1 (Data Ingestion) may proceed now.** No open question blocks it, its inputs are the frozen
domain model and storage schema, and it does not consume any of the untested exposure functions.

Conditions, each tied to the phase it gates:

| # | Condition | Gates | Severity |
|---|---|---|---|
| **1** | Test the exposure/valuation cluster — `gross_notional`, `market_value`, `quantity`, `fifo_lots`, `open_positions` | **P2.8, P2.9** | **BLOCKER for P2.9** |
| **2** | Test the kill-switch and regime gates — `blocks_new_entries`, `permits_new_entries`, `has_unreconciled` | **P2.10** | **BLOCKER for P2.10** |
| **3** | Close Q-P1.1-1 (US settlement/good-faith) and test `settlement_date_for` | **P2.9** | BLOCKER for P2.9 |
| **4** | Close Q-P1.1-6 | **P2.2** | BLOCKER for P2.2 |
| **5** | Convert the harnesses off bare `assert` (B-5 / GAP-2) | all | HIGH — currently `-O` runs prove almost nothing |
| **6** | Test `loosens` and `assert_no_env_risk_reads` | P6.2, any limit change | HIGH — two-person rule and the risk-from-env lint are unexercised |
| **7** | Close Q-P1.2-6's five runtime assertions | P6.4 | MEDIUM |
| **8** | Resolve C-1, C-2, C-5 | — | LOW, documentary |

**Why not GO:** conditions 1, 2 and 6 mean the code that computes the numbers the risk engine
compares against constitutional limits has never been run by a test. Block A invariant 1 makes
the risk engine the thing that overrides every AI output; its inputs being unexercised is not
acceptable at P2.9.

**Why not NO GO:** nothing is contradictory, no constitutional number is wrong, the schema
executes, the audit chain provably detects tampering, and P2.1 touches none of the gaps.

---

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | Measure coverage with stdlib `trace`, not install `coverage` | Block A forbids a dependency where stdlib suffices | Yes | Low — `trace` is slower, equally accurate for line counts |
| 2 | Count a function exercised only if a line in its body ran | Name-grep produced 15 false positives (callables passed without parens, properties) | Yes | Low |
| 3 | Verdict GO WITH CONDITIONS, not NO GO | P2.1 is genuinely unblocked; blocking all of Stage 2 on P2.9's gaps would be wrong | Yes | Medium — if P2.1 turns out to consume an untested function |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|---|---|---|---|
| 1 | The four Stage 1 code drops each had an X2 review | X2 findings appear in P1.1 and P1.2 artifacts; P1.3/P1.4 have harnesses but no separate review record | Search session history | Medium |
| 2 | `trace` line counts approximate statement coverage adequately | No stdlib AST-accurate statement counter without more code | Compare against `coverage.py` in a throwaway venv | Low — function column is exact regardless |

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|---|---|---|---|
| G-1 | Close conditions 1, 2, 6 before P2.1, or in parallel with it? | Owner | §5 above | P2.8, P2.9, P2.10 |
| G-2 | Is the PDT floor 25,000 verified? It is unregistered in STAGE-0-FREEZE §6 | FINRA Rule 4210(f)(8)(B) | Rule text | P3.2, P6.3 |
| G-3 | Did P1.3 and P1.4 receive an X2 review? | Session history | Look for X2 naming SPEC-P1.3/P1.4 | Stage 2 quality |

## CONTRACTS EXPORTED

| Name | Kind | Signature or schema | Consumers |
|---|---|---|---|
| GAP-AUDIT-P1 | document | This file | X4 RED TEAM, all Stage 2 phases |
| THREE-TICK-MATRIX-P1 | table | §1 | P2.x planning |
| SILENT-GAP-REGISTER-P1 | table | §2, 19 functions + 3 gaps | P2.8, P2.9, P2.10, P6.4 |
| STAGE-2-READINESS-VERDICT | verdict | §5 — GO WITH CONDITIONS, 8 conditions | P2.1 entry |

---

# STAGE 1 AUDITED — GO WITH CONDITIONS
