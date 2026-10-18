---
id: ROADMAP-V1
version: 0.3
status: DRAFT
phase: Roadmap for v1 under Model B
depends_on: [MODEL-B-DECISION v0.3, STAGE-0-OWNER-DECISIONS v0.1, SCOPE-MULTI-USER v0.4]
produces: [RM-MAP, RM-ORDER, RM-NEW-1, PhaseStatus, RoadmapEntry]
---

# Roadmap for v1 (Model B: signals only)

Date: 2026-10-14. `docs/PROMPT-PACK.md` is not edited (it is read, not edited, in the new run).
This file says how each pack phase is used for v1. The GitHub tracker (issue #37) is not changed;
the Owner may mirror this table there.

Version history: 0.1 (2026-10-14) phase map and order. 0.2 (2026-10-17) Block B conformance
pass: RM-MAP and RM-NEW-1 named in the text (0.1 listed RM-NEW-1 in `produces` without defining
it), section 4 adds a typed form of the phase map, and the four mandatory tables are added. No
phase changes status and the order is unchanged. 0.3 (2026-10-17) Block C conformance pass:
section 5 (blocking questions BQ-41 and BQ-42 with [DEFAULT-52] and [DEFAULT-53]), section 6
(edge cases), section 7 (non-blocking details); RM-E4 carries its default inline. No phase changes
status and the order is unchanged.

Status meanings: **In** (run as written), **Adapted** (run with the instruction in the note, which
the phase receives through `MODEL-B-DECISION.md`), **Deferred** (not in v1; returns only with a
separately approved execution phase, MB-8), **Re-run** (already run once; must be run again under
Model B), **New** (not in the pack).

## 1. Phase map (RM-MAP)

| Phase | v1 status | Note |
|-------|-----------|------|
| P0.1 Decisions | **Re-run** | ADR-01 now covers users, not only the operator; broker-dependent ADR items per MODEL-B-DECISION section 6 |
| P0.2 Providers | **Re-run** | Data providers only, with licences for a commercial signals service; brokers deferred |
| P0.3 Budget | **Re-run** | Commercial data licences, delivery service, no order path |
| X3, X5 Stage 0 | Re-run after the three above | |
| P1.1 Domain | Adapted | Signal, model portfolio, strategy, user, plan, disclosure, jurisdiction; order and fill types not in the v1 live path |
| P1.2 Storage | Adapted | Published-signal and track-record tables, 5-year retention, append-only; user tables without broker data (MB-AC-4) |
| P1.3 Config | Adapted | Per-market publication switches (MB-AC-10); risk numbers per BA-4 |
| P1.4 Audit | Adapted | Audit before publication (MB-AC-5); OWD-2's two sinks |
| P2.1 to P2.7 | In | Data, validation, scanner, features, scoring, regime, decision engine |
| P2.8 Sizing | Adapted | Model-portfolio weights under BA-4; no per-user sizing (MB-10) |
| P2.9 Risk engine | Adapted | Gates signals and model-portfolio changes, not orders |
| P2.10 Kill switch | Adapted | Stops publication (BA-3) |
| P3.1 Broker abstraction | Deferred | MB-8 |
| P3.2 Execution engine | Deferred | MB-8 |
| P3.3 Position monitor | Adapted | Monitors model-portfolio positions from market data, for exit signals and the track record |
| P3.4 Exit engine | Adapted | Produces exit signals |
| P4.1 to P4.4 | In | Plus AI-use labelling and disclosure (IN-2, MB-AC-7) |
| P5.1 Backtest | In | The simulated broker inside the backtester is research, not execution |
| P5.2, P5.3, P5.4 | In | |
| P5.5 Chaos and recovery | Adapted | No broker reconciliation; publication-pipeline drills |
| P6.1 Observability | In | |
| P6.2 Security | Adapted | User accounts, authentication, data protection, per-user isolation |
| P6.3 Compliance | Adapted | SEBI RA Regulations; US Advisers Act or publisher exclusion; disclosures; records |
| P6.4 Deploy | In | Plus the CI checks of MB-AC-1 and MB-AC-3 |
| P6.5 Go-live gates | Adapted | Gates for publishing in each market: legal review, registration, licensed data, paper track record |
| P6.6 Learning | In | |
| **PB.1 Signal delivery** (RM-NEW-1) | **New** | User-facing delivery: plans, subscriptions, signal pages and notifications, disclosures, consent, support. A prompt must be written in the pack's format before it runs; it follows P6.2 and precedes P6.5 |

## 2. Order to run (RM-ORDER)

1. P0.1, P0.2, P0.3 re-run under Model B, each in a new conversation, each fed this roadmap,
   `MODEL-B-DECISION.md` and `SCOPE-MULTI-USER.md` v0.2.
2. X3 and X5 for Stage 0.
3. Stage 1: P1.1, P1.2, P1.3, P1.4.
4. Stage 2 up to P2.10 (adapted).
5. Stage 3: P3.3 and P3.4 (adapted) only.
6. Stage 4.
7. Stage 5.
8. Stage 6, with PB.1 between P6.2 and P6.5.
9. X4 Red Team before any signal is published to any user.

## 3. Acceptance for the roadmap itself

- Every pack phase has exactly one status above.
- No Deferred phase is run in v1.
- PB.1 has a written prompt before it runs.

## 4. Typed form of the phase map

The phase map is read by every later phase and by the X reviews to decide whether a phase may
run. Its typed form:

```python
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictBool


class PhaseStatus(StrEnum):
    IN = "In"
    ADAPTED = "Adapted"
    DEFERRED = "Deferred"
    RE_RUN = "Re-run"
    NEW = "New"


PhaseId = Annotated[str, Field(pattern=r"^(P[0-6]\.[0-9]{1,2}|PB\.[0-9]|X[0-9])$")]


class RoadmapEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    phase_id: PhaseId
    status: PhaseStatus
    note: Annotated[str, Field(max_length=500)]
    prompt_written: StrictBool
```

| Field | Type | Unit | Timezone | Nullable | Valid range | Violation means |
|-------|------|------|----------|----------|-------------|-----------------|
| `phase_id` | `str` | none | n/a | no | `P0.1` to `P6.99`, `PB.0` to `PB.9`, `X0` to `X9`; unique across the map | The entry is rejected; a phase with no valid entry may not run |
| `status` | `PhaseStatus` | none | n/a | no | One of the five values in the status meanings above | The entry is rejected; the phase may not run |
| `note` | `str` | none | n/a | no (empty string allowed for status In) | 0 to 500 characters; non-empty when status is Adapted, Deferred, Re-run or New | An Adapted phase without its instruction may not run, because it would run as written |
| `prompt_written` | `bool` | none | n/a | no | `true` for every pack phase; for a New phase, `true` only once a prompt in the pack's format exists in the repository | A New phase with `false` may not run |

A row in section 1 that names several phases (the "X3, X5", "P2.1 to P2.7", "P4.1 to P4.4" and
"P5.2, P5.3, P5.4" rows) is one entry per phase, all with that row's status and note.

### 4.1 Error paths

Every path denies the phase run; none falls back to running the phase as written.

| # | Condition | Fail-closed behaviour |
|---|-----------|-----------------------|
| RM-E1 | A phase is requested that has no entry in RM-MAP | Not run; the requester is told the phase is not in the v1 map and the map needs a new version first |
| RM-E2 | A phase with status Deferred is requested | Not run; MB-8 requires a separately approved execution phase |
| RM-E3 | A phase with status New is requested and `prompt_written` is `false` | Not run; the prompt is written and recorded first (section 3) |
| RM-E4 | A phase is requested before the phases ahead of it in RM-ORDER have a recorded result ([DEFAULT-52]: committed with the Owner's yes) | Not run; the missing upstream phases are named |
| RM-E5 | Two entries carry the same `phase_id` | The map is invalid; no phase runs until a new version resolves it |

## 5. Blocking questions and the defaults used

Numbering continues from `MODEL-B-DECISION.md` (BQ-40, [DEFAULT-51]).

| # | Question | Options | Default used | If the default is wrong |
|---|----------|---------|--------------|-------------------------|
| BQ-41 | What counts as a phase's "recorded result" for RM-ORDER and RM-E4? | (a) a draft spec file exists; (b) the spec is committed on `main` after the Owner's yes to its diff; (c) (b) plus a passed X review | [DEFAULT-52] (b). X reviews (X3, X5) gate the end of a stage, not each phase. | Under (a), a phase builds on a draft the Owner never approved. Consequence of (b) today: no new-run spec is committed yet (`git log -- "docs/new specs"` is empty, 2026-10-17), so no phase after P0.3 may start until the Stage 0 re-run specs are committed. |
| BQ-42 | When an upstream spec gets a new version after a downstream phase has run, is the downstream phase re-run? | (a) always; (b) never, a dated notice only; (c) a dated notice, plus a re-run when the change alters a contract the downstream spec imports or an X review asks for one | [DEFAULT-53] (c). | Under (a), every typo fix re-runs the pack; under (b), a changed contract is silently out of date downstream. |

## 6. Edge cases for the rules this file writes

| Rule | Edge case | Resolution |
|------|-----------|------------|
| RM-MAP | X1, X2 and X4 have no row of their own. | They are templates applied to phases (code, review, red team), not phases with one place in the order. They are In wherever the pack applies them; RM-E1 does not apply to them. X4 is also a gate in RM-ORDER step 9. |
| RM-MAP | A row covers a range ("P2.1 to P2.7"). | The range is inclusive: P2.1, P2.2, P2.3, P2.4, P2.5, P2.6 and P2.7 (section 4). |
| RM-MAP | An Adapted phase's note conflicts with its pack prompt. | The note governs for v1, through `MODEL-B-DECISION.md`; the phase records the conflict in its own problems section. |
| RM-MAP | A Deferred phase holds a contract an In phase needs (for example an order type that P5.1's simulated broker uses). | The In phase defines what it needs inside its own package (`v2/backtest`); nothing is imported from a Deferred phase, which has no v1 code. |
| RM-ORDER | A Stage 0 re-run changes a decision that Stage 1 has not yet consumed. | Nothing to redo; Stage 1 reads the committed version. |
| RM-ORDER | X3 or X5 asks for a change to a Stage 0 spec. | A new version of that spec, committed with the Owner's yes ([DEFAULT-52]); downstream handling per [DEFAULT-53]. |
| RM-ORDER | The Owner asks for a phase out of order. | RM-E4 applies: the missing upstream phases are named and the Owner decides; the map is not bypassed silently. |
| RM-NEW-1 | PB.1 needs user, plan or subscription fields that P1.1 did not define. | P1.1 gets a new version ([DEFAULT-53]); PB.1 does not define its own copy of a domain type. |
| RM-NEW-1 | PB.1 needs a delivery provider (email, push). | It is a provider choice, made in a P0.2-style evidence table inside PB.1 or a P0.2 re-run; it is not a second application host (`STAGE-0-OWNER-DECISIONS.md` section 12, OWD-7). |
| RM-E3 | A prompt for PB.1 exists only in chat. | Not written for RM-E3: `prompt_written` becomes `true` only when the prompt is a file in the repository. |
| RM-E5 | Two rows name the same phase with the same status. | Still invalid; one entry per phase. |

## 7. Non-blocking details resolved in this file

| # | Detail | Resolution |
|---|--------|------------|
| RD-1 | Dates in this file | Calendar dates in `Asia/Kolkata`, the Owner's timezone. |
| RD-2 | Phase identifier format | Exactly as the pack writes it (`P2.10`, not `P2.1.0`); the pattern in section 4 is the rule. |
| RD-3 | A phase that runs over several conversations | One phase, one entry; its result is recorded when its spec is committed ([DEFAULT-52]). |

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|----------|-----------|-------------|-----------------------|
| RM-MAP | Each pack phase has one v1 status (section 1) | MB-1 and MB-8 remove the execution path; the rest of the pack still applies | Yes, by a new version of this file | Every later phase: a wrongly Deferred phase leaves a gap, a wrongly kept phase builds execution code that MB-1 forbids |
| RM-ORDER | P0.1 to P0.3 re-run first, then X3 and X5, then Stages 1 to 6 without P3.1 and P3.2 (section 2) | The Stage 0 specs assumed a single own-account trader with orders; every later phase consumes them | Yes, before Stage 1 starts | Stage 1 built on Stage 0 specs that still assume execution |
| RM-NEW-1 | New phase PB.1 Signal delivery, between P6.2 and P6.5 | The pack has no phase for user-facing delivery, which Model B makes the product; delivery needs P6.2's user authentication and must exist before P6.5's go-live gates | Yes | Delivery built without authentication, or go-live gates with no delivery path to gate |
| RM-D-4 | The phase map gets a typed form with error paths (section 4) | Block B: no prose-only types; deciding whether a phase may run needs a deterministic rule | Yes | None at run time; the map is a planning record |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|------------|------------------------|---------------|-----------------|
| DEFAULT-52 | A phase's result counts once its spec is committed with the Owner's yes | BQ-41 | Owner confirms the working rule | RM-ORDER gating changes |
| DEFAULT-53 | Upstream version changes: dated notice, re-run only when an imported contract changes or an X review asks | BQ-42 | X5 for each stage | Downstream specs re-run more or less often |
| RM-A-1 | PB.1 needs no data or model output beyond what P2.1 to P4.4 produce | PB.1 has no prompt yet | Write the PB.1 prompt; check its inputs against the contracts those phases export | PB.1 moves earlier, or an earlier phase gains an Adapted note |
| RM-A-2 | The simulated broker inside P5.1 does not break MB-1, because it never reaches a real broker | MB-1 forbids any component that can submit an order at a broker; a backtest fill model sends nothing outside the process | MB-AC-2 static test of network calls; X2 review of P5.1 | P5.1 becomes Adapted with a stricter boundary |

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|----------|---------------------|-----------------------------|--------------------|
| RM-Q-1 | Which delivery channels does PB.1 build? | Owner | `MODEL-B-DECISION.md` MB-RQ-5 | PB.1 prompt |
| RM-Q-2 | Is the service paid, free or both? | Owner | `MODEL-B-DECISION.md` MB-RQ-3 | PB.1 prompt (plans and subscriptions) |

## CONTRACTS EXPORTED

| Name | Kind (type/table/event/endpoint/config key) | Signature or schema | Consumers |
|------|---------------------------------------------|---------------------|-----------|
| RM-MAP | rule identifier | Section 1; typed as `list[RoadmapEntry]` in section 4 | Every later phase; X reviews |
| RM-ORDER | rule identifier | Section 2 | Every later phase; X5 |
| RM-NEW-1 | rule identifier | PB.1 row of section 1 | PB.1 prompt; P6.5 |
| `PhaseStatus` | type | `StrEnum`: In, Adapted, Deferred, Re-run, New (section 4) | X reviews |
| `RoadmapEntry` | type | `phase_id: PhaseId`, `status: PhaseStatus`, `note: str`, `prompt_written: bool` (section 4) | X reviews |
