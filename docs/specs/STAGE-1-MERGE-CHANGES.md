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
