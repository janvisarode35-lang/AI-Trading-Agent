---
id: SPEC-P1.3-CONFIG
version: 0.1
status: DRAFT
phase: P1.3 — Configuration & Policy DSL
depends_on: [SPEC-P1.1-DOMAIN v0.2, SPEC-P1.2-STORAGE v0.1, SPEC-P0.1-DECISIONS v0.3, SPEC-P0.2-PROVIDERS v0.5, SPEC-P0.3-BUDGET v0.5, STAGE-0-FREEZE v1.1]
produces: [config/policy.yaml, src/config/loader.py, class.PolicyLoader, class.PolicyGate, class.PolicyDocument, class.Rule, class.EffectiveConfig, class.PolicyVerdict, class.VaultRef, enum.RuleAction, enum.RuleMode, enum.RuleScope, enum.Comparison, enum.Severity, enum.KillScope, enum.Layer, fn.content_hash, fn.canonical_bytes, fn.verify_signature, fn.merge_layers, fn.assert_change_authorised, fn.lint_no_env_risk_reads, fn.infra_env, const.INFRA_ENV_ALLOWLIST, const.ACTION_PRECEDENCE, RULE-IDS EXP-001..LLM-003]
---

# SPEC-P1.3 — Configuration & Policy DSL

**Phase:** Stage 1 — SPECIFY, prompt `P1.3`
**Date:** 2026-08-27
**Author role:** Engineer building the policy layer the risk engine reads

> **The whole point of this phase in one line:** after P1.3, there is exactly one place a risk
> number can come from, and a code path that tries any other route fails a test.

---

## 0. Governing material

### 0.1 What binds this phase

| Requirement | Source | Discharged in |
|---|---|---|
| `_pct` is a **fraction**, never integer percent | P0.1 §6, P0.3 §15.1 | §3.3, validator |
| Limits are **inclusive**: `lte 0.05` passes at exactly `0.05` | P0.1 §6 | §3.2 |
| Windows count **completed exchange sessions** | P0.1 §6 | §3.2 `Measurement.window` |
| Every configuration key from P0.1 §10.2 present, unchanged | P0.1 §10.2 | `policy.yaml` §4 |
| Budget / latency / storage keys from P0.3 §14.4 | P0.3 §14.4 | `policy.yaml` §4 |
| `hitl.risk_deny_override_permitted = false`, **immutable** | ADR-09, invariant I2 | §5.3, `Governance` validator |
| `killswitch.restore_state_on_boot = TRIPPED`, **immutable** | ADR-10, invariant I3 | rule `KILL-001` |
| `fx.system_may_convert = false`, **immutable** | ADR-15 | `policy.yaml` §4 |
| `llm.may_receive_portfolio_state = false`, **immutable** | `[DEFAULT-7]` of P0.1 | rule `LLM-001` |
| Per-pool **and** consolidated evaluation; stricter binds | ADR-15 §4 | `LOSS-001/003/004` |
| Fail-closed on missing, stale or ambiguous input | `[CONST-6]` | §3.4 — enforced at the type level |
| `config_hash` is the FK target for `run_context` | SPEC-P1.2 §6.9 | §5.4 |

### 0.2 A note on what this phase is *not*

P1.3 owns **the rule set, the ordering, and the combination**. It does **not** own the
measurement arithmetic — "what is the 20-session median ADDV of this instrument" belongs to P2.9,
which has the data. `PolicyGate.evaluate()` therefore takes an `evaluator` callable. That split is
deliberate: the part that must be byte-identical no matter who implements it is the part that
decides *which* rule binds, and it lives here.

---

## 1. BLOCKING questions — and the defaults applied

| # | Question | Options | Default applied | What breaks if the default is wrong |
|---|---|---|---|---|
| **1** | When `MODIFY` and `DENY` both fire, which binds? | (a) MODIFY — proceed at reduced size; (b) **DENY** | **(b) DENY** `[DEFAULT-C1]` | Under (a) a sizing rule can negotiate a denial down into a smaller trade — a position that violated the 5% cap becomes a legal 4% position and the breach is never recorded as one. DENY is the more restrictive answer and the only one that keeps a limit a limit |
| **2** | What is the deterministic evaluation order? | (a) declaration order in the file; (b) severity, then id; (c) **rule id, lexicographic** | **(c)** `[DEFAULT-C2]` | (a) makes a YAML reshuffle a behavioural change; (b) makes editing a severity reorder the audit record, so two policy versions with identical rules produce different records. Rule id is stable for the life of the rule, so a given policy version's audit record is byte-reproducible |
| **3** | Does the gate short-circuit on the first DENY? | (a) yes, stop at the first failure; (b) **no, evaluate every rule** | **(b)** `[DEFAULT-C3]` | "Which *other* limits would also have failed" is exactly what an investigator needs after a loss. Short-circuiting makes the audit record depend on evaluation order. Cost: 47 evaluations instead of ~1, against a 60 s `RISK` stage budget |
| **4** | Signature scheme? | (a) HMAC-SHA256, stdlib, zero new dependency; (b) **Ed25519 via `cryptography`** | **(b)** `[DEFAULT-C4]` | §5.3's two-person rule requires **attributing** a signature to an individual. Every holder of a shared HMAC key produces identical signatures, so "two distinct approvers signed this" is unprovable under (a). The two-person rule and a shared-secret MAC are incompatible, and the rule is the requirement |
| **5** | Does a live policy change reach an in-flight decision? | (a) yes, re-read per decision; (b) **no, bound at run start** | **(b)** `[DEFAULT-C5]` | ADR-14 freezes the order list at pipeline time. A config that changed mid-run would mean some decisions in one audit record were taken under limits that no longer exist and cannot be reconstructed. See §5.4 |
| **6** | May the operator-override layer touch a risk rule? | (a) yes, it is the top layer; (b) **no — a load failure** | **(b)** `[DEFAULT-C6]` | An operator who can loosen a limit at runtime has defeated `[CONST-1]` and ADR-09 alike. A limit change is a new signed version with §5.3's approvals, never a runtime knob. A denied key is a **load failure**, not a warning and not a silent drop — the attempt belongs in the audit trail |
| **7** | How many approvers to loosen a limit? | (a) 1, matching ADR-09 row 2; (b) **2 distinct identities** | **(b)** `[DEFAULT-C7]` | See §5.3 — this is stricter than a frozen ADR, which is permitted, and it has a real operational consequence stated there |
| **8** | Is a monitor-mode rule evaluated? | (a) skipped entirely; (b) **evaluated and recorded, but does not bind** | **(b)** `[DEFAULT-C8]` | A rule you never evaluate is a rule you cannot promote to `enforce` with any confidence. `CASH-002` exists in monitor mode precisely so the day-trade counter is proven correct **before** it ever becomes binding under a margin account |
| **9** | What happens on a `MODIFY`? | (a) apply and proceed; (b) **apply, then re-evaluate the whole set** | **(b)** `[DEFAULT-C9]`, bounded at `MAX_MODIFY_PASSES = 4` | A modified quantity is a different proposal and must face every rule again — a size reduced for liquidity can still breach the cash buffer. Bounded because two rules that each shrink what the other grows would otherwise loop; on exhaustion the verdict is DENY |
| **10** | Where do secrets live? | (a) a separate encrypted file; (b) **Vault, referenced by URI** | **(b)** `[DEFAULT-C10]` | `[CONST]` already mandates HashiCorp Vault. A second secret store is a second thing to rotate, audit and lose. The reference is in the file; the value never is, and never enters the content hash — so rotating a credential does not invalidate a signed policy version |

---

## 2. NON-BLOCKING details resolved

| # | Detail | Resolution |
|---|---|---|
| 1 | Rule id format | `^[A-Z]{2,7}-\d{3}$`. Families: `EXP` exposure, `LOSS`, `SIZE`, `LIQ`, `RATE`, `STOP`, `EXEC`, `HOLD`, `EDGE`, `CASH`, `INST`, `UNIV`, `PORT`, `TURN`, `DATA`, `FX`, `RECON`, `REGIME`, `KILL`, `AUDIT`, `LLM`. **Ids are never reused**, even after a rule is deleted — an id in an old audit record must resolve to one meaning forever |
| 2 | Threshold sources | Exactly one of `threshold` (a constant), `threshold_ref` (another config key, e.g. `universe.US.min_price`), or `threshold_input` (a **measured** bound — `CASH-001` is `intended_notional <= settled_cash`, where writing a constant would be a fiction). A `threshold_input` must also appear in `inputs`, or the fail-closed check cannot see it go missing |
| 3 | Rolling windows | `sessions:N` counts completed exchange sessions; `rolling_seconds:N` / `rolling_days:N` are wall clock and are named explicitly. `RATE-001` uses `rolling_seconds:60`, **not** a fixed minute bucket — a bucket reset permits 40 orders across a boundary |
| 4 | Decimal in YAML | Money and price thresholds are quoted strings (`"5.00"`), parsed to `Decimal`. An unquoted `5.00` is a YAML float, and a float threshold is the float-money bug wearing a different hat |
| 5 | `null` vs absent | `threshold: null` means "this comparison takes no constant" (`in`, `exists`, `multiple_of`). Absent means the same. Neither ever means zero |
| 6 | Canonical hash input | Sorted keys, `Decimal` → string, no insignificant whitespace, UTF-8. Verified: `canonical_bytes({"v": Decimal("0.050")}) == b'{"v":"0.050"}'` |
| 7 | Comment preservation | The YAML carries the **authority** of every value as a comment *and* as a required `authority` field on every rule. The comment is for the human; the field is for the validator, which rejects a rule with no authority |
| 8 | Layer file naming | `policy.yaml`, `policy.market.<US\|IN>.yaml`, `policy.env.<name>.yaml`, `policy.override.yaml`. Absent layer files are simply skipped — a missing market layer is not an error, because the defaults are complete |
| 9 | `layering` cannot be layered | The layering block is read from the **base layer only**. A layer that could rewrite the deny-list would make the deny-list self-defeating |
| 10 | Empty policy dir | `PolicyLoadError`, process does not start. A system that cannot read its limits does not trade |

---

## 3. The rule schema

### 3.1 Every field, and why it exists

| Field | Type | Required | Purpose |
|---|---|---|---|
| `id` | `str` | yes | Stable identity, never reused. Names the binding rule in every audit record |
| `description` | `str` 10–400 | yes | What a human reads at 3 a.m. |
| `authority` | `str` | **yes** | The frozen decision this derives from. **A rule with no authority is a rule someone invented**, and the loader rejects it |
| `scope` | enum | yes | `global` / `strategy` / `market` / `instrument` / `pool` / `consolidated` / `pool_and_consolidated` |
| `mode` | `enforce` \| `monitor` | yes | A monitor rule is evaluated and recorded but does not bind (§4.3) |
| `severity` | `CRITICAL`…`LOW` | yes | Alert routing. **Not** evaluation order (§4.2) |
| `threshold` / `threshold_ref` / `threshold_input` | — | one of | §2 row 2 |
| `comparison` | enum | yes | `lte lt gte gt eq in not_in multiple_of exists` |
| `measurement.basis` | `str` | yes | *What* is measured |
| `measurement.window` | `str` | yes | Over what span — validated against the known set |
| `measurement.timing` | `str` | yes | At what moment |
| `inputs` | `tuple[str]` ≥1 | yes | The exact data the rule needs. Drives the fail-closed check |
| `action` | `ALLOW`\|`DENY`\|`MODIFY`\|`KILL` | yes | What happens on breach |
| `on_missing_input` | `DENY`\|`KILL` | **yes** | §3.4 |
| `modify` | block | if MODIFY | `{target, to}` |
| `kill_scope` | `POOL`\|`GLOBAL` | if KILL | |
| `exempts` | `tuple[str]` | no | Only an `ALLOW` rule may grant exemptions (`KILL-002`) |

### 3.2 A threshold without a window and a timing is not a rule

It is a number. "position ≤ 5%" is read three different ways by three engineers unless all of
`basis`, `window` and `timing` are pinned. `EXP-001` pins them: 5% **of that pool's NAV**,
measured on the **intended post-fill weight**, **before the trade**. Bounds are inclusive —
exactly `0.050` passes; breach is strictly greater.

### 3.3 The `_pct` trap, closed at the type level

P0.3 §15.1 records that its own v0.2 shipped `warn_pct: int = 70`. The failure is silent in the
dangerous direction: `0.70` misread as a percentage is harmless; `70` misread as a fraction is
7,000%. The `Rule` validator rejects any threshold on a `*_pct` basis that is not inside `[0,1]`.
**Verified by test** (`t_integer_percent_on_a_pct_basis_is_rejected`).

### 3.4 Fail-closed is a type constraint, not a convention

`on_missing_input` is typed to `DENY | KILL`. `[CONST-6]` admits nothing else, and a rule that
*could* fail open is not a risk rule. A policy file containing one does not load.

`LOSS-003` and `LOSS-004` are the two rules whose `on_missing_input` is **KILL** rather than DENY,
and the reason is worth stating: if peak NAV cannot be established, the drawdown is *unknown*, and
an unknown drawdown against a kill-switch rule is the one case where halting beats declining a
trade. Every other rule declines the trade.

---

## 4. Precedence and conflict resolution

### 4.1 The action lattice

```
KILL  >  DENY  >  MODIFY  >  ALLOW
```

**The question the prompt asks — MODIFY and DENY both fire — resolves to DENY.** DENY is the more
restrictive answer. Resolving the other way would let a sizing rule talk a denial down into a
smaller trade: a position that breached the 5% cap becomes a legal 4% position and the breach is
never recorded as one. Verified by `t_deny_beats_modify`.

`KILL` beats `DENY` because a kill is a statement about the *book*, not about one order; declining
the order while leaving the book unhalted would be the wrong half of the answer.

### 4.2 The total ordering

Rules are evaluated in **ascending lexicographic rule-id order** `[DEFAULT-C2]`, and **every rule
is evaluated** — no short-circuit `[DEFAULT-C3]`. Within one action, the binding rule is the
lowest id. That makes the audit record byte-reproducible for a given policy version and a given
set of facts.

Severity plays **no part** in ordering. It routes alerts. Ordering on severity would mean editing
a severity reorders the audit record of rules that did not change.

### 4.3 Monitor mode

A `monitor` rule is evaluated, and its outcome is written to the audit record, but it cannot bind
the verdict. `CASH-002` (PDT day-trade counter) is the live example: ADR-12 selects a cash account
where PDT does not apply, so the rule is monitor-only — but the counter is computed and stored
anyway, so it is **proven correct before it ever becomes binding** under a future margin account.
Switching to margin flips `mode` and is a config change, not a code change. That is the whole
reason ADR-13 Chain D specified both counters up front.

### 4.4 Exemptions

Only an `ALLOW` rule may grant them. `KILL-002` exempts kill-switch liquidation from
`CASH-001`, `CASH-002`, `KILL-001`, `HOLD-001`, `TURN-001`, `TURN-002` and `EXEC-001` — a PDT flag
or a good-faith violation is a 90-day inconvenience; an uncontrolled drawdown is permanent.

**It deliberately does not exempt `EXP-*`, `LOSS-*` or `INST-001`.** Liquidation only ever
*reduces* exposure, so those rules cannot bind against it — an exemption there would be dead
scope, and dead scope in an exemption is how an exemption grows.

---

## 5. Versioning, signing and change control

### 5.1 Content hash

SHA-256 over `canonical_bytes()`: sorted keys, `Decimal` as string, no insignificant whitespace,
UTF-8. Order-independent and change-sensitive, both verified by test.

**Secrets are not in the hash input.** `secret_refs` holds references; the referenced values never
enter this computation. Rotating a credential therefore does not invalidate a signed policy
version — which is what makes ADR-09 row 11's 4-hour credential-rotation SLA survivable.

### 5.2 Signature

Ed25519 detached signature over the content hash, public key held in Vault. Verification failure
is `PolicySignatureError` and **the process does not start**: an unverified policy is an unknown
set of limits.

`[DEFAULT-C4]` accepts `cryptography` as a dependency, against `[CONST]`'s "no new dependency that
ten lines of stdlib would cover." The justification is specific: **stdlib `hmac` would cover
integrity but not attribution.** Every holder of a shared HMAC key produces identical signatures,
so under HMAC the statement "two distinct approvers signed this" is unprovable — and §5.3 is
built entirely on that statement.

### 5.3 Who may change what — the two-person rule

| Direction | Approvals | Authority |
|---|---|---|
| **Tighten** a limit | **0** — automatic | ADR-09 row 3: "tightening is always safe" |
| **Loosen** a limit | **2 distinct identities** | This spec, §5.3 |
| **Override a risk DENY** | **Impossible. No approver, no code path** | ADR-09 final row, invariant I2 |

**Direction is judged against the rule's comparison, not the raw number.** Raising a threshold
loosens an `lte` rule and *tightens* a `gte` rule; `PORT-001` (`cash_pct >= 0.20`) is loosened by
*lowering* it. Getting this backwards would let a limit be relaxed down the tightening path, which
needs no approval at all. `loosens_for()` implements it; `t_loosening_direction_respects_comparison`
tests both directions. For a non-ordinal comparison any change is treated as loosening — we cannot
prove it is a tightening, and `[CONST-6]` resolves the ambiguity conservatively.

**Two distinct *identities*, not two approvals.** Two signatures from one person are one person's
judgement twice; the check normalises and de-duplicates. Verified by
`t_two_distinct_approvers_required_to_loosen`, which asserts that `["js", "JS "]` is refused.

**This is stricter than a FROZEN ADR, and that is why it is permitted.** ADR-09 row 2 authorises
the Owner *alone* to increase a limit. Requiring two is a tightening of that control, and ADR-09
row 3 says tightening is always safe and needs no approval — so no constitutional amendment is
required and **none has been made**.

> **Operational consequence, stated rather than discovered.** At team size 1 (`[DEFAULT-3]` of
> P0.1) this makes limit increases **impossible** until a second approver is enrolled. That is
> deliberate and it is safe: every emergency action available to a single operator is a tightening
> or a kill, and both remain unblocked. If the Owner needs to raise a limit, the process is to
> enrol a second approver first — which is the correct process, not an obstacle to it.

### 5.4 How a live change propagates — and deliberately does not

**A policy change never reaches an in-flight decision** `[DEFAULT-C5]`.

1. `RunContext.config_hash` is bound at **run start** and is a foreign key to
   `config_version.config_hash` (SPEC-P1.2 §6.9).
2. Every audit event in that run carries that `run_id`, and therefore that config hash.
3. A new signed policy version is written to `config_version` and takes effect at the **next run
   boundary**.
4. ADR-14 already freezes the order list at pipeline time; re-reading policy at placement time
   would reintroduce the intraday decision path ADR-13 forecloses.

The property this buys: **every decision in an audit record was taken under exactly one set of
limits, and that set is reconstructable by hash.** A config that changed mid-run would leave some
decisions governed by limits that no longer exist anywhere.

**The one exception is tightening, and it is not an exception to the rule above.** A tightening
takes effect at the next run boundary like anything else. What acts immediately is the **kill
switch**, which is infrastructure-level and independent of the policy layer entirely
(`[CONST-7]`) — that is precisely why it is not a policy rule.

---

## 6. Environment layering

```
defaults  →  market  →  environment  →  operator_override
(lowest precedence)                     (highest)
```

Later layers override earlier ones key by key, deep-merged. Verified by
`t_layer_precedence_is_last_wins`.

**The operator_override layer is deny-listed for `rules.`, `governance.` and `kill_switch.`**
`[DEFAULT-C6]`. A denied key raises `PolicyLayerError` and the process does not start. It is a
load failure rather than a silent drop because an operator who *tried* to override a limit is
information the audit trail should hold.

The `Layering` model validates its own shape: `defaults` must be lowest, `operator_override` must
be highest, no layer may repeat, and `rules.` must be in the deny-list. A policy that relaxed any
of those does not load.

---

## 7. No risk number from the environment — three enforcements

**The rule:** a risk number comes from `policy.yaml`. Nothing else. Not an environment variable,
not a module constant, not a literal at a call site.

| # | Enforcement | Mechanism |
|---|---|---|
| **1** | **Single loader** | `PolicyLoader` is the only reader of the policy file. `PolicyGate` takes an `EffectiveConfig`; it does not load one |
| **2** | **Lint** | `lint_no_env_risk_reads()` **AST-scans** every `.py` under `src/`. Text-searching for `os.environ` would miss `from os import environ` and would false-positive on the string in a comment. The AST sees the call — all three forms (`os.environ[...]`, `os.getenv(...)`, bare `environ.get(...)`) are caught |
| **3** | **Test** | `tests/verify_p13_config.py::t_lint_finds_no_violation_in_src` fails CI on any violation. `t_lint_catches_a_planted_violation` proves the lint is not vacuous by planting each of the three forms in turn and asserting each is caught |

The allowlist is **six infrastructure names**, none of which is a risk number:
`TRADING_DB_URL`, `TRADING_VAULT_ADDR`, `TRADING_VAULT_ROLE`, `TRADING_ENV`,
`TRADING_POLICY_PATH`, `TRADING_POLICY_SIGNATURE_PATH` — where the database is, where Vault is,
which layer to load. `infra_env()` is the only sanctioned reader and refuses any name outside that
set, so adding one is a reviewed change to a constant rather than a new `os.getenv` somewhere.

Two files may touch `os.environ` at all: `src/config/loader.py` and `src/config/env.py`. Any
other file doing so is a lint failure regardless of which variable it reads.

---

## 8. Secrets

**Syntax:** `vault://<mount>/<path>#<key>` — e.g. `vault://kv/data/trading/alpaca#api_key`.

**Resolution:** at load, through the Vault client, using the role named by `TRADING_VAULT_ROLE`.
Resolved values are held in memory only. They are **never** written to the effective-config dump,
**never** logged, and **never** part of the content-hash input (§5.1).

**A literal secret in the policy file is a load failure.** `assert_not_a_literal_secret()` rejects
base64-shaped blobs, `sk-`/`api_`-prefixed tokens and bare hex strings ≥32 chars, and the check
runs over **every value in the merged document**, not only under `secret_refs`. The heuristic is
deliberately shaped to catch the paste rather than to prove absence: a false positive is a
one-line move to Vault; a false negative is a credential in git history for the life of the
repository.

---

## 9. The effective-config dump

At run start, after layering and validation, `EffectiveConfig.audit_payload()` is written to the
audit log as an `event_class = SYSTEM` event, carrying:

| Field | Purpose |
|---|---|
| `policy_version` | Human-readable version |
| `content_hash` | The value bound into `RunContext.config_hash` (§5.4) |
| `layers_applied` | Which layers actually contributed — a missing market file is visible here |
| `rule_count` / `enforced_rule_count` | The two differ whenever a rule is in monitor mode; equal counts would mean nothing is being monitored, which is itself worth seeing |
| `effective_config` | The fully-merged, **redacted** document |

Because the dump precedes any decision and carries the same hash the run is keyed by, an
investigator reading a decision six years later can reconstruct the exact limits it was taken
under — which is what `[CONST-5]` is for.

---

## 10. The rule inventory

**47 rules.** 45 `enforce`, 2 `monitor`. By action: 37 `DENY`, 6 `MODIFY`, 3 `KILL`, 1 `ALLOW`
(the `KILL-002` exemption). By severity: 27 `CRITICAL`, 12 `HIGH`, 7 `MEDIUM`, 1 `LOW`.

| Family | Ids | Covers |
|---|---|---|
| `EXP` | 001–006 | Position 5%, sector 20%, gross 2×, net 1×, account-type gross 1.0×, 7.5% forced trim |
| `LOSS` | 001–004 | Daily 2%, weekly 5%, pool drawdown 10% → KILL, consolidated drawdown 10% → GLOBAL KILL |
| `SIZE` | 001–002 | Risk per trade 1%, round-down to increment |
| `LIQ` | 001 | 1% of 20-session median ADDV |
| `RATE` | 001–002 | 20 orders/min global, 10 per strategy |
| `STOP` / `EXEC` | 001 each | `entry − 2.5×ATR(14)`; limit default, market only for emergency exit |
| `HOLD` / `EDGE` | 001–003 / 001 | 3-session floor, 40-session time stop, 120-session hard max; 2× cost edge floor |
| `CASH` | 001–002 | Settled-cash sizing; PDT counter (monitor) |
| `INST` | 001–002 | Deny-by-default allowlist; ACTIVE-only |
| `UNIV` | 001–005 | Price, market cap, ADDV, history, reported quarters |
| `PORT` / `TURN` | 001–002 each | 20% cash buffer, 15–25 band (monitor); 4 entries, 20% NAV per session |
| `DATA` / `FX` / `RECON` / `REGIME` | 001–003 / 001 / 001 / 001 | Staleness, bar finality, tick multiple; missing FX blocks both pools; unreconciled blocks the pool; UNKNOWN regime blocks entries |
| `KILL` / `AUDIT` | 001–002 each | Not-ARMED denies; liquidation exemption; audit-write precondition; chain break → GLOBAL KILL |
| `LLM` | 001–003 | No portfolio state; sanitiser required; STANDARD tier only |

**Every one of the thirteen HARD RISK NUMBERS in Block A maps to a rule**, and
`t_const_thresholds_match_the_constitution` asserts each threshold equals the constitutional value
rather than merely existing.

---

## 11. Error paths

| Condition | Exception | Behaviour |
|---|---|---|
| No `policy.yaml` | `PolicyLoadError` | **Process does not start** |
| Malformed YAML, or not a mapping | `PolicyLoadError` | Process does not start |
| Any validation failure | `PolicyLoadError` | Process does not start |
| Signature missing when required | `PolicySignatureError` | Process does not start |
| Signature or hash mismatch | `PolicySignatureError` | Process does not start |
| `operator_override` touches a denied prefix | `PolicyLayerError` | Process does not start |
| Loosening with < 2 distinct approvers | `PolicyGovernanceError` | Change refused |
| Malformed `vault://` reference | `VaultReferenceError` | Process does not start |
| Literal secret anywhere in the document | `VaultReferenceError` | Process does not start |
| Env read outside the allowlist | `RiskNumberFromEnvError` | CI failure |
| A rule input is absent at evaluation | *(no exception)* | `rule.on_missing_input` — DENY or KILL |
| The evaluator raises | *(no exception)* | Treated as an ambiguous state → `on_missing_input` |
| `MODIFY` loop exceeds `MAX_MODIFY_PASSES` | — | Verdict is DENY |

Note the split in the last three rows: a **load-time** problem raises and stops the process; an
**evaluation-time** problem produces a fail-closed verdict and is recorded. The system must be
able to say "I denied this and here is why", which it cannot do if the risk engine crashed.

---

## 12. Verification

`tests/verify_p13_config.py` — **39/39 PASS**, against the real `config/policy.yaml`.

| Group | What it proves |
|---|---|
| Load | The real file loads; 47 rules; hash is 64 hex |
| Constitution coverage | All 13 Block A risk numbers have a rule, **and each threshold equals the constitutional value** |
| Fail-closed | Every rule's `on_missing_input` ∈ {DENY, KILL}; a fail-open rule is rejected by the model |
| `_pct` trap | An integer `70` on a `*_pct` basis is rejected |
| Immutables | `risk_deny_override_permitted: true` is rejected; `min_approvals_to_loosen: 1` is rejected; requiring approval to tighten is rejected |
| Two-person rule | Direction respects comparison in both directions; one approver refused; the same person twice refused; two distinct identities accepted |
| Layering | Override of `rules.` / `governance.` / `kill_switch.` all refused; an operational knob accepted; last-wins precedence |
| Hash & signature | Order-independent, change-sensitive; `Decimal` hashes as string; signature required by default; round-trip verifies; wrong hash and wrong key both refused |
| Secrets | Vault syntax accepted and five malformed forms refused; three literal-secret shapes refused; the dump carries references, never values |
| **Gate precedence** | **DENY beats MODIFY**; KILL beats DENY; ties break by rule id; monitor records without binding; missing facts fail closed for all 47 rules; an evaluator exception fails closed; every rule appears in the outcome record |
| §7 lint | No violation in `src/`; a planted violation is caught in **all three** syntactic forms; `infra_env` refuses a non-allowlisted name |

**The validator earned its keep during authoring.** It rejected two real defects in this phase's
own `policy.yaml` on first run: `CASH-001` declared `comparison: lte` with no threshold — the rule
compares against *measured* settled cash, which the schema had no way to express, and which
produced the `threshold_input` field; and `FX-001` failed the rule-id pattern, which had assumed
a minimum of three letters in a family name.

---

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | **DENY beats MODIFY** | Otherwise a sizing rule negotiates a denial into a smaller trade and the breach is never recorded as one | No | **Critical** — it is the difference between a limit and a suggestion |
| 2 | **Evaluation order is rule id, not severity or file order** | Stable for the life of the rule, so a policy version's audit record is byte-reproducible; severity ordering would reorder records when a severity is edited | Yes | High — a non-reproducible audit record is not an audit record |
| 3 | **No short-circuit; every rule evaluated** | "Which other limits would also have failed" is what an investigator needs. Cost is 47 evaluations against a 60 s stage budget | Yes | Medium |
| 4 | **`on_missing_input` is typed to DENY\|KILL** | `[CONST-6]` admits nothing else. A policy containing a fail-open rule does not load | No | **Critical** |
| 5 | **`LOSS-003`/`LOSS-004` fail to KILL, not DENY** | An unknown drawdown against a kill-switch rule is the one case where halting beats declining | No | High |
| 6 | **Ed25519, accepting `cryptography` as a dependency** | A shared-secret MAC cannot attribute a signature to an individual, and §5.3 is built on exactly that attribution | Yes | Medium — the alternative is abandoning the two-person rule |
| 7 | **Two distinct approver identities to loosen; zero to tighten** | Stricter than ADR-09 row 2, permitted because ADR-09 row 3 makes tightening always safe. Consequence at team size 1 stated in §5.3 | Yes | Medium — blocks limit increases until a second approver exists, which is the intent |
| 8 | **Direction judged against the rule's comparison** | Raising a threshold loosens `lte` and tightens `gte`. Getting it backwards routes a loosening down the no-approval path | No | **Critical** |
| 9 | **`operator_override` may not touch `rules.`/`governance.`/`kill_switch.`; a denied key is a load failure** | An operator who can loosen a limit at runtime has defeated `[CONST-1]` and ADR-09 | No | **Critical** |
| 10 | **Config is bound at run start; a change never reaches an in-flight decision** | Every decision in an audit record was taken under exactly one reconstructable set of limits | No | High |
| 11 | **Secrets excluded from the hash input** | Credential rotation must not invalidate a signed policy version, or ADR-09 row 11's 4-hour SLA is unsurvivable | Yes | Medium |
| 12 | **Lint is AST-based, not textual** | Text search misses `from os import environ` and false-positives on comments | Yes | Medium — a vacuous lint is worse than none |
| 13 | **Monitor mode evaluates and records without binding** | A rule never evaluated cannot be promoted to enforce with confidence. `CASH-002` proves the PDT counter before margin makes it binding | Yes | Low |
| 14 | **Only an ALLOW rule may grant exemptions, and `KILL-002` does not exempt `EXP-*`/`LOSS-*`** | Liquidation only reduces exposure, so those rules cannot bind against it; dead scope in an exemption is how an exemption grows | Yes | Medium |
| 15 | **`authority` is a required field on every rule** | A rule with no authority is a rule someone invented. The loader rejects it | No | High |
| 16 | **`threshold_input` for rules bounded by a measured value** | `CASH-001` is `notional <= settled_cash`; a constant there would be a fiction | Yes | Low |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|---|---|---|---|
| 1 | `[DEFAULT-C4]` `cryptography` is acceptable despite `[CONST]`'s dependency rule | The two-person rule requires attribution, which a stdlib MAC cannot give | Owner ratification of the dependency | Fall back to HMAC and abandon per-approver attribution — i.e. abandon the two-person rule as a *provable* control |
| 2 | `[DEFAULT-C7]` Two approvers is the right number | The prompt requires a two-person rule; ADR-09 names one | Owner decision | If 1 is correct, `min_approvals_to_loosen` drops to 1 and the `Governance` validator relaxes. Note the validator currently *forbids* 1, so this is a deliberate one-way door |
| 3 | India universe thresholds (`min_price_inr`, ranks) | `[RS §4]` gives market cap and ADDV for India but not a price floor or hysteresis ranks; ADR-14 gives the *shape* | ADR-11's India activation gate; NSE listing statistics | India is unfunded, so nothing live depends on it. Wrong values would mis-size the India universe on the day the gate opens — **Q-P1.3-2** |
| 4 | `MAX_MODIFY_PASSES = 4` is enough | No rule pair currently oscillates; 4 is headroom over the 2 passes any current combination needs | P2.9 integration; assert the pass count never exceeds 2 in practice | If a future rule pair oscillates, the verdict is DENY — fail-closed, but a silently un-tradeable name. Instrument the pass count |
| 5 | Ed25519 public key is retrievable from Vault at boot | `[CONST]` mandates Vault; the retrieval path is P6.2's | P6.2 | If Vault is unreachable at boot the process does not start — correct, and consistent with ADR-09 row 11's fail-closed halt |
| 6 | `assumed_round_trip_bps` 25 US / 90 IN | ADR-13 Chain F, labelled ASSUMPTION there | P5.3, after ≥200 **live** fills (rule N11 excludes paper) | `EDGE-001` gates on it. Too low → trades that do not clear cost; too high → no trades. Measurement-by-design **Q13** |

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|---|---|---|---|
| **Q-P1.3-1** | Who is the second approver, and how is their identity bound to a signing key? | Owner | Enrol a second Ed25519 key pair in Vault under a distinct identity | **Any limit increase.** Not blocking P1.4 — tightening and kill both work at team size 1 |
| **Q-P1.3-2** | India universe price floor and hysteresis ranks | `[RS §4]` gives cap and ADDV only | NSE listing statistics at the ADR-11 activation gate | India activation. Unfunded, so not blocking |
| **Q-P1.3-3** | Does the `RISK` stage's 60 s budget hold with 47 rules evaluated without short-circuit, across ~20 candidates? | Measurement in P2.9 | Time `PolicyGate.evaluate()` over a full candidate set | **P2.9.** 47 in-memory comparisons per candidate should be sub-millisecond, but P0.3 §6.1 sets the budget and it should be measured rather than assumed |
| **Q-P1.3-4** | Should `PORT-002` (15–25 position band) be `enforce` rather than `monitor`? | Observation after 20 live sessions | Count sessions where the open-position count leaves the band | P6.6. Promoting it is a tightening — no approval needed (ADR-09 row 3) |
| **Q13** *(carried)* | Round-trip transaction cost | P5.3, ≥200 live fills | Measured slippage + fees, paper excluded (N11) | Feeds `EDGE-001` |
| **Q-P1.1-1** *(carried)* | US settlement cycle and good-faith rules | Broker documentation | Feeds `CASH-001`'s `settled_cash` semantics | **P2.9** |

## CONTRACTS EXPORTED

| Name | Kind | Signature or schema | Consumers |
|---|---|---|---|
| `config/policy.yaml` | file | 47 rules + the frozen config keys from P0.1 §10.2 and P0.3 §14.4 | P2.9, P2.10, every phase that reads a limit |
| `PolicyLoader.load()` | method | `(market?, environment?, signature?, public_key_pem?, require_signature=True) -> EffectiveConfig` | P2.9, P6.4 |
| `EffectiveConfig` | model | `policy_version`, `content_hash`, `layers_applied`, `document`, `redacted` | P2.9, P1.4 |
| `EffectiveConfig.audit_payload()` | method | The `SYSTEM` audit event written at run start (§9) | P1.4, P6.1 |
| `PolicyDocument` | model | Validated whole file; `rule(id)`, `evaluation_order()` | P2.9 |
| `PolicyDocument.evaluation_order()` | method | Deterministic total order, id-ascending | **P2.9** — the ordering contract |
| `Rule` | model | §3.1's fields; `binds` property for monitor mode | P2.9 |
| `PolicyGate.evaluate()` | method | `(facts, evaluator) -> PolicyVerdict`; evaluates all rules, never short-circuits | **P2.9** |
| `PolicyVerdict` | model | `action`, `binding_rule_id`, `kill_scope`, `modifications`, `outcomes`, `permits_trade` | P2.9, P2.10, P1.4 |
| `RuleOutcome` | model | Per-rule record incl. the fail-closed reason — the audit payload | P1.4 |
| `ACTION_PRECEDENCE` | constant | `(KILL, DENY, MODIFY, ALLOW)` | P2.9 |
| `content_hash()` / `canonical_bytes()` | functions | The bytes the signature covers | P1.4, P6.4 |
| `assert_change_authorised()` | function | The two-person rule | P6.2, P6.4 |
| `loosens_for()` | function | Direction relative to a rule's comparison | P6.2 |
| `merge_layers()` | function | Layering with the operator deny-list | P6.4 |
| `VaultRef` | model | `vault://<mount>/<path>#<key>` | P6.2 |
| `lint_no_env_risk_reads()` / `assert_no_env_risk_reads()` | functions | The §7 lint | **CI**, P6.4 |
| `infra_env()` | function | The only sanctioned environment read | P6.2, P6.4 |
| `INFRA_ENV_ALLOWLIST` | constant | Six infrastructure names, no risk numbers | P6.2 |
| Rule ids `EXP-001`…`LLM-003` | identifiers | Stable, never reused; named in every audit record | P2.9, P1.4, P6.1, P6.3 |

---

**END OF SPEC-P1.3-CONFIG v0.1**
