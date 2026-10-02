# X3 — MERGE, Stage 1 re-run — full report

| | |
|---|---|
| Template | `docs/PROMPT-PACK.md`, "X3 — Merge", all seven DO steps |
| Run on | 2026-10-02, in its own conversation |
| Commit | `b8b1340c3bd66c5b4983b1397f510f02fc30c27d`, branch `main`, working tree clean |
| Required by | `STAGE-1-FREEZE.md` §11.6 step 4 |
| Form | **Full re-merge**, not a delta. Reason at §0.2 |
| Repository changes | **None.** Nothing edited, staged, committed or pushed |
| Not opened | `AI-Trading-Agent-stage1-review-drafts` — not opened, not listed, not read |

> **Publication note, 2026-10-02.** This is the report as produced by the read-only re-run, published
> on the Owner's instruction. Three things were changed for publication and nothing else: this
> note; file references turned into links; and the `REPO` path line in the two evidence scripts,
> which now locates the repository from the script's own position instead of a local path. The two
> `.proposed.diff` files are kept as the reviewed artifacts. They were applied to
> `STAGE-1-FREEZE.md` and `STAGE-1-MERGE-CHANGES.md` in the commit that published this folder, so
> they no longer apply to the current tree. "Repository changes: None" below describes the re-run
> itself.

**Reading this report.** Every finding has an id. `X3R-M` is a producer/consumer contract
mismatch (step 2). `X3R-C` is a contradiction (step 3). `X3R-G` is a coverage gap (step 6).
`X3R-E` is an error in the existing 2026-08-31 record. `X3R-Q` is a new open question. I use a
new prefix because the record already has two colliding "N-" series and an "R-" series.

---

## 0. Summary

### 0.1 The result in one paragraph

The counts in the 2026-08-31 record reproduce: 118 contracts, 32 assumptions. Open questions are
now 32 rows and 30 unique ids, because `Q-P1.2-7` was added. But the record's two central
conclusions do not reproduce. It says no contract name is exported by two specs, and that there is
no producer/consumer signature mismatch. Both are wrong. I found one duplicate contract name with
two different behaviours, and two mismatches that stop one spec's output being accepted by
another spec's code. Both mismatches already existed at `605ff40`; the SPEC-P1.2 re-open did not
cause them. The re-open itself is consistent: the specification's DDL for the two changed
functions is identical to the migration, line for line.

### 0.2 Why a full re-merge and not a delta

A delta is only safe if the baseline is right. I checked the baseline first and it was not:

- its contracts table has a wrong Consumers cell in 7 of 118 rows (X3R-E3);
- its "no duplicate names" claim is false (X3R-E1);
- its "no signature mismatches" claim rests on a test that checks column names in one direction
  only (X3R-E2).

None of those is in the part of the stage that changed. A delta would have carried them forward.
So every count, table and comparison below was rebuilt from the four specs, the code and the git
history.

### 0.3 The findings that matter most

| Id | Severity | Finding | Existed at `605ff40`? |
|---|---|---|---|
| **X3R-M1** | HIGH | The audit envelope (P1.4) and the audit table (P1.2) compute two different hashes for one event, the database overwrites the application's hash, and 5 envelope fields have no column | Yes |
| **X3R-M2** | HIGH | `EffectiveConfig.audit_payload()` (P1.3) is rejected by `AuditEnvelope` (P1.4). It carries 132 JSON numbers, 28 of them floats; P1.4 bans all JSON numbers | Yes |
| **X3R-M3** | MEDIUM | `canonical_bytes` is exported by both P1.3 and P1.4 with different behaviour | Yes |
| **X3R-C5** | MEDIUM | India price floor: the research summary says ₹100, `policy.yaml` says ₹50.00, and P1.3 says the research summary gives no figure | Yes |
| **X3R-G1** | MEDIUM | Earnings blackout, a named risk control in the research summary, appears in no Stage 0 or Stage 1 spec and in no policy rule | Yes |
| **X3R-C14** | MEDIUM | SPEC-P1.2 carries `status: FROZEN` and, in the same header, "NOT re-frozen" | No — arises from the re-open |

### 0.4 What this changes for the Stage 2 gate

The record says no open question blocks P2.1. That no longer holds as written. `EVENT_REGISTRY`
names P2.1 as the producer of three audit event types, and the pack's appendix says "P1.4 (audit)
before anything that emits events". With X3R-M1 open there is no agreed way to persist an audit
event. The record's gate also omits `A-14`, which `STAGE-0-FREEZE` §10 makes a precondition of
P2.9.

### 0.5 What I did not verify

| Item | State |
|---|---|
| Any database behaviour: that the migration executes, object counts, the 36-check runtime suite, the two other shell suites | **NOT VERIFIED.** I started no container and did not touch `ai-trading-tsdb`. I rely on nothing from §11.12 for a finding; where I cite it, I say so |
| Whether P1.3 and P1.4 ever received an X2 review (record question F-2) | **NOT VERIFIED.** No X2 record for either exists in the repository |
| Whether a Stage 0 spec decided the 5-second staleness figure away (X3R-C6) | **NOT VERIFIED.** A text search found no such decision |
| What bytes the policy signature covers when thresholds are YAML floats | Read from `loader.py:489–513` and `:742`; **not executed as a test** |
| N-6, N-7, N-8 of the second X2 | The record does not say what they are, so I cannot say whether any finding here repeats one |

---

## 1. Step 1 — merge into one coherent document

### 1.1 Form

The 2026-08-31 merge indexed the four specs instead of concatenating them, and recorded that as a
deviation from X3's wording. I keep that form and the deviation stands. A fifth hand-kept copy of
4,591 lines would drift from the specs; X3R-M7 below is an example of exactly that drift between
SPEC-P1.2 and its own migration.

Spec ids and version headers are preserved as they stand at `b8b1340`.

### 1.2 The artifacts at `b8b1340`

SHA-256, first 16 hex characters, over the **git blob** (`git show b8b1340:<path> | sha256sum`),
so they reproduce on any platform.

| Artifact | Version | SHA-256 (16), git blob | Lines | Changed since `605ff40`? |
|---|---|---|---|---|
| `docs/specs/SPEC-P1.1-DOMAIN.md` | 0.3 | `c8c086c84fb19a24` | 1,210 | no |
| `docs/specs/SPEC-P1.2-STORAGE.md` | **0.5** | `e3e754eca1df1ef8` | 2,397 | **yes** |
| `docs/specs/SPEC-P1.3-CONFIG.md` | 0.1 | `5c8e9188df7e9429` | 485 | no |
| `docs/specs/SPEC-P1.4-AUDIT.md` | 0.1 | `63aec1bd1fe03a3a` | 499 | no |
| `src/domain/models.py` | P1.1 v0.3 | `f3b510059c447f85` | 2,896 | no |
| `migrations/0001_initial.sql` | P1.2 v0.5 | `42ca24cf63cc847b` | 1,599 | **yes** |
| `src/config/loader.py` | P1.3 v0.1 | `047fa57dbcdde5af` | 1,077 | no |
| `config/policy.yaml` | P1.3 v0.1 | `751385d1765bd60a` | 1,253 | no |
| `src/audit/events.py` | P1.4 v0.1 | `64313743c4480ca6` | 719 | no |
| `src/audit/chain.py` | P1.4 v0.1 | `8298a736650d8971` | 481 | no |

Four specs total 4,591 lines (the record says 4,440).

**X3R-E9 — the record's §2 hash table does not describe the frozen files.** Five of its ten
hashes differ from the blobs above although the file is unchanged since `605ff40`. For
`loader.py`, `policy.yaml` and `events.py` the record's value equals the hash of my working-tree
file, which has Windows line endings (this is the record's own X2-4/e). For SPEC-P1.1 the record's
`91cef3bff594bec4` matches neither the blob nor the working tree: the hashes were taken at
`8b24083`, before the merge itself edited the four spec headers (MERGE-CHANGES R-1, R-2).

### 1.3 What changed between `605ff40` and `b8b1340`

`git diff --stat 605ff40..b8b1340`: 10 files, 2,663 insertions, 240 deletions. Four commits:
`09f204c`, `c8225ed`, `c9f30e3`, `b8b1340`.

| File | Kind of change |
|---|---|
| `SPEC-P1.2-STORAGE.md` | v0.1 → v0.5. §9.3 comment, §9.4 and §9.5 DDL, §6.11 and §13 row 14, DECISIONS row 10, new `Q-P1.2-7`, header |
| `migrations/0001_initial.sql` | The same DDL changes |
| `STAGE-1-FREEZE.md` | §11 and §12 added |
| `STAGE-1-GAP-AUDIT.md` | New file (X5 of 2026-08-31) |
| `tests/verify_p12_runtime_behaviours.sh`, `tests/verify_p11_x5_conditions.py` | New files |
| Four Python harnesses | Moved off bare `assert` |

**The other three specs and all four Python modules are byte-identical to `605ff40`.**

### 1.4 Is the re-opened spec consistent with its code?

I extracted every ```` ```sql ```` block from SPEC-P1.2 in the assembly order §6 declares and
compared it, section by section, with `migrations/0001_initial.sql`.

| Section | Spec lines | Migration lines | Differing lines |
|---|---|---|---|
| §6.0–§6.9, §9.1, §7, §8.2–§8.4, §9.2, §9.3 | equal | equal | **0** |
| **§9.5** `verify_audit_chain()` — changed by the re-open | 76 | 76 | **0** |
| **§9.4** `audit_chain_assign()` — changed by the re-open | 105 | 124 | 19 |
| **§6.10** policies, aggregates, as-of functions, grants | 244 | 275 | 37 |

The §9.4 difference is the `READ COMMITTED` guard (X2 finding H-1). The migration has it; the
spec does not. The record already carries this as N-2. It existed at `605ff40`.

The §6.10 difference is `cagg_audit_events_daily`. The spec computes
`pg_column_size(payload)`; the migration computes `octet_length(payload::text)` (X2 finding B-4).
It also existed at `605ff40`. I could not find it itemised in the record. See X3R-M7.

**So the v0.1 → v0.5 changes themselves are carried identically in spec and migration.** The two
differences that exist are older, and both are in the direction "migration fixed, spec not".

---

## 2. Step 2 — consolidated contracts

### 2.1 Count

Generated from the four `## CONTRACTS EXPORTED` tables. The full table is in
[`evidence/consolidated-tables.generated.md`](evidence/consolidated-tables.generated.md).

| Spec | Rows |
|---|---|
| SPEC-P1.1-DOMAIN | 44 |
| SPEC-P1.2-STORAGE | 33 |
| SPEC-P1.3-CONFIG | 20 |
| SPEC-P1.4-AUDIT | 21 |
| **Total** | **118** |

The record's 118 is correct. The re-open added and removed no contract row. It changed the
behaviour behind two of them:

| Row | Contract | What changed v0.1 → v0.5 | Declared shape |
|---|---|---|---|
| 69 | `trading.audit_log` | `payload_hash` now covers 11 columns, not 8. Every hash under the old preimage is invalid | Row text unchanged. It still says "`ENABLE ALWAYS` triggers", which Finding A showed do not protect a hypertable |
| 70 | `trading.verify_audit_chain(bigint)` | Now also reports `content mutated` and `duplicate seq`. Pins `TimeZone` and `DateStyle` | `RETURNS TABLE (broken_at bigint, reason text)` — unchanged |

### 2.2 Mismatches between producer and consumer

#### X3R-M1 — HIGH — the audit envelope and the audit table disagree

**Producer:** SPEC-P1.4 — `AuditEnvelope`, `canonical_json()`, `verify_chain()`.
**Consumer and co-producer:** SPEC-P1.2 — `trading.audit_log`, `audit_chain_assign()`,
`verify_audit_chain()`.

| | SPEC-P1.4 and `src/audit/events.py` | SPEC-P1.2 and `migrations/0001_initial.sql` |
|---|---|---|
| What is hashed | 15 keys, as one canonical-JSON object (`hash_preimage()`, `events.py`) | 11 columns, concatenated as text (§9.4, migration line 1512) |
| Payload rendering | The application's `jcs-nonum-1` string | `payload::text`, PostgreSQL's `jsonb` rendering |
| Time rendering | `occurred_at.isoformat()` | `occurred_at::text` under pinned GUCs |
| Who sets `payload_hash` | The application | The trigger, which overwrites `NEW.payload_hash` on insert |
| Fields | 18 | 13 columns |

Five envelope fields have no column: `canonical_schema`, `schema_version`, `causation_id`,
`input_hash`, `reproducibility` (measured: model fields minus column names). `Q-P1.2-7` lists
the first four. **The fifth, `reproducibility`, is not in `Q-P1.2-7`.** P1.4 §5 makes that bundle
mandatory for six event types, and no spec says where it is stored.

Three statements in the specs are untrue as a result:

- SPEC-P1.4 CONTRACTS, `canonical_json()` / `canonical_bytes()`: consumer is "**P1.2's hash
  trigger**". The trigger does not call it and cannot.
- SPEC-P1.4 §6.2: "This supersedes P1.2 §9.4's interim `NEW.payload::text`." §9.4 at v0.5 still
  hashes `NEW.payload::text`.
- SPEC-P1.2 OPEN QUESTIONS, `Q-P1.2-1`: "**Closed** … the application supplies the canonical
  string and the hash covers that, so `jsonb`'s text rendering never enters." It does enter.

Consequence: a row written through the trigger and read back into `verify_chain()` would fail
P1.4's content check on every row, because the stored hash is the database's. Not executed — no
writer exists — but it follows directly from the two definitions.

**Recommended resolution.** One decision, by the Owner, on `Q-P1.2-7`, widened to include
`reproducibility`: either the table gains the missing columns and the trigger hashes the
application's canonical string, or the database preimage is declared the hash of record and P1.4
§6.1 and `hash_preimage()` are changed to match. Until then, treat it as blocking the first
writer of `audit_log`. Not designed here.

#### X3R-M2 — HIGH — the config dump cannot be written to the audit log

**Producer:** SPEC-P1.3 — `EffectiveConfig.audit_payload()`, consumers "P1.4, P6.1". §9 says it
"is written to the audit log as an `event_class = SYSTEM` event".
**Consumer:** SPEC-P1.4 — `AuditEnvelope`, event type `EFFECTIVE_CONFIG_RENDERED`. §6.2 rule 4:
"No JSON numbers anywhere in a payload."

Run in an isolated copy of `b8b1340`, Python 3.11.9, pydantic 2.13.5:

```
ENVELOPE REJECTED the P1.3 payload as produced: NonCanonicalPayloadError
   payload[EFFECTIVE_CONFIG_RENDERED].rule_count is a JSON number (47). ...
JSON-number leaves in audit_payload(): 132
float leaves 28      e.g. $.effective_config.rules[0].threshold 0.05
int leaves 104       e.g. $.rule_count 47
Decimal leaves: 0
```

The registry requires the keys `rule_count` and `enforced_rule_count`, and P1.3 produces both as
`int`. So the event the registry defines cannot be built from the payload the producer returns.
P1.4 §10 says what follows: "event not written".

The 28 floats are a second problem inside the same finding. `policy.yaml` writes thresholds as
unquoted YAML, for example `threshold: 0.050` on `EXP-001`. YAML reads that as a float. P1.3 §2
row 4 requires quoting for "money and price thresholds" only, so fractions fall outside its own
rule, while P1.1 and P1.4 both exclude floats outright. The loaded rule threshold is
`Decimal('0.05')`, not `0.050`.

**Recommended resolution.** The Owner chooses the side: `audit_payload()` renders every numeric
as a string, or P1.4 exempts this event. The first is consistent with P1.4 DECISIONS row 1, which
is marked not reversible. Either way one FROZEN spec changes, which is a re-open under
`STAGE-0-FREEZE` §7 T5 and needs its own X2. Separately decide whether fraction thresholds in
`policy.yaml` must be quoted.

#### X3R-M3 — MEDIUM — one contract name, two specs, two behaviours

`canonical_bytes` is row 89 (P1.3, consumers "P1.4, P6.4") and row 106 (P1.4, consumers "P1.2's
hash trigger, P6.3").

```
P1.3: canonical_bytes({"b":1,"a":Decimal("0.050"),"c":True}) -> b'{"a":"0.050","b":1,"c":true}'
P1.4: canonical_bytes({"b":1,"a":"0.050","c":True})          -> raises NonCanonicalPayloadError
```

For an all-string input both return the same bytes. P1.3's accepts JSON numbers; P1.4's refuses
them. P1.3 names P1.4 as a consumer of its version.

**Recommended resolution.** Rename one. `policy_canonical_bytes` for P1.3's is the smaller
change, because P1.4's name is fixed by its hash contract.

#### X3R-M4 — MEDIUM — `AuditEvent` is exported but does not exist

Row 41: SPEC-P1.1 exports `AuditEvent`, kind "model", consumers "P1.4, every effectful phase".
`src/domain/models.py` has no such class; line 2776 says it was "SUPERSEDED". SPEC-P1.1's own
version note and SPEC-P1.4 §0 say the same. But SPEC-P1.1's `produces:` header still lists
`model.AuditEvent`, its §10.3 still says "P1.1 owns the chained envelope", and its CONTRACTS row
is unchanged. So two specs export one concept under two names with different field sets
(12 fields in P1.1 §10.3, 18 in `AuditEnvelope`).

**Recommended resolution.** Remove row 41 and the header entry from SPEC-P1.1 and mark §10.3
superseded in full. Documentary; no decision changes.

#### X3R-M5 — LOW — the as-of functions do not all take two cutoffs

Row 75 and SPEC-P1.2 §3.3 item 4: each function "takes **both** cutoffs". From the migration:

| Function | Arguments | Market cutoff | Knowledge cutoff |
|---|---|---|---|
| `fundamentals_asof` | `uuid, timestamptz, timestamptz` | yes | yes |
| `news_asof` | `uuid, timestamptz, timestamptz` | yes | yes |
| `symbol_asof` | `text, text, date, timestamptz` | a date | yes |
| `instrument_asof` | `uuid, timestamptz` | **no** | yes |
| `universe_asof` | `text, date` | a date | **no** |
| `bars_asof` | `uuid, timestamptz, timestamptz` | yes | **no** |

`bars_asof` exists, is `SECURITY DEFINER`, and is granted to `backtest_ro`. It is in neither the
CONTRACTS table nor the `produces:` header.

**Recommended resolution.** Correct the row and §3.3 to say what each function takes, and add
`bars_asof`. Whether `universe_asof` and `bars_asof` need a knowledge cutoff is a P5.1 question.

#### X3R-M6 — LOW — contract rows that differ from the code they describe

| Row | Contract | The row says | The code says |
|---|---|---|---|
| 11 | `Instrument` | a `tick_source` field | no such field (16 fields, none of that name) |
| 16 | `TradingCalendar` | `session(exchange, date)` | `session(self, trading_date)`; the calendar is per exchange |
| 44 | `DomainError` hierarchy | "28 named exceptions" | 29 subclasses; §12 lists 29 |
| 103 | `Producer` | "17 components" | 19 enum members; 17 used. `P2.8_SIZER` and `P3.4_EXIT` produce nothing |
| 113 | `write_before_act()` | "returns `ActOutcome`" | returns `tuple[ActOutcome, Any]` |
| 86 | `PolicyVerdict` | six named members | also a `passes: int` field |

#### X3R-M7 — LOW — SPEC-P1.2's DDL is not the migration, in two places

See §1.4. `cagg_audit_events_daily` and the H-1 guard. A reader implementing from the frozen spec
would rebuild two defects the migration has already fixed.

**Recommended resolution.** Back-port both to the spec as documentary corrections at the next
SPEC-P1.2 amendment.

### 2.3 What I checked and found clean

- **Every enum that has a `CHECK` list I could match to it.** 23 of 23 equal, including `OrderState`,
  `PositionState`, `KillSwitchState`, `AuditEventClass`, `RunType`, `InstrumentType`.
- **The Block A numeric limits** against the loaded policy, 13 rule thresholds: `EXP-001` 0.05, `EXP-002` 0.2,
  `EXP-003` 2.0, `EXP-004` 1.0, `LOSS-001` 0.02, `LOSS-002` 0.05, `LOSS-003` and `LOSS-004` 0.1,
  `SIZE-001` 0.01, `LIQ-001` 0.01, `RATE-001` 20, `RATE-002` 10, `STOP-001` 2.5. All match.
- **P1.3's inventory:** 47 rules; 45 enforce, 2 monitor; 37 DENY, 6 MODIFY, 3 KILL, 1 ALLOW;
  27 CRITICAL, 12 HIGH, 7 MEDIUM, 1 LOW; `on_missing_input` 44 DENY, 3 KILL. All as stated.
- **P1.4's inventory:** 42 event types; 14/10/8/3/3/2/2 by class; 25 effectful; 6 reproducible.
- **Signatures:** `PolicyLoader.load()`, `PolicyGate.evaluate()`, `verify_chain()`,
  `replay_run()`, `benchmark_verification()`, `EffectiveConfig` — all as declared.
- **P1.2's inventory against the migration text:** 37 tables, 8 hypertables, 3 continuous
  aggregates, 12 functions, 16 indexes, 4 roles, 3 `EXCLUDE` constraints.
- **The six Python suites, both modes, in the isolated copy:**

| Suite | Normal | `-O` |
|---|---|---|
| `verify_p11_invariants.py` | exit 0, PASSED 42 | exit 0, PASSED 42 |
| `verify_p11_p12_contract.py` | exit 0, 21 pairs ALIGNED | exit 0, ALIGNED |
| `verify_p11_x2_regressions.py` | exit 0, PASSED 21 | exit 0, PASSED 21 |
| `verify_p11_x5_conditions.py` | exit 0, PASSED 12 | exit 0, PASSED 12 |
| `verify_p13_config.py` | exit 0, PASSED 39 | exit 0, PASSED 39 |
| `verify_p14_audit.py` | exit 0, PASSED 36 | exit 0, PASSED 36 |

All six pass while X3R-M1 and X3R-M2 are present. No suite constructs an envelope from P1.3's
payload, and none compares the two hashes.

### 2.4 Errors in the existing record's contracts section

| Id | The record says | What I found |
|---|---|---|
| **X3R-E1** | §3 C-3: "Checked all 118 exported contracts for duplicate names … **None**" | `canonical_bytes`, rows 89 and 106 (X3R-M3) |
| **X3R-E2** | §4: "Signature mismatches between producer and consumer: **none found**", resting on `verify_p11_p12_contract` | That test checks that each column name exists on the model. It does not check the reverse direction, types, or hashes. X3R-M1 and X3R-M2 are both mismatches |
| **X3R-E3** | §4, Consumers column | Wrong in 7 rows: 1, 2, 3, 8, 9, 30, 42. The generator split on `\|` inside the Signature cell. Row 1 `Market` shows `IN`; the spec says "every phase, every table" |
| **X3R-E4** | §3 C-2: six contracts missing from P1.4's `produces:` header | Correct for P1.4, but the same defect is in all four specs — see X3R-C2 |

---

## 3. Step 3 — contradictions

Each is presented with both sources and a recommended resolution. **None is resolved here.**

### Carried from the 2026-08-31 record

**X3R-C1 — `depends_on` version drift. Was 2 instances, now 4.**

| Spec | Declares | Actual at `b8b1340` |
|---|---|---|
| SPEC-P1.2-STORAGE | `SPEC-P1.1-DOMAIN v0.1` | v0.3 |
| SPEC-P1.3-CONFIG | `SPEC-P1.1-DOMAIN v0.2` | v0.3 |
| SPEC-P1.3-CONFIG | `SPEC-P1.2-STORAGE v0.1` | **v0.5** — new |
| SPEC-P1.4-AUDIT | `SPEC-P1.2-STORAGE v0.1` | **v0.5** — new |

`STAGE-1-FREEZE` and `STAGE-1-GAP-AUDIT` also still declare `SPEC-P1.2-STORAGE v0.1`.
*Resolution:* bump all at re-freeze. The P1.4 one is not only documentary: P1.4 was written
against an 8-column preimage and v0.5 has 11.

**X3R-C2 — contracts in the table but not the `produces:` header. Was P1.4 only; it is all four.**

| Spec | In the CONTRACTS table, absent from the header | In the header, absent from the code |
|---|---|---|
| P1.1 | `PoolNAV`, `ConsolidatedNAV`, `DomainError` hierarchy | `src/domain/errors.py`, `type.InstrumentId`, `model.NAV`, `model.AuditEvent` |
| P1.2 | `account`, `run_context`, `universe_version`, **`verify_audit_chain`** | — (`bars_asof` is in the code and in neither) |
| P1.3 | `RuleOutcome`, `loosens_for`, `assert_no_env_risk_reads` | — |
| P1.4 | `BreakKind`, `ChainBreak`, `IntentRecord`, `benchmark_verification`, `promote_to_action`, `uuid7_timestamp_ms` | — |

*Resolution:* regenerate each header from its table and from the code.

**X3R-C3 — duplicate contract names.** The record says none. There is one. See X3R-M3.

**X3R-C4 — Block A numbers stated two ways.** None found; I agree with the record (§2.3 above).
But the record's attached observation is wrong — see X3R-E5 in §3.3.

### New in this re-run

**X3R-C5 — MEDIUM — India price floor.**
- `master-research-summary.md` §4, line 118: "Price > $5/**₹100**".
- `config/policy.yaml` line 117: `min_price_inr: "50.00"  # ASSUMPTION`.
- SPEC-P1.3 ASSUMPTIONS row 3 and `Q-P1.3-2`: "`[RS §4]` gives market cap and ADDV for India but
  **not a price floor**".

The third statement is false, and it is the stated reason for the second.
*Resolution:* set ₹100 citing `[RS §4]`, or record an Owner decision for ₹50. India is unfunded,
so nothing live depends on it today.

**X3R-C6 — LOW — staleness threshold.**
- `master-research-summary.md` §8: "reject data >5s old for real-time".
- `config/policy.yaml` `DATA-001`: `threshold: 600` seconds, authority `[CONST-6]`.

*Resolution:* add the authority for 600 s to the rule. ADR-13's daily-bar design probably makes
5 s inapplicable, but I found no decision that says so. NOT VERIFIED.

**X3R-C7 — LOW — SPEC-P1.2 counts its own constraints two ways.**
- §6.11: "240 `CHECK` constraints".
- §8: "§6's DDL carries 47 `CHECK`, 6 `UNIQUE` and 3 `EXCLUDE` constraints".

The migration text contains `CHECK (` 240 times and `EXCLUDE USING` 3 times.
*Resolution:* correct §8. §6.11 also says "every `SECURITY DEFINER` function pins `search_path` —
PASS, 12 functions"; there are 12 functions and 6 are `SECURITY DEFINER`.

**X3R-C8 — LOW — how `prev_hash` is built.**
- SPEC-P1.1 §10.3: "`prev_hash` — SHA-256 **of** the previous event's `payload_hash`".
- SPEC-P1.2 §9.4 (`NEW.prev_hash := v_prev`) and SPEC-P1.4 §6.4: `prev_hash` **equals** the
  predecessor's `payload_hash`.

*Resolution:* P1.1 §10.3 is the superseded text; remove it with X3R-M4.

**X3R-C9 — MEDIUM — the risk verdict is defined three ways, and three fields are named two ways.**

| Source | Verdict values | On a size breach |
|---|---|---|
| SPEC-P1.1 §8.2, `RiskDecision` | `ALLOW`, `DENY`. "A three-valued verdict with a 'reduce' member would put the risk engine in the sizing business" | `DENY` carries an informational maximum; "the sizer may re-propose **once**" |
| SPEC-P1.3 §4.1, `RuleAction` | `KILL`, `DENY`, `MODIFY`, `ALLOW` | 6 `MODIFY` rules; modify then re-evaluate, up to `MAX_MODIFY_PASSES = 4` |
| `master-research-summary.md` §6 Phase 8 | `APPROVE`, `REJECT`, `REDUCE_SIZE`, `KILL` | — |

No spec states how a `PolicyVerdict` becomes a `RiskVerdict`.

| Concept | Name A | Name B |
|---|---|---|
| The limit that bound | `binding_constraint` — P1.1 `RiskVerdict`, P1.2 `risk_evaluation` | `binding_rule_id` — P1.3 `PolicyVerdict`, P1.4 `RISK_EVALUATED` payload |
| The policy hash | `config_hash` — P1.1, P1.2, P1.4 bundle | `content_hash` — P1.3; `policy_content_hash` — P1.4 `RISK_EVALUATED` |
| Kill scope | `KillSwitchScope` — P1.1 | `KillScope` — P1.3. Same two values, two enums |

*Resolution:* P2.9 must state the mapping before it is specified. Pick one name per concept at
the next amendment. This is not a behavioural defect today because P2.9 does not exist.

**X3R-C10 — the canonicalisation is recorded as closed and is not.** This is the documentary
side of X3R-M1: SPEC-P1.2 `Q-P1.2-1` "Closed" against SPEC-P1.2 `Q-P1.2-7` open, in the same
table. The record lists it under X2-4/a. *Resolution:* reopen `Q-P1.2-1` or fold it into
`Q-P1.2-7`.

**X3R-C11 — LOW — test counts stated two ways.**
- SPEC-P1.1 §15.4: "43/43" and "20/20". Measured: 42 and 21.
- SPEC-P1.2 §6.11 and the `Q-P1.2-6` row: the DDL "has not been executed". The record says it
  has. I did not execute it.

**X3R-C12 — LOW — stale version labels and references to files that do not exist.**

| Where | Says | Fact |
|---|---|---|
| SPEC-P1.1 footer | "END OF SPEC-P1.1-DOMAIN v0.1", then "CONTINUE: src/domain/models.py" | v0.3 |
| SPEC-P1.1 header prose | "Status remains DRAFT" | `status: FROZEN` |
| SPEC-P1.2 footer; migration line 3 | "v0.1" | v0.5 |
| SPEC-P1.2 line 16 | "Consumes: SPEC-P1.1-DOMAIN v0.1 (DRAFT)" | v0.3, FROZEN |
| SPEC-P1.1 `produces:` | `src/domain/errors.py` | no such file |
| SPEC-P1.3 §7; `loader.py:160` | `src/config/env.py` | no such file |
| `policy.yaml:6`; `loader.py:13` | `tests/verify_p13_no_env_risk.py` | no such file; the test is in `verify_p13_config.py` |
| SPEC-P1.2 §6 | `migrations/versions/0001_initial.sql` | `migrations/0001_initial.sql` |
| SPEC-P1.2 §11 | Alembic revisions | no Alembic tree; one raw SQL file |

**X3R-C13 — LOW — the table allows what the envelope forbids.**
- SPEC-P1.4 §4 and §10: `is_paper` and `is_backtest` are mutually exclusive; `event_id` is
  UUIDv7.
- `trading.audit_log`: no `CHECK` against both flags being true (`run_context` has one);
  `event_id` defaults to `gen_random_uuid()`, a version 4 UUID.

*Resolution:* decide with X3R-M1.

**X3R-C14 — MEDIUM — SPEC-P1.2's status contradicts itself.**
- Header: `status: FROZEN`.
- Same header, `frozen_by:`: "… **NOT re-frozen**, awaiting X2 re-review".
- `STAGE-1-FREEZE` §8: "SPEC-P1.2-STORAGE **v0.1** … FROZEN". §11.6: "**v0.4** still carries
  `status: FROZEN`". The file is v0.5.

The pack's rule 3 lets a code phase cite a spec whose status is `FROZEN`. A reader of the header
alone would cite it. *Resolution:* see §7.

### 3.3 Not contradictions, and one correction to the record

- **28 triggers (SPEC-P1.2 §6.11) against 27 (record §2, §11.12).** The migration creates 14
  static triggers and 14 in a loop. `scripts/apply-migration.sh` counts
  `information_schema.triggers`, which does not list `TRUNCATE` triggers, and there is exactly
  one. That would give 27. Reasoned from the script, **NOT VERIFIED** by execution.
- **18,538 events/s (SPEC-P1.4) against 35,853 measured here.** Machine-dependent.
- **X3R-E5.** MERGE-CHANGES §2 C-4 and its open question 2, repeated by GAP-AUDIT C-5: "20
  orders/min … appears **only** in `config/policy.yaml` and in no spec prose." SPEC-P1.3 §10,
  line 348: "`RATE` | 001–002 | 20 orders/min global, 10 per strategy". P1.3 is unchanged since
  `605ff40`, so the statement was wrong when written.

---

## 4. Step 4 — consolidated assumptions

### 4.1 Count and de-duplication

32 rows across the four `## ASSUMPTIONS` tables (13, 8, 6, 5). The record's 32 is correct, but
it did not de-duplicate, which step 4 requires (**X3R-E6**). Two pairs are the same assumption:

| Kept | Duplicate | Assumption |
|---|---|---|
| P1.1 #2 | P1.2 #2 | `Price` at 6 dp is enough |
| P1.2 #4 | P1.4 #5 | ~1,000 B mean audit row, 15,000 events per session |

**30 distinct.** Full text in [`evidence/consolidated-tables.generated.md`](evidence/consolidated-tables.generated.md).

### 4.2 Assumptions the specs rely on that are in no ASSUMPTIONS table

| Id | Assumption | Where it is relied on |
|---|---|---|
| **X3R-A1** — new since the re-open | `0001_initial.sql` has never been deployed, so no production audit history exists | SPEC-P1.2 §9.4 comment and record §11.4, §11.8. It is the only reason v0.5 was allowed to invalidate every stored hash |
| X3R-A2 | PDT is a margin-account rule with a $25,000 floor | SPEC-P1.1 §9.4, `ASSUMPTION [VERIFY-P0.2]`. GAP-AUDIT already flags it as tracked by no register |

### 4.3 Ranked by impact if false

| Rank | Assumption | Source | If false |
|---|---|---|---|
| 1 | `[CONST-2]` is enforced structurally at the `Decision` constructor | P1.1 #8 | `[CONST-1]` is decorative |
| 2 | Off-VM anchor storage is write-once with distinct credentials | P1.4 #3 | No tamper evidence across sessions. Also the only answer to Finding A's residual |
| 3 | No production audit history exists (X3R-A1) | P1.2 §9.4 | Every stored hash is invalid and a clean chain reports as tampered |
| 4 | US and India settlement are both T+1 | P1.1 #11 | `settled_cash` sizing is wrong |
| 5 | ~1,000 B audit row, 15,000 events per session | P1.2 #4 ≡ P1.4 #5 | Disk model breaks near 10× |
| 6 | Round-trip cost 25 bps US, 90 bps India | P1.3 #6 | Every edge estimate; `EDGE-001` |
| 7 | The off-VM WAL receiver fits the 5 s exit budget | P1.2 #8 | RPO 0 and the exit budget cannot both hold |
| 8 | No natural-person data enters the log | P1.4 #2 | Erasure law conflicts with an immutable log |
| 9 | `cryptography` is acceptable; two approvers is right | P1.3 #1, #2 | The two-person rule is not provable |
| 10 | PDT rule and floor (X3R-A2) | P1.1 §9.4 | An unverified regulatory number in a frozen spec |
| 11 | Compression 15× and 4× | P1.2 #3 | Disk; still 4× headroom at 8× |
| 12 | `SECURITY DEFINER` as-of functions cover every backtest read | P1.2 #1 | A backtest is blocked — loud and safe |
| 13 | A merger preserves holding period and basis; FIFO; no India wash-sale rule | P1.1 #12, #13, #6 | Tax reporting |
| 14–30 | The remaining 17 | — | Local and recoverable |

The re-open changed one ranking input. Before v0.5, rank 3 did not exist.

---

## 5. Step 5 — consolidated open questions

### 5.1 Count

32 rows (11, 9, 6, 6). **30 unique ids.** One id repeats: `Q-P1.1-1`, in P1.1, P1.2 and P1.3; the
three restatements agree. The record's 31 rows and 29 unique were correct on 2026-08-31. The
difference is `Q-P1.2-7`.

### 5.2 What changed since the 2026-08-31 merge

| Q | Change |
|---|---|
| **`Q-P1.2-7`** | **New.** Four §6.1 keys have no column. Its own text says it "blocks the first writer". X3R-M1 adds a fifth field |
| `Q-P1.2-6` | The row still reads "the DDL is unexecuted". The record says the migration runs and a 36-check suite covers the five behaviours, with assertion 1 inverted to pin Finding A. **NOT VERIFIED** by me. The row is stale either way |
| `Q-P1.2-1` | Marked closed; contradicted by `Q-P1.2-7` (X3R-C10) |
| `Q-P1.4-4` | Asks whether `audit_log` should gain a `canonical_schema` column. That is one of `Q-P1.2-7`'s four. Fold it in |
| `Q-P1.2-3` | Asks whether compression interacts with the `ENABLE ALWAYS` triggers. Finding A changes its premise; the question is still open |
| `Q-P1.2-5` | Says it blocks "P1.4". P1.4 is finished and has no writer. It now belongs to the first writer |

### 5.3 New questions raised by this re-run

| Id | Question | Blocks |
|---|---|---|
| **X3R-Q1** | Which side changes for X3R-M2: P1.3's payload or P1.4's rule? | Any run. `EFFECTIVE_CONFIG_RENDERED` is written at run start |
| **X3R-Q2** | Where is the `ReproducibilityBundle` stored? | P2.5, P2.6, P2.7, P2.9 — each produces a type that requires one |
| **X3R-Q3** | How does a `PolicyVerdict` map to a `RiskVerdict` (X3R-C9)? | P2.9 |
| **X3R-Q4** | Is earnings blackout in scope, and if so which rule id (X3R-G1)? | P2.9 |
| **X3R-Q5** | India price floor: ₹100 or ₹50 (X3R-C5)? | India activation |

### 5.4 Which now block Stage 2

| Phase | Blocked by | Note |
|---|---|---|
| **P2.1** | **`Q-P1.2-7` / X3R-M1** | P2.1 produces `DATA_RECEIVED`, `FX_RATE_RECORDED`, `CORPORATE_ACTION_APPLIED`. The record's "none blocks P2.1" does not hold for any P2.1 code that writes an audit event |
| **Any run** | **X3R-Q1** | The run-start config event cannot be built |
| P2.2 | `Q-P1.1-6` | As the record says. It is answered by a measurement taken during P2.1 |
| P2.3 | `Q-P1.2-7` | Produces two event types |
| P2.5, P2.6, P2.7 | `Q-P1.2-7`, X3R-Q2 | Each produces a reproducible event type |
| P2.9 | `Q-P1.1-1`, `Q-P1.1-2`, **`A-14`**, X3R-Q2, X3R-Q3, X3R-Q4 | `Q-P1.3-3` is measured inside P2.9, so it is an acceptance test, not a prior blocker |
| P2.10 | X3R-G2 | The kill-switch trigger list is not specified |

**X3R-E8.** `A-14` — does `[CONST-6]` DENY apply to exposure-reducing actions — is in no Stage 1
document. `STAGE-0-FREEZE` §10: "**A-14 must be ratified before P2.9**". The record's §6.1 and §9
omit it.

Still open and not blocking a named Stage 2 phase: `Q-P1.1-8` (an independent X2 of P1.1) and
record question F-2 (whether P1.3 and P1.4 had an X2 at all). The pack's appendix says the review
is never optional. **NOT VERIFIED** either way.

---

## 6. Step 6 — coverage matrix

### 6.1 Method, and why the record's matrix is replaced

The record's §7 marks a research-summary section "covered" if any spec cites `[RS §n]`. That
measures citation, not coverage (**X3R-E7**). It shows §11 Risk Management as covered by "P0.1"
alone, though SPEC-P1.3 carries all 47 rules, and it reports exactly two gaps.

Below, each requirement is mapped individually. States:

- **S1** — covered by a Stage 1 spec, with the place named.
- **S0** — decided in Stage 0; Stage 1 has nothing to add.
- **Later** — outside Stage 1's scope and owned by a named later phase.
- **GAP** — I found it in no Stage 0 or Stage 1 spec, in `policy.yaml`, or in the code, by text
  search. A gap marked "for Stage 1" is one I think a Stage 1 spec should have carried.

### 6.2 Matrix

| RS § | Requirement | State | Where |
|---|---|---|---|
| 1 | Deterministic risk override | S1 | P1.1 §7.5, §8.2; P1.3 §4 |
| 1 | LLM gating | S0 / Later | P0.3; P4.2 |
| 1 | Every decision logged and reproducible | S1 | P1.4 §4, §5 — subject to X3R-M1 |
| 2 | Unique strategy id on every order | S1 | P1.1 `Order.strategy_id`; `ORDER_INTENT` payload |
| 2, 16 | 10 OPS threshold | S0 | P0.1 ADR-13; `RATE-001` |
| 4 | US and India scope | S1 | `Market`, `Exchange`, `PoolId` |
| 4 | Market cap, volume, price filters — US | S1 | `UNIV-001`…`003` |
| 4 | Price filter — India ₹100 | **Contradiction** | X3R-C5 |
| 4 | Momentum-or-value filter; volatility filter | S0 / Later | P0.1 ADR-14; P2.3 |
| 4 | BUY / HOLD / SELL / NO-TRADE | S1 | `SignalDirection`, `DecisionAction` |
| 4 | Confidence score 0–100 | S1 | P1.1 §13: a fraction in [0, 1], one meaning |
| 4 | Thesis with bull and bear case and invalidation conditions | S1 | P1.1 §7.4; P1.2 §8.3 |
| 4, 6 | Exit hierarchy: emergency, high, medium, low | **GAP** | X3R-G7. No type and no mention. P3.4 owns the logic; P1.1 has no vocabulary for it |
| 4 | Position ≤ 5%, sector ≤ 20%, daily loss ≤ 2%, drawdown ≤ 10% | S1 | `EXP-001`, `EXP-002`, `LOSS-001`, `LOSS-003`/`004` |
| 4 | Liquidity requirement | S1 | `LIQ-001` |
| 4, 6 | **Earnings blackout** | **GAP, for Stage 1** | X3R-G1 |
| 4 | Limit orders preferred | S1 | `EXEC-001` |
| 4 | Duplicate-order protection | S1 | P1.1 `Order.client_order_id`; P1.2 `UNIQUE (account_id, client_order_id)`; P1.4 §7 |
| 4 | Retry with exponential backoff | Later | P3.1 |
| 4 | Alerting: Telegram, dashboard, SMS | S0 / Later | ADR-01; P6.1 |
| 4 | Audit trail with cryptographic verification | S1 | P1.2 §9; P1.4 §6 |
| 4 | Never "trade lost → change strategy" | S0 | ADR-07; P6.6 |
| 5 | Risk and kill switch deterministic | S1 | P1.3; P1.1 §11.3 |
| 5 | Agent messages structured, logged, validated | S1 | Pydantic models; `EVENT_REGISTRY` |
| 5 | Agent messages rate-limited | **GAP** | X3R-G4. Order rate only (`RATE-001`/`002`) |
| 5, 15 | Agent messages origin-tagged | **GAP** | X3R-G4. P4.1 |
| 6 | Timestamp and tag all data; never substitute a missing value | S1 | P1.1 §6 (`as_of`, `retrieved_at`, `source`); `[CONST-6]` throughout |
| 6 | Combined score weights | S0 | P0.1 §C-4 |
| 6 | Risk output APPROVE / REJECT / REDUCE_SIZE / KILL | **Contradiction** | X3R-C9 |
| 8 | Schema validation, de-duplication, anomaly detection | Later | P2.2 |
| 8 | Reject real-time data older than 5 s | **Contradiction** | X3R-C6 |
| 9 | Model allocation | Later | P2.5, P4.x |
| 9 | LLM never sizes, executes, or changes limits | S1 | P1.1 §7.4, §7.5; P1.3 §6 `[DEFAULT-C6]` |
| 10 | Stack | S0 | P0.1; AD-5 amends the LLM line |
| 11 | Risk per trade 1% | S1 | `SIZE-001` |
| 11 | ATR stop `entry − 2.5 × ATR` | S1 | `STOP-001`; P1.1 §8.1 |
| 11 | Trailing stop | **GAP** | X3R-G3. `OrderType` has no trailing member; `InvalidationKind` has none |
| 11 | Time stop | S1 | `HOLD-002`; `InvalidationKind.TIME_STOP` |
| 11 | Thesis stop | S1 | `InvalidationKind.NEWS_EVENT`, `FUNDAMENTAL_BREACH` |
| 11 | Gross ≤ 2×, net ≤ 1×, order rates 20 and 10 | S1 | `EXP-003`, `EXP-004`, `RATE-001`, `RATE-002` |
| 11 | Weekly loss ≤ 5% | S1 | `LOSS-002` |
| 11 | Price data must be fresh, fail-closed | S1 | `DATA-001`; P1.1 §6.7 |
| 11 | Policy file with enforce / monitor mode, fail-closed default | S1 | P1.3 §3, §4.3 |
| 11 | Kill trigger: drawdown > 10% | S1 | `LOSS-003`, `LOSS-004` |
| 11 | Kill triggers: daily loss, weekly loss | **Differs** | Policy action is `DENY`, not `KILL`. Block A names only drawdown as tripping the switch |
| 11 | Kill triggers: volatility > 3σ, API failure > 5 retries, agent loop > 10, data quality | **GAP** | X3R-G2 |
| 11 | Manual kill, separate channel | S1 / Later | P1.1 §11.3; P2.10 |
| 11 | Kill requires human re-enable | S1 | P1.1 §11.3; `kill_switch_event` `CHECK`; `KILL-001` |
| 12 | Order types: limit, market, stop-limit | S1 | `OrderType` |
| 12 | Seven-stage progression to live | Later | P6.5 |
| 13 | Survivorship-bias-free data | S1 | P1.2 §5.4, invariant I7 |
| 13 | No look-ahead bias | S1 | P1.2 §3 |
| 13 | Transaction costs | S1 / Later | `assumed_round_trip_bps`; P5.3 |
| 13 | Walk-forward, 34+ windows | S1 | `model_registry` `CHECK`; AD-2 |
| 13 | Monte Carlo simulation | **GAP** | X3R-G8. No mention. P5.1 |
| 13 | Success criteria: Sharpe, Sortino and others | S0 | P0.1 |
| 14 | Monitoring metrics, alert levels, VaR, drift | Later | P6.1 |
| 14 | Audit record must hold: timestamp, symbol, model versions, scores, order, execution, exit reason | S1 | P1.4 envelope, bundle and registry keys |
| 14 | Audit record must hold: **price, portfolio state, decision reason, confidence** | **GAP** | X3R-G5. `DECISION_MADE` requires none of them |
| 14 | Append-only, searchable, verifiable, retained | S1 | P1.2 §9; P1.4 §6, §8 |
| 15 | Secrets in Vault, never in the environment | S1 | P1.3 §7, §8 |
| 15 | Secret rotation every 30 days | Later | P6.2. Stage 1 states only the 4-hour SLA |
| 15 | Static IP, VPC, firewall, TLS | Later | P6.2 |
| 15 | Input sanitisation; output validation | S1 / Later | P1.1 §6.5; P4.1, P4.4 |
| 15 | State tampering and memory poisoning | S1 | P1.2 §9; P1.4 §6 — subject to Finding A, open |
| 16 | PDT | S1 | `CASH-002`, monitor mode; P1.1 §9.4 |
| 16 | Wash sales | S1 | P1.1 §9.1; P1.2 `lot` |
| 16 | Best execution | **GAP** | X3R-G6. Named in Block A item 9; in no spec |
| 16 | Broker hosting, two-factor authentication | S0 / Later | P0.2; P6.3 |
| 19–21 | Decisions made, open questions, missing research | S0 | P0.1 |

Sections 1–3 (other than the rows above), 7, 17, 18, 22 and 23 are narrative, diagrams or
process and carry no further requirement.

### 6.3 Gaps, listed explicitly

| Id | Gap | Belongs to | Why it matters |
|---|---|---|---|
| **X3R-G1** | Earnings blackout | **Stage 1** — P1.3. Its prompt asks for "a complete policy.yaml containing every rule" | A named risk control with no rule id and no decision removing it. `policy.yaml` says "every constitutional risk number appears here"; this one is in the research summary and not in Block A, which may be how it was lost |
| **X3R-G2** | Four automatic kill triggers | P2.10 | No rule id and no Stage 0 decision |
| **X3R-G3** | Trailing stop | P3.4, with a P1.1 type | The domain cannot express it |
| **X3R-G4** | Origin tagging; message rate limits | P4.1 | Prompt-injection control |
| **X3R-G5** | Four audit fields the research summary requires on every decision | P1.4 or P2.7 | The registry's required keys are a floor |
| **X3R-G6** | Best execution | P6.3 | It is in the Constitution |
| **X3R-G7** | Exit hierarchy vocabulary: emergency, high, medium, low | P3.4, with a P1.1 type | The domain has no type for it |
| **X3R-G8** | Monte Carlo simulation | P5.1 | Deferred, and recorded nowhere |
| — | §9 AI/ML models; §14 monitoring | Stage 4; P6.1 | The record's two gaps. I agree both are deliberate |

The record says "Two real gaps". I count the same two as deliberate and scheduled, **eight more
that are not recorded anywhere** (X3R-G1 to G8, over nine matrix rows), and four contradictions
or differences with the research summary.

Totals for the 70 rows: 37 covered by a Stage 1 spec; 6 decided in Stage 0; 7 split between
Stage 0 or 1 and a later phase; 7 owned by a later phase; 4 contradictions or differences; 9 gaps.

---

## 7. Step 7 — master version and spec status

I change no status and re-freeze nothing. This is what each **should** carry and why. The Owner
decides.

| Artifact | Carries now | Should carry | Why |
|---|---|---|---|
| SPEC-P1.1-DOMAIN v0.3 | `FROZEN` | **`FROZEN`**, unchanged | Byte-identical since the freeze; nothing re-opened. X3R-M4 and X3R-C8 are documentary and can wait for its next amendment. `Q-P1.1-8` is still owed |
| SPEC-P1.2-STORAGE v0.5 | `FROZEN`, with "NOT re-frozen" in the same header | **`DRAFT`** until re-freeze, then `FROZEN` at v0.5 | Block B defines two statuses. A spec that has been re-opened and not re-frozen is not `FROZEN`, and rule 3 keys on that word (X3R-C14). On the merge evidence v0.5 can be re-frozen: its changed DDL equals the migration. It must carry `Q-P1.2-7` as a named blocker, not as "not blocking today" |
| SPEC-P1.3-CONFIG v0.1 | `FROZEN` | **`FROZEN`**, with X3R-M2 recorded against it | Unchanged since the freeze. X3R-M2 means it or P1.4 must be re-opened under T5 before any run writes its config event |
| SPEC-P1.4-AUDIT v0.1 | `FROZEN` | **`FROZEN`**, with X3R-M1 and X3R-M2 recorded against it | Unchanged. Its `depends_on` names a P1.2 version three steps old, and its §6.2 and one CONTRACTS row state something untrue about P1.2 |
| STAGE-1-FREEZE | `version: 1.0`, `depends_on … SPEC-P1.2-STORAGE v0.1` | **`version: 1.1`**, `depends_on … v0.5`, when the Owner adopts §12 | The record's own N-4. My diff leaves the header alone because it is outside §12 |
| STAGE-1-MERGE-CHANGES | `version: 1.0` | **`version: 1.1`** on the same condition | It gains a section |

**On re-freezing Stage 1.** X3 is one input. On the merge evidence alone:

1. Nothing found here is a defect introduced by the v0.1 → v0.5 change.
2. X3R-M1 and X3R-M2 are real, pre-date the re-open, and are not blocked by any existing gate.
   Freezing over them is defensible only if the gate names them as blockers of the phases in
   §5.4. Freezing with the record's current gate text would repeat X3R-E2.
3. The X5 re-run should be given §5.4 and §6.3 as inputs.

---

## 8. CHANGES — what moved, what conflicted, what was resolved

| | |
|---|---|
| **Moved** | Nothing. No spec text was relocated or rewritten. The consolidated tables were regenerated from the specs |
| **Conflicted** | 12 contradictions (X3R-C1, C2 and C5 to C14; C3 is X3R-M3 and C4 found none), 7 contract mismatches (X3R-M1 to M7), 9 errors in the 2026-08-31 record (X3R-E1 to E9), 8 unrecorded coverage gaps (X3R-G1 to G8) |
| **Resolved** | **Nothing.** Step 3 forbids silent resolution, and this run was read-only |

Compared with the 2026-08-31 merge:

| Item | 2026-08-31 | This re-run |
|---|---|---|
| Contracts | 118 | 118 |
| Duplicate contract names | none | **1** |
| Producer/consumer mismatches | none | **2 HIGH, 2 MEDIUM, 3 LOW** |
| Assumptions | 32, not de-duplicated | 32 rows, **30 distinct**, plus 2 unlisted |
| Open questions | 29 unique | **30 unique**, plus 5 raised here |
| Questions blocking P2.1 | none | **`Q-P1.2-7`** |
| `depends_on` drift | 2 | **4** |
| Coverage gaps | 2, both scheduled | the same 2, plus **8 unrecorded**, plus 4 contradictions or differences with the research summary |

---

## 9. Evidence

### 9.1 Environment

- Windows 11, Git Bash. Python 3.11.9, pydantic 2.13.5, PyYAML 6.0.3, cryptography 46.0.7.
- Isolated copy: `git archive b8b1340 | tar -x` into the session scratch folder, outside the
  repository. All imports and all suites ran there.
- Nothing from the repository was imported in place. The two inventory scripts read the
  repository with `ast` and `re` only.
- No container was started. `ai-trading-tsdb` was not connected to.
- `git status --porcelain` on the repository returned nothing at the start and at the end.

### 9.2 Commands

| Purpose | Command | Result |
|---|---|---|
| Confirm the commit | `git rev-parse HEAD`; `git status --porcelain=v1 --untracked-files=all` | `b8b1340c…`; empty |
| History | `git log --oneline 605ff40..b8b1340`; `git diff --stat 605ff40..b8b1340` | 4 commits; 10 files, +2,663 −240 |
| Spec change | `git diff 605ff40..b8b1340 -- docs/specs/SPEC-P1.2-STORAGE.md` | read in full |
| Four standard tables | `py -3.11 evidence/extract.py tables.json` | 44/33/20/21 contracts; 13/8/6/5 assumptions; 11/9/6/6 questions |
| Code and migration inventory | `py -3.11 evidence/code_inventory.py code.json` | 37 tables, 8 hypertables, 3 aggregates, 12 functions, 16 indexes, 14 static triggers, 240 `CHECK (`, 3 `EXCLUDE`, 6 `SECURITY DEFINER` |
| Spec DDL against migration | inline script, per `-- ===== section` marker | 56 differing lines, all in §6.10 and §9.4 |
| Pre-existing drift | `git show 605ff40:migrations/0001_initial.sql \| grep -c "read committed"` → 1; `… \| grep -c "octet_length(payload::text)"` → 3; `git show 605ff40:docs/specs/SPEC-P1.2-STORAGE.md \| grep -c "pg_column_size(payload)"` → 2 | both differences existed at `605ff40` |
| Registry counts | import `audit.events` in the copy | 42 types, 25 effectful, 6 reproducible, 19 `Producer` members, 17 used |
| X3R-M3 | call both `canonical_bytes` | output quoted in §2.2 |
| X3R-M2 | `PolicyLoader(Path("config")).load(require_signature=False).audit_payload()` into `AuditEnvelope(...)` | `NonCanonicalPayloadError`; 132 numeric leaves |
| X3R-M1 fields | `set(AuditEnvelope.model_fields)` minus the `audit_log` column names | 5 fields |
| Enums against `CHECK` | inline script over `code.json` | 23 of 23 equal |
| Header against table | inline script over `tables.json` | X3R-C2 |
| Python suites | `py -3.11 [-O] tests/<suite>.py`, six suites, in the copy | twelve runs, all exit 0 |
| Blob hashes | `git show b8b1340:<path> \| sha256sum` | §1.2 |
| Coverage | `grep -c` for 28 terms across the seven specs, `policy.yaml` and `models.py` | §6 |

### 9.3 Files in this folder

| File | What it is |
|---|---|
| `X3-report.md` | This report |
| [`STAGE-1-FREEZE.section12.proposed.diff`](STAGE-1-FREEZE.section12.proposed.diff) | Replaces the §12 "pending" notice. Sections 1–11 untouched |
| [`STAGE-1-MERGE-CHANGES.proposed.diff`](STAGE-1-MERGE-CHANGES.proposed.diff) | Appends a dated re-run section. Existing sections untouched |
| [`evidence/consolidated-tables.generated.md`](evidence/consolidated-tables.generated.md) | The 118 contracts, 32 assumptions and 32 question rows, generated |
| [`evidence/extract.py`](evidence/extract.py), [`evidence/code_inventory.py`](evidence/code_inventory.py) | The two scripts that produced the counts |

### 9.4 The two proposed diffs

Both were generated with `git diff` in a throwaway repository holding the two files exactly as
`git show b8b1340:<path>` returns them. Their `index` lines name the same blobs the repository
holds at `b8b1340`: `1d7f4e2` for `STAGE-1-FREEZE.md` and `6e382d5` for
`STAGE-1-MERGE-CHANGES.md`.

| Check, run in the repository | Result |
|---|---|
| `git apply --check --verbose STAGE-1-FREEZE.section12.proposed.diff` | `Checking patch docs/specs/STAGE-1-FREEZE.md...` — exit 0 |
| `git apply --check --verbose STAGE-1-MERGE-CHANGES.proposed.diff` | `Checking patch docs/specs/STAGE-1-MERGE-CHANGES.md...` — exit 0 |
| `git apply --check --cached` on each (against the index, which is `b8b1340`) | exit 0, exit 0 |
| `git apply --check` on both together | exit 0 |
| `git apply --check --whitespace=error-all` on both | exit 0 |
| `git apply --stat` | `STAGE-1-FREEZE.md`: 206 insertions, 12 deletions. `STAGE-1-MERGE-CHANGES.md`: 113 insertions, 0 deletions |

The freeze diff has one hunk, starting at line 1193. Its 12 deleted lines are all inside the old
§12 notice (lines 1196 to 1211); nothing above line 1196 is changed. The merge-changes diff only
adds lines after the last existing line.

**Neither diff was applied.** After the checks: `git status --porcelain=v1 --untracked-files=all`
returned nothing, `git rev-parse HEAD` returned `b8b1340c…`, and `git diff --stat` returned
nothing.

One thing to know before applying: `docs/specs/STAGE-1-FREEZE.md` has CRLF line endings in this
working tree and LF in git (`core.autocrlf=true`). `git apply` handled that in the check. A tool
other than git may not.
