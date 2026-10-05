# DECISIONS — index of decision records

**Created:** 2026-10-05 · **Required by:** `docs/PROMPT-PACK.md` appendix, and
`docs/specs/STAGE-1-FREEZE.md` §11.6 step 6.

**This file is an index. It decides nothing and restates nothing.** Every decision lives in the
record named beside it. If this file and a record disagree, the record is right and this file is
out of date. A decision that has no record does not belong here; write the record first.

Section and line references were checked against commit `f3a7b23`.

---

## 1. Authority and procedure

| Question | Where it is answered |
|---|---|
| What "frozen" means | `docs/specs/STAGE-0-FREEZE.md` §1 |
| When a frozen decision may be re-opened (triggers T1 to T5) | `STAGE-0-FREEZE.md` §7 |
| Who may re-open, and what record is required | `STAGE-0-FREEZE.md` §8 |
| Stage 0 change log | `STAGE-0-FREEZE.md` §9 |
| Stage 1 change log | `docs/specs/STAGE-1-FREEZE.md` §11 |
| Project invariants, fixed stack, hard risk numbers | `docs/PROMPT-PACK.md`, Block A |

---

## 2. Architecture decisions — Stage 0

All frozen by `STAGE-0-FREEZE.md` §3. The text of each ADR is in
`docs/specs/SPEC-P0.1-DECISIONS.md` §3; its one-line index is §2 of that file.

| Id | Subject | Record |
|---|---|---|
| ADR-01 | Frontend | SPEC-P0.1 §3 |
| ADR-02 | Orchestration | SPEC-P0.1 §3 |
| ADR-03 | Kubernetes | SPEC-P0.1 §3 |
| ADR-04 | Alternative data | SPEC-P0.1 §3 |
| ADR-05 | Multi-asset scope | SPEC-P0.1 §3 |
| ADR-06 | Vector database | SPEC-P0.1 §3 |
| ADR-07 | Model retraining cadence | SPEC-P0.1 §3 |
| ADR-08 | Champion/challenger protocol | SPEC-P0.1 §3 |
| ADR-09 | Human-in-the-loop | SPEC-P0.1 §3 |
| ADR-10 | Disaster recovery | SPEC-P0.1 §3 |
| ADR-11 | Single-market-first vs dual-market | SPEC-P0.1 §3 |
| ADR-12 | Long-only vs long/short | SPEC-P0.1 §3 |
| ADR-13 | Holding period | SPEC-P0.1 §3 |
| ADR-14 | Universe size and rebalance cadence | SPEC-P0.1 §3 |
| ADR-15 | Base currency, FX, dual-market NAV | SPEC-P0.1 §3 |
| AD-1 | Replacement of assumption A14 (operating cost) | SPEC-P0.1 §0.5.1; STAGE-0-FREEZE §5 |
| AD-2 | Walk-forward roll length | SPEC-P0.1 §0.5.1; STAGE-0-FREEZE §5 |
| AD-3 | US backup broker | SPEC-P0.1 §0.5.1; STAGE-0-FREEZE §5 |
| AD-4 | India broker roles | SPEC-P0.1 §0.5.1; STAGE-0-FREEZE §5 |
| AD-5 | LLM primary and fallback — conditional on M-7 | SPEC-P0.1 §0.5.1; STAGE-0-FREEZE §5 |

**Constitutional amendment.** AD-5 amends Block A's FIXED STACK line. The amendment is recorded at
`STAGE-0-FREEZE.md` §3.1. The Block A text in `docs/PROMPT-PACK.md` (line 87) still carries the
earlier wording.

The disposition of the twenty Stage 0 amendments (A-1 to A-20) is at `STAGE-0-FREEZE.md` §4.
A-14 was not applied and is carried; see §7 below.

---

## 3. Frozen rule sets

| Set | Record |
|---|---|
| Invariants I1 to I10 | SPEC-P0.1 §10.3 |
| Provider correctness rules N1 to N15; N16 added 2026-08-26 | SPEC-P0.2 §10.5; STAGE-0-FREEZE §9 |
| Budget rules B1 to B12 | SPEC-P0.3 §15 |
| Policy rules, 47, `EXP-001` to `LLM-003` | `config/policy.yaml`; inventory at SPEC-P1.3 §10 |

---

## 4. Per-phase decision tables

Each spec ends with a `DECISIONS MADE` table. Row counts as of `f3a7b23`.

| Record | Version | Status in header | `DECISIONS MADE` | Rows |
|---|---|---|---|---|
| `SPEC-P0.1-DECISIONS.md` | 0.3 | FROZEN | §7 | 23 |
| `SPEC-P0.2-PROVIDERS.md` | 0.5 | FROZEN | §7 | 20 |
| `SPEC-P0.3-BUDGET.md` | 0.5 | FROZEN | end of file | 17 |
| `SPEC-P1.1-DOMAIN.md` | 0.3 | FROZEN | end of file | 22 |
| `SPEC-P1.2-STORAGE.md` | 0.5 | FROZEN, and "NOT re-frozen" in the same header | end of file | 18 |
| `SPEC-P1.3-CONFIG.md` | 0.1 | FROZEN | end of file | 16 |
| `SPEC-P1.4-AUDIT.md` | 0.1 | FROZEN | end of file | 16 |
| `STAGE-1-FREEZE.md` | 1.0 | ACTIVE | after §10 | 4 |
| `STAGE-1-MERGE-CHANGES.md` | 1.0 | ACTIVE | after §5; after §9 (re-run) | 2; 3 |
| `STAGE-1-GAP-AUDIT.md` | 1.0 | ACTIVE | after §5; after §10 (re-run) | 3; 3 |

The status of SPEC-P1.2 is an open matter (X3R-C14). It is listed in §7 and is not settled here.

---

## 5. Owner decisions taken during Stage 1

| Date | Subject | Record |
|---|---|---|
| 2026-09-01 | Finding A: `audit_log` stays a hypertable; the finding is accepted, not fixed | STAGE-1-FREEZE §11.5 |
| 2026-10-01 | BLOCKER-P1: commit `c9f30e3` is kept and the process deviation recorded | STAGE-1-FREEZE §11.6, §11.10 |
| 2026-10-02 | The fourth X2's verdict accepted as the X2 PASS for the technical drop | STAGE-1-FREEZE §11.6, §11.12 |
| 2026-10-02 | X3 and X5 to be re-run, each in its own conversation | STAGE-1-FREEZE §11.6 |
| 2026-10-02 | Remediation E deferred; neither approved nor rejected | STAGE-1-FREEZE §11.11 |

Changes made to frozen Stage 1 artifacts under Phase-author authority (SPEC-P1.2 v0.1 to v0.5)
are the rows of the change log at STAGE-1-FREEZE §11.

---

## 6. Assumptions since verified or falsified

Each spec's `ASSUMPTIONS` table is the register. This section lists only the places where a
record states that an assumption or a claim has since been verified or falsified.

| What | Outcome | Record |
|---|---|---|
| Stage 0 open items Q4/M-5, M-2, M-3 | Retrieved and resolved 2026-08-26 | STAGE-0-FREEZE §6.1; SPEC-P0.1 §9.3 |
| Stage 0 items closed by P0.2 and P0.3 | Closed | SPEC-P0.1 §9.1 |
| Migration 0001 executes | Verified | STAGE-1-FREEZE §2, §11.12 |
| `ENABLE ALWAYS` protects `audit_log` under replica role | **Falsified** — Finding A | STAGE-1-FREEZE §11.1, §11.5 |
| "No supported mechanism" exists to prevent the bypass | **Overstated**; the text is left as written by Owner decision | STAGE-1-FREEZE §11.11 |
| The database hash preimage is deterministic | **Falsified**, then fixed at v0.3 and v0.4 — Finding C | STAGE-1-FREEZE §11.4, §11.7 |
| The CONTENT check covers the SPEC-P1.4 §6.1 key set | **Falsified**, then fixed at v0.5 | STAGE-1-FREEZE §11.8 |
| No contract name is exported by two specs; no producer/consumer mismatch | **Falsified** | STAGE-1-FREEZE §12.3, §12.9 |
| Order rates appear in no spec prose (C-5) | **Falsified**; withdrawn | STAGE-1-GAP-AUDIT §8 |
| `[CONST-2]` is enforced at the `Decision` constructor | Verified within Stage 1's scope | X5 report §4, in `docs/specs/reviews/X5-RERUN-2026-10-02/` |
| The research summary gives no India price floor | **Contradicted** by the summary; not decided | STAGE-1-FREEZE §12.4 (X3R-C5) |

Assumptions that remain unverified are ranked at STAGE-1-FREEZE §12.5 and in the X5 report §4.

---

## 7. Decisions that are open

**None of these is decided by this file.** Each is listed so that it is not lost, with the record
that states it and the phase it gates.

| Id | Subject | Record | Gates |
|---|---|---|---|
| X3R-C14 | Status of SPEC-P1.2 v0.5 | STAGE-1-FREEZE §12.4, §12.8 | Stage 1 re-freeze |
| §11.6 step 7 | Re-freeze of Stage 1; rewrite of the Stage 2 entry gate | STAGE-1-FREEZE §11.6, §13 | Stage 2 entry |
| Q-P1.2-7 / X3R-M1 | The audit envelope and the audit table; where the reproducibility bundle is stored (X3R-Q2); who owns the audit writer (X5R-Q1) | SPEC-P1.2 OPEN QUESTIONS; STAGE-1-FREEZE §12.3; STAGE-1-GAP-AUDIT §9, §10 | P2.1 code that writes an audit event |
| X3R-M2 / X3R-Q1 | The effective-config dump against the no-JSON-numbers rule | STAGE-1-FREEZE §12.3 | First run that writes its config event |
| X5R-Q2 | Whether a change of `mode`, `action` or `comparison` is a loosening | STAGE-1-GAP-AUDIT §9 | Any policy change |
| A-14 | Whether a `[CONST-6]` DENY applies to exposure-reducing actions | STAGE-0-FREEZE §4, §6.2, §10 | P2.9 |
| X3R-Q3 | How a `PolicyVerdict` becomes a `RiskVerdict` | STAGE-1-FREEZE §12.4 (X3R-C9) | P2.9 |
| X3R-Q4 / X5R-G5 | Earnings blackout | STAGE-1-FREEZE §12.7; STAGE-1-GAP-AUDIT §9 | P2.9 |
| X5R-Q3 | Whether daily and weekly loss trip the kill switch | STAGE-1-GAP-AUDIT §9 | P2.10 |
| X3R-Q5 | India price floor | STAGE-1-FREEZE §12.4 | India activation |
| Remediation E | Finding A's proposed remediation | STAGE-1-FREEZE §11.11 | Deferred |
| Q-P1.3-1 | The second approver | SPEC-P1.3 OPEN QUESTIONS | Any limit increase |
| Q-P1.4-1 | Where anchors are published | SPEC-P1.4 OPEN QUESTIONS | P6.2, P6.4 |
| F-2 / G-3; Q-P1.1-8 | Whether SPEC-P1.3 and SPEC-P1.4 had an X2; an independent X2 of SPEC-P1.1 | STAGE-1-FREEZE OPEN QUESTIONS; STAGE-1-GAP-AUDIT OPEN QUESTIONS; SPEC-P1.1 OPEN QUESTIONS | Not assigned to a phase |
| M-7 | DeepSeek data-retention terms; AD-5 is conditional on it | STAGE-0-FREEZE §6.2, §7 (T2) | AD-5 |

Open questions that wait on an external fact or a measurement, not on a decision, are in each
spec's `OPEN QUESTIONS` table and in STAGE-0-FREEZE §6.

---

## 8. Keeping this file

- Add a row when a record gains a decision. Add the record first.
- Move a row out of §7 only when the record that closes it exists, and cite that record.
- Do not copy the text of a decision into this file.
