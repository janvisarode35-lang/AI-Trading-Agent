---
id: STAGE-1-MERGE-CHANGES
version: 1.0
status: ACTIVE
phase: Stage 1 — SPECIFY, closure (template X3 — MERGE, second output)
depends_on: [STAGE-1-FREEZE v1.0]
produces: [MERGE-CHANGE-LOG-P1]
---

# X3 MERGE — what moved, what conflicted, what was resolved

Companion to `STAGE-1-FREEZE.md`. X3's output contract requires "a CHANGES file listing what
moved, what conflicted, and what was resolved".

**Run at:** 2026-08-31 (UTC) · **HEAD:** `8b24083`

---

## 1. What moved

Nothing moved. No spec text was relocated, rewritten or deleted by this merge.

The merge is by index and consolidation (STAGE-1-FREEZE §1), so the four specs remain the source
of truth and are byte-identical to their pre-merge state apart from the two header lines in §3.

| Consolidated view | Rows | Built from |
|---|---|---|
| CONSOLIDATED-CONTRACTS-P1 | 118 | the four `## CONTRACTS EXPORTED` tables |
| CONSOLIDATED-ASSUMPTIONS-P1 | 32 | the four `## ASSUMPTIONS` tables |
| CONSOLIDATED-OPEN-QUESTIONS-P1 | 29 unique | the four `## OPEN QUESTIONS` tables, deduplicated by Q-id |
| RS-COVERAGE-MATRIX-P1 | 23 | every `[RS §n]` citation in a Stage 0 or Stage 1 spec |

All four were **generated from the spec files**, not transcribed. Re-running the generator against
unchanged specs reproduces them exactly.

Deduplication note: 31 open-question rows across four specs collapse to 29 unique Q-ids. Exactly
one id is duplicated — **`Q-P1.1-1`** (US settlement / good-faith rules), which appears in all
three of P1.1-DOMAIN, P1.2-STORAGE and P1.3-CONFIG, contributing the two collapsed rows. First
occurrence wins; no question was dropped.

That one question being restated by every spec that touches it is a signal, not noise:
`Q-P1.1-1` is the most widely depended-on open item in Stage 1 and it blocks **P2.9**.

---

## 2. What conflicted

### C-1 — `depends_on` version drift · **2 instances · UNRESOLVED**

| Spec | Declares | Actual |
|---|---|---|
| SPEC-P1.2-STORAGE | `SPEC-P1.1-DOMAIN v0.1` | v0.3 |
| SPEC-P1.3-CONFIG | `SPEC-P1.1-DOMAIN v0.2` | v0.3 |

Three downstream specs pin three different versions of one upstream. Documentary only —
`verify_p11_p12_contract` reports 21 table/model pairs ALIGNED, so P1.2 does not contradict
v0.3; it was simply written before it.

### C-2 — six contracts under-declared · **UNRESOLVED**

`SPEC-P1.4-AUDIT`'s `produces:` header lists 22 contracts. Its own CONTRACTS table and
`src/audit/` carry six more: `BreakKind`, `ChainBreak`, `IntentRecord`,
`benchmark_verification()`, `promote_to_action()`, `uuid7_timestamp_ms()`.

All six verified present in code. `produces:` is what a downstream phase reads to know what it may
import, so an under-declared header invites a consumer to re-implement what exists.

### C-3 — duplicate contract names · **NONE FOUND**

All 118 exported contracts checked for a name exported by two specs with mismatched signatures.
Zero. The producer/consumer boundary between the four specs is clean.

### C-4 — constitutional numbers stated two ways · **NONE FOUND**

Seven Block-A numbers traced across all seven specs plus `config/policy.yaml`: position ≤5% NAV,
sector ≤20% NAV, daily loss ≤2%, max drawdown ≤10%, stop = 2.5 × ATR(14), 20 orders/min,
liquidity ≤1% of ADDV. Every occurrence agrees. No number is stated two ways.

One structural observation, not a conflict: `20 orders/min global` appears **only** in
`config/policy.yaml` and in no spec prose. It is correctly implemented; it is simply undocumented
outside the policy file.

---

## 3. What was resolved

| # | Change | Files |
|---|---|---|
| R-1 | `status: DRAFT` → `status: FROZEN` | all four Stage 1 specs |
| R-2 | Added `frozen_by: STAGE-1-FREEZE.md (2026-08-31)`, matching the Stage 0 header convention | all four Stage 1 specs |

**Nothing else was resolved.** C-1 and C-2 were deliberately left open: X3 step 3 requires
contradictions to be "presented with the two sources and a recommended resolution", not fixed
silently. Recommended fixes are in STAGE-1-FREEZE §3.

---

## 4. Deviation from the X3 template

X3 step 1 says "merge into one coherent document". This run produced an **index plus consolidated
cross-spec tables** instead of a physical concatenation of 4,440 spec lines.

Rationale: a concatenated copy becomes a second source of truth that drifts from the first, and
C-1 is a live instance of exactly that failure mode already present in this project. STAGE-0-FREEZE
took the same approach.

Recorded here so the deviation is visible rather than assumed. If a single physical document is
required later, it must be generated from the specs, never hand-maintained.

---

## 5. State after the merge

| | |
|---|---|
| Stage 1 specs | 4, all **FROZEN** |
| Consolidated contracts | 118, no signature mismatches |
| Open questions | 29 unique; **4** block a Stage 2 phase; **none block P2.1** |
| RS coverage | 15/23 sections cited; 2 real gaps (§9 → Stage 4, §14 → P6.1), both scheduled |
| Unresolved conflicts | C-1, C-2 — both documentary, both LOW |
| Still required before P2.1 | **X5 GAP AUDIT** |

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | Generate consolidated tables rather than transcribe them | A transcribed table is a copy that drifts; a generated one is reproducible from source | Yes | Low |
| 2 | Carry C-1 and C-2 rather than fix them in this run | X3 step 3 forbids silent resolution | Yes | Low — both documentary |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|---|---|---|---|
| 1 | Deduplicating `Q-P1.1-1` by first occurrence loses nothing | Its three occurrences restate one upstream question with the same disposition | Diff the three occurrences of `Q-P1.1-1` across P1.1, P1.2 and P1.3 | Low — a differing restatement would be missed |

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|---|---|---|---|
| 1 | Fix C-1 and C-2 now or carry them? | Owner | STAGE-1-FREEZE §3 | None directly |
| 2 | Should `20 orders/min` be documented in a spec, not only `policy.yaml`? | Owner | §2 C-4 above | P2.9 traceability |

## CONTRACTS EXPORTED

| Name | Kind | Signature or schema | Consumers |
|---|---|---|---|
| MERGE-CHANGE-LOG-P1 | document | This file | X5 GAP AUDIT, audit trail of the freeze |

---

# X3 RE-RUN — 2026-10-02

**Run at:** 2026-10-02 · **HEAD:** `b8b1340` · Required by STAGE-1-FREEZE §11.6 step 4, and made
in its own conversation. The result of record is STAGE-1-FREEZE §12. This section is its CHANGES
file. The full report and its evidence are in `docs/specs/reviews/X3-RERUN-2026-10-02/`.

**Sections 1 to 5 above describe the 2026-08-31 merge and are left as written.** Where this
section differs from them, this section is the later finding.

The re-run was read-only. It edited no file in this repository, and it sets no status.

## 6. What moved

Nothing moved. The four specs are still the source of truth and the merge is still by index.

One spec changed between the two merges: SPEC-P1.2-STORAGE, v0.1 → v0.5, with
`migrations/0001_initial.sql`. The other three specs, and `models.py`, `loader.py`, `policy.yaml`,
`events.py` and `chain.py`, are byte-identical to `605ff40`.

| Consolidated view | 2026-08-31 | 2026-10-02 | Why it differs |
|---|---|---|---|
| Contracts | 118 | 118 | No row added or removed. Rows 69 and 70 changed behaviour, not shape |
| Assumptions | 32 | 32 rows, **30 distinct** | §1 did not de-duplicate. Two pairs are the same assumption |
| Open questions | 31 rows, 29 unique | **32 rows, 30 unique** | `Q-P1.2-7` added at v0.5 |
| Coverage | 23 sections, by citation | **70 requirements, mapped one by one** | §1's method counted citations |

## 7. What conflicted

Full text, with both sources for each, is in STAGE-1-FREEZE §12.3 and §12.4.

**Contract mismatches — §2 C-3 and §5's "no signature mismatches" are withdrawn.**

| Id | Severity | Mismatch | Existed at `605ff40` |
|---|---|---|---|
| X3R-M1 | HIGH | P1.4's envelope and P1.2's `audit_log` hash one event two ways; five envelope fields have no column | yes |
| X3R-M2 | HIGH | P1.3's `EffectiveConfig.audit_payload()` is rejected by P1.4's `AuditEnvelope` | yes |
| X3R-M3 | MEDIUM | `canonical_bytes` is exported by P1.3 and by P1.4, with different behaviour | yes |
| X3R-M4 | MEDIUM | P1.1 still exports `AuditEvent`, which no longer exists | yes |
| X3R-M5, M6, M7 | LOW | As-of function signatures; six contract rows; two DDL blocks that differ from the migration | yes |

**Contradictions.**

| Id | State against §2 above |
|---|---|
| X3R-C1 | **C-1 grew from 2 instances to 4.** P1.3 and P1.4 both declare `SPEC-P1.2-STORAGE v0.1`; it is v0.5 |
| X3R-C2 | **C-2 is in all four specs**, not P1.4 alone |
| X3R-C5 to C14 | New. Ten contradictions; C5, C9 and C14 are MEDIUM, the rest LOW |

**Coverage gaps.** Eight that no document records, X3R-G1 to G8. X3R-G1, earnings blackout,
belongs to Stage 1.

**Corrections to this file.**

| Where | Stated | Found |
|---|---|---|
| §2 C-3 | No contract name is exported by two specs | `canonical_bytes`, rows 89 and 106 |
| §2 C-4, and OPEN QUESTIONS row 2 | "`20 orders/min global` appears **only** in `config/policy.yaml` and in no spec prose" | SPEC-P1.3 §10, line 348: "20 orders/min global, 10 per strategy". Open question 2 has no subject |
| §5 | "**none block P2.1**" | `Q-P1.2-7` blocks any P2.1 code that writes an audit event |
| §5 | "2 real gaps" | The same 2, plus 8 unrecorded |
| §4 | 4,440 spec lines | 4,591 at `b8b1340` |

## 8. What was resolved

**Nothing.** X3 step 3 forbids silent resolution, and the re-run was read-only. R-1 and R-2 above
are not repeated: no status was set and no header was edited.

Recommended statuses, for the Owner to decide, are in STAGE-1-FREEZE §12.8. In one line:
SPEC-P1.2 should read `DRAFT` until it is re-frozen; the other three stay `FROZEN`.

## 9. State after the re-run

| | |
|---|---|
| Stage 1 specs | 4. Three `FROZEN` and unchanged. SPEC-P1.2 v0.5 **not re-frozen** |
| Consolidated contracts | 118. **2 HIGH, 2 MEDIUM and 3 LOW mismatches** |
| Open questions | 30 unique, plus 5 raised by the re-run (X3R-Q1 to Q5) |
| Blocking P2.1 | **`Q-P1.2-7`**, for any audit-writing code |
| Unresolved conflicts | 12 contradictions; 7 mismatches; 8 coverage gaps |
| Still required before P2.1 | X5 re-run; `DECISIONS.md`; the Owner's re-freeze (§11.6 steps 5 to 7) |

## DECISIONS MADE — re-run

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | Full re-merge, not a delta | The 2026-08-31 baseline was wrong in parts the P1.2 change does not touch | Yes | Low |
| 2 | Map coverage by requirement, not by citation | A section can be cited and still leave a requirement uncovered | Yes | Low |
| 3 | Resolve nothing and set no status | X3 step 3; the re-run's scope was read-only | Yes | None |

## ASSUMPTIONS — re-run

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|---|---|---|---|
| 1 | The database results in STAGE-1-FREEZE §11.12 hold | The re-run started no database | Re-run the three shell suites | Low for this merge: no finding here depends on them |
| 2 | A text search finds every mention of a requirement | Coverage gaps were established by searching nine files for 28 terms | Read the Stage 0 specs for each gap | Medium — a gap may be a decision worded differently |

## OPEN QUESTIONS — re-run

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|---|---|---|---|
| X3R-Q1 | Which side changes for X3R-M2 — P1.3's payload or P1.4's no-numbers rule? | Owner | STAGE-1-FREEZE §12.3 | Any run |
| X3R-Q2 | Where is the `ReproducibilityBundle` stored? | P1.2 and P1.4 jointly | `Q-P1.2-7`, widened | P2.5, P2.6, P2.7, P2.9 |
| X3R-Q3 | How does a `PolicyVerdict` map to a `RiskVerdict`? | P2.9 | SPEC-P1.1 §8.2 against SPEC-P1.3 §4 | P2.9 |
| X3R-Q4 | Is earnings blackout in scope, and under which rule id? | Owner | `master-research-summary.md` §4, §6 Phase 8 | P2.9 |
| X3R-Q5 | India price floor: ₹100 or ₹50? | Owner | `master-research-summary.md` §4 line 118; `policy.yaml` line 117 | India activation |

## CONTRACTS EXPORTED — re-run

| Name | Kind | Signature or schema | Consumers |
|---|---|---|---|
| MERGE-CHANGE-LOG-P1, 2026-10-02 section | document | Sections 6 to 9 above | X5 re-run, Owner reconciliation |
