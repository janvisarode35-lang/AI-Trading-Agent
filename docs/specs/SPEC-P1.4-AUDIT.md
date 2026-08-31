---
id: SPEC-P1.4-AUDIT
version: 0.1
status: DRAFT
phase: P1.4 — Audit Trail & Event Model
depends_on: [SPEC-P1.1-DOMAIN v0.3, SPEC-P1.2-STORAGE v0.1, SPEC-P1.3-CONFIG v0.1, SPEC-P0.1-DECISIONS v0.3, SPEC-P0.3-BUDGET v0.5, STAGE-0-FREEZE v1.1]
produces: [src/audit/events.py, src/audit/chain.py, fn.uuid7, fn.canonical_json, fn.canonical_bytes, class.AuditEnvelope, class.ReproducibilityBundle, class.EventSpec, enum.EventType, enum.Producer, const.EVENT_REGISTRY, const.EFFECTFUL_EVENT_TYPES, const.REPRODUCIBLE_EVENT_TYPES, fn.verify_chain, fn.assert_chain_intact, class.Anchor, fn.verify_against_anchor, fn.write_before_act, fn.recover_incomplete_intents, fn.replay_run, fn.export_for_regulator, const.CANONICAL_SCHEMA_VERSION]
---

# SPEC-P1.4 — Audit Trail & Event Model

**Phase:** Stage 1 — SPECIFY, prompt `P1.4`
**Date:** 2026-08-27
**Author role:** Engineer designing the system of record

> **The audit log is the system of record.** Not the database's derived tables, not the broker's
> statement, not the application logs. Every other store is a projection of it, and where they
> disagree, this wins for the question *what did the system do and why*.

---

## 0. What this phase changed upstream

P1.4 supersedes two earlier decisions. Both are recorded here and applied in the affected specs;
**no frozen Stage 0 artifact was touched** (hashes re-verified unchanged).

| Superseded | Was | Now | Why |
|---|---|---|---|
| **P1.1 §2 row 10** — identifier type | `uuid4` for surrogate ids | **UUIDv7** for audit event ids; `uuid4` elsewhere; `seq` still authoritative for ordering | P1.1's own reasoning was *"stdlib has no UUIDv7 and `[CONST]` forbids a dependency that ten lines of stdlib would cover."* That rule says **implement the ten lines**, not avoid the format. The implementation is twenty lines (§4.1). A randomly-sorting event id makes every range scan over the audit trail a full scan |
| **P1.1 `[DEFAULT-9]`** — envelope/catalogue split | "P1.1 owns the chained envelope, P1.4 owns the event catalogue" | **One envelope, `audit.events.AuditEnvelope`.** P1.1 keeps only the `AuditEventClass` **enum**, which `audit.events` imports rather than redefines | Building P1.4 showed the split produces **two models of one concept**. The real envelope needs `causation_id`, `schema_version`, `input_hash` and a reproducibility bundle; a domain-layer copy lacking them is a second definition free to drift from the one that actually writes rows |

**Closed:** `Q-P1.2-1` — the canonical JSON serialisation the hash chain covers. Defined in §6.2.

---

## 1. BLOCKING questions — and the defaults applied

| # | Question | Options | Default applied | What breaks if the default is wrong |
|---|---|---|---|---|
| **1** | What canonical form does the hash cover? | (a) `jsonb::text` from PostgreSQL; (b) full RFC 8785 JCS; (c) **JCS with JSON numbers banned** | **(c)** `[DEFAULT-A1]` | (a) is not stable across major versions — a Postgres upgrade would invalidate every historical hash. (b)'s number canonicalisation (ECMAScript `Number::toString`) is the one part genuinely hard to implement identically twice, and it is exactly where a float re-enters. Banning JSON numbers makes canonicalisation *key sorting plus whitespace*, which two implementations cannot disagree about |
| **2** | Is `recorded_at` inside the hash? | (a) yes; (b) **no** | **(b)** `[DEFAULT-A2]` | `recorded_at` is when we wrote it down, not what happened. Hashing it means a replayed write can never reproduce the hash, which defeats the replay tool. `occurred_at` **is** hashed |
| **3** | One global chain or one per stream? | (a) **one global**; (b) per market / per run | **(a)** `[DEFAULT-A3]`, carried from P1.2 `[DEFAULT-S9]` | Per-stream chains need a merge proof to establish global ordering. Cost of one chain is a serialised insert path at ~0.3 writes/second (P0.3 §6.1) — three orders of magnitude from contention |
| **4** | Does the chain alone prove tamper evidence? | (a) yes; (b) **no — anchoring is required** | **(b)** `[DEFAULT-A4]` | Rewrite one row and recompute every hash after it and the result is a **perfectly consistent chain telling a different story**. §12 demonstrates this passing internal verification. Only a hash published where the rewriter has no write access reveals it |
| **5** | Anchor cadence? | (a) hourly; (b) **per session close**; (c) daily | **(b)** `[DEFAULT-A5]` | 252 anchors/year, 2,520 over ten years — trivial to store and re-verify. It bounds any undetectable rewrite to **one session's events**, which aligns the blast radius with the unit the business already reasons about |
| **6** | What does a run-crash between the audit write and the side effect produce? | (a) retry the effect; (b) **UNKNOWN, reconcile against the broker using the intent's idempotency key** | **(b)** `[DEFAULT-A6]` | (a) double-sends. The window between effect and outcome-write **cannot be eliminated** — no protocol makes a broker call and a local commit atomic — but it can be made *recoverable*, which is what the intent row is for (§7) |
| **7** | Is every event reproducible, or only some? | (a) all; (b) **model- and decision-derived events only** | **(b)** `[DEFAULT-A7]` | A `ReproducibilityBundle` on every `CANDIDATE_SCREENED` row would multiply the dominant storage line (P0.3 §2.3: audit is 97% of compressed data) for events that are pure observations. Six event types carry it; §5 lists them |
| **8** | Are payloads redacted for PII? | (a) redact at write; (b) **structurally avoid PII**; (c) redact at export | **(b)** `[DEFAULT-A8]` | The system trades its owner's own capital with no client data (`[DEFAULT-3]` of P0.1), so the only personal data is the operator's own identity. Redaction at write destroys the record; redaction at export means the store still holds it. Avoiding it structurally means there is nothing to redact — see §8.2 |
| **9** | Export format for a regulator? | (a) CSV; (b) single JSON array; (c) **NDJSON, canonical form, one event per line** | **(c)** `[DEFAULT-A9]` | An export of 10M events must stream, not materialise, and a partial export must still parse. Canonical form means the recipient can **recompute the chain themselves** without trusting our verifier — which is the whole point of handing it over |
| **10** | Where does replay's re-derivation live? | (a) here; (b) **in the phase that owns the computation** | **(b)** `[DEFAULT-A10]` | P2.9 owns risk arithmetic, P2.5 owns scoring. P1.4 owns the harness, the diff and the verdict, because *those* must be identical regardless of which computation is being checked |

---

## 2. NON-BLOCKING details resolved

| # | Detail | Resolution |
|---|---|---|
| 1 | UUIDv7 monotonicity | 12 bits of `rand_a` are a within-millisecond counter (RFC 9562 §6.2), under a lock, so ids minted in the same millisecond still sort in creation order. On counter exhaustion the timestamp advances by 1 ms rather than colliding |
| 2 | Clock going backwards | `uuid7()` never emits a decreasing timestamp: it clamps to the last issued millisecond and increments the counter. NTP stepping the clock backwards must not produce ids that sort before existing ones |
| 3 | Empty `causation_id` in the hash | Serialised as `""`, never omitted. An omitted key changes the canonical string; a root event and a caused event must differ in the hash by content, not by key presence |
| 4 | Booleans in payloads | Permitted. Only *numbers* are banned — `true`/`false`/`null` canonicalise unambiguously |
| 5 | `seq` in the hash | As a **string** (`"41"`), like every other numeric. Consistency with rule 4 of §6.2 beats special-casing |
| 6 | Chain verification of an empty set | Vacuously intact. A slice that happens to be empty is not an incident |
| 7 | `deep=False` | A structural-only scan (sequence + linkage, no content re-hash) for a fast sweep. Documented as *not* catching content mutation, and a test asserts exactly that, so nobody mistakes the fast path for the real one |
| 8 | Duplicate `seq` | Its own break kind. A gap and a duplicate have different causes — a delete versus a double-insert — and collapsing them loses the diagnosis |
| 9 | Anchor absent from the live chain | Reported as a `GAP` at the anchored seq, not as a missing anchor. The anchor is the trusted side |
| 10 | Producer per event type | Exactly one. Two producers for one type means two code paths can disagree about what the event means |
| 11 | Event type removal | **Never permitted.** An event type in a six-year-old row must still resolve to exactly one meaning. Adding is an additive migration (P1.2 §11.2) |
| 12 | `input_hash` vs `payload_hash` | `input_hash` covers the **input that produced** the event; `payload_hash` covers the event itself. Two events with identical payloads produced by different inputs are different events, and only `input_hash` can tell you |

---

## 3. The event taxonomy

**42 event types**, each with exactly one producer, one trigger and one required payload key set.
By class: 14 `ACTION`, 10 `EVALUATION`, 8 `SYSTEM`, 3 `KILL_SWITCH`, 3 `APPROVAL`, 2 `NAV`,
2 `RISK`. **25 are effectful**; **6 require a reproducibility bundle**. 17 distinct producers.

The registry is executable (`EVENT_REGISTRY` in `src/audit/events.py`) and is the authority: an
envelope written with a class that disagrees with the registry **fails validation**, because
RULE-B4 keys write durability on that class.

| Group | Types | Producer | Class |
|---|---|---|---|
| **Lifecycle** | `RUN_STARTED`, `RUN_FINISHED`, `EFFECTIVE_CONFIG_RENDERED` | Orchestrator | SYSTEM |
| **Ingest** | `DATA_RECEIVED`, `DATA_REJECTED`, `FX_RATE_RECORDED`, `CORPORATE_ACTION_APPLIED`, `UNIVERSE_RECONSTITUTED` | P2.1 / P2.2 / P2.3 | EVALUATION / NAV / ACTION |
| **Analysis** | `CANDIDATE_SCREENED`, `SCORE_COMPUTED`, `REGIME_CLASSIFIED`, `GATE_OPENED`, `GATE_CLOSED` | P2.3 / P2.5 / P2.6 / P4.2 | EVALUATION |
| **LLM** | `LLM_CALLED`, `LLM_OUTPUT_ACCEPTED`, `LLM_OUTPUT_REJECTED` | P4.3 / P4.4 | EVALUATION |
| **Decision & risk** | `DECISION_MADE`, `RISK_EVALUATED`, `LIMIT_BREACHED` | P2.7 / P2.9 | ACTION / RISK |
| **Execution** | `ORDER_INTENT`, `ORDER_SENT`, `ORDER_ACKED`, `ORDER_REJECTED`, `ORDER_CANCELED`, `ORDER_STATE_UNKNOWN`, `FILL_RECEIVED` | P3.1 / P3.2 | ACTION |
| **Portfolio** | `POSITION_OPENED`, `POSITION_CLOSED`, `POSITION_UNRECONCILED`, `RECONCILIATION_COMPLETED`, `NAV_SNAPSHOT` | P3.3 | ACTION / NAV |
| **Control** | `KILL_SWITCH_ARMED`, `KILL_SWITCH_TRIPPED`, `KILL_SWITCH_RESET`, `CONFIG_CHANGED`, `MODEL_DEPLOYED`, `APPROVAL_REQUESTED`, `APPROVAL_GRANTED`, `APPROVAL_EXPIRED` | P2.10 / P6.6 | KILL_SWITCH / SYSTEM / APPROVAL |
| **Integrity** | `CHAIN_ANCHORED`, `CHAIN_VERIFIED`, `INTEGRITY_INCIDENT` | P6.1 | SYSTEM |

**Beyond the prompt's minimum list**, six types exist because Stage 0 and Stage 1 findings demand
them: `ORDER_STATE_UNKNOWN` (P1.1's fail-closed order state), `POSITION_UNRECONCILED` and
`RECONCILIATION_COMPLETED` (ADR-10 §2's pool-wide entry block), `EFFECTIVE_CONFIG_RENDERED`
(P1.3 §9), `APPROVAL_EXPIRED` (ADR-09's SLA defaults), and `CHAIN_ANCHORED` (§6.3).

### 3.1 Class promotion — RULE-B4(a)

An `EVALUATION` event that becomes the **reason** for an action is promoted to `ACTION` class and
therefore written durably *before* the decision citing it. A Tier-1 screen row for a name that gets
selected is **evidence**, not a scan result. `promote_to_action()` implements it.

---

## 4. The envelope

Every event carries, without exception:

| Field | Type | Purpose |
|---|---|---|
| `event_id` | **UUIDv7** | Time-ordered identity (§4.1) |
| `seq` | `int`, gapless | **The authoritative ordering.** Assigned by the database under an advisory lock (P1.2 §9.4) |
| `causation_id` | `UUID \| None` | The event that **directly** caused this one. `None` for a root |
| `run_id` | `UUID` | The correlation id — every event in one causal tree shares it |
| `event_type` / `event_class` | enums | Registry-validated |
| `schema_version` | `str` | Envelope shape. A reader six years out must know which shape it holds |
| `canonical_schema` | `str` | Which canonicalisation produced the hash (`jcs-nonum-1`) |
| `occurred_at` / `recorded_at` | UTC | What happened, and when we wrote it. The **gap between them is observability data** — a growing gap is a system falling behind |
| `actor` | `str` | Component or approver identity |
| `is_paper` / `is_backtest` | `bool` | Rule N11, mutually exclusive |
| `input_hash` | sha256 | Hash of the **full input** that produced the event |
| `payload` | mapping | Registry-validated required keys; **no JSON numbers** |
| `reproducibility` | bundle \| None | Required for six types (§5) |
| `prev_hash` / `payload_hash` | sha256 | The chain (§6) |

### 4.1 UUIDv7

`48b unix_ts_ms | 4b version(7) | 12b counter | 2b variant | 62b random`. Monotonic within a
millisecond and across threads; never emits a decreasing timestamp even if the wall clock steps
backwards. Verified over 4,000 concurrent mints across 8 threads: no collisions, and string sort
equals creation order.

**`seq` remains authoritative for ordering.** A UUIDv7 is time-ordered but **not gapless**, and
chain verification needs gapless. UUIDv7 gives locality; `seq` gives the proof.

---

## 5. Reproducibility

The test for whether a field belongs in the bundle is blunt: **if changing it changes the output,
and it is not captured, the decision is not reproducible.**

| Group | Fields | Why |
|---|---|---|
| **Code** | `code_version` (git SHA), `runtime` (interpreter, implementation, OS, arch), `library_versions` | A `Decimal` context or a locale differs between runtimes. "It reproduced on my machine" is not a reproduction |
| **Config** | `config_hash`, `policy_version` | P1.3 §5.4 binds one config hash per run; this is the pointer back |
| **Model** | `model_id`, `model_version`, `model_artifact_sha256` | Hash **of the artifact**, not of its name. Two artifacts can share a version string; they cannot share a digest |
| **Data** | `input_snapshot_refs`, `input_hash`, `market_asof`, `knowledge_asof` | **Not the data — a reference** the bitemporal as-of functions resolve (P1.2 §3.3), plus a hash of the exact rows returned. Both cutoffs, because one alone cannot make an as-of read reproducible |
| **Randomness** | `random_seeds` | An unseeded RNG makes a model output irreproducible, and "close enough" is not a defence to a regulator |
| **LLM** | `llm_prompt_hash`, `llm_response_hash`, `llm_sampling_parameters` | Temperature, top_p, seed, max_tokens, stop. All three travel together or none does — validated, because any one alone cannot reproduce the output |

**Six event types require it:** `SCORE_COMPUTED`, `REGIME_CLASSIFIED`, `LLM_CALLED`,
`LLM_OUTPUT_ACCEPTED`, `DECISION_MADE`, `RISK_EVALUATED`. An envelope of one of those types
without a bundle **fails validation**.

Storing references rather than data is what keeps this affordable: P0.3 §2.3 already has the audit
trail at 97% of compressed application data, and a data snapshot per event would multiply the
dominant line.

---

## 6. Tamper evidence

### 6.1 What is hashed, in what order

```
sha256( canonical_json({
    canonical_schema, schema_version, seq, prev_hash, event_id, causation_id,
    run_id, event_type, event_class, occurred_at, actor, is_paper, is_backtest,
    input_hash, payload
}) )
```

**The key set is pinned explicitly and nowhere else.** It is deliberately *not* the model's field
order — reordering a Pydantic model would then silently invalidate every historical hash — and not
alphabetical, because a field rename would do the same. Changing the set is a `schema_version`
bump. A test asserts the exact key set, and asserts that **`recorded_at` is absent** (`[DEFAULT-A2]`).

Chaining is *in the content*: `prev_hash` sits inside the preimage, so the digest function is plain.

### 6.2 Canonical serialisation — closes `Q-P1.2-1`

**`jcs-nonum-1`** — RFC 8785 (JCS) with one added restriction:

1. Object keys sorted by UTF-16 code unit.
2. No insignificant whitespace (`,` and `:` separators).
3. UTF-8 output, minimal escaping.
4. **No JSON numbers anywhere in a payload. Every numeric is a string.**
5. No duplicate keys; no `NaN`/`Infinity`.

Rule 4 is the one that earns its place. JCS's number canonicalisation is the only part of RFC 8785
genuinely hard to implement identically in two languages, and it is precisely where a float would
re-enter after P1.1 spent a whole section keeping floats out. Banning JSON numbers reduces
canonicalisation to key sorting plus whitespace — something two implementations cannot disagree
about — and makes P1.1's Decimal-as-string convention a **validated precondition** of the audit
log rather than a habit. `NonCanonicalPayloadError` is raised at construction, so a
non-canonicalisable payload means the event is not written and therefore (`[CONST-5]`) the action
does not happen.

**This supersedes P1.2 §9.4's interim `NEW.payload::text`.** P1.2 flagged that `jsonb`'s text
rendering is not guaranteed stable across major versions; under `jcs-nonum-1` the application
supplies the canonical string and the hash covers that, so a Postgres upgrade cannot invalidate
history.

### 6.3 Anchoring — and why the chain alone is not enough

A hash chain proves **internal consistency**. It does not stop someone with write access from
rewriting the whole tail: recompute every hash from the mutation forward and the result is a
perfectly consistent chain telling a different story. **§12 demonstrates exactly this passing
internal verification.**

An anchor closes it. Once seq *N*'s hash is published off-VM, every event at or below *N* is
frozen, because rewriting them changes a hash that already exists somewhere the rewriter does not
control.

- **Cadence:** one anchor per session close — 252/year, 2,520 over ten years.
- **Destination:** off-VM object storage, write-once, distinct credentials from the database
  (P6.2 owns the placement).
- **Blast radius:** an undetectable rewrite is bounded to **one session's events**.
- **Verification:** `verify_against_anchor()` — a live hash differing from the anchored one is an
  `ANCHOR_MISMATCH`, which is an integrity incident, not a discrepancy.

### 6.4 The verification procedure and its cost at 10M events

Three independent checks, all three necessary:

| # | Check | Catches |
|---|---|---|
| 1 | **Sequence** — `seq` increments by exactly one | A **deleted** row |
| 2 | **Linkage** — `prev_hash` equals the predecessor's `payload_hash` | An **inserted** or **reordered** row |
| 3 | **Content** — recompute each row's hash from its own content | A **mutated** row |

Check 3 is the one a naive implementation omits, and omitting it is the difference between an
attacker needing to rewrite *every* subsequent row and needing to rewrite *one*.

**Measured cost: 18,538 events/second deep verification → 10,000,000 events in ~9.0 minutes.**
Measured on this build (`benchmark_verification`, 8,000-event sample, projected linearly; the
walk is O(n) with constant memory per event). 10M events is roughly **2.6 years** of production at
P0.3's 15,000 events/session — so this is the cost of the routine annual audit, not a hypothetical.

Verifying a **slice** is first-class: ADR-10 §5 verifies "across the outage window", and
`expected_prev_hash` attaches the slice to the chain it came from.

### 6.5 What is claimed, and what is not

**Tamper-EVIDENT. Not tamper-proof.** Nothing inside a database survives a superuser, who can
`DROP TRIGGER`, disable a constraint, or edit the heap directly. P1.2 §9.6 says the same about its
grants and triggers. What this design guarantees is that **a mutation cannot go unnoticed** — by
the chain within a session, and by the anchor across sessions. Claiming more would be a claim a
regulator would test.

---

## 7. Write-before-act

### 7.1 The protocol

```
1. WRITE INTENT, durably (synchronous_commit = remote_write, P1.2 §10.3)
      └─ fails? → THE ACTION DOES NOT HAPPEN. Return. Do not retry blind.
2. PERFORM THE EFFECT, carrying the intent's idempotency key
3. WRITE OUTCOME
```

**The dangerous window is between 2 and 3, and it cannot be eliminated** — no protocol makes a
broker call and a local commit atomic. What it can be is *recoverable*, which is why step 1 exists
and why the key travels into step 2.

| Crash point | State | Recovery |
|---|---|---|
| Before 1 | Nothing happened | Nothing to do |
| Between 1 and 2 | Intent with no effect | **Benign.** The reconciler finds no matching broker order → `ABANDONED` |
| Between 2 and 3 | Effect landed, unrecorded | **The dangerous one.** The world moved and our record did not → ask the broker with the same key |
| After 3 | Complete | Nothing to do |

### 7.2 Idempotent recovery on restart

For every intent with no recorded outcome, ask the broker using the **same idempotency key**
(rule N12's client-side dedupe). Three answers, three actions:

| Broker says | Action |
|---|---|
| Has it (filled or open) | **RECORD_OUTCOME.** Do not re-send |
| Does not have it | **ABANDONED.** The effect never landed |
| Cannot say / unreachable | **UNRECONCILED.** Denies new entries pool-wide until a human resolves it (ADR-10 §2) |

**Idempotent by construction:** running recovery twice produces the same result, because it only
ever records what the broker already believes. Verified by test.

---

## 8. Retention, PII, export, search

### 8.1 Retention

**`audit_log` has no retention policy. Ever.** `audit.retention_years = indefinite` (P0.1 §10.2);
invariant I4 replays risk counters from it; ADR-10 §5 makes a gap a hard stop. P1.2 §5.4 encodes
the absence, and its migration comments mark adding one as a spec violation rather than a tuning
decision.

Ten years of audit is ~9.45 GB compressed (P0.3 §2.2) against a 250 GB volume. **Retention is not
a cost problem here**, and treating it as one is how an audit trail acquires a hole.

### 8.2 PII — structurally avoided rather than redacted

The system trades **its owner's own capital**, with no client data (`[DEFAULT-3]` of P0.1). The
only personal data in scope is the operator's own identity in `actor` and `approver`.

- **No natural-person data enters a payload.** Approver identity is a stable pseudonymous operator
  id, not a name or an email.
- **No vendor content is stored raw.** `NewsItem` exposes only `body_sanitised` (rule N14), and the
  raw body is not reachable from the domain model at all.
- **No secrets.** P1.3 §8's Vault references are what appear in the config dump; values never are.

Redaction-at-write destroys the record; redaction-at-export means the store still holds it.
Having nothing to redact is the only option that survives both a regulator and a breach.
**If the ownership model ever changes** — friends-and-family or client money — this section is
void and rule N15's licensing review fires alongside it. That is an ADR-09 row 12 change, not a
configuration one.

### 8.3 Regulator export

**NDJSON, one canonical event per line, in `seq` order**, each carrying `prev_hash` and
`payload_hash`. Streams rather than materialises; a partial export still parses; and because each
line is the canonical form, **the recipient can recompute the chain themselves without trusting
our verifier** — which is the entire point of handing it over. A test re-chains an export from
scratch and asserts it links.

`include_payload=False` produces a metadata-only manifest for scoping discussions before payloads
are handed over.

### 8.4 Search

Served by P1.2's schema, not by scanning the log:

| Question | Path |
|---|---|
| What happened in this run? | `audit_log_run_idx (run_id, occurred_at)` |
| What caused this? | Walk `causation_id` — a test walks a 6-deep chain to its root |
| Replay the drawdown counter | `audit_log_counter_idx`, partial on `event_class IN ('NAV','RISK','KILL_SWITCH')` — ~2% of rows, and the only classes invariant I4 replays |
| Verify a window | `PRIMARY KEY (seq, occurred_at)` range scan |
| Everything about an instrument | `payload` is `jsonb`; a GIN index is added when a named query needs it, not before (P1.2 §7) |

---

## 9. The replay tool

```
replay_run(events, run_id, re_derive) -> ReplayResult
```

For every reproducible event in a run, re-derive it from its bundle and diff field by field
against what was recorded. `re_derive` is supplied by the phase that owns the computation
`[DEFAULT-A10]`; P1.4 owns the harness, the diff and the verdict.

**Two failure modes, reported separately, because they mean different things:**

| Result | Meaning |
|---|---|
| `diffs` non-empty | **Non-determinism.** The same inputs produced a different output — a bug in the model, the code, or an uncaptured seed |
| `missing_reproducibility` non-empty | **A gap in what we captured.** The event cannot be re-derived at all |

Collapsing them would let a capture gap read as a clean replay, which is the worse of the two
errors to make.

---

## 10. Error paths

| Condition | Behaviour |
|---|---|
| Payload contains a JSON number | `NonCanonicalPayloadError` → event not written → **action does not happen** |
| Event class disagrees with the registry | Validation error → not written. RULE-B4 keys durability on the class |
| Required payload key missing | Validation error → not written |
| Reproducible event without a bundle | Validation error → not written |
| Naive timestamp | Validation error → not written |
| `is_paper` and `is_backtest` both true | Validation error → not written (rule N11) |
| `seq > 0` with the genesis hash, or `seq == 0` without it | Validation error → not written |
| Event causes itself | Validation error → not written |
| Chain gap / fork / content mutation / duplicate seq | `ChainError` → **HARD STOP.** No trading resumes (ADR-10 §5) |
| Anchor mismatch | `ANCHOR_MISMATCH` → integrity incident → hard stop |
| Audit write fails before an effect | The action does not happen (`[CONST-5]`) |
| Crash between effect and outcome | `UNKNOWN_NEEDS_RECONCILE` → §7.2 recovery |
| Broker unreachable during recovery | `UNRECONCILED` → pool-wide entry block |

---

## 11. Verification

`tests/verify_p14_audit.py` — **36/36 PASS**.

### 11.1 The required self-check

> *"one runnable self-check proving that a mutated row fails verification"*

`t_AAA_mutated_row_fails_verification` builds a valid 12-event chain, verifies it, then applies
**three** mutation shapes — because they are caught by three different checks, and a verifier
implementing only one looks fine until the day it matters:

```
mutated    -> CONTENT_MUTATED at seq 5: stored payload_hash 8c744e033aa9... != recomputed ffb2e63e31b4...
re-hashed  -> FORK at seq 6: prev_hash 8c744e033aa9... does not match the preceding payload_hash ffb2e63e31b4...
deleted    -> GAP at seq 8: expected seq 7, found 8
```

`t_AAB_full_tail_rewrite_is_caught_only_by_the_anchor` then demonstrates the attack the chain
alone **cannot** catch: rewrite seq 4 and re-chain 5–9, and internal verification passes cleanly.
The anchor catches it. That test exists to stop a later reader concluding the chain is sufficient.

### 11.2 Coverage

| Group | Proves |
|---|---|
| UUIDv7 | Version 7; 2,000 ids sort in creation order; 4,000 concurrent mints across 8 threads collide zero times; timestamp recoverable |
| Canonicalisation | Key-order independent; **rejects every JSON-number shape** including `Decimal` and nested; UTF-8 stable |
| Taxonomy | All 23 of the prompt's required types present; all 42 have a complete spec; effectful set matches `[CONST-5]`'s scope; wrong class rejected; missing payload key rejected; missing bundle rejected |
| Envelope | Naive timestamp, paper-XOR-backtest, genesis rules, self-causation all rejected; **preimage key set pinned and `recorded_at` proven absent**; causation chain walkable 6 deep |
| Verification | Slice verification with `expected_prev_hash`; duplicate seq; `deep=False` documented limitation asserted; empty chain vacuous |
| **Cost** | **18,538 events/s → 10M in 9.0 min** |
| Write-before-act | Audit failure ⇒ **no side effect**; death between effect and outcome ⇒ reconcilable; recovery idempotent across all three broker answers |
| Replay | Identical run ⇒ no diff; non-determinism detected; missing bundle reported **separately**; LLM bundle fields must travel together |
| Export | NDJSON in seq order; **re-chained from scratch by the test**, proving independent verifiability |

---

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | **No JSON numbers in an audit payload** | Removes JCS's only hard part and the last route back to float money. Canonicalisation becomes key-sorting, which two implementations cannot disagree about | No — it is the hash contract | **Critical** — a canonicalisation two systems disagree about invalidates every hash |
| 2 | **`recorded_at` is not hashed** | It is when we wrote it down, not what happened; hashing it makes replay impossible | No | High |
| 3 | **The preimage key set is pinned explicitly** | Not model field order (a reorder would invalidate history), not alphabetical (a rename would) | No | **Critical** |
| 4 | **Anchoring is required; the chain alone is insufficient** | A full-tail rewrite passes internal verification — demonstrated, not asserted | No | **Critical** |
| 5 | **One anchor per session close** | Bounds an undetectable rewrite to one session; 2,520 anchors over ten years | Yes | Medium |
| 6 | **UUIDv7, superseding P1.1 §2 row 10** | P1.1's own rule says implement ten lines of stdlib rather than take a dependency. A randomly-sorting id makes every audit range scan a full scan | Yes | Medium |
| 7 | **One envelope, superseding P1.1 `[DEFAULT-9]`** | The envelope/catalogue split produced two models of one concept, free to drift | Yes | High |
| 8 | **Six event types carry a reproducibility bundle, not all 42** | Audit is already 97% of compressed data (P0.3 §2.3); a bundle on every screen row multiplies the dominant line | Yes | Medium |
| 9 | **Bundle stores data REFERENCES plus a hash, not data** | Storage, and the as-of functions already make the reference resolvable and reproducible | Yes | High — storing data would break P0.3's disk model |
| 10 | **Three verification checks; content re-hash is not optional** | Without it an attacker rewrites one row instead of all subsequent rows | No | **Critical** |
| 11 | **Write-before-act cannot close the 2→3 window; it makes it recoverable** | No protocol makes a broker call and a local commit atomic. Saying otherwise would be false comfort | No | **Critical** |
| 12 | **Recovery asks the broker; it never re-sends** | Re-sending on an unknown outcome is how one order becomes two | No | **Critical** |
| 13 | **PII structurally avoided, not redacted** | Redaction-at-write destroys the record; redaction-at-export leaves it in the store | Yes — void if the ownership model changes | High |
| 14 | **NDJSON canonical export** | Streams; partially parseable; recipient can verify without trusting us | Yes | Low |
| 15 | **Replay reports non-determinism and capture gaps separately** | Collapsing them lets a capture gap read as a clean replay | Yes | Medium |
| 16 | **Event types are never removed** | A type in a six-year-old row must resolve to one meaning forever | No | High |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|---|---|---|---|
| 1 | 18,538 events/s holds at 10M rows | Measured on an 8,000-event in-memory sample; the walk is O(n) with constant memory | Re-benchmark against 10M rows loaded from TimescaleDB during P6.4 | The real cost adds I/O — the projection covers CPU only. If disk-bound, verification becomes a streaming job rather than a batch one. **Recorded as Q-P1.4-3** |
| 2 | `[DEFAULT-A8]` No natural-person data enters the log | `[DEFAULT-3]` of P0.1 fixes the ownership model at owner-only capital | Review at P6.3 | If the ownership model changes, §8.2 is void, GDPR/DPDP erasure conflicts head-on with an immutable log, and that conflict is an ADR-09 row 12 amendment |
| 3 | Off-VM anchor storage is write-once with distinct credentials | `[CONST]` mandates Vault; P6.2 owns placement | P6.2/P6.4 | An anchor store the database's credentials can rewrite provides **no** additional guarantee — it would be security theatre, and worse than none because it would be believed |
| 4 | One anchor per session bounds the blast radius acceptably | No regulatory requirement names a cadence | Q-P1.4-2 — check whether SEBI or SEC name one | A required cadence tightens the parameter; the mechanism is unchanged |
| 5 | ~1 KB mean event, 15,000/session | P0.3 §2.1/§9.4, that document's most load-bearing assumption | Measurement-by-design **Q15**, via `cagg_audit_events_daily` after 20 live sessions | P0.3 §9.4 stress-tests to 10×; at 150,000/session the 250 GB volume needs resizing |

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|---|---|---|---|
| **Q-P1.4-1** | Where are anchors published, and with what credentials? | P6.2 | An object store with object-lock / write-once semantics and credentials distinct from the database role | **P6.2/P6.4 go-live.** Until then the chain is session-internal only |
| **Q-P1.4-2** | Do SEBI or SEC name a required audit retention, format or anchoring cadence? | Regulatory review | SEBI circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013 on record retention; SEC 17a-4 on WORM storage | **P6.3.** Our indefinite retention is likely to exceed any minimum; the **format** may not match. Folds into carried item `Q10` |
| **Q-P1.4-3** | Does deep verification hold ~18.5k events/s when reading from TimescaleDB rather than memory? | Measurement in P6.4 | Verify 10M rows from a compressed hypertable; compare against the in-memory projection | P6.4's operational runbook. If I/O-bound, verification becomes streaming |
| **Q-P1.4-4** | Should P1.2's `audit_log` gain a `canonical_schema` column? | P1.2's own X2 | The envelope carries it; the table does not. A future `jcs-nonum-2` would need per-row disambiguation to verify old rows | **P1.2 X2.** Additive column, cheap now (P1.2 §11.2 rule 1), expensive after the table has rows |
| **Q15** *(carried)* | Audit event rate and row width | Measurement, 20 live sessions | `cagg_audit_events_daily` | Feeds P0.3 §9.4 and the T4 re-open trigger |
| **Q10** *(carried)* | Record-retention minima | Regulatory review | As Q-P1.4-2 | P6.3 |

## CONTRACTS EXPORTED

| Name | Kind | Signature or schema | Consumers |
|---|---|---|---|
| `AuditEnvelope` | model | §4's fields; `hash_preimage()`, `compute_hash()`, `verify_self()` | **Every effectful phase** |
| `EventType` | enum | 42 members, never removed | every phase |
| `EVENT_REGISTRY` | mapping | `EventType -> EventSpec(class, producer, trigger, required keys, effectful, repro)` | every producer phase |
| `EFFECTFUL_EVENT_TYPES` | frozenset | 25 types `[CONST-5]`'s protocol governs | P3.2, P2.10 |
| `REPRODUCIBLE_EVENT_TYPES` | frozenset | 6 types requiring a bundle | P2.5, P2.9, P4.3 |
| `Producer` | enum | 17 components; one per event type | every phase |
| `ReproducibilityBundle` | model | §5's fields; `capture_runtime()` | P2.5, P2.6, P2.7, P2.9, P4.3 |
| `uuid7()` / `uuid7_timestamp_ms()` | functions | RFC 9562 §5.7, monotonic, thread-safe | P1.2 writer, every producer |
| `canonical_json()` / `canonical_bytes()` | functions | `jcs-nonum-1`; raises on a JSON number | **P1.2's hash trigger**, P6.3 |
| `CANONICAL_SCHEMA_VERSION` | constant | `"jcs-nonum-1"` | P1.2, P6.3 |
| `verify_chain()` | function | `(events, require_genesis, expected_prev_hash, deep) -> VerificationResult` | P6.1, P6.4, boot sequence |
| `assert_chain_intact()` | function | Raises `ChainError` — ADR-10 §5's hard stop | boot sequence, P6.4 |
| `BreakKind` / `ChainBreak` | enum + record | 6 break kinds, each with its diagnosis | P6.1 |
| `Anchor` / `verify_against_anchor()` | model + function | §6.3 | P6.1, P6.2 |
| `benchmark_verification()` | function | `(make_events, n) -> (events_per_second, seconds_at_10M)` | P6.4 runbook |
| `write_before_act()` | function | `[CONST-5]`'s exact ordering; returns `ActOutcome` | **P3.2**, P2.10 |
| `recover_incomplete_intents()` | function | Idempotent restart recovery (§7.2) | **P3.2**, P6.4 |
| `IntentRecord` | record | The pre-effect row carrying the idempotency key (rule N12) | P3.2 |
| `replay_run()` | function | `(events, run_id, re_derive) -> ReplayResult` | **P5.1**, P6.6 |
| `export_for_regulator()` | function | NDJSON iterator, canonical, seq-ordered | **P6.3** |
| `promote_to_action()` | function | RULE-B4(a) class promotion | P1.2 writer, P2.3 |

---

**END OF SPEC-P1.4-AUDIT v0.1**
