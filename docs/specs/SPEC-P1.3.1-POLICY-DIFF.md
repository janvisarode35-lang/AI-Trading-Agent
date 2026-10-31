---
id: SPEC-P1.3.1-POLICY-DIFF
version: 0.3.4
status: FROZEN
phase: P1.3.1 — Policy diff and the two-person rule over every field (issue #6; STAGE-1-GAP-AUDIT condition 12; X5R-G2, X5R-G9). Step 1 of #6's execution sequence (spec run), revised after the step-2 X2 review, the step-2b, step-2c and step-2d delta reviews, and the step-2e narrow review
depends_on: [SPEC-P1.1-DOMAIN v0.3, SPEC-P1.2-STORAGE v0.5, SPEC-P1.3-CONFIG v0.1 (§5.3 as amended by d8067b6), SPEC-P1.4-AUDIT v0.1 (event catalogue and jcs-nonum-1 only), SPEC-P0.1-DECISIONS v0.3 (ADR-09), STAGE-1-GAP-AUDIT §9 and §10 (at 4397c4f), DECISIONS.md "Owner rulings — X5 conditions 3, 12, 13, 14" (ratified 2026-10-16)]
produces: [src/config/policy_diff.py, fn.diff_policies, fn.derive_combinations, fn.diff_policy_dirs, fn.authorisation_digest, fn.assert_policy_change_authorised, fn.assert_authorisation_current, fn.action_direction, fn.rule_action_direction, fn.scope_direction, fn.key_direction, class.PolicyDiff, class.PolicyChange, class.ApprovalSignature, class.PolicyAuthorisation, class.PolicyDiffError, class.StaleAuthorisationError, class.InForceAnchorError, class.ApprovalExpiredError, class.InForceStore, enum.Direction, enum.ChangeKind, enum.KeyDirection, const.MARKETS, const.IN_FORCE_STORE, const.VAULT_RESOLVER, const.APPROVAL_DIGEST_TAG, const.APPROVAL_TTL_HOURS, const.ACTION_LADDER, const.HALT_ENTRIES_RULES, const.SCOPE_NARROWER_THAN, const.CONFIG_KEY_DIRECTIONS, const.RULE_FIELDS, const.CLASSIFICATION_BASES, tests/verify_p13_policy_diff.py, tests/mutate_x5r_g9.py, tests/mutate_policy_diff_code.py, AMENDMENT SPEC-P1.3 §5.3]
supersedes: SPEC-P1.3.1-POLICY-DIFF v0.3.3 DRAFT (uncommitted, narrow-reviewed in step 2e); v0.3.2 DRAFT (uncommitted, delta-reviewed in step 2d); v0.3.1 DRAFT (uncommitted, delta-reviewed in step 2c); v0.3 DRAFT (commit 8b850ae, delta-reviewed in step 2b); v0.2 DRAFT (uncommitted, reviewed in step 2); v0.1 DRAFT (commit d8067b6)
frozen_by: Owner, 2026-10-31 (issue #6 step 3)
---

# SPEC-P1.3.1 — Policy diff, and the two-person rule over every field

> **In one line:** the change list and the set of configurations it covers are derived from the
> policy files, never supplied by the person asking for approval; every change is classified by
> Owner Ruling 12; anything the diff cannot classify needs two people; and an approval is valid
> only for the exact version it was diffed against.

**FROZEN at v0.3.4 by the Owner, 2026-10-31 (#6 execution sequence, step 3).** X1 implements this text
and nothing beyond it. v0.2 was reviewed by X2 in a separate session: FIX-THEN-SHIP, 1 BLOCKER, 4 HIGH, 7
MEDIUM, 5 LOW. v0.3 (8b850ae) addressed all of them (§0.4). The step-2b delta review of v0.3 found
no BLOCKER and one new HIGH (X2D-1), plus X2D-2 to X2D-6; v0.3.1 addressed all six (§0.5). The
step-2c delta review of v0.3.1 closed all six and found no BLOCKER and no HIGH, plus X2E-1 to
X2E-6; v0.3.2 addressed them (§0.6). The step-2d delta review of v0.3.2 found no BLOCKER, 4 HIGH, 4
MEDIUM and 5 LOW (X2F-1 to X2F-13); v0.3.3 addressed them (§0.8). The step-2e narrow review closed
X2F-1 to X2F-4 and found 1 HIGH, 2 MEDIUM and 5 LOW (X2G-1 to X2G-8); this version addresses them
(§0.9). That reviewer judged that no further spec review is needed and that the code X2 (step 4) can
confirm these fixes. §10 item 12 was done in the commit that froze this spec.
The code and tests committed in d8067b6 implement v0.1, not this version.

---

## 0. Governing material

### 0.1 What binds this phase

| Requirement | Source | Discharged in |
|---|---|---|
| A change loosens if it widens the permitted set | Ruling 12 (DECISIONS.md; full text #16 comment 6221092946) | §3.1 |
| Threshold direction depends on `comparison` | Ruling 12, `threshold` row | §3.5 C-01 to C-07 |
| Moving down the action ladder loosens; `HALT_ENTRIES` must be ranked | Ruling 12 `action` row; Ruling 14; #6 comments 6221094775 and 6222485680 | §3.2, B2 |
| `enforce` → `monitor` always loosens | Ruling 12, `mode` row | §3.5 C-11 |
| Any `comparison` change is UNDECIDABLE and fails closed to LOOSENS | Ruling 12, `comparison` row | §3.5 C-08 |
| Narrowing `scope` loosens, widening tightens | Ruling 12, `scope` row | §3.3, [DEFAULT-B4] |
| Rule removal always loosens; rule addition never loosens | Ruling 12, removal and addition rows | §3.6 |
| `severity` never loosens on its own; judged on any accompanying action change | Ruling 12, `severity` row | §3.5 C-14, C-15 |
| UNDECIDABLE is a real fourth outcome and is never passed as neutral | Ruling 12 | §3.1, §5 |
| Pin `threshold`, `action`, `mode`, `comparison`, `scope` of every constitutional rule | Ruling 12, "Required tests" | §7.2 |
| Pin `scope` and `mode` for all 47 rules | Ruling 12, "Required tests" | §7.2 |
| The five X5R-G9 mutations must each make a test fail | Ruling 12; STAGE-1-GAP-AUDIT §9 | §7.3 |
| `require()` only, no bare `assert`; suites hold under `python -O` | #6 prompt; `tests/verify_p11_x5_conditions.py` | §7.1 |
| A test counts only if it fails when the thing it tests is broken | #6 PO/BA pass, step 5 | §7.1, §7.3, §7.5, §7.7 |
| An exposure-reducing action is never blocked by a missing, stale or ambiguous input; "reducing" is computed by the risk engine | Ruling 13a (A-14) | §1 B1, §9 F-5 |
| Within one action, the binding rule is the lowest id | SPEC-P1.3 §4.2 (FROZEN); loader.py `_combine` | §1 B5, §3.6 C-40, §9 F-14 |
| Tightening needs no approval | ADR-09 row 3 (SPEC-P0.1 §3) | §3.1, §6 |
| Adding or removing an `InstrumentType` needs Owner approval | ADR-09 row 7 | §3.7, DECISION 21 |
| A limit increase has a 24 h SLA; on expiry the request is denied | ADR-09 row 2 | §5.3, DECISION 23 |
| `config_version` is the stored record of applied versions; a run binds one `config_hash` | SPEC-P1.2 §6.9; SPEC-P1.3 §5.4 | §1 B6, §5.3 |
| `min_approvals_to_loosen ≥ 2`, `min_approvals_to_tighten = 0` | SPEC-P1.3 §5.3, `Governance` validator | §5 |
| An approval is attributable to one individual (Ed25519, not a shared MAC) | SPEC-P1.3 §5.2, DECISION 6 | §5.2 |
| A live change never reaches an in-flight decision | SPEC-P1.3 §5.4 | §5.5 |
| Every decision is written to the audit trail before it takes effect; payloads are `jcs-nonum-1` (no JSON numbers) | `[CONST-5]`; SPEC-P1.4 §6.2 | §5.4 |

### 0.2 What this phase is not

- **Not code.** `src/config/policy_diff.py` and the tests are regenerated by X1 from this frozen
  version.
- **Not the loader.** Defects in `src/config/loader.py` (§9) belong to SPEC-P1.3 v0.2. This spec
  states what the diff assumes about them, and where a loader defect makes a ruling row unsound, it
  closes the hole in the diff with a fail-closed derived record (B3, B5) until the loader is fixed.
- **Not the gate.** Which rules bind against an exposure-reducing order is P2.9's question
  (Ruling 13a). This spec governs who may change a rule, not how the gate applies it.
- **Not the HALT_ENTRIES action itself.** Ruling 14 adds it to the DSL in #17. This spec only ranks
  it (§3.2).
- **Not key enrolment.** Who the second approver is, and how their key reaches Vault, is
  Q-P1.3.1-1 / P6.2. This spec states how an enrolled key is checked (§5.2).

### 0.3 What changed from v0.1, and why

v0.1 was written by a run that never saw Ruling 12. Where it conflicts with the ruling, the ruling
wins. The full list, each tied to the ruling line, is in the step-1 change note in
`AI-Trading-Agent-stage1-fresh-reviews/X5R-G9/` (outside the repository).

| # | Ruling 12 says | v0.1 / d8067b6 did | v0.2 and v0.3 do |
|---|---|---|---|
| a | **Any** `comparison` change is UNDECIDABLE | Judged comparison and threshold as one interval: `lte→lt` and `lte→eq` were TIGHTENS (zero approvals); `eq→lte` was LOOSENS | Any comparison change is UNDECIDABLE, and so is every other predicate field changed with it (C-08) |
| b | Pin `scope` and `mode` for **all 47 rules** | Pinned 20 rules only (v0.1 DECISION 8) | All 47 pinned for `scope` and `mode`; 20 pinned for all five attributes (§7.2) |
| c | The action ladder ranks `HALT_ENTRIES` | Ladder `KILL > DENY > MODIFY > ALLOW` | Ladder includes `HALT_ENTRIES`; its position against `DENY` is BLOCKING question B2 |
| d | `severity` never loosens on its own | Severity downgrade was LOOSENS | NEUTRAL alone; takes the direction of an accompanying action change (C-14, C-15) |
| e | Rule addition never loosens | Addition of an exemption-granting rule was LOOSENS; a `pre_exit` addition was UNDECIDABLE | An addition is TIGHTENS or NEUTRAL. Effects on *other* rules are derived records: exemptions (C-36, B3) and kill-scope displacement (C-40, B5) |
| f | Narrowing scope loosens, widening tightens | Pool family only; every other pair UNDECIDABLE without a reason | A defined narrowness order, and a stated reason for each of the 19 pairs it cannot order (§3.3, B4) |
| g | Threshold direction depends on comparison only | Exit-path overlay on a hand-kept rule set | No overlay in the body; the overlay is BLOCKING question B1 |
| — | Rule removal always loosens | Removal of KILL-002 was UNDECIDABLE | LOOSENS (C-33) |
| — | `enforce→monitor` always loosens | On an exemption-granting rule it was UNDECIDABLE | LOOSENS (C-11) |

### 0.4 What changed from v0.2, and why (step-2 X2 review)

Review: `AI-Trading-Agent-stage1-fresh-reviews/X5R-G9/STEP2-X2-SPEC-REVIEW.md`. Every Ruling 12 row
is unchanged. Each fail-open path the review measured is closed without changing a ruled row's
output, by a derived record or a precondition.

| Finding | Sev | v0.3 change | Where |
|---|---|---|---|
| X2S-1 | BLOCKER | A change that lets a rule take a KILL ahead of an existing GLOBAL kill now emits a derived UNDECIDABLE record (C-40), so it is two-person. New BLOCKING question B5 with that fail-closed default; root fix recommended for SPEC-P1.3 v0.2. §7.4's C-09, C-12, C-16 cases corrected; new cases and code mutation M-13. §6 amendment qualifies "adding a rule never loosens". New F-14, F-15 | §1 B5, §3.6, §6, §7.4, §7.7, §9 |
| X2S-2 | HIGH | The combination set is derived from the two policy directories (`derive_combinations`), never supplied. An unknown market layer fails closed | §5.1, §5.3 |
| X2S-3 | HIGH | An authorisation is applied only if, at the moment the `config_version` row is written, every combination's in-force hash still equals the diffed `old_content_hash` and the candidate still hashes to `new_content_hash` (`assert_authorisation_current`, a compare-and-swap) | §5.3, §8 |
| X2S-4 | HIGH | A mutation counts as killed only if a *named* pin fails with a message naming the mutated rule and field, in both modes. A negative control (pins stubbed) must report every mutation SURVIVED | §7.3, §7.5, §7.7, §10 |
| X2S-5 | HIGH | B1's "What breaks" restated: TURN-002 and its config key, `holding.min_sessions`, and added DENY rules can block a protective exit at **zero** approvals; 13a does not cover a threshold breach. New carried requirement for P2.9 (Q-P1.3.1-11) | §1 B1, DECISION 7, ASSUMPTION 1 |
| X2S-6 | MEDIUM | `required_approvals` is a decimal-integer string; a test canonicalises a real authorisation through P1.4's `canonical_json` | §4, §7.4 |
| X2S-7 | MEDIUM | B2 cites #6 comment 6221094775 and names the ratified full text (#16) as option (b); recommending (a) is stated as an amendment of a ratified ruling | §1 B2, §0.1, F-11 |
| X2S-8 | MEDIUM | `action_direction` and `scope_direction` return their basis; the coverage test counts those, so C-10 is reachable | §4, §5.1, §7.4 |
| X2S-9 | MEDIUM | A new or retired combination is diffed against what the loader would have produced for it; the layer file itself is a `LAYER_ADDED` / `LAYER_REMOVED` record, UNDECIDABLE (C-41) | §3.8, §5.1 |
| X2S-10 | MEDIUM | Each approval is an Ed25519 signature over `authorisation_digest`, verified against that identity's enrolled key; distinct identities *and* distinct keys are required | §4, §5.2 |
| X2S-11 | MEDIUM | `CONFIG_KEY_DIRECTIONS` gives a direction to exact keys only; the sole wildcard is the final `**` | §3.7 |
| X2S-12 | MEDIUM | Condition-12 text rewritten for the state at 4397c4f (OPEN, reopened); the "reopen now" text and Q-P1.3.1-8 removed | §9 F-13, §10 |
| X2S-13 | LOW | C-35's rationale reworded; a C-36 case with a monitor-mode grantor added | §3.6, §7.4 |
| X2S-14 | LOW | `verify_p13_config.py` runs under `--must-pass`, and must exit 0 on every mutation | §7.3 |
| X2S-15 | LOW | Validators added to the type block; §8 gains a catch-all row | §4, §8 |
| X2S-16 | LOW | ADR-09 row 7 stated; removing an `InstrumentType` stays TIGHTENS, and the departure is recorded with the condition that keeps it safe | §3.7, DECISION 21, ASSUMPTION 12 |
| X2S-17 | LOW | Closure text states Ruling 12's requirement | §10 |

### 0.5 What changed from v0.3, and why (step-2b delta review)

Review: `AI-Trading-Agent-stage1-fresh-reviews/X5R-G9/STEP2b-X2-DELTA-REVIEW.md`. Verdict on v0.3:
FIX-THEN-SHIP, no BLOCKER; X2S-1 closed and re-measured; 15 of 17 step-2 findings closed, X2S-3
and X2S-10 partly closed. Their residues are X2D-1 and X2D-2.

| Finding | Sev | v0.3.1 change | Where |
|---|---|---|---|
| X2D-1 | HIGH | The compare-and-swap no longer takes any caller-supplied reference. "In force" is read by this module from the authoritative stored record, on the writer's own transaction. **No frozen spec defines such a record** (SPEC-P1.2 §6.9 `config_version` has no per-combination in-force marker), so this is **BLOCKING question B6**, with a fail-closed default: until the store exists in a frozen spec, every apply fails with `InForceAnchorError`. Q-P1.3.1-13 asks P1.2 / P6.4 for the store. New §7.4 case (B passes v1's directory after A is applied → refused); M-15 now means "anchor read from a directory"; new F-16 | §1 B6, §5.1, §5.3, §8, §9, §10 item 10, ASSUMPTION 10 |
| X2D-2 | MEDIUM | The `public_key_for` parameter is removed. Keys come from one fixed source: the identity → Vault-reference map `governance.signature.approver_key_refs` in the **in-force** document. The frozen loader already accepts that map (measured); a change to it is UNDECIDABLE (two-person). Keys are compared as raw 32-byte Ed25519 keys, not PEM bytes. The enrolment bootstrap this creates at team size 1 is **BLOCKING question B7** (fail-closed default) | §1 B7, §2 row 11, §5.2, §8, Q-P1.3.1-14 |
| X2D-3 | MEDIUM | Each authorisation carries `request_id` and `requested_at`, both inside the signed digest. The writer refuses to apply it more than 24 h after `requested_at`, measured on the database clock (ADR-09 row 2), and writes `APPROVAL_EXPIRED` | §4, §5.1, §5.3, §5.4, DECISION 23 |
| X2D-4 | LOW | C-40 also fires when R reads a config key through `threshold_ref` / `allowed_values_ref` and any config record in the diff is non-NEUTRAL, and when a C-26 shrink removes R from a grantor's `exempts` | §3.6, §7.4, M-21 |
| X2D-5 | LOW | The approval digest preimage starts with the fixed tag `APPROVAL_DIGEST_TAG = "SPEC-P1.3.1 approval v1\n"` | §4, §5.1, M-20 |
| X2D-6 | LOW | §7.5's expected test for a `scope` or `mode` mutation on a constitutional rule is either `t_pin_<R>` or `t_scope_and_mode_pinned_for_every_rule` | §7.5 |

### 0.6 What changed from v0.3.1, and why (step-2c delta review)

Review: `AI-Trading-Agent-stage1-fresh-reviews/X5R-G9/STEP2c-X2-DELTA-REVIEW.md`. Verdict on v0.3.1:
FIX-THEN-SHIP, no BLOCKER, no HIGH; X2D-1 to X2D-6 closed. The reviewer asked that X2E-1, X2E-3 and
X2E-4 be fixed before the Owner answers B6 and B7, because they change what those two questions
ask. These fixes change no Ruling 12 row, classification or default; the Owner's answers, which do
change C-09 and C-10, are in §1. Each fix was re-measured on `config/policy.yaml` on 2026-10-31.

| Finding | Sev | v0.3.2 change | Where |
|---|---|---|---|
| X2E-1 | MEDIUM | B6's store holds a row for every combination the in-force files derive. A combination that exists only because this change adds its env file is anchored by the stored row of (m, None): the two are one effective document with one hash (measured). Any other combination with no row raises | §1 B6, §5.3, §7.4, §8, M-23 |
| X2E-2 | MEDIUM | B6's required shape gains `previous_config_hash` and a store-side constraint, so the store enforces the compare-and-swap even if the Python call is skipped. The adapter is named `IN_FORCE_STORE`, and a new AST test keeps it out of `src/` | §1 B6, §4, §7.6, M-22, Q-P1.3.1-13 |
| X2E-3 | MEDIUM | B7 is restated for both steps, 0→1 and 1→2: zero identities are listed today (measured, F-17), so the first entry cannot be approved under any option v0.3.1 offered. ASSUMPTION 16 corrected | §1 B7, §9 F-17 |
| X2E-4 | MEDIUM | B7 (b) is allowed once, ever: it is refused if the history holds any earlier bootstrap or any version listing two or more identities. It is named an amendment of ADR-09 that adds a row, not a row 12 action | §1 B7 |
| X2E-5 | LOW | §5.3's failure sentence now separates expiry from every other failure. `requested_at` must be a real time, not only the right shape | §4, §5.3, §7.4, M-24 |
| X2E-6 | LOW | The clock tolerance is stated: zero, in both checks. P6.2's tooling takes `requested_at` from the database when the request opens | §5.2, §7.4, ASSUMPTION 18 |

Found while making these fixes, beyond the review:

- **A retired combination had no end state.** After an env file is removed, its row stayed current,
  and every later apply would fail §5.3's combination-set check. B6's shape now closes that row.
- **The store's constraint had no valid first insert.** The store's first rows are now a defined
  genesis, outside the approval path (§0.7).
- **§5.2 relied on a loader path that does not exist.** `loader.py` parses `vault://` references but
  has no resolver. The resolver is now this module's `VAULT_RESOLVER`, `None` until P6.2.
- **B2's evidence was understated.** #17 comment 6221174702 gives both wordings in one sentence, and
  #37 comment 6221220445 also writes the chain. No record writes it the other way (F-11).

**One departure from the review's wording.** X2E-3 suggested a bootstrap of "the Owner plus,
optionally, the second approver". This spec requires both. With `min_approvals_to_loosen` at 2, a
map listing only the Owner could never grow, and it would spend the one bootstrap X2E-4 allows.

### 0.7 What changed from the DeepSeek run of the same step

DeepSeek was given this step independently, on v0.3.1 (chat `a93a093a-9fd2-48c8-b85c-2fdc9adea39e`,
2026-10-31). It first declined, reading B7 (b) as a way to fake two-person approval. Told that the
default is no bootstrap, it did everything except write bootstrap text, as was agreed with it. Each
point below was tested against this spec and `loader.py` before it was adopted. The full record is
`AI-Trading-Agent-stage1-fresh-reviews/X5R-G9/STEP3-DEEPSEEK-COMPARISON.md`.

| DeepSeek's point | Outcome | Where |
|---|---|---|
| The first apply on an empty store can never pass | **Adopted.** The store's first rows are a *genesis* written by P6.4's first deployment, outside the approval path. An empty store raises `InForceAnchorError` | §1 B6, §5.3, §7.4, §8 |
| The first rows must be told apart from B7's bootstrap | **Adopted**, and tightened: a genesis version may list no approver, pinned by `t_no_approver_is_listed`, so a map cannot enter by that door | §1 B6, §7.2 |
| A bootstrap signed by a listed key is circular; it needs B6 | **Adopted.** It is signed with the existing policy key, which is outside the map, and cannot run before the store exists | §1 B7 |
| One bootstrap, ever, freezes the map if an approver is lost for good | **Adopted** as a stated cost of B7 (b). It fails closed | §1 B7 |
| A compromised writer can append a valid-looking row and event | **Adopted** as a stated limit of the store check. Re-verifying signatures is carried, not required here | §1 B6, Q-P1.3.1-13 |
| The store's guarantees need the store's own tests | **Adopted**, carried to P1.2 / P6.4 | Q-P1.3.1-13 |
| `conn` should only reach the store adapter | **Adopted** | §7.6, M-25 |
| The exactly-24-hour boundary is unstated | **Adopted** as a test. "More than" stands, so exactly 24 h passes; DeepSeek proposed the opposite, which would change the spec's words for no gain | §7.4 |
| A retired row blocks reviving an env file | **Already closed** by v0.3.2's closing row. Revival test added | §7.4 |
| `audit_log` may be append-only only by convention | **Partly right; v0.3.2 wrongly called it no defect (X2F-13).** `0001_initial.sql` has no-update, no-delete and no-truncate triggers, but its Finding A note records that `ENABLE ALWAYS` does not protect a hypertable: under replica role, update and delete succeed. The defence there is detection, so B6 now requires a plain table | §1 B6 |
| Compare the anchor with the loader's output for the in-force directory | **Rejected.** A directory chosen by the caller is exactly the hole X2D-1 closed | — |
| Refuse a `conn` by a baked `instance_id` | **Rejected.** It defends against a deliberate writer, who could fake that too. X2E-2's store-side check is the right layer | — |

### 0.8 What changed from v0.3.2, and why (step-2d delta review)

Review: `AI-Trading-Agent-stage1-fresh-reviews/X5R-G9/STEP2d-X2-DELTA-REVIEW.md`. Verdict on v0.3.2:
FIX-THEN-SHIP, no BLOCKER, 4 HIGH. DeepSeek ran the same review independently (chat
`535d5a3d-7705-4b62-a1b1-744805830bd0`) and agreed on X2F-2 (its B-06), X2F-4 (its H-01), X2F-6 (its
B-01), part of X2F-10 and X2F-11 item 3. The record is
`AI-Trading-Agent-stage1-fresh-reviews/X5R-G9/STEP2d-COMPARISON.md`. The Owner's answers stand: every
fix below handles a consequence of an answer, and none changes one.

| Finding | Sev | v0.3.3 change | Where |
|---|---|---|---|
| X2F-1 | HIGH | An approval is single-use. `InForceStore` gains `request_used`, §5.3 refuses a used `request_id`, and the store refuses one too. A reused version keeps its `config_version` row, so a byte-identical revert is possible and a replay is not | §1 B6, §4, §5.3, §6, §7.4, M-26 |
| X2F-2 | HIGH | A `config_version` insert needs an in-force row in the same transaction, and a non-backtest run may bind only the current in-force hash. SPEC-P1.3 §5.4 item 3 is amended to match. New F-18 | §1 B6, §6, §9, §10 item 10, Q-P1.3.1-13 |
| X2F-3 | HIGH | The model checks that `gated_paths`, `required_approvals` and the approval count cohere. §5.3 re-derives the authorisation from `old_dir` and requires it equal `auth`. X2D-1 stays closed: the anchor still comes only from the store. `old_dir` is checked for its effective documents, not its file set (X2G-4) | §4, §5.1, §5.3, §7.4, M-27 |
| X2F-4 | HIGH | The Owner's ladder stands. Because `DENY → HALT_ENTRIES` stops a rule denying exits, `t_halt_entries_rules_are_pinned` allows only the rules Ruling 14 names, and v0.3.4 adds a governance gate (C-42). §3.2 tells #17 to edit that pin. DECISION 3 restated | §3.2, §7.2(f), §7.3 |
| X2F-5 | MEDIUM | New Q-P1.3.1-15: a `HALT_ENTRIES` outcome decides entries only. For an exit, the gate resolves the binding set without it. Carried to #17 | §6, §10 item 13 |
| X2F-6 | MEDIUM | Genesis is one audited transaction, by a named role, only on an empty store and `config_version`, checked by the deployment against the pins, and never re-run by a restore | §1 B6, §7.2(e), Q-P1.3.1-13 |
| X2F-7 | MEDIUM | Each map entry pins its key: `{ref, raw_key_sha256}`, with the value format corrected in v0.3.4 (X2G-1). Rotating a key is a map change, so two-person | §5.2, §7.4, M-28 |
| X2F-8 | MEDIUM | B2's row states again that (a) amends the ratified text. New §10 item 12 requires DECISIONS.md to record it before the freeze | §1, §9 F-11, §10 |
| X2F-9 | LOW | Genesis is one transaction; the previous hash is the one current at the start of the transaction; the store is a plain table | §1 B6 |
| X2F-10 | LOW | Test wording corrected: M-22, M-23, the two AST tests, and a hand-built hash for the (m, None) compare | §7.4, §7.6, §7.7 |
| X2F-11 | LOW | Expiry is checked first. The clock is read after the lock, with `clock_timestamp()`. `ApprovalExpiredError` carries `reason`, and only `EXPIRED` writes an event | §4, §5.3, §5.4, §8 |
| X2F-12 | LOW | Layer-set format, the digest exception, loader errors at apply, `require_signature=False`, the exception's attributes, and the fixture for the five mutations are now stated | §5.1, §5.3, §7.3, §7.4 |
| X2F-13 | LOW | Stale text corrected in §0.6, §0.7 and §10 | those sections |

DeepSeek's points not raised by step 2d:

| Point | Outcome | Where |
|---|---|---|
| Only current rows are returned by `in_force_hashes` (its B-02) | **Adopted** as one line in the docstring. Its `(hash, is_current)` tuple is rejected: a reader that must filter is one more way to get it wrong | §4 |
| `ApprovalExpiredError` must be caught before `StaleAuthorisationError` (its B-04) | **Adopted** | §5.3 |
| One current row per combination needs a unique index (its L-05) | **Adopted** | §1 B6 |
| `derive_combinations` has no old directory at genesis (its H-06) | **Adopted**: `derive_combinations(d, d)` | §1 B6 |
| The Vault module must not be imported by this one (its L-06) | **Adopted** | §7.6 |
| Removing a layer proves nothing if the hash ignores layer names (its H-07) | **Rejected.** A candidate without the file derives three combinations and the authorisation holds six, so §5.3's set check refuses it | — |
| Force two people on Ruling 14's own change (its H-02) | **Rejected.** It contradicts the Owner's answer to B2 | — |
| Add `required_approvals` and `gated_paths` to the digest (its M-02) | **Rejected** as redundant: X2F-3's re-derivation at apply detects any edit | — |
| `t_ladder_agrees_with_gate_precedence` is tautological (its H-05) | **Rejected.** The literal C-09 cases pin the order; M-3 proves it | — |
| Split M-24 (its M-24 note) | **Rejected.** Its premise is false: `strptime` refuses `23:59:60` (measured) | — |
| Remove §5.2's local clock check (its B-03) | **Partly adopted**: named, and labelled an early refusal. Kept, because it refuses a bad request before a key is touched | §5.2 |

### 0.9 What changed from v0.3.3, and why (step-2e narrow review)

Review: `AI-Trading-Agent-stage1-fresh-reviews/X5R-G9/STEP2e-X2-NARROW-REVIEW.md`. Verdict on v0.3.3:
FIX-THEN-SHIP; X2F-1 to X2F-4 closed and X2D-1 still closed, measured on approve, apply, revert and
replay. Two defects came from fixes proposed in step 2d: X2G-1 and X2G-2. DeepSeek ran the same narrow
pass independently (chat `9e825cf9-23a5-4afb-9520-1420a5071214`). The Owner's answers stand. No Ruling 12
row changes.

| Finding | Sev | v0.3.4 change | Where |
|---|---|---|---|
| X2G-1 | HIGH | `raw_key_sha256` is `sha256:<64 lower-case hex>`. Bare hex fails the loader's literal-secret scan, so no map could load; the prefixed form loads (re-measured 2026-10-31). A new test loads the signatures fixture through `PolicyLoader` | §5.2, §7.4 |
| X2G-2 | MEDIUM | The used-request check now runs before expiry, so a replay after 24 h writes nothing. `APPROVAL_EXPIRED` means "presented after expiry", not "this request was refused after verifying it" | §5.3, §5.4, §7.4, M-30 |
| X2G-3 | MEDIUM | Only a named policy-writer role may insert into the store. Its migration revokes INSERT from `app_rw`, and the store's suite tests that | §1 B6, Q-P1.3.1-13 |
| X2G-4 | LOW | §5.3 says plainly that `old_dir` is checked for its effective documents, not its file set, and what that can cost: C-41's record only | §5.2, §5.3 |
| X2G-5 | LOW | Step 7 re-derives through an internal helper, without §5.2's process-clock check | §5.2, §5.3 |
| X2G-6 | LOW | An environment with no env file binds its (m, None) row | §1 B6 |
| X2G-7 | LOW | Three wording gaps in the amendment closed | §6 |
| X2G-8 | LOW | The `HALT_ENTRIES` pin reads the raw mapping of every derived combination, and has a self-check that shows it can fail | §7.2(f) |
| In passing | — | X2F-9 item 1 finished: genesis's null is judged at the start of its transaction | §1 B6 |

DeepSeek's narrow pass:

| Point | Outcome | Where |
|---|---|---|
| R-5: the `HALT_ENTRIES` pin is a test, not a gate; a candidate directory outside the repository never meets it | **Adopted.** New C-42: moving any rule outside `HALT_ENTRIES_RULES` to `HALT_ENTRIES`, from anything but `KILL`, is UNDECIDABLE. Ruling 14's own change stays free | §3.2, §3.5, §4, §7.4, M-29 |
| R-3: "in the database or at process start" lets the weaker one ship | **Adopted**: in the database, with the process check as defence in depth | §1 B6 |
| R-2: a run could claim to be a backtest | **Adopted** as a clause: the exemption reads `run_context.is_backtest`, fixed when the row is inserted | §1 B6, Q-P1.3.1-13 |
| R-6: a late replay writes `APPROVAL_EXPIRED` | **Adopted**, the same defect as X2G-2 | §5.3 |
| R-4: `old_dir` looks like an anchor | **Wording adopted.** Its own conclusion is that a caller cannot choose the anchor, which step 2e measured. Step 7 now says it is a coherence check. Dropping `old_dir` is rejected: the store holds hashes, not the documents §5.2 needs | §5.3 |

---

## 1. BLOCKING questions — and the defaults applied

Each default is used in the body and marked `[DEFAULT-Bn]` there, and listed again in ASSUMPTIONS.
B1 to B4 are v0.2's; B5 is new in v0.3 (X2S-1); B6 and B7 are new in v0.3.1 (X2D-1, X2D-2), and
v0.3.2 restates B6's required shape and B7 (X2E-1 to X2E-4). The X2
reviews' references to "B1–B5" use this numbering.

**Answers, 2026-10-31.** The table after this one keeps each question for the record. B2's and B7's
rows carry evidence and fixes added since they were first put.
`[DEFAULT-Bn]` in the body now means the answered choice.

| # | Answer | By | Note |
|---|---|---|---|
| B1 | **(A)** no overlay | Owner stated no preference, so the default stands under the Owner's delegation of technical decisions | The one answer that is not fail-closed for exits. Q-P1.3.1-11 is therefore a hard requirement on P2.9 (§10 item 11) |
| B2 | **(a)** `KILL > HALT_ENTRIES > DENY > MODIFY > ALLOW` | **Owner** | This **amends** Rulings 12 and 14 as ratified. DECISIONS.md must record it before the freeze (§10 item 12, F-11) |
| B3 | **(b)**, with (d) recommended for SPEC-P1.3 v0.2 | Delegation: fail-closed, reversible, both runs agree | |
| B4 | **(a)**, with (c) recommended for SPEC-P1.3 v0.2 | Delegation: as B3 | |
| B5 | **(a)**, with (d) recommended for SPEC-P1.3 v0.2 | Delegation: as B3 | §10 item 9 applies |
| B6 | **(a)**, in the required shape stated below | Delegation: as B3 | §10 item 10 applies |
| B7 | **(a)** no bootstrap for now | **Owner** | Reopened when a second approver exists. Until then no LOOSENS or UNDECIDABLE change can be approved |

| # | Question | Options | Default applied | What breaks if the default is wrong |
|---|---|---|---|---|
| **B1** | **Exit-path overlay.** Is a change that narrows the permitted set of a rule that can stand between the book and a risk-reducing exit still a TIGHTENS (zero approvals)? No ruling covers this. Ruling 12 says threshold direction depends on comparison. Ruling 13a says an exposure-reducing action is never blocked by a *missing, stale or ambiguous input*; it says nothing about a threshold breach | **(A)** No overlay. Ruling 12 applies as written. Exit protection becomes an explicit P2.9 requirement (Q-P1.3.1-11). **(B)** v0.1's overlay: on an explicit rule set, a would-be TIGHTENS becomes UNDECIDABLE (two people). **(C)** An overlay derived from a per-rule `applies_to: entry \| exit \| both` field once SPEC-P1.3 v0.2 adds it (F-5) | **(A)** `[DEFAULT-B1]`. It is the reading that conforms to Ruling 12; the step-2 review agrees. **It is not the fail-closed choice for exits — (B) is.** The Owner should decide on the blast radius in the next column, which v0.2 understated | Under (A), these need **zero approvals** and pass every pin: (1) TURN-002 0.20→0.02 (C-01). TURN-002 counts `intended_notional` of every order, exits included, and KILL-002 exempts it only for kill-switch liquidation, so on a volatile day it can deny a protective stop-out once 2% of pool NAV has traded. (2) Lowering `turnover.max_nav_traded_pct_per_session`, its config duplicate. (3) Raising HOLD-001's threshold or `holding.min_sessions` (discretionary exits only, per HOLD-001's notes). (4) Adding any enforce DENY rule (C-34). For the constitutional exit-path rules (RATE-001/002, DATA-001, LIQ-001, EXEC-001 including its emergency set) and KILL-002's `exempts`, a tightening is also zero governance approvals but fails a pin, so it needs a reviewed code change: one person, the Owner (ADR-09 row 10), plus an X2. Under (B) or (C), at team size 1 all of these are impossible until a second approver is enrolled |
| **B2** | **Where does `HALT_ENTRIES` rank against `DENY`?** Every record that writes the ladder as a chain gives `KILL > HALT_ENTRIES > DENY > MODIFY > ALLOW`: #6 comments 6221094775 ("Condition 12 — RULED") and 6222485680, #37 comment 6221220445, and #17 comment 6221174702. The prose of the ratified full text (#16 comment 6221092946, twice), DECISIONS.md "Consequential work" and #17 comment 6221093871 puts `HALT_ENTRIES` "between MODIFY and DENY", which would be `KILL > DENY > HALT_ENTRIES > MODIFY > ALLOW`. #17 comment 6221174702 has both in one sentence: "between `MODIFY` and `DENY` on the lattice, which becomes `KILL > HALT_ENTRIES > DENY > MODIFY > ALLOW`". No record writes the chain the other way. DECISIONS.md names the #16 comment as the full text | **(a)** `KILL > HALT_ENTRIES > DENY` (every written chain). **(b)** `KILL > DENY > HALT_ENTRIES` (**the ratified text**). **(c)** Both orders agree on every other pair; leave `HALT_ENTRIES` and `DENY` unordered, so a change between them is UNDECIDABLE | **(c)** `[DEFAULT-B2]`, fail-closed. The permitted sets are genuinely incomparable under Ruling 12's own test: `HALT_ENTRIES` blocks *more* entries (the whole pool for the rest of the period, even after the loss recovers) and permits *more* exits (always, by Ruling 14). If the Owner wants a total order, this spec recommends (a), **which means amending the ratified text**, because the pool-wide, period-long entry block is the stronger control on the side the ladder exists for, and exits are governed by 13a rather than by rank | Under (c), Ruling 14's own change (LOSS-001/002 from DENY to HALT_ENTRIES, #17) is UNDECIDABLE, so it needs two identities: **at team size 1 that blocks #17's policy edit** until B2 is answered or a second approver is enrolled. Under (a) the same change is TIGHTENS and free; under (b) it is LOOSENS. The diff changes in one constant either way (§4) |
| **B3** | **An added rule that grants exemptions.** Ruling 12 says addition never loosens. But `PolicyGate` drops every exempted rule from the binding set, KILL included, and grants exemptions whatever the grantor's mode (F-3). One added ALLOW rule (`exists` on `audit_event_id`, `exempts: [LOSS-003, LOSS-004]`) loads; at a 25% drawdown the gate returns ALLOW where the real policy returns KILL — in `enforce` and in `monitor` mode (measured 2026-10-21) | **(a)** Literal: the addition is NEUTRAL; nothing else is recorded. **(b)** The addition record stays as the addition row says; a derived record per newly exempted rule, `rules.<X>.exempted_by.<G>`, is LOOSENS by Ruling 12's scope row (X no longer covers the orders G passes). **(c)** v0.1: the addition itself LOOSENS (contradicts the addition row). **(d)** Forbid new exemption-granting rules at load (SPEC-P1.3 v0.2 validator) | **(b)** `[DEFAULT-B3]`, fail-closed, plus (d) recommended for SPEC-P1.3 v0.2. (b) applies two ruling rows without changing either | Under (a), one identity — or none, for a monitor-mode grantor — could switch off the kill switch with zero governance approvals; only the pin in §7.2(c) would stop it at CI |
| **B4** | **What does `scope` order?** Ruling 12 reads scope as coverage ("fewer instruments covered means more permitted"). In the schema, scope is the *aggregation cell* a rule is measured over. No scope value names a market or an instrument to filter on | **(a)** Narrowness is containment of evaluation sets: `pool` and `consolidated` are each narrower than `pool_and_consolidated`. Every other pair is UNDECIDABLE with a stated reason (§3.3). **(b)** Treat cell refinement as narrowing. **(c)** SPEC-P1.3 v0.2 adds a per-rule aggregation kind (`additive \| ratio \| property`), which makes the refinement pairs decidable | **(a)** `[DEFAULT-B4]`, fail-closed; (c) recommended for SPEC-P1.3 v0.2. (b) is unsafe: RATE-002 `strategy → global` and EXP-001 `pool → consolidated` both move to a coarser cell, and the first tightens while the second loosens (SPEC-P1.1 §9.3) | Friction only: 19 of 21 pairs need two people, and every scope change already fails the all-47 scope pin |
| **B5** | **KILL scope resolution (new, X2S-1).** SPEC-P1.3 §4.2 (FROZEN) makes the lowest-id rule bind within an action, and `_combine` takes the verdict's `kill_scope` from that rule. A KILL from `on_missing_input: KILL` on a non-KILL rule carries `kill_scope = None`. So a change Ruling 12 classes TIGHTENS — an added KILL/POOL rule, `action` up to KILL, `on_missing_input` → KILL, scope widening, `inputs` growth, `monitor → enforce`, or a tightened predicate on such a rule — can replace LOSS-004's GLOBAL kill with a POOL kill or a kill with no scope. Measured: CASH-001 DENY→KILL/POOL and FX-001 `on_missing_input` → KILL each turn KILL/LOSS-004/GLOBAL into KILL/POOL or KILL/None, pass every pin, and need zero approvals under v0.2. By C-17, GLOBAL → POOL loosens | **(a)** Rows unchanged; a derived record `rules.<G>.kill_displaced_by.<R>`, UNDECIDABLE, for every existing GLOBAL kill rule G that a changed or added rule R can now displace (C-40). **(b)** The review's overlay: reclassify R's TIGHTENS records as UNDECIDABLE (changes the output of ruled rows). **(c)** Nothing: the measured zero-approval kill loosening stands. **(d)** Root fix in SPEC-P1.3 v0.2: a KILL verdict is GLOBAL if any binding KILL outcome's rule has `kill_scope: GLOBAL` or no `kill_scope`; pinned by a gate test | **(a)** `[DEFAULT-B5]`, fail-closed, plus **(d)** recommended for SPEC-P1.3 v0.2; once (d) lands and is pinned, C-40 is removed by a revision of this spec. (a) is UNDECIDABLE rather than LOOSENS because the effect is mixed: where R and G both fire, the verdict narrows from GLOBAL (C-17: loosens); where only R fires, there is a new kill (tightens) | Under (a), every change to a rule that can take a non-GLOBAL KILL ahead of LOSS-004 or AUDIT-002 is two-person, including tightenings of LOSS-003 (constitutional, so already a pin failure). At team size 1 those are impossible until a second approver is enrolled. If the Owner prefers (c), the kill switch can be narrowed from GLOBAL to POOL with zero approvals and a green CI |
| **B6** | **Where is "the version in force" recorded? (new, X2D-1)** The compare-and-swap (§5.3) must compare each combination's diffed `old_content_hash` with the hash actually in force, read from a source the caller cannot choose. SPEC-P1.2 §6.9 `config_version` records applied versions (`config_hash`, `payload`, `applied_at`), but it has no market or environment column and no in-force marker. SPEC-P1.3 §5.4 says only that a new version "takes effect at the next run boundary". No frozen spec says which `config_hash` is in force for a combination | **(a)** Fail closed. `assert_authorisation_current` reads the anchor itself, by a fixed query on the writer's transaction, from the store that a frozen spec (P1.2 / P6.4) defines for "in-force `config_hash` per (market, environment)". Until that spec exists, the function raises `InForceAnchorError` for every authorisation, so **no policy change can be applied through this path**. **(b)** Infer "in force" from existing data: the latest `config_version` row by `applied_at` whose `payload` matches the combination, or the `config_hash` of the latest `run_context` for the market. **(c)** v0.3: the caller passes an `in_force_dir` (the X2D-1 hole) | **(a)** `[DEFAULT-B6]`, fail-closed, with Q-P1.3.1-13 asking P1.2 / P6.4 for the store. Required shape: **(1) Rows.** A plain table, not a hypertable, because `ENABLE ALWAYS` does not protect a hypertable (`0001_initial.sql`, Finding A). One current `config_hash` for **every** combination `derive_combinations(d, d)` derives from the in-force directory d, including (None, None) and each (None, e), so a combination is never absent because nothing runs it (X2E-1). At most one row per combination is current, enforced by a unique index, not by a trigger alone. **(2) Closing.** A combination the applied version no longer derives gets a closing row in the same transaction, so it stops being current. **(3) Compare-and-swap.** Each row carries `previous_config_hash` and `request_id`. A database constraint or trigger rejects an insert whose `previous_config_hash` is not the hash current **at the start of the transaction** for that combination (for a combination new in the change, for its (m, None) combination), requires a `CONFIG_CHANGED` event citing the same `request_id` in the transaction, and refuses a `request_id` used by any earlier transaction (X2E-2, X2F-1, X2F-9). **(4) Reused versions.** A version whose hash is already in `config_version` is reused, not re-inserted, and the in-force row is still written, so a byte-identical revert can be applied (X2F-1). **(5) Nothing runs outside it (X2F-2).** A `config_version` insert requires an in-force row for that hash in the same transaction, genesis apart, by a deferred constraint. A non-backtest run may bind only the current in-force hash of its (market, environment), refused in the database, with a process-start check as defence in depth. An environment with no env file binds its (m, None) row, the same document (X2G-6). Backtests are exempt, because they legitimately rebind old versions; the exemption reads `run_context.is_backtest`, which is fixed when the row is inserted. **(6) The limit.** This stops a skipped or misdirected call. It does not stop a writer who forges the `CONFIG_CHANGED` event: that boundary is the approvers' signatures, which can be re-verified from the event's payload. **(7) Genesis (X2F-6, X2F-9).** The store's first rows are its genesis, written outside the approval path by P6.4's first deployment, in one transaction: one row per combination, each with a null `previous_config_hash`, naming the signed policy version and its commit. A null is accepted only in the one transaction that first populates the store: both the store and `config_version` were empty at the start of that transaction, and `audit_log` holds no earlier genesis event. Only a named deployment role may write it; `app_rw` gets no such grant. It writes its own audit event in that transaction. P6.4 loads every combination of the deployed directory and refuses any listed approver (F-17), and refuses a directory whose hash differs from the file at the named commit, or a commit where `tests/verify_p13_policy_diff.py` does not exit 0. A disaster-recovery restore restores the store and never re-runs genesis. Genesis is not B7's bootstrap. **(8) After genesis**, rows are written only in the transaction that inserts or reuses the `config_version` rows, under the policy-change lock, with their history kept, append-only, and only by a named policy-writer role. The store's migration revokes INSERT from `app_rw`, which default privileges would otherwise grant (X2G-3). (b) is rejected: `payload` carries no combination key, and `run_context` records the past, not what is deployed. Either would be this spec inventing semantics for a frozen table. (c) reopens X2S-3 | Under (a), no policy change can be applied by the approval path until P1.2 / P6.4 define the store. Nothing is live yet (no writer exists; P6.4 is unwritten), so today that costs nothing. It does make the store a hard prerequisite for the first policy change after go-live. If (a) is wrong because the Owner prefers an inferred anchor (b), stale-base undo (X2S-3) becomes possible wherever the inference picks the wrong row |
| **B7** | **How is the first approver map installed? (new, X2D-2; restated in v0.3.2, X2E-3, X2E-4)** Approver keys are read from the in-force policy's `governance.signature.approver_key_refs` (§5.2). That map does not exist today: `governance.signature` is `{algorithm, public_key_ref, required}`, so **zero** identities are listed (measured, F-17). Adding the first entry is C-38 "added", UNDECIDABLE, and needs two approvals counted against an empty map. Adding a second to a map of one needs two approvals from one identity. So both steps, 0→1 and 1→2, are impossible through the approval path | **(a)** No bootstrap. The map stays empty. **(b)** One bootstrap, **once ever**. A single reviewed code-and-policy deployment (ADR-09 row 10) by the Owner installs the first map, naming the Owner **and** the second approver together, signed with the existing policy key (`governance.signature.public_key_ref`), which is outside the map, and recorded as its own audit event. It cannot run before the B6 store exists, because its refusal reads that store's history. It is authorised by an amendment of ADR-09 that adds a row for it; enrolling an approver is not itself a row 12 item. It is refused if the in-force history (the B6 store, append-only, with `config_version.payload` for the maps) holds any earlier bootstrap event or any version whose map listed two or more identities, so a map that shrinks back cannot bootstrap again (X2E-4). A map naming the Owner alone is refused: it would spend the one bootstrap and could never grow. **(c)** Keep approver keys outside the policy (Vault only, P6.2) and trust Vault's own access control | **(a)** `[DEFAULT-B7]`, fail-closed. Choosing a bootstrap path is an Owner decision about who may create an approver. This spec recommends **(b)**: it is a single, audited, Owner-only event that cannot recur. It costs nothing today, because it needs the B6 store and a second person, and neither exists yet. Its later cost: if one of two approvers is lost for good, the map cannot change, and gated changes stop until the Owner amends ADR-09 again. That fails closed, and enrolling three people reduces it. Under (b) the rule is specified with the B6 store (Q-P1.3.1-14); no code in this spec implements it | Under (a), no LOOSENS or UNDECIDABLE change can ever be approved, because no approver can ever be listed. That is already the effective state today (Q-P1.3-1 is open); (a) only makes it permanent until the Owner rules. Tightenings and the kill switch are unaffected |

---

## 2. NON-BLOCKING details resolved

| # | Detail | Resolution |
|---|---|---|
| 1 | Rule count | **47** rules, counted from `config/policy.yaml` at HEAD (4397c4f; unchanged since d8067b6): 45 `enforce`, 2 `monitor` (CASH-002, PORT-002); 37 DENY, 6 MODIFY, 3 KILL, 1 ALLOW. Agrees with SPEC-P1.3 §10 and Ruling 12's "47" |
| 2 | Which rules are "constitutional" | A rule whose `authority` contains `[CONST` or `IMMUTABLE`: **20 rules** (§7.2). Wider than Block A's 13 hard numbers; wider is the fail-closed reading |
| 3 | Float vs Decimal | YAML parses `0.050` as a float. Both sides are compared as `Decimal(str(v))`. `0.050 → 0.05` is no change; `20 → 20.0` is a recorded change classified NEUTRAL |
| 4 | Inclusive bounds | Strictness lives in the comparison; any comparison change is UNDECIDABLE (C-08) |
| 5 | An `eq` threshold that moves | `{a} → {b}`: neither contains the other, so UNDECIDABLE (C-03) |
| 6 | Threshold on `in`, `not_in`, `exists`, `multiple_of` | These take no constant (SPEC-P1.3 §2 row 5). Any threshold change on one is UNDECIDABLE (C-04) |
| 7 | Value sets | `inputs`, `exempts`, `allowed_values`, `allowed_values_emergency`, `disallowed_values` and set-valued config keys compare as sets. Reordering is not a change. Members are compared by their canonical string, so a mixed-type set (`[true, "X"]`) never needs a native sort |
| 8 | Lists of mappings in config | `hitl.actions` and `latency.stages` flatten by index; their leaves are unlisted keys, so any change is UNDECIDABLE |
| 9 | Absent vs `null` | Absent is `CONFIG_ADDED` / `CONFIG_REMOVED`. A value changed to `null` is a value change; a numeric check on `null` fails, so UNDECIDABLE |
| 10 | Renamed rule | Ids are never reused (SPEC-P1.3 §2 row 1). A rename is a removal (LOOSENS, C-33) plus an addition |
| 11 | Approver identity | Strip, lower-case, drop empties; must match `^[a-z0-9][a-z0-9._-]{0,63}$` after normalisation. `["js", " JS"]` is one person. Two identities whose enrolled public keys are equal **as raw 32-byte Ed25519 keys** are one approver (§5.2). PEM bytes are never compared: the same key with different line endings is still one key (X2D-2, measured) |
| 12 | Empty diff | Zero changes → zero approvals. A re-signed identical document is not a policy change |
| 13 | Record order | Changes sort by `(path, field or "", basis)`; diffs sort by `(market or "", environment or "")`. The record is byte-reproducible |
| 14 | Time | No change record carries a timestamp. Time lives in the P1.4 audit envelope (UTC `occurred_at`) |
| 15 | Units and numbers | A change record carries no unit and no JSON number. Every field is a string or an enum value, so it canonicalises under P1.4's `jcs-nonum-1` |
| 16 | Monitor rules | Classified as if they bound, as in v0.1: otherwise loosen-in-monitor then promote is two free steps |
| 17 | ALLOW rules without exemptions | Classified by the same rows, though they cannot bind a verdict |
| 18 | Interpreter | Every suite runs with and without `python -O`, on `py -3.11` locally and Python 3.12+ in CI (condition 15) |
| 19 | KILL-002's predicate | `eq` with no comparand; the loader accepts it (F-8). Any predicate change on it is UNDECIDABLE by C-08 or C-04 |
| 20 | Which combinations exist | `({None} ∪ MARKETS) × ({None} ∪ E)`, where `MARKETS = ("US", "IN")` (SPEC-P1.1 `Market`) and `E` is every `<name>` with a `policy.env.<name>.yaml` in the old or the new directory. `policy.override.yaml`, when present, applies to every combination. 3 × 1 = 3 combinations today |
| 21 | String order of rule ids | Python `str` ordering, the same order `PolicyDocument.evaluation_order()` uses. `AUDIT-001 < AUDIT-002 < … < LOSS-003 < LOSS-004 < PORT-001` |

---

## 3. Classification rules

### 3.1 The principle

Ruling 12: **a change loosens if it widens the permitted set** — the set of orders, positions or
states the policy lets through. It tightens if it narrows that set, is neutral if the set is
unchanged, and is **UNDECIDABLE** when the diff cannot prove either. UNDECIDABLE is a real outcome,
not an error, and for approval it counts as LOOSENS.

How this spec applies it, in order:

1. Where Ruling 12 has a row for the field, the row decides that field's record.
2. Where it has no row, its principle decides, but only when the effect on the permitted set is
   provable from the documents alone.
3. Otherwise the change is UNDECIDABLE, and the reason is written into the record.
4. Where a change to one rule alters what **another** rule does — an exemption (C-36), a displaced
   GLOBAL kill (C-40) — that effect is a separate, derived record against the other rule. The
   ruled record is never overwritten.

This spec adds no principle the ruling does not state. That is why B1 has no overlay, while B3 and
B5 have derived records: those apply the ruling's own scope row and C-17 to the rule actually
affected.

**Direction is never inferred from the raw number.** `LimitChange.loosens` raising
`NotImplementedError` is correct (loader.py §8).

### 3.2 The action ladder, including `HALT_ENTRIES`

```
KILL  >  HALT_ENTRIES  >  DENY  >  MODIFY  >  ALLOW
```

The order of `HALT_ENTRIES` and `DENY` is the Owner's answer to B2.

| Pair (old → new) | Direction | Basis |
|---|---|---|
| Same value | NEUTRAL | C-09 |
| Up the ladder | TIGHTENS | C-09 |
| Down | LOOSENS | C-09 |
| To `HALT_ENTRIES`, on a rule outside `HALT_ENTRIES_RULES`, from anything but `KILL` | UNDECIDABLE | C-42 |
| Either value not in `ACTION_LADDER` | UNDECIDABLE | C-10 |

**How the diff ranks `HALT_ENTRIES` before it exists.** The ladder is defined over action values
(strings). A policy that uses `HALT_ENTRIES` today fails `PolicyDocument` validation, so the diff
raises `PolicyDiffError` and authorises nothing (§8). When #17 adds the member, the diff needs no
change, but #17 must edit `t_halt_entries_rules_are_pinned` (§7.2(f)) in that reviewed change. The ladder
ranks entries. A `DENY → HALT_ENTRIES` move narrows entries, yet exits are always permitted under
`HALT_ENTRIES` (Ruling 14), so on any other rule it would stop that rule denying exits (X2F-4). The
Owner's answer stands, and on LOSS-001 and LOSS-002, the rules Ruling 14 names, it is C-09: TIGHTENS. On
any other rule neither direction is provable, so it is UNDECIDABLE (C-42). `action_direction` still
returns the bare ladder; `rule_action_direction` applies C-42. The pin stops it at CI, and C-42 stops it
at governance for a candidate directory CI never saw. `t_every_action_is_ranked` (§7.6) fails CI if `RuleAction` gains a value the ladder lacks.
`action_direction()` returns `(Direction, basis)` so C-09 and C-10 are tested now (§7.4).

The gate's `ACTION_PRECEDENCE` (SPEC-P1.3 §4.1) is a separate total order for binding, which #17
must extend. `t_ladder_agrees_with_gate_precedence` requires the two to agree on every pair the
ladder orders.

### 3.3 The scope narrowness order `[DEFAULT-B4]`

**Definition.** Scope A is *narrower* than scope B when every evaluation a rule performs under A is
also performed under B. Two strict relations:

```
pool          ─┐
               ├──<  pool_and_consolidated
consolidated  ─┘
```

ADR-15 §4 (`risk_evaluation.stricter_binds: true`, IMMUTABLE) makes `pool_and_consolidated`
evaluate both, with the stricter binding. Moving to it widens (TIGHTENS, C-12); moving away narrows
(LOOSENS, C-12); the same scope is NEUTRAL (C-12).

**Every other pair is UNDECIDABLE (C-13), for one of four reasons.**

| Reason | Meaning |
|---|---|
| **R1 Refinement** | One scope's cells partition the other's. An additive count against an upper bound acts *more* on the coarser cell (RATE-002 `strategy → global`); a ratio to the cell's NAV acts *less* (EXP-001 `pool → consolidated`, SPEC-P1.1 §9.3). The schema does not say which |
| **R2 Crossing** | The cells overlap without nesting (a strategy is confined neither to one instrument nor, by any frozen spec, to one pool) |
| **R3 Same cells, different basis** | `market`/`pool`, and `global`/`consolidated`, name the same cells but different measurement bases; equality is not provable |
| **R4 Disjoint evaluation sets** | `pool_and_consolidated` evaluates the pool and consolidated cells; the other scope evaluates a cell that is neither |

| # | Pair | Order | Reason |
|---|---|---|---|
| 1 | `pool` – `pool_and_consolidated` | `pool` narrower | containment (C-12) |
| 2 | `consolidated` – `pool_and_consolidated` | `consolidated` narrower | containment (C-12) |
| 3 | `global` – `strategy` | none | R1 |
| 4 | `global` – `market` | none | R1 |
| 5 | `global` – `instrument` | none | R1 |
| 6 | `global` – `pool` | none | R1 |
| 7 | `global` – `consolidated` | none | R3 |
| 8 | `global` – `pool_and_consolidated` | none | R4 |
| 9 | `strategy` – `market` | none | R2 |
| 10 | `strategy` – `instrument` | none | R2 |
| 11 | `strategy` – `pool` | none | R2 |
| 12 | `strategy` – `consolidated` | none | R1 |
| 13 | `strategy` – `pool_and_consolidated` | none | R4 |
| 14 | `market` – `instrument` | none | R1 |
| 15 | `market` – `pool` | none | R3 |
| 16 | `market` – `consolidated` | none | R1 |
| 17 | `market` – `pool_and_consolidated` | none | R4 |
| 18 | `instrument` – `pool` | none | R1 |
| 19 | `instrument` – `consolidated` | none | R1 |
| 20 | `instrument` – `pool_and_consolidated` | none | R4 |
| 21 | `pool` – `consolidated` | none | R1 |

**For B4 option (c) only, not applied:** with a declared aggregation kind, a refinement pair becomes
decidable — additive with an upper bound: coarser TIGHTENS; additive with a lower bound: coarser
LOOSENS; ratio to the cell's NAV: coarser LOOSENS (a weighted average acts less); property of one
instrument: UNDECIDABLE.

Note that a C-12 TIGHTENS on a rule that can take a non-GLOBAL KILL still produces a C-40 record
(§3.6): LOSS-003 `pool → pool_and_consolidated` is the measured case.

### 3.4 Joint changes

| Changed together in one rule | Classification |
|---|---|
| `comparison` and any of `threshold`, `threshold_ref`, `threshold_input`, `allowed_values`, `disallowed_values`, `allowed_values_ref` | Every one of those records is UNDECIDABLE (C-08) |
| `action` and `severity` | The severity record takes the action record's direction (C-15) |
| `action` to or from `MODIFY`, with `modify` appearing or disappearing | The `modify` record takes the action record's direction (C-18) |
| `action` to or from `KILL`, with `kill_scope` appearing or disappearing | The `kill_scope` record takes the action record's direction (C-18). C-40 is evaluated independently (§3.6) |
| `action` of KILL-002 away from `ALLOW` | The loader requires `exempts` to be emptied in the same change; each record is classified on its own row |

### 3.5 Every `Rule` field, for a rule present in both versions

`RULE_FIELDS` must equal `set(Rule.model_fields)` (§7.6). Each row has a basis id carried on every
record it produces.

| Basis | Field | Condition | Direction | Authority / reasoning |
|---|---|---|---|---|
| **C-01** | `threshold` | Comparison unchanged and `lte` or `lt`; both constants | higher **LOOSENS**; lower **TIGHTENS**; same number NEUTRAL | Ruling 12: raising an `lte` bound loosens |
| **C-02** | `threshold` | Comparison unchanged and `gte` or `gt`; both constants | higher **TIGHTENS**; lower **LOOSENS**; same number NEUTRAL | Ruling 12: raising a `gte` bound tightens. Applies to HOLD-001 and EDGE-001 like any other `gte` rule `[DEFAULT-B1]` |
| **C-03** | `threshold` | Comparison unchanged and `eq`; values differ | UNDECIDABLE | `{a}` and `{b}` are disjoint |
| **C-04** | `threshold` | Comparison is `in`, `not_in`, `exists` or `multiple_of`; threshold appears, disappears or changes | UNDECIDABLE | These comparisons take no constant |
| **C-05** | `threshold` / `threshold_ref` / `threshold_input` | The threshold source switches | UNDECIDABLE on each changed field | A constant cannot be ordered against a value read elsewhere |
| **C-06** | `threshold_ref` | Repointed | UNDECIDABLE | The referenced key is classified on its own (§3.7) |
| **C-07** | `threshold_input` | Changed | UNDECIDABLE | A different measured bound |
| **C-08** | `comparison` | **Any change** | UNDECIDABLE, and every predicate field changed with it (§3.4) | Ruling 12 `comparison` row |
| **C-09** | `action` | Both values on the ladder (§3.2) | down **LOOSENS**; up **TIGHTENS**; same NEUTRAL | Ruling 12 `action` row |
| **C-10** | `action` | A value outside the ladder | UNDECIDABLE | Fail closed |
| **C-42** | `action` | To `HALT_ENTRIES` from anything but `KILL`, on a rule outside `HALT_ENTRIES_RULES` | UNDECIDABLE | Entries narrow, exits widen (Ruling 14). Ruling 12's principle cannot prove either. Takes precedence over C-09. `KILL → HALT_ENTRIES` stays C-09: LOOSENS |
| **C-11** | `mode` | `enforce → monitor` | **LOOSENS**, on every rule | Ruling 12 `mode` row: always |
| C-11 | `mode` | `monitor → enforce` | **TIGHTENS** | The rule now binds |
| **C-12** | `scope` | Containment pair or same scope (§3.3) | widening **TIGHTENS**; narrowing **LOOSENS**; same NEUTRAL | Ruling 12 `scope` row |
| **C-13** | `scope` | Any other pair | UNDECIDABLE; R1 to R4 in the record | `[DEFAULT-B4]` |
| **C-14** | `severity` | `action` unchanged | **NEUTRAL** | Ruling 12: reporting metadata, not a control |
| **C-15** | `severity` | `action` also changed | the action record's direction | Ruling 12 |
| **C-16** | `on_missing_input` | Ladder `KILL > DENY` (and §3.2 for any future value) | `KILL → DENY` **LOOSENS**; `DENY → KILL` **TIGHTENS** | Principle. A `DENY → KILL` on a rule that sorts before a GLOBAL kill rule also produces C-40 |
| **C-17** | `kill_scope` | `KILL` on both sides | `GLOBAL → POOL` **LOOSENS**; `POOL → GLOBAL` **TIGHTENS** | A global halt stops a superset of what a pool halt stops |
| **C-18** | `kill_scope`, `modify` | Appear or disappear with an action change to or from `KILL` / `MODIFY` | the action record's direction | §3.4 |
| **C-19** | `kill_scope` | Appears or disappears on a rule that is not `KILL` on both sides | UNDECIDABLE | SPEC-P1.3 §3.1 defines it only for `KILL` |
| **C-20** | `allowed_values` | `in` on both sides, comparison unchanged | grow **LOOSENS**; shrink **TIGHTENS**; both ways UNDECIDABLE | Under `in` the set *is* the permitted set |
| **C-21** | `allowed_values` | Any other comparison | UNDECIDABLE | `eq` with a set has no stated set semantics |
| **C-22** | `disallowed_values` | `not_in` on both sides, comparison unchanged | grow **TIGHTENS**; shrink **LOOSENS**; both ways UNDECIDABLE | The deny-set is the complement of the permitted set |
| **C-23** | `disallowed_values` | Any other comparison | UNDECIDABLE | |
| **C-24** | `allowed_values_emergency` | Any | grow **LOOSENS**; shrink **TIGHTENS** `[DEFAULT-B1]`; both ways UNDECIDABLE | The permitted set for an emergency exit |
| **C-25** | `allowed_values_ref` | Any change | UNDECIDABLE | A repointed reference |
| **C-26** | `exempts` | Any | grow **LOOSENS** (plus C-36 records); shrink **TIGHTENS** `[DEFAULT-B1]`; both ways UNDECIDABLE | An exemption narrows the exempted rule's coverage (Ruling 12 scope row) |
| **C-27** | `inputs` | Any | superset **TIGHTENS**; subset **LOOSENS**; swap UNDECIDABLE | Each input is one more fail-closed path. A superset on a rule with `on_missing_input: KILL` that sorts before a GLOBAL kill rule also produces C-40 |
| **C-28** | `measurement.basis` / `.window` / `.timing` | Any change, one record per subfield | UNDECIDABLE | Not monotone in the threshold |
| **C-29** | `modify.to` | Numeric on both sides, same `*_pct` target | higher **LOOSENS**; lower **TIGHTENS** | EXP-006 trimming to 6% instead of 4% trims less |
| **C-30** | `modify.to`, `modify.target` | Symbolic, other numeric, or target changed | UNDECIDABLE | The arithmetic of a symbolic target lives in P2.9 |
| **C-31** | `authority` | Any change | UNDECIDABLE | It keys membership of the pinned constitutional set (§7.2): governance, not reporting |
| **C-32** | `description`, `notes` | Any change | NEUTRAL | Free text |
| — | `id` | — | not a field change | A different id is a removal plus an addition |

### 3.6 Rule addition and removal, and derived records

| Basis | Change | Direction | Authority / reasoning |
|---|---|---|---|
| **C-33** | Rule **removed**, any rule | **LOOSENS** | Ruling 12: removal always loosens |
| **C-34** | Rule **added**, `enforce`, action `KILL`, `HALT_ENTRIES`, `DENY` or `MODIFY` | **TIGHTENS** | Ruling 12: addition never loosens. A `pre_exit` addition is included `[DEFAULT-B1]`. C-40 may also apply |
| **C-35** | Rule **added**, `monitor`, or action `ALLOW` | **NEUTRAL** | The added rule cannot bind a verdict itself: a monitor rule never binds and an ALLOW outcome is never binding. **Any exemption it grants is a separate C-36 record, whatever its mode** — `PolicyGate` grants exemptions from monitor-mode rules too (F-3) |
| **C-36** | **Derived.** The new version contains a pair (G exempts X) that the old version does not — G is new, or G's `exempts` grew — in any mode of G | One `RULE_EXEMPTED` record at `rules.X.exempted_by.G`, **LOOSENS** `[DEFAULT-B3]` | Ruling 12 scope row: X no longer covers the orders G passes |
| **C-40** | **Derived.** A rule R in the new version is *kill-capable below GLOBAL*: `mode: enforce`, (`action: KILL` or `on_missing_input: KILL`), and `kill_scope` not `GLOBAL`. The trigger fires when any of these holds: (1) R is added; (2) R has at least one record in this diff whose direction is not NEUTRAL; (3) R has a `threshold_ref` or `allowed_values_ref`, and any `CONFIG_*` record in this diff is not NEUTRAL (X2D-4 (a)); refs may be templated or unresolvable (F-1), so any config change counts, failing closed; (4) a C-26 shrink in this diff removes R from some rule's `exempts` (X2D-4 (b)). G is a rule present in both versions that, in the old version, is `enforce`, `action: KILL`, `kill_scope: GLOBAL`, and `R.id < G.id` | One `RULE_KILL_DISPLACED` record at `rules.G.kill_displaced_by.R`, **UNDECIDABLE** `[DEFAULT-B5]` | SPEC-P1.3 §4.2 makes R's KILL bind ahead of G's, with R's scope. Where both fire, the verdict narrows from GLOBAL (C-17: loosens); where only R fires, there is a new kill (tightens). Neither contains the other |

C-40 at today's file: the GLOBAL kill rules are AUDIT-002 and LOSS-004. 30 of the 47 ids sort before
LOSS-004, and 1 (AUDIT-001) before AUDIT-002. LOSS-003 is already kill-capable below GLOBAL and
sorts before LOSS-004, so on the unedited policy a LOSS-003 and LOSS-004 co-breach yields
KILL/LOSS-003/POOL (F-14, measured). That is an existing defect, not a change, so it produces no
record. Any non-NEUTRAL change to LOSS-003 does.

### 3.7 Non-rule configuration

Every leaf outside `rules` is classified by `CONFIG_KEY_DIRECTIONS`: an ordered table of **exact
dotted keys** whose last entry is `("**", UNDECIDABLE)`. There is no other wildcard (X2S-11): a key
that does not exist yet, even under a known prefix such as `turnover.`, gets no direction until a
reviewed change lists it. The table below lists the 72 directed keys at today's file (v0.2's 71 plus
`holding.min_sessions`).

| Basis | Change | Direction |
|---|---|---|
| **C-37** | Value change on a listed key | By its `KeyDirection`; a same-number re-representation NEUTRAL |
| **C-38** | Key added or removed | Added: UNDECIDABLE, unless listed `NEUTRAL`. Removed: **LOOSENS**, unless listed `NEUTRAL` |
| **C-39** | An unlisted key, a type change, a set changed by both adding and removing, or a numeric key turned non-numeric or `null` | UNDECIDABLE |

| Kind | Exact keys |
|---|---|
| NEUTRAL (9) | `policy_version`, `metadata.description`, `metadata.authored_by`, `metadata.authored_at`, `cost.verified_monthly_usd.paper`, `cost.verified_monthly_usd.live`, `cost.vm_monthly_usd`, `cost.backup_monthly_usd`, `cost.total_operating_is_complete` |
| TRUE_LOOSENS (5) | `governance.risk_deny_override_permitted`, `hitl.risk_deny_override_permitted`, `kill_switch.auto_re_enable_permitted`, `fx.system_may_convert`, `llm.may_receive_portfolio_state` |
| FALSE_LOOSENS (8) | `kill_switch.requires_human_to_re_enable`, `risk_evaluation.evaluate_per_pool`, `risk_evaluation.evaluate_consolidated`, `risk_evaluation.stricter_binds`, `llm.replay_requires_approval`, `llm.replay_offpeak_only`, `account.enforce_settled_cash`, `account.enforce_day_trades` |
| LOWER_LOOSENS (25) | `governance.min_approvals_to_loosen`, `account.pdt_equity_floor_usd`, `portfolio.min_cash_pct`, `decision.min_edge_multiple_of_cost`, `cost.assumed_round_trip_bps.US`, `cost.assumed_round_trip_bps.IN`, `holding.time_stop_min_return_pct`, **`holding.min_sessions`**, `storage.records_retention_years`, `promotion.min_wf_windows`, `promotion.min_closed_trades`, `promotion.shadow_min_sessions`, `promotion.dsr_threshold`; for each of `US` and `IN`: `universe.<m>.min_addv_position_multiple`, `universe.<m>.min_sessions_history`, `universe.<m>.min_reported_quarters`; `universe.US.min_market_cap_usd`, `universe.US.min_addv_usd_floor`, `universe.US.min_price_usd`, `universe.IN.min_market_cap_inr`, `universe.IN.min_addv_inr_floor`, `universe.IN.min_price_inr` |
| HIGHER_LOOSENS (23) | `account.pdt_max_day_trades_5d`, `portfolio.max_position_pct`, `portfolio.forced_trim_pct`, `turnover.max_new_entries_per_session`, `turnover.max_nav_traded_pct_per_session`, `holding.time_stop_sessions`, `holding.hard_max_sessions`, `llm.gate_width`, `llm.max_concurrency`, `llm.spend_alarm_warn_usd_month`, `llm.spend_alarm_critical_usd_month`, `latency.exit.stale_bar_critical_seconds`, `dr.rpo_state_seconds`, `dr.rto_safe_minutes`, `dr.rto_operational_hours`, `storage.disk_warn_pct`, `storage.disk_critical_pct`; for each of `US` and `IN`: `universe.<m>.max_instruments`, `universe.<m>.enter_rank`, `universe.<m>.exit_rank` |
| SET_GROW_LOOSENS (1) | `instrument_allowlist.tradeable` |
| SET_SHRINK_LOOSENS (1) | `instrument_allowlist.permanently_banned` |
| UNDECIDABLE | `**` — everything else, last entry |

`<m>` is notation in this table only; the constant lists both exact keys. `holding.min_sessions`
duplicates HOLD-001 (`gte 3`) and is classified the same way under `[DEFAULT-B1]`; under B1 option
(B) it returns to the catch-all.

**ADR-09 row 7.** Adding *or removing* an `InstrumentType` needs Owner approval. Here, adding a
type to `tradeable` is LOOSENS (two identities) and removing one is TIGHTENS (zero). The removal is
a recorded departure from row 7 (DECISION 21): every applied policy version must carry a valid
policy signature (SPEC-P1.3 §5.2), and at team size 1 the only enrolled signer is the Owner
(ASSUMPTION 12). If a non-Owner signer is ever enrolled, P6.2 must require an Owner approval for any
`instrument_allowlist` change.

### 3.8 Layer files

| Basis | Change | Direction |
|---|---|---|
| **C-41** | A layer file (`policy.market.<m>.yaml`, `policy.env.<e>.yaml`, `policy.override.yaml`) exists in one directory and not the other | One `LAYER_ADDED` or `LAYER_REMOVED` record, path `layers.market.<m>` / `layers.env.<e>` / `layers.override`, in every combination the file applies to: **UNDECIDABLE** |

The content effect is classified separately: each combination's effective document is diffed
against what the loader produces for that combination from the other directory, which skips absent
layer files (X2S-9). So the first `policy.market.IN.yaml` (ADR-11 India activation) is approvable:
it yields a C-41 record plus a record for every value it changes.

---

## 4. Types

```python
from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Final, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

_RULE_ID = r"^[A-Z]{2,7}-\d{3}$"
_VERSION = r"^\d+\.\d+\.\d+$"
_HASH = r"^[0-9a-f]{64}$"
_BASIS = r"^C-\d{2}$"
_IDENTITY = r"^[a-z0-9][a-z0-9._-]{0,63}$"
_UUID7 = r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
_UTC_SECOND = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
_UTC_SECOND_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class Direction(str, Enum):
    LOOSENS = "LOOSENS"
    TIGHTENS = "TIGHTENS"
    NEUTRAL = "NEUTRAL"
    UNDECIDABLE = "UNDECIDABLE"


class ChangeKind(str, Enum):
    RULE_ADDED = "RULE_ADDED"
    RULE_REMOVED = "RULE_REMOVED"
    RULE_FIELD = "RULE_FIELD"
    RULE_EXEMPTED = "RULE_EXEMPTED"              # derived, C-36 [DEFAULT-B3]
    RULE_KILL_DISPLACED = "RULE_KILL_DISPLACED"  # derived, C-40 [DEFAULT-B5]
    CONFIG_ADDED = "CONFIG_ADDED"
    CONFIG_REMOVED = "CONFIG_REMOVED"
    CONFIG_VALUE = "CONFIG_VALUE"
    LAYER_ADDED = "LAYER_ADDED"                  # C-41
    LAYER_REMOVED = "LAYER_REMOVED"              # C-41


class KeyDirection(str, Enum):
    NEUTRAL = "NEUTRAL"
    HIGHER_LOOSENS = "HIGHER_LOOSENS"
    LOWER_LOOSENS = "LOWER_LOOSENS"
    TRUE_LOOSENS = "TRUE_LOOSENS"
    FALSE_LOOSENS = "FALSE_LOOSENS"
    SET_GROW_LOOSENS = "SET_GROW_LOOSENS"
    SET_SHRINK_LOOSENS = "SET_SHRINK_LOOSENS"
    UNDECIDABLE = "UNDECIDABLE"


_RULE_KINDS = frozenset({ChangeKind.RULE_ADDED, ChangeKind.RULE_REMOVED, ChangeKind.RULE_FIELD,
                         ChangeKind.RULE_EXEMPTED, ChangeKind.RULE_KILL_DISPLACED})
_DERIVED_KINDS = frozenset({ChangeKind.RULE_EXEMPTED, ChangeKind.RULE_KILL_DISPLACED})


class PolicyChange(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: ChangeKind
    path: Annotated[str, Field(min_length=1, max_length=300)]
    rule_id: Annotated[str, Field(pattern=_RULE_ID)] | None
    field: Annotated[str, Field(min_length=1, max_length=80)] | None
    related_rule_id: Annotated[str, Field(pattern=_RULE_ID)] | None = None
    old: str | None
    new: str | None
    direction: Direction
    basis: Annotated[str, Field(pattern=_BASIS)]
    reason: Annotated[str, Field(min_length=1, max_length=600)]

    @model_validator(mode="after")
    def _coherent(self) -> PolicyChange:
        if (self.kind in _RULE_KINDS) != (self.rule_id is not None):
            raise ValueError("rule_id is set iff the change is about a rule")
        if (self.kind is ChangeKind.RULE_FIELD) != (self.field is not None):
            raise ValueError("field is set iff kind is RULE_FIELD")
        if (self.kind in _DERIVED_KINDS) != (self.related_rule_id is not None):
            raise ValueError("related_rule_id is set iff the record is derived")
        added = (ChangeKind.RULE_ADDED, ChangeKind.CONFIG_ADDED, ChangeKind.LAYER_ADDED)
        removed = (ChangeKind.RULE_REMOVED, ChangeKind.CONFIG_REMOVED, ChangeKind.LAYER_REMOVED)
        if self.kind in added and self.old is not None:
            raise ValueError("an addition has no old value")
        if self.kind in removed and self.new is not None:
            raise ValueError("a removal has no new value")
        if self.basis not in CLASSIFICATION_BASES:
            raise ValueError(f"unknown classification basis {self.basis}")
        return self

    @property
    def requires_two_person(self) -> bool:
        return self.direction in (Direction.LOOSENS, Direction.UNDECIDABLE)


def _change_key(c: PolicyChange) -> tuple[str, str, str]:
    return (c.path, c.field or "", c.basis)


class PolicyDiff(BaseModel):
    """The complete change list for ONE (market, environment) combination."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    market: Annotated[str, Field(pattern=r"^(US|IN)$")] | None
    environment: Annotated[str, Field(pattern=r"^[a-z0-9_-]{1,32}$")] | None
    old_version: Annotated[str, Field(pattern=_VERSION)]
    new_version: Annotated[str, Field(pattern=_VERSION)]
    old_content_hash: Annotated[str, Field(pattern=_HASH)]
    new_content_hash: Annotated[str, Field(pattern=_HASH)]
    changes: tuple[PolicyChange, ...]

    @model_validator(mode="after")
    def _ordered(self) -> PolicyDiff:
        keys = [_change_key(c) for c in self.changes]
        if keys != sorted(keys) or len(set(keys)) != len(keys):
            raise ValueError("changes must be unique and sorted by (path, field, basis)")
        return self

    @property
    def requires_two_person(self) -> bool:
        return any(c.requires_two_person for c in self.changes)


class ApprovalSignature(BaseModel):
    """One approver's Ed25519 signature over authorisation_digest(diffs), hex-encoded."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    identity: Annotated[str, Field(pattern=_IDENTITY)]
    signature_hex: Annotated[str, Field(pattern=r"^[0-9a-f]{128}$")]


class PolicyAuthorisation(BaseModel):
    """What was approved: written to the audit trail before the new version takes effect.

    Every field is a string or a model of strings, so it canonicalises under jcs-nonum-1.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    diffs: Annotated[tuple[PolicyDiff, ...], Field(min_length=1)]
    request_id: Annotated[str, Field(pattern=_UUID7)]
    requested_at: Annotated[str, Field(pattern=_UTC_SECOND)]
    digest: Annotated[str, Field(pattern=_HASH)]
    approvals: tuple[ApprovalSignature, ...]
    required_approvals: Annotated[str, Field(pattern=r"^[0-5]$")]
    gated_paths: tuple[str, ...]

    @model_validator(mode="after")
    def _ordered(self) -> PolicyAuthorisation:
        combos = [(d.market or "", d.environment or "") for d in self.diffs]
        if combos != sorted(combos) or len(set(combos)) != len(combos):
            raise ValueError("diffs must be unique and sorted by (market, environment)")
        ids = [a.identity for a in self.approvals]
        if ids != sorted(set(ids)):
            raise ValueError("approvals must be distinct and sorted by identity")
        if list(self.gated_paths) != sorted(set(self.gated_paths)):
            raise ValueError("gated_paths must be distinct and sorted")
        try:
            parsed = datetime.strptime(self.requested_at, _UTC_SECOND_FORMAT)
        except ValueError as exc:
            raise ValueError("requested_at is not a real UTC time") from exc
        if parsed.strftime(_UTC_SECOND_FORMAT) != self.requested_at:
            raise ValueError("requested_at does not round-trip")
        gated = sorted({c.path for d in self.diffs for c in d.changes if c.requires_two_person})
        if list(self.gated_paths) != gated:
            raise ValueError("gated_paths must be the paths of the two-person records")
        if (self.required_approvals == "0") != (not gated):
            raise ValueError("required_approvals is 0 exactly when nothing is gated")
        if len(self.approvals) < int(self.required_approvals):
            raise ValueError("fewer approvals than required")
        return self


#: The two markets (SPEC-P1.1 Market). A market layer file for any other name fails closed.
MARKETS: Final[tuple[str, ...]] = ("US", "IN")
#: Domain separation for approval signatures (X2D-5): prefixed to the digest preimage, so an
#: approval can never be read as a policy signature (SPEC-P1.3 §5.2) or anything else.
APPROVAL_DIGEST_TAG: Final[bytes] = b"SPEC-P1.3.1 approval v1\n"
#: ADR-09 row 2: an approval request expires 24 h after requested_at; on expiry it is denied.
APPROVAL_TTL_HOURS: Final[int] = 24
#: The approval ladder, most restrictive first (the Owner's answer to B2).
ACTION_LADDER: Final[tuple[str, ...]] = ("KILL", "HALT_ENTRIES", "DENY", "MODIFY", "ALLOW")
#: The rules Ruling 14 moves to HALT_ENTRIES. Any other rule moved there is UNDECIDABLE (C-42).
HALT_ENTRIES_RULES: Final[frozenset[str]] = frozenset({"LOSS-001", "LOSS-002"})
#: (narrower, wider). Every other distinct pair is UNDECIDABLE ([DEFAULT-B4]).
SCOPE_NARROWER_THAN: Final[frozenset[tuple[str, str]]] = frozenset(
    {("pool", "pool_and_consolidated"), ("consolidated", "pool_and_consolidated")}
)
#: C-01 .. C-42, each a row of §3.5 to §3.8.
CLASSIFICATION_BASES: Final[frozenset[str]] = frozenset(f"C-{n:02d}" for n in range(1, 43))


class InForceStore(Protocol):
    """The B6 store as this module reads it. Implemented by that store's module and by tests."""

    def in_force_hashes(self, conn: Any) -> Mapping[tuple[str | None, str | None], str]:
        """The current config_hash of every combination with a current row, read on conn.

        Closed rows are never returned, so presence in the mapping means current.
        """
        ...

    def database_time(self, conn: Any) -> datetime:
        """clock_timestamp() on conn, read after the policy-change lock is held, timezone-aware UTC."""
        ...

    def request_used(self, conn: Any, request_id: str) -> bool:
        """True if any in-force row already carries this request_id."""
        ...


#: None until a frozen spec defines the B6 store. Assigned only by that store's module and tests.
IN_FORCE_STORE: InForceStore | None = None
#: None until P6.2 delivers Vault. Takes a vault:// reference, returns an Ed25519 public key in PEM.
VAULT_RESOLVER: Callable[[str], bytes] | None = None
```

Field contract:

| Model.field | Type | Unit / tz | Null? | Valid range | A violation means |
|---|---|---|---|---|---|
| `PolicyChange.kind` | `ChangeKind` | — | no | enum | Model rejects; no change list exists |
| `PolicyChange.path` | `str` | — | no | 1–300. `rules.<ID>`, `rules.<ID>.<field>`, `rules.<X>.exempted_by.<G>`, `rules.<G>.kill_displaced_by.<R>`, `layers.<…>`, or a dotted config key | Model rejects |
| `PolicyChange.rule_id` | `str` | — | iff not a rule change | rule-id pattern. For derived records, the rule affected (X or G) | Model rejects |
| `PolicyChange.field` | `str` | — | iff not `RULE_FIELD` | 1–80 | Model rejects |
| `PolicyChange.related_rule_id` | `str` | — | iff not derived | the rule that caused it (G for C-36, R for C-40) | Model rejects |
| `PolicyChange.old` / `.new` | `str` | as stored; `Decimal` via `str`, sets sorted by canonical string | `None` = absent | — | — |
| `PolicyChange.direction` | `Direction` | — | no | enum | Model rejects |
| `PolicyChange.basis` | `str` | — | no | one of `CLASSIFICATION_BASES` | Model rejects |
| `PolicyChange.reason` | `str` | — | no | 1–600; written to the audit record verbatim | Model rejects |
| `PolicyDiff.market` | `str` | — | `None` = no market layer | `US` \| `IN` | Model rejects |
| `PolicyDiff.environment` | `str` | — | `None` = no env layer | `^[a-z0-9_-]{1,32}$` | Model rejects |
| `PolicyDiff.old_version` / `.new_version` | `str` | — | no | `^\d+\.\d+\.\d+$` | Model rejects |
| `PolicyDiff.old_content_hash` / `.new_content_hash` | `str` | — | no | 64 lower-case hex: `EffectiveConfig.content_hash` for that combination | Model rejects |
| `PolicyDiff.changes` | tuple | — | no (may be empty) | unique, sorted by `(path, field or "", basis)` | Model rejects → `PolicyDiffError` |
| `ApprovalSignature.identity` | `str` | — | no | normalised (§2 row 11) | Model rejects |
| `ApprovalSignature.signature_hex` | `str` | — | no | 128 lower-case hex (64-byte Ed25519 signature) | Model rejects |
| `PolicyAuthorisation.diffs` | tuple | — | no | ≥ 1, unique, sorted by `(market or "", environment or "")` | Model rejects |
| `PolicyAuthorisation.request_id` | `str` | — | no | UUIDv7, lower-case (SPEC-P1.4's id format) | Model rejects |
| `PolicyAuthorisation.requested_at` | `str` | UTC, ISO-8601, whole seconds, `Z` suffix | no | not after the database clock when applied; at most `APPROVAL_TTL_HOURS` before it | Model rejects the format and any value that is not a real time; §5.3 refuses expired or future requests |
| `PolicyAuthorisation.digest` | `str` | — | no | `authorisation_digest(diffs, request_id, requested_at)` (§5.1) | Recomputed and compared in §5.2 step 3 and §5.3 |
| `PolicyAuthorisation.approvals` | tuple | — | no (may be empty) | distinct identities, sorted | Model rejects |
| `PolicyAuthorisation.required_approvals` | `str` | identities | no | `0`–`5` as a decimal string: `0` if nothing is gated; else the largest `min_approvals_to_loosen` over the **old** effective documents | Model rejects |
| `PolicyAuthorisation.gated_paths` | tuple | — | no | distinct, sorted paths of every LOOSENS / UNDECIDABLE change | Model rejects |

---

## 5. The approval path

### 5.1 Functions

| Function | Behaviour |
|---|---|
| `derive_combinations(old_dir: Path, new_dir: Path) -> tuple[tuple[str \| None, str \| None], ...]` | §2 row 20, over the files present in **either** directory. A `policy.market.<m>.yaml` with `m` not in `MARKETS`, or an env file whose name fails the `PolicyDiff.environment` pattern, raises `PolicyDiffError`. Never accepts a combination list from a caller (X2S-2) |
| `diff_policies(old_raw, new_raw, *, market=None, environment=None, old_layers=frozenset(), new_layers=frozenset()) -> PolicyDiff` | Validates both effective documents with `PolicyDocument` and emits every record of §3 for one combination, including C-41 from the two layer-name sets. Each set holds the names of the layer files present in that directory, for example `policy.env.paper.yaml`, read from the directory listing: `layers_applied` omits an empty file. Raises `PolicyDiffError` on validation failure |
| `diff_policy_dirs(old_dir, new_dir) -> tuple[PolicyDiff, ...]` | For each derived combination, loads both directories with `PolicyLoader(dir).load(market=m, environment=e, require_signature=False)`, takes `EffectiveConfig.redacted` as the raw mapping and `EffectiveConfig.content_hash` as the hash, and calls `diff_policies`. A combination whose layer files exist in only one directory is still loaded from both: the loader skips absent files (X2S-9). Any `PolicyError` from the loader becomes `PolicyDiffError` |
| `authorisation_digest(diffs, request_id, requested_at) -> str` | SHA-256 hex of `APPROVAL_DIGEST_TAG + canonical_json({"request_id": …, "requested_at": …, "combinations": [{"market": m or "", "environment": e or "", "old_content_hash": …, "new_content_hash": …}, …]}).encode("utf-8")`. Combinations are in `PolicyAuthorisation` order; P1.4's `jcs-nonum-1` canonicaliser. The tag gives domain separation (X2D-5) |
| `assert_policy_change_authorised(old_dir, new_dir, approvals: Sequence[ApprovalSignature], *, request_id: str, requested_at: str) -> PolicyAuthorisation` | §5.2. There is **no key-lookup parameter**: keys are resolved inside the module (X2D-2) |
| `assert_authorisation_current(auth: PolicyAuthorisation, conn, old_dir: Path, candidate_dir: Path) -> None` | §5.3. `conn` is the writer's open database transaction. The module reads the in-force anchor, the clock and the used-request check **itself**, from that transaction, through `IN_FORCE_STORE`; **no hash or time is taken from the caller**, and `old_dir` is verified against the store before it is read (X2D-1, X2D-3, X2F-3). Raises `InForceAnchorError`, `StaleAuthorisationError` or `ApprovalExpiredError` |
| `action_direction(old: str, new: str) -> tuple[Direction, str]` | §3.2; the string is the basis, `C-09` or `C-10`. Also used for `on_missing_input` (C-16 is the basis recorded there) |
| `rule_action_direction(rule_id: str, old: str, new: str) -> tuple[Direction, str]` | §3.2. C-42 where it applies, otherwise `action_direction`. `diff_policies` uses this for the `action` field. It takes strings, so C-42 is tested before `RuleAction` has the member |
| `scope_direction(old: str, new: str) -> tuple[Direction, str, str]` | §3.3; direction, basis (`C-12` or `C-13`), and the containment note or reason class R1–R4 |
| `key_direction(path: str) -> KeyDirection` | First match in `CONFIG_KEY_DIRECTIONS` |

### 5.2 Authorising a change

`assert_policy_change_authorised` does, in order:

1. **Derive** the combinations and the diffs with `diff_policy_dirs`. No caller-supplied change list
   or combination list is accepted anywhere on the approval path. `assert_change_authorised()` and
   `LimitChange` (loader.py §8) are not called on it; `loosens_for()` stays only as a test oracle.
2. **Count required approvals.** If no change is gated, `required_approvals` is `"0"`. Otherwise it
   is the largest `governance.min_approvals_to_loosen` among the **old** effective documents —
   never the new one, so a version cannot lower its own threshold and approve itself.
3. **Resolve keys from one fixed source** (X2D-2). The key source is the map
   `governance.signature.approver_key_refs`, identity → `{ref, raw_key_sha256}`, in the **old**
   (in-force) effective document of
   the `(None, None)` combination. `Governance.signature` is a free mapping, so the frozen loader
   accepts it (re-measured on this shape, 2026-10-31). Each reference is a `vault://` reference (SPEC-P1.3 §8), resolved through
   `VAULT_RESOLVER` (§4) to an Ed25519 public key in PEM, then reduced to its **raw 32-byte key**.
   `loader.py` parses references but has no client, so the resolver lives here (Q-P1.3.1-14). No
   caller supplies keys or a lookup. Tests assign `VAULT_RESOLVER` at module level, never per call.
   - Each map entry is `{ref, raw_key_sha256}`: the reference, and the SHA-256 of that raw key,
     written `sha256:<64 lower-case hex>` and compared with the prefix removed. Bare hex must not be
     used: the loader's literal-secret scan refuses it (X2G-1, measured). The policy hash excludes
     referenced values (SPEC-P1.3 §5.1), so without this pin a key could be
     replaced in Vault with no policy record. With it, rotating a key is a map change, and so
     two-person (X2F-7).
   - An identity not in the map, a reference that does not resolve, a key that is not Ed25519, or a
     raw key whose SHA-256 differs from `raw_key_sha256` raises `PolicyGovernanceError`.
   - While no Vault client exists (P6.2), `VAULT_RESOLVER` is `None` and no reference resolves, so
     no approval can be counted. That is fail-closed.
   - Because the map is read from the old document, a caller who supplies a doctored `old_dir`
     changes `old_content_hash`, and §5.3's anchor check refuses the authorisation when it is
     applied.
4. **Verify approvals** (X2S-10). Each signature is verified with loader.py `verify_signature`
   over `authorisation_digest(diffs, request_id, requested_at).encode("ascii")`, against the key
   from step 3. Any failure raises `PolicyGovernanceError`; a bad signature is never skipped.
   `requested_at` later than the local UTC clock (`datetime.now(timezone.utc)`, an early refusal
   only), or more than `APPROVAL_TTL_HOURS` before it, raises `ApprovalExpiredError`. §5.3 re-checks the age against the database clock, which is the
   binding check. The tolerance is **zero** in both checks (X2E-6): a `requested_at` even one second
   ahead of the clock is refused. That fails closed, and the request can simply be retried. P6.2's
   tooling takes `requested_at` from the database when the request is opened, so that skew between
   the tooling and the database cannot arise. This step's clock check belongs to the public function
   only: §5.3 step 7 re-derives through an internal helper, `_derive_authorisation`, which runs every
   other step of this section (X2G-5).
5. **Count distinct approvers.** Identities are distinct after normalisation, and two identities
   whose raw keys are equal count once.
6. If the count is below `required_approvals`, raise `PolicyGovernanceError` naming every gated
   path. Otherwise return the `PolicyAuthorisation`.

### 5.3 Applying an authorisation (X2S-3, X2D-1, X2D-3)

An authorisation is bound to four things:

- the exact version it was diffed against, **as recorded in storage, not as a caller describes it**;
- the exact version it approved;
- a 24-hour window;
- one use.

`assert_authorisation_current(auth, conn, old_dir, candidate_dir)` must be called by the writer that
inserts or reuses the `config_version` rows. It runs inside the same transaction (`conn`), after the
writer has taken the lock that serialises policy changes. The writer and its lock belong to P1.2 /
P6.4; this is a precondition they import. Using `conn`, the function itself, in this order:

1. **Reads the store** (X2D-1). Through `IN_FORCE_STORE` (§4), by a fixed query, it reads the in-force
   `config_hash` of every combination from the store B6 names, and the database clock. There is no
   parameter through which a hash, lookup or time could be supplied. `IN_FORCE_STORE` is assigned only
   by the B6 store's module, once a frozen spec defines it, and by tests. **None is assigned by
   default.** Replacing it at run time is a code change (ADR-09 row 10), not a call argument. **Under
   `[DEFAULT-B6]`, no frozen spec defines that store yet, so this step raises `InForceAnchorError` and
   nothing is applied.** A store with no rows at all also raises `InForceAnchorError`: its first rows
   are the genesis (B6), not an approved change.
2. **Refuses a used request** (X2F-1, X2G-2). If `IN_FORCE_STORE.request_used(conn, auth.request_id)` is
   true, it raises `StaleAuthorisationError`. An approval is spent once, even if the version it was given
   against returns. This comes first, so a replay at any age writes nothing.
3. **Checks expiry** (X2D-3, ADR-09 row 2, X2F-11), before any other comparison, so an unused request
   past its 24 h is always recorded as expired, even if it is also stale. The clock is `clock_timestamp()`
   on `conn`, read after the lock is held, never a caller's or a process clock.
   `transaction_timestamp()` is not used, because it stands still for as long as a transaction is held
   open.
   - `requested_at` after that time raises `ApprovalExpiredError` with `reason` `FUTURE`. Nothing is
     written, and the request may be retried.
   - `requested_at` more than `APPROVAL_TTL_HOURS` before it raises `ApprovalExpiredError` with
     `reason` `EXPIRED`, and the writer records an `APPROVAL_EXPIRED` event (§5.4): the request is
     denied, not deferred. Exactly `APPROVAL_TTL_HOURS` is not "more than", so it passes.
4. **Compares the anchor.**
   - The set of combinations with a current in-force row, united with
     `derive_combinations(candidate_dir, candidate_dir)`, must equal the authorisation's
     combination set.
   - A combination with a stored row must have that hash equal its `old_content_hash`.
   - A combination (m, e) with no stored row, whose diff carries a `LAYER_ADDED` record for its own
     env file `e`, is new in this change (X2E-1). It is anchored by the stored row of (m, None),
     whose hash must equal its `old_content_hash`. This is exact: that env file does not exist in
     the version in force, so the two are one effective document with one hash (measured).
   - Any other combination with no stored row, or one the authorisation did not diff, raises
     `StaleAuthorisationError`.
5. **Checks the candidate.** The `content_hash` of every combination loaded from `candidate_dir`, with
   `require_signature=False`, must equal `new_content_hash`.
6. **Checks the digest.** `authorisation_digest(auth.diffs, auth.request_id, auth.requested_at)` must
   equal `auth.digest`, or it raises `StaleAuthorisationError`.
7. **Re-derives the authorisation** (X2F-3). **Step 4 is the anchor; this step is a coherence check.**
   Every combination loaded from `old_dir` must hash to its `old_content_hash`, which step 4 has proved
   equal to the store. `_derive_authorisation(old_dir, candidate_dir, auth.approvals, auth.request_id,
   auth.requested_at)` (§5.2, without its clock check) then runs, and its result must equal `auth`.
   X2D-1 stays closed: the anchor comes only from the store, and `old_dir` cannot change it. `old_dir` is
   checked for its effective documents, not its file set: an empty layer file does not change the hash.
   That can cost only C-41's record, because the effective documents are still fully classified, so a
   loosening inside a new layer stays gated. Binding the file set would need a stored list of layer
   names, which this does not justify (X2G-4).

Any `PolicyError` or `PolicyDiffError` from steps 5 to 7, and any difference at step 7, raises
`StaleAuthorisationError`.

On any failure, no `config_version` row, in-force row or `CONFIG_CHANGED` event is written. For
`reason` `EXPIRED`, the writer writes and commits `APPROVAL_EXPIRED` (§5.4) and nothing else; every
other failure writes nothing at all. That event means an authorisation was **presented after its expiry**.
It is not proof that a real request was refused: step 3 runs before anything authenticates `requested_at`
(X2G-2). `ApprovalExpiredError` is a `StaleAuthorisationError`, so the
writer must catch it first. The candidate must then be re-diffed and re-approved against the version
now in force. With a stored anchor, the measured X2S-3 pattern fails at step 4. That pattern is two
proposals built on one base, where B's writer passes v1's directory after A is applied. Without a
stored anchor, nothing is applied at all.

### 5.4 What is written to the audit trail

From SPEC-P1.4 §3's catalogue, before the new `config_version` rows:

- one `CONFIG_CHANGED` event (class SYSTEM), whose payload is `auth.model_dump(mode="json")`
  canonicalised with `jcs-nonum-1`. Every value is a string (X2S-6);
- one `APPROVAL_GRANTED` event (class APPROVAL) per counted approver;
- on expiry (§5.3 step 3, `reason` `EXPIRED`), one `APPROVAL_EXPIRED` event (class APPROVAL) instead of the two above,
  carrying `request_id`.

The new in-force row(s) of the B6 store are written in the same transaction, after these events.
`trading.config_version.approval_id` (SPEC-P1.2 §6.9) holds one id and cannot name two approvers
(F-12, Q-P1.3.1-6).

### 5.5 Propagation

Unchanged from SPEC-P1.3 §5.4: an applied version takes effect at the next run boundary and never
reaches an in-flight decision.

---

## 6. AMENDMENT — SPEC-P1.3 §5.3, exact replacement text

**What is there now.** d8067b6 rewrote SPEC-P1.3 §5.3 to v0.1 of this spec, header left at v0.1
FROZEN; 4397c4f left it as is pending this re-run. Current lines 205–250: a table with an
"Undecidable" row; the paragraphs "The change list is derived", "Every field is classified", "The
two-person rule applies", "**A smaller pass set is not a tightening on a rule that can block an
exit**", "The approval count is the active version's", "Two distinct *identities*"; the unchanged
"This is stricter than a FROZEN ADR"; and the operational-consequence note.

**Replace everything from the heading `### 5.3 Who may change what — the two-person rule` up to,
but not including, `### 5.4`, with:**

> ### 5.3 Who may change what — the two-person rule
>
> | Direction of a change | Approvals | Authority |
> |---|---|---|
> | **Tightens** | **0** — automatic | ADR-09 row 3: "tightening is always safe" |
> | **Neutral** | **0** | SPEC-P1.3.1 §3 |
> | **Loosens** | **2 distinct identities** | This spec, §5.3; Owner Ruling 12 (DECISIONS.md, 2026-10-16) |
> | **Undecidable** — the diff cannot prove a direction | **2 distinct identities** | Owner Ruling 12: UNDECIDABLE fails closed to LOOSENS |
> | **Override a risk DENY** | **Impossible. No approver, no code path** | ADR-09 final row, invariant I2 |
>
> A policy change is every difference between the version in force and the version proposed, in
> every (market, environment) combination, and it needs the largest approval count that any one of
> those differences needs.
>
> **The change list is derived, never declared.** `assert_policy_change_authorised()`
> (SPEC-P1.3.1 §5) derives the combinations from the policy files and the changes from the
> effective documents. A caller cannot leave a change or a combination out by not mentioning it.
> `assert_change_authorised()` and `LimitChange` are not on the approval path; `loosens_for()`
> remains only as a test oracle.
>
> **Every field is classified, by Owner Ruling 12.** A change loosens when it widens the permitted
> set.
>
> - **Threshold:** direction depends on the comparison. Raising an `lte` or `lt` bound loosens;
>   raising a `gte` or `gt` bound tightens. Any change of an `eq` bound is undecidable.
> - **Action:** moving down `KILL > HALT_ENTRIES > DENY > MODIFY > ALLOW` loosens.
> - **Mode:** `enforce` → `monitor` loosens, always.
> - **Comparison:** any change is undecidable.
> - **Scope:** narrowing loosens and widening tightens, on the order SPEC-P1.3.1 §3.3 defines; a
>   pair that order cannot rank is undecidable.
> - **Removing** a rule loosens, always. **Adding** a rule is itself never a loosening. What an
>   added or changed rule does to *other* rules is recorded against them: an exemption it grants
>   loosens the exempted rule's scope, and a kill it can take ahead of an existing GLOBAL kill
>   (§4.2's lowest-id binding) is undecidable for that GLOBAL rule (SPEC-P1.3.1 §3.6).
> - **Severity** never loosens on its own; changed together with the action, it takes the
>   action's direction.
>
> Every other rule field, every key outside `rules`, and every layer file is classified by
> SPEC-P1.3.1 §3, which ends in UNDECIDABLE for anything it does not name.
>
> **UNDECIDABLE is a fourth outcome, not an error, and it is never passed as neutral.** For
> approval it counts as a loosening (`[CONST-6]`).
>
> **The approval count is the version in force's.** `min_approvals_to_loosen` is read from the
> version being replaced, never from the version being approved.
>
> **Two distinct *identities*, not two approvals.** Each approval is an Ed25519 signature over a
> domain-tagged digest of the request id, the request time, and the exact old and new content
> hashes of every combination. The signing identity must be listed, with its key reference and a pin of that key, in
> the policy version in force; nobody supplies keys at approval time. Identities are normalised and
> de-duplicated (`["js", "JS "]` is one person), and two identities with the same raw key are one
> approver.
>
> **An approval is valid only for the version it was given against, only for 24 hours, and only
> once.** It is applied only if, in the transaction that records the new in-force version:
>
> - every combination's in-force hash, read from storage and never from the caller, equals the
>   hash the change was diffed against. A combination that exists only because this change adds
>   its environment file is compared through its (market, no environment) combination, which is
>   the same document;
> - the candidate still hashes to what was approved;
> - no more than 24 hours have passed since the request, by the database clock (ADR-09 row 2);
> - its request has not been used before, even if the version it was given against has returned.
>
> Otherwise the request is denied and must be re-diffed and re-approved. Until a frozen spec
> defines where the in-force hash of each combination is stored, in a store that itself refuses an
> out-of-sequence row (SPEC-P1.3.1 B6), no policy change can be applied by this path.
>
> **The constitution is also pinned in code.** `tests/verify_p13_policy_diff.py` pins the
> `threshold`, `action`, `mode`, `comparison` and `scope` of every rule whose authority cites
> `[CONST]` or `IMMUTABLE`, and the `scope` and `mode` of every rule. Changing a pinned value also
> needs a reviewed code change (ADR-09 row 10), whatever its direction.
>
> **This is stricter than a FROZEN ADR, and that is why it is permitted.** ADR-09 row 2 authorises
> the Owner *alone* to increase a limit. Requiring two is a tightening of that control, and ADR-09
> row 3 says tightening is always safe and needs no approval — so no constitutional amendment is
> required and **none has been made**.
>
> > **Operational consequence, stated rather than discovered.** At team size 1 (`[DEFAULT-3]` of
> > P0.1), every LOOSENS and every UNDECIDABLE change is **impossible** until a second approver is
> > enrolled. That includes any comparison change, any edit to a config key SPEC-P1.3.1 does not
> > name, any new layer file, and any change to a rule that can take a non-GLOBAL kill ahead of a
> > GLOBAL one. No approver is listed in the policy today, and the Owner has ruled that there is no
> > enrolment path for now (SPEC-P1.3.1 B7), so neither the first approver nor the second can be
> > added through this path. Tightenings
> > that change no other rule, and the kill switch, remain unblocked as decisions; applying any
> > change waits on the in-force record (B6).

**Also replace SPEC-P1.3 §5.4 item 3 (X2F-2) with:**

> 3. A new signed policy version takes effect at the **next run boundary**, and only if it is the
>    in-force version of that run's (market, environment), recorded in the one transaction that
>    inserts or reuses its `config_version` row (SPEC-P1.3.1 B6). A backtest may bind an older version.

**Differences from the d8067b6 text, and the ruling line or finding behind each:**

| d8067b6 text | Replacement | Why |
|---|---|---|
| "comparison and threshold judged jointly on the pass set" | Threshold by comparison; any comparison change undecidable | Ruling 12, `threshold` and `comparison` rows |
| "`action` on the KILL > DENY > MODIFY > ALLOW lattice" | Ladder with `HALT_ENTRIES` | Ruling 12 `action` row; Ruling 14; B2 |
| "`scope` by coverage" | Scope by SPEC-P1.3.1 §3.3 | Ruling 12 `scope` row; B4 |
| (no addition or severity rule) | Addition never loosens; effects on other rules recorded against them; severity follows the action | Ruling 12, addition and severity rows; B3; B5 (X2S-1) |
| "every (market, environment) combination that will be loaded" | Combinations derived from the policy files | X2S-2, X2S-9 |
| "Two distinct identities … normalised" | Signed by identities listed in the in-force policy, over a domain-tagged digest; identical raw keys count once | X2S-10, X2D-2, X2D-5; B7 |
| (absent) | Approval bound to the stored in-force version, to a 24 h window, and to one use | X2S-3, X2D-1, X2D-3, X2F-1; ADR-09 row 2; B6 |
| (absent) | SPEC-P1.3 §5.4 item 3 replaced | X2F-2; B6 |
| Paragraph "**A smaller pass set is not a tightening on a rule that can block an exit** …" | **Removed** | No ruling covers it; B1 default (A) |
| (absent) | Pins paragraph | Ruling 12, "Required tests" |
| Operational consequence names limit increases only | Names UNDECIDABLE cases, layer files, kill displacement | B5, C-41 |

**If the Owner chooses B1 option (B)**, insert after the "UNDECIDABLE is a fourth outcome"
paragraph:

> **A narrower permitted set is not a tightening on a rule that can stand between the book and a
> risk-reducing exit.** On KILL-002's `exempts`, EXEC-001's `allowed_values_emergency`, HOLD-001,
> TURN-002, RATE-001, RATE-002, DATA-001 and LIQ-001, and on any rule whose `measurement.timing` is
> `pre_exit`, a change that would otherwise tighten is UNDECIDABLE (Owner ruling on SPEC-P1.3.1 B1).

**Not part of this amendment, but owed elsewhere:** SPEC-P1.3 §4.1's gate lattice must gain
`HALT_ENTRIES`, and a `HALT_ENTRIES` outcome must decide entries only (#17, Q-P1.3.1-15); SPEC-P1.3 §4.2 / `_combine` should take B5 option (d); SPEC-P1.3's CONTRACTS
rows for `assert_change_authorised` and `loosens_for` must say "not on the approval path"; the
header version and freeze record are Q-P1.3.1-9; the per-combination in-force store is
Q-P1.3.1-13 (P1.2 / P6.4); and documenting `governance.signature.approver_key_refs` in SPEC-P1.3 §3
and §5.2 is Q-P1.3.1-14.

---

## 7. Test requirements

### 7.1 Rules that apply to every test

1. **`require()` only.** No bare `assert` in `tests/verify_p13_policy_diff.py`,
   `tests/mutate_x5r_g9.py` or `tests/mutate_policy_diff_code.py`. `t_no_bare_assert` parses each
   file with `ast` and fails on any `ast.Assert` node.
2. **Both interpreters.** Every suite runs as `py -3.11 <suite>` and `py -3.11 -O <suite>`, and on
   Python 3.12+ in CI (condition 15).
3. **A test counts only if it fails when the thing it tests is broken, and the evidence names that
   test.** A suite exiting non-zero is not evidence on its own (X2S-4). Every suite prints one line
   per failure, `FAILED <test_name>: <message>`, and every pin failure message begins with
   `<RULE-ID>.<field>` (for example `EXP-002.action`).
4. **Real file.** Pins read `config/policy.yaml` through `PolicyLoader` and compare against literal
   tables in the test file.

### 7.2 Pins

**(a) Five attributes for the 20 constitutional rules**, plus `on_missing_input`, `kill_scope`,
`allowed_values`, `allowed_values_emergency`, `disallowed_values`, `measurement` (basis, window,
timing), `inputs`, absence of `threshold_ref` and `threshold_input`, and `binds`. One test per
rule, `t_pin_<RULE_ID with _>`.

| Rule | action | mode | comparison | scope | threshold / value set |
|---|---|---|---|---|---|
| EXP-001 | DENY | enforce | lte | pool | 0.050 |
| EXP-002 | DENY | enforce | lte | pool | 0.200 |
| EXP-003 | DENY | enforce | lte | pool | 2.0 |
| EXP-004 | DENY | enforce | lte | pool | 1.0 |
| LOSS-001 | DENY | enforce | lte | pool_and_consolidated | 0.020 |
| LOSS-002 | DENY | enforce | lte | pool_and_consolidated | 0.050 |
| LOSS-003 | KILL (POOL; on missing KILL) | enforce | lte | pool | 0.100 |
| LOSS-004 | KILL (GLOBAL; on missing KILL) | enforce | lte | consolidated | 0.100 |
| SIZE-001 | MODIFY | enforce | lte | pool | 0.010 |
| LIQ-001 | MODIFY | enforce | lte | instrument | 0.010 |
| RATE-001 | DENY | enforce | lte | global | 20 |
| RATE-002 | DENY | enforce | lte | strategy | 10 |
| STOP-001 | DENY | enforce | eq | instrument | 2.5 |
| EXEC-001 | DENY | enforce | in | instrument | allowed `{LIMIT}`; emergency `{MARKET, LIMIT}` |
| DATA-001 | DENY | enforce | lte | instrument | 600 |
| REGIME-001 | DENY | enforce | not_in | market | disallowed `{UNKNOWN}` |
| KILL-001 | DENY | enforce | in | global | allowed `{ARMED}` |
| AUDIT-001 | DENY | enforce | exists | global | — |
| LLM-001 | DENY | enforce | eq | global | allowed `{false}` |
| LLM-002 | DENY | enforce | exists | global | — |

`t_constitutional_set_is_exactly_the_table` pins membership. When #17 applies Ruling 14, LOSS-001
and LOSS-002 become `HALT_ENTRIES` in a reviewed edit to this table.

**(b) `scope` and `mode` for all 47 rules** (`t_scope_and_mode_pinned_for_every_rule`; on failure
it reports every mismatch, one `<RULE-ID>.<field>` per message line), and
`t_pinned_rule_set_is_exactly_the_file` (the 47 ids below and no others).

| Scope | Rules (all `enforce` unless marked) |
|---|---|
| `pool` (15) | EXP-001, EXP-002, EXP-003, EXP-004, EXP-005, EXP-006, LOSS-003, SIZE-001, CASH-001, **CASH-002 (monitor)**, PORT-001, **PORT-002 (monitor)**, TURN-001, TURN-002, RECON-001 |
| `instrument` (13) | SIZE-002, LIQ-001, STOP-001, EXEC-001, HOLD-001, HOLD-002, HOLD-003, EDGE-001, INST-001, INST-002, DATA-001, DATA-002, DATA-003 |
| `global` (9) | RATE-001, FX-001, KILL-001, KILL-002, AUDIT-001, AUDIT-002, LLM-001, LLM-002, LLM-003 |
| `market` (6) | UNIV-001, UNIV-002, UNIV-003, UNIV-004, UNIV-005, REGIME-001 |
| `pool_and_consolidated` (2) | LOSS-001, LOSS-002 |
| `consolidated` (1) | LOSS-004 |
| `strategy` (1) | RATE-002 |

Promoting PORT-002 (Q-P1.3-4) or CASH-002 is a TIGHTENS for governance but also a reviewed edit to
this table.

**(c) Kept:** `t_exemption_scope_is_pinned` — KILL-002 is `ALLOW`/`enforce` with `exempts` exactly
`{CASH-001, CASH-002, KILL-001, HOLD-001, TURN-001, TURN-002, EXEC-001}`, and no other rule carries
`exempts`. **(d) New:** `t_kill_scope_rules_are_pinned` — the rules with `action: KILL` or
`on_missing_input: KILL` are exactly LOSS-003 (POOL), LOSS-004 (GLOBAL) and AUDIT-002 (GLOBAL).
This is the test-time half of B5: it fails the CASH-001 and FX-001 edits of X2S-1. **(e) New:**
`t_no_approver_is_listed` — `governance.signature` in the real file has no `approver_key_refs`
(F-17), so a map cannot enter by a plain policy edit. At genesis, the deployment check in B6 refuses
one. The same check run on the §7.4 signatures fixture, which lists a map, must fail. If the Owner
later adopts B7 (b), the bootstrap's reviewed change edits this pin. **(f) New (X2F-4):**
`t_halt_entries_rules_are_pinned` — over the raw mapping of **every** derived combination, no rule has
`action: HALT_ENTRIES` today. It reads raw mappings because a policy using that action does not load
yet, and every combination because a layer may carry a `rules:` list (X2G-8). #17's reviewed edit makes
that set exactly LOSS-001 and LOSS-002, and no other rule. The same check run on a mapping with HOLD-001
at `HALT_ENTRIES` must fail. This is the test-time half of C-42.

### 7.3 The five X5R-G9 mutations

`tests/mutate_x5r_g9.py` applies each to a throwaway copy of the repository.

**Harness contract (X2S-4, X2S-14):**

- `--must-fail SUITE`: a mutation is **KILLED** only if, in both `python` and `python -O`, the suite
  exits non-zero **and** its `FAILED` lines include the expected test (table below) with a message
  line beginning `<RULE-ID>.<field>` for the mutated rule and field. Any other failure does not
  count.
- `--must-pass SUITE`: the suite must exit 0 in both modes on every mutation, or the harness exits
  non-zero.
- Every mutated policy must still **load**, or the harness reports `[INVALID]` and exits non-zero.
- `--negative-control`: re-runs every mutation against a copy of the must-fail suite in which the
  body of every pin test — `t_pin_*`, `t_scope_and_mode_pinned_for_every_rule`,
  `t_constitutional_set_is_exactly_the_table`, `t_pinned_rule_set_is_exactly_the_file`,
  `t_exemption_scope_is_pinned`, `t_kill_scope_rules_are_pinned`, `t_halt_entries_rules_are_pinned` — is replaced by `return None`.
  It exits 0 only if **every** mutation is reported **SURVIVED**. This proves the harness attributes
  kills to pins and not to incidental fixture failures.

| Mutation | Diff classification | Basis | Expected failing test (message prefix) | One approver |
|---|---|---|---|---|
| EXP-002 `action` → ALLOW | LOOSENS | C-09 | `t_pin_EXP_002` (`EXP-002.action`) | refused |
| LOSS-001 `mode` → monitor | LOOSENS | C-11 | `t_pin_LOSS_001` or `t_scope_and_mode_pinned_for_every_rule` (`LOSS-001.mode`) | refused |
| LOSS-004 `threshold` → 0.200 | LOOSENS | C-01 | `t_pin_LOSS_004` (`LOSS-004.threshold`) | refused |
| EXEC-001 `allowed_values` += MARKET | LOOSENS | C-20 | `t_pin_EXEC_001` (`EXEC-001.allowed_values`) | refused |
| STOP-001 `comparison` → lte | UNDECIDABLE | C-08 | `t_pin_STOP_001` (`STOP-001.comparison`) | refused |

**Acceptance:** both of these exit 0 —
`py -3.11 tests/mutate_x5r_g9.py --must-fail tests/verify_p13_policy_diff.py --must-pass tests/verify_p13_config.py`
(five `[KILLED]` lines; `verify_p13_config.py` passes on all five, reproducing X5R-G9), and the same
command with `--negative-control` (five `[SURVIVED]` lines).

`t_x5r_g9_each_mutation_is_gated` diffs the real file against each mutation, on a fixture that adds
the same approver map to both sides so that keys resolve (X2F-12), and requires exactly
one change with the direction and basis above, `PolicyGovernanceError` for one signed approval and
for one identity signing twice, and success for two distinct enrolled identities (test keys
generated in the test, never real ones). It is not counted as mutation evidence.

### 7.4 Classification and authorisation tests — the required cases

Each case asserts `direction` and `basis`, and the full set of records produced.
`t_every_basis_is_exercised` fails unless the bases produced across this suite — from diff records
and from the basis returned by `action_direction`, `rule_action_direction` and `scope_direction` (X2S-8) — equal
`CLASSIFICATION_BASES`.

| Basis | Required cases (expected) |
|---|---|
| C-01 | LOSS-004 0.10→0.20 LOOSENS; EXP-001 0.05→0.04 TIGHTENS (no C-40: EXP-001 is not kill-capable); RATE-001 20→20.0 NEUTRAL; TURN-002 0.20→0.02 TIGHTENS, authorised with zero approvals (records B1's blast radius) |
| C-02 | PORT-001 0.20→0.10 LOOSENS; 0.20→0.30 TIGHTENS; HOLD-001 3→30 TIGHTENS; EDGE-001 2.0→1.5 LOOSENS |
| C-03 | RECON-001 0→1 UNDECIDABLE; STOP-001 2.5→3.0 UNDECIDABLE |
| C-04 | SIZE-002 threshold null→1 (`multiple_of`) UNDECIDABLE |
| C-05 | EXP-001 `threshold` → `threshold_ref: portfolio.max_position_pct` UNDECIDABLE |
| C-06 | UNIV-004 `threshold_ref` repointed UNDECIDABLE |
| C-07 | CASH-001 `threshold_input` settled_cash→cash (inputs extended) UNDECIDABLE |
| C-08 | STOP-001 eq→lte; EXP-001 lte→lt; EXP-001 lte→eq; EDGE-001 gte→gt; CASH-001 lte→lt; EXP-001 lte→lt with threshold 0.10 (both records); EXEC-001 in→not_in with the value set moved — all UNDECIDABLE |
| C-09 | EXP-002 DENY→ALLOW LOOSENS; SIZE-001 MODIFY→DENY TIGHTENS; REGIME-001 DENY→KILL with `kill_scope: POOL`: action and kill_scope records TIGHTENS, **no** C-40 (REGIME-001 sorts after both GLOBAL kill rules), zero approvals. `action_direction`: KILL→HALT_ENTRIES LOOSENS; HALT_ENTRIES→MODIFY LOOSENS; MODIFY→HALT_ENTRIES TIGHTENS; HALT_ENTRIES→KILL TIGHTENS; **HALT_ENTRIES→DENY LOOSENS; DENY→HALT_ENTRIES TIGHTENS** (the answered order); DENY→DENY NEUTRAL — each with basis C-09 |
| C-10 | `action_direction`: "FOO"→DENY and DENY→"FOO" UNDECIDABLE, each with basis C-10 |
| C-42 | `rule_action_direction`: HOLD-001 DENY→HALT_ENTRIES, RECON-001 DENY→HALT_ENTRIES and INST-002 MODIFY→HALT_ENTRIES UNDECIDABLE, each with basis C-42; LOSS-001 DENY→HALT_ENTRIES TIGHTENS, basis C-09; HOLD-001 KILL→HALT_ENTRIES LOOSENS, basis C-09 |
| C-11 | LOSS-001 enforce→monitor LOOSENS; KILL-002 enforce→monitor LOOSENS; PORT-002 monitor→enforce TIGHTENS (no C-40); old = real file with LOSS-003 in monitor, new = real file: TIGHTENS **plus** C-40 on LOSS-004 |
| C-12 | LOSS-001 pool_and_consolidated→pool LOOSENS; LOSS-004 consolidated→pool_and_consolidated TIGHTENS (no C-40: LOSS-004 is GLOBAL); LOSS-003 pool→pool_and_consolidated: scope record TIGHTENS **plus** `rules.LOSS-004.kill_displaced_by.LOSS-003` UNDECIDABLE, refused with one approver (v0.2 expected TIGHTENS alone — X2S-1); `scope_direction` same scope NEUTRAL, basis C-12 |
| C-13 | RATE-002 strategy→global (R1); EXP-001 pool→consolidated (R1); UNIV-001 market→pool (R3); SIZE-002 instrument→strategy (R2); RATE-001 global→pool_and_consolidated (R4) — all UNDECIDABLE with the reason class in `reason`. `scope_direction` over all 49 ordered pairs equals §3.3 |
| C-14 | EXP-001 CRITICAL→LOW NEUTRAL; HOLD-002 MEDIUM→CRITICAL NEUTRAL; authorised with zero approvals |
| C-15 | EXP-002 DENY→ALLOW with CRITICAL→LOW: severity LOOSENS; SIZE-001 MODIFY→DENY with HIGH→LOW: severity TIGHTENS |
| C-16 | REGIME-001 `on_missing_input` DENY→KILL TIGHTENS, no C-40, zero approvals; **FX-001** DENY→KILL: TIGHTENS **plus** C-40 on LOSS-004, refused with one approver; **AUDIT-001** DENY→KILL: TIGHTENS plus C-40 on **both** AUDIT-002 and LOSS-004; LOSS-003 KILL→DENY LOOSENS (plus C-40) |
| C-17 | LOSS-004 kill_scope GLOBAL→POOL LOOSENS; LOSS-003 POOL→GLOBAL TIGHTENS, no C-40 |
| C-18 | SIZE-001 MODIFY→DENY with `modify` removed: modify record TIGHTENS; LOSS-003 KILL→DENY with `kill_scope` removed: kill_scope record LOOSENS; **CASH-001** DENY→KILL with `kill_scope: POOL`: action and kill_scope records TIGHTENS **plus** C-40 on LOSS-004, refused with one approver (X2S-1) |
| C-19 | `kill_scope: POOL` added to EXP-001 (DENY) UNDECIDABLE |
| C-20 | EXEC-001 +MARKET LOOSENS; INST-002 +HALTED LOOSENS; KILL-001 +TRIPPED LOOSENS; EXEC-001 [LIMIT]→[MARKET] UNDECIDABLE |
| C-21 | LLM-001 [false]→[true] UNDECIDABLE |
| C-22 | REGIME-001 +BEAR TIGHTENS; [UNKNOWN]→[BEAR] UNDECIDABLE |
| C-23 | `disallowed_values` added to EXEC-001 (`in`) UNDECIDABLE |
| C-24 | EXEC-001 emergency +STOP LOOSENS; emergency → [LIMIT] TIGHTENS |
| C-25 | INST-001 `allowed_values_ref` → `instrument_allowlist.read_only` UNDECIDABLE |
| C-26 | KILL-002 +EXP-001 LOOSENS plus a C-36 record for EXP-001; KILL-002 minus CASH-001 TIGHTENS |
| C-27 | EXP-001 +fx_rate TIGHTENS; minus mark_price LOOSENS with `mark_price` in `reason`; swap UNDECIDABLE; LOSS-003 +fx_rate TIGHTENS **plus** C-40 on LOSS-004 |
| C-28 | LOSS-002 window `sessions:3`, basis `nav_current`, timing `end_of_session`: three UNDECIDABLE records |
| C-29 | EXP-006 modify.to 0.04→0.06 LOOSENS; →0.03 TIGHTENS |
| C-30 | SIZE-001 modify.to symbolic change UNDECIDABLE; modify.target changed UNDECIDABLE |
| C-31 | EXP-001 authority `[CONST]` → `ADR-14` UNDECIDABLE |
| C-32 | description and notes edits NEUTRAL; authorised with zero approvals |
| C-33 | EXP-002 removed LOOSENS; KILL-002 removed LOOSENS; EXP-001 renamed to EXP-007 at 0.08: removal LOOSENS and the set is gated |
| C-34 | Added enforce DENY rule TIGHTENS; added enforce DENY `pre_exit` rule TIGHTENS; added **KILL-003** (LOSS-004's predicate, `kill_scope: POOL`): addition TIGHTENS **plus** C-40 on LOSS-004, refused with one approver; added **TURN-009** KILL/POOL: TIGHTENS, no C-40 (sorts after both GLOBAL kill rules) |
| C-35 | Added monitor DENY rule NEUTRAL; added ALLOW rule without exemptions NEUTRAL |
| C-36 | Added KILL-003 (ALLOW, `exists` on `audit_event_id`, exempts LOSS-003 and LOSS-004): addition NEUTRAL, plus `rules.LOSS-003.exempted_by.KILL-003` and `rules.LOSS-004.exempted_by.KILL-003` LOOSENS, refused with one approver; **the same rule with `mode: monitor`: the same two C-36 records** (X2S-13) |
| C-37 | universe.US.min_price_usd "5.00"→"1.00" LOOSENS; cost.assumed_round_trip_bps.US 25→5 LOOSENS, →40 TIGHTENS; portfolio.max_position_pct 0.05→0.08 LOOSENS; portfolio.min_cash_pct 0.20→0.10 LOOSENS; account.enforce_settled_cash false LOOSENS; instrument_allowlist.tradeable +ETF LOOSENS; permanently_banned −OPTION LOOSENS; llm.gate_width 15→30 LOOSENS; holding.min_sessions 3→30 TIGHTENS, 3→1 LOOSENS; turnover.max_nav_traded_pct_per_session 0.20→0.02 TIGHTENS; metadata.description NEUTRAL; policy_version NEUTRAL |
| C-38 | portfolio.max_gross_override added UNDECIDABLE; universe.US.min_price_usd removed LOOSENS |
| C-39 | schedule.US.pipeline_utc changed UNDECIDABLE; instrument_allowlist.tradeable [COMMON_STOCK]→[ETF] UNDECIDABLE; **turnover.min_sessions_between_reentry added (UNDECIDABLE), then changed 5→0 in a second diff: UNDECIDABLE**, not TIGHTENS (X2S-11) |
| C-40 | Covered by the C-11, C-12, C-16, C-18, C-27 and C-34 cases above. **Indirect triggers (X2D-4):** on a base edited so that EXP-005 is `action: KILL`, `kill_scope: POOL` and uses `threshold_ref`, lowering a referenced config key adds `rules.LOSS-004.kill_displaced_by.EXP-005`; on a base where KILL-002 exempts LOSS-003, removing LOSS-003 from `exempts` (C-26 TIGHTENS) adds `rules.LOSS-004.kill_displaced_by.LOSS-003`. The pins fail on these bases, which is expected; the diff is what is tested |
| C-41 | New dir adds `policy.market.IN.yaml` with EXP-001 at 0.10: in each IN combination, `LAYER_ADDED` UNDECIDABLE plus `rules.EXP-001.threshold` LOOSENS; the US and market-less combinations have no records |

**Authorisation tests:**

- **Combinations are derived (X2S-2).** The C-41 fixture is refused with one approver even though
  the test passes no combination list; the API has no parameter for one. A
  `policy.market.XX.yaml` raises `PolicyDiffError`. An env file present in only one directory adds
  its combinations.
- **Retired combination (X2S-9).** Removing a market layer yields `LAYER_REMOVED` plus the value
  records, and is approvable with two identities.
- **Signatures (X2S-10, X2D-2, X2D-5).** Keys come from the old document's
  `governance.signature.approver_key_refs`. The test substitutes the Vault resolver at module level
  and generates its own keys.
  - An identity absent from the map → `PolicyGovernanceError`.
  - A signature over a different digest → `PolicyGovernanceError`.
  - A signature over the digest *without* `APPROVAL_DIGEST_TAG` → `PolicyGovernanceError`.
  - Two identities whose references resolve to the same raw key, one in LF-PEM and one in
    CRLF-PEM → counted once, refused for a gated change.
  - Two distinct listed keys → accepted.
  - A resolved key whose raw SHA-256 differs from the map's `raw_key_sha256` →
    `PolicyGovernanceError` (X2F-7).
  - The signatures fixture, with `sha256:`-prefixed pins, loads through `PolicyLoader` (X2G-1). The
    same fixture with bare hex pins raises `VaultReferenceError`.
  - `assert_policy_change_authorised` has no parameter that accepts keys or a key lookup
    (`inspect.signature`).
  - With no Vault resolver installed, every gated change is refused.
- **In-force anchor (X2S-3, X2D-1; B6).**
  - With no B6 store adapter installed — today's state under `[DEFAULT-B6]` —
    `assert_authorisation_current` raises `InForceAnchorError` for every authorisation, including
    a pure tightening.
  - With a test adapter installed at module level: v1 in force, LOSS-004 at 0.10. Proposal A
    (LOSS-004 0.10→0.08) and proposal B (a description edit) are both authorised against v1's
    directory. A is applied, and the adapter now reports v2a's hashes. B's writer then calls the
    function, passing v1's directory as `old_dir`. The store disagrees with v1's hashes, so the call
    raises `StaleAuthorisationError` at the anchor, before `old_dir` is read.
  - A candidate directory edited after approval → `StaleAuthorisationError`.
  - A row missing for a combination the in-force files derive → `StaleAuthorisationError`.
  - First env layer (X2E-1): rows for today's three combinations, and a candidate that adds
    `policy.env.paper.yaml`. The three new combinations are anchored by their (m, None) rows and
    the call passes. A new combination with a hand-built `old_content_hash` that differs from its
    (m, None) row raises `StaleAuthorisationError`. With no `LAYER_ADDED` record, and an **empty** env
    file so that the hashes agree, it also raises: only that fixture catches M-23.
  - Retired env layer: rows including the paper combinations, and a candidate that removes the
    file. The call passes. A paper row left current after an earlier removal raises
    `StaleAuthorisationError`, because the combination sets differ.
  - Revival: after that removal closes the paper rows, a candidate that adds the file again, with
    different content, is anchored by the (m, None) rows and passes, including when (m, None) has
    changed in between.
  - An adapter that returns no rows at all → `InForceAnchorError`.
  - Replay (X2F-1): v1→v2 is applied, v2→v1 is applied, then the first authorisation is presented
    again inside 24 h. Every hash matches, and the call raises `StaleAuthorisationError`, because
    `request_used` is true.
  - Late replay (X2G-2): the same, more than 24 h after `requested_at` → plain
    `StaleAuthorisationError`, not `ApprovalExpiredError`, so nothing is written.
  - Stripped authorisation (X2F-3): real diffs with gated records and `approvals=()`,
    `required_approvals="0"`, `gated_paths=()`, digest recomputed → model rejects. The same with the
    records blanked, so that the model accepts it → `StaleAuthorisationError` at step 7.
  - A doctored `old_dir`: the call raises `StaleAuthorisationError` at step 7.
  - A digest mismatch, and a candidate that no longer loads → `StaleAuthorisationError`.
  - The function has no parameter for a hash or a time (`inspect.signature`), and the anchor is read
    from the store whatever `old_dir` holds.
- **Expiry (X2D-3).** Each case is checked against the database time the adapter returns.
  - `requested_at` 24 h minus 1 s earlier → passes.
  - Exactly 24 h earlier → passes ("more than" is strict).
  - 24 h plus 1 s earlier → `ApprovalExpiredError`, with `reason` `EXPIRED` and `request_id` set.
  - `requested_at` 1 s in the future → `ApprovalExpiredError`, with `reason` `FUTURE` (tolerance zero,
    X2E-6).
  - More than 24 h old, unused and also stale → `reason` `EXPIRED`: expiry is checked before the
    anchor (X2F-11).
  - Changing `requested_at` after signing changes the digest → `PolicyGovernanceError`.
- **Canonical payload (X2S-6).** `src/audit/events.canonical_json(auth.model_dump(mode="json"))`
  succeeds for a real `PolicyAuthorisation` with gated changes.
- **Models (X2S-15, X2E-5).** Unsorted `changes`, unsorted or duplicate `diffs`, unnormalised or
  duplicate approver identities, `required_approvals` outside `0`–`5`, and a `requested_at` of
  `2026-13-45T99:99:99Z`, `2026-02-30T00:00:00Z` or `2026-01-01T23:59:60Z`, `gated_paths` that differ
  from the two-person records' paths, `required_approvals` `0` with a gated path or non-`0` with none,
  and fewer approvals than required are each rejected.
- **Counts.** A mixed set (one TIGHTENS, one LOOSENS) is refused with one identity and accepted with
  two. A pure tightening that displaces nothing is accepted with zero. With old
  `min_approvals_to_loosen` 3 and new 2, two identities are refused and three accepted.
- **Fail-closed.** An unvalidatable version (`on_missing_input: ALLOW`) raises `PolicyDiffError`.
  An identical pair yields no changes and authorises with zero identities. Two runs over equal
  inputs give equal objects.
- **Redaction equals the hashed mapping.** For every combination of the real directory,
  `content_hash(EffectiveConfig.redacted) == EffectiveConfig.content_hash`. This guards the diff's
  use of `redacted` as the effective mapping (ASSUMPTION 13).
- **Oracle.** `t_diff_agrees_with_loosens_for_on_every_ordinal_threshold`: for every rule with a
  numeric threshold and an `lte`/`lt`/`gte`/`gt` comparison, ×1.5 and ×0.5 (capped at 1 on
  `*_pct`), the threshold record is LOOSENS iff `loosens_for` is true, and TIGHTENS otherwise. C-40
  records are excluded from this comparison.

### 7.5 The sweep

`tests/mutate_x5r_g9.py --sweep --must-fail tests/verify_p13_policy_diff.py` generates every
mutation below, applies each to a throwaway copy, and applies the §7.3 harness contract. The
expected test for a mutation of rule R's field f is `t_pin_<R>` if R is constitutional and f is a
pinned field other than `scope` or `mode`. If f is `scope` or `mode`, it is **either**
`t_scope_and_mode_pinned_for_every_rule` **or**, for a constitutional R, `t_pin_<R>` (X2D-6, as in
§7.3's LOSS-001 row). The message prefix is `R.f`. Counts at today's `policy.yaml` (re-measured by the step-2 review with its own
script, matching exactly):

| Family | Rules | Generated | Load |
|---|---|---|---|
| Every other `mode` | all 47 | 47 | 47 |
| Every other `scope` | all 47 | 282 | 282 |
| Every other `action` | 20 constitutional | 60 | 20 |
| Every other `comparison` | 20 constitutional | 160 | 104 |
| `threshold` ×2 and ×½ | the 14 constitutional rules with a numeric threshold | 28 | 28 |
| Value sets: EXEC-001 +MARKET; KILL-001 +TRIPPED; LLM-001 [true]; REGIME-001 [BEAR]; EXEC-001 emergency [LIMIT] | 5 named | 5 | 5 |
| **Total** | | **582** | **486** |

Acceptance: 486 loadable, 486 KILLED by attribution, exit 0; and the same run with
`--negative-control` reports 486 SURVIVED and exits 0.

### 7.6 Completeness tests

- `t_every_rule_field_is_classified`: `set(RULE_FIELDS) == set(Rule.model_fields)`.
- `t_every_action_is_ranked`: every `RuleAction` value is in `ACTION_LADDER`, and
  `ACTION_LADDER ⊆ {RuleAction values} ∪ {"HALT_ENTRIES"}`.
- `t_ladder_agrees_with_gate_precedence` (§3.2).
- `t_every_scope_pair_is_classified`: all 49 ordered pairs, agreeing with §3.3.
- `t_config_keys_are_exact`: every pattern in `CONFIG_KEY_DIRECTIONS` except the last contains no
  `*`, `?` or `[`; the last is `("**", UNDECIDABLE)`; every listed key exists in today's file.
- `t_every_basis_is_exercised` (§7.4).
- `t_no_bare_assert` (§7.1).
- `t_v1_authorisation_not_on_the_approval_path`: no module under `src/` other than
  `src/config/loader.py` calls `assert_change_authorised` (AST scan).
- `t_store_adapter_assigned_only_by_store_module` (X2E-2, X2F-10): no module under `src/` binds
  `IN_FORCE_STORE` or `VAULT_RESOLVER`, other than their `= None` declarations in
  `src/config/policy_diff.py`, and that file holds no other binding of them. The AST scan covers names
  and attributes; `setattr`, `globals()`, `vars()` and `__dict__`, by flagging either name as a string
  constant; and any `import … as` or `def` that binds them. Once a frozen spec names the B6 store's
  module, or P6.2's Vault module, this test allows that one module, which `policy_diff.py` must not
  import.
- `t_defaults_are_none`: a fresh subprocess imports `src.config.policy_diff` and reports that both
  names are `None`. No fixture can reset this.
- `t_conn_reaches_only_the_store_adapter` (X2F-10): in `src/config/policy_diff.py`,
  `assert_authorisation_current` has a parameter named exactly `conn`; `conn` is used at least twice;
  and every use is the first positional argument of a direct call
  `IN_FORCE_STORE.<method>(conn, …)` (AST scan). That is the required call form. This module runs no
  SQL of its own.

### 7.7 The tests fail when the code is broken

`tests/mutate_policy_diff_code.py` applies each code mutation below to a throwaway copy of
`src/config/policy_diff.py` and runs `tests/verify_p13_policy_diff.py` in both modes. A mutation is
caught only if the **named** test is among the `FAILED` lines in both modes; a negative control
with those tests stubbed must report every mutation uncaught. The X2 of the code (step 4) re-runs
it.

| # | Code mutation | Must be caught by (named test) |
|---|---|---|
| M-1 | `requires_two_person` excludes UNDECIDABLE | the C-08 authorisation case; `t_x5r_g9_each_mutation_is_gated` |
| M-2 | DENY and MODIFY swapped in `ACTION_LADDER` | the C-09 case |
| M-3 | `HALT_ENTRIES` and `DENY` swapped in `ACTION_LADDER` | the C-09 case (HALT_ENTRIES→DENY LOOSENS) |
| M-4 | A comparison change classified by interval containment (v0.1 behaviour) | the C-08 case (`lte→lt`) |
| M-5 | Severity classified on its own rank | the C-14 case |
| M-6 | Approval count read from the new version | the counts test (old 3, new 2) |
| M-7 | Approver de-duplication removed | the signatures test (one identity twice) |
| M-8 | C-36 records not emitted | the C-36 case |
| M-9 | `SCOPE_NARROWER_THAN` pairs reversed | the C-12 case |
| M-10 | C-01 and C-02 directions swapped | the C-01 case; the oracle test |
| M-11 | Config catch-all set to NEUTRAL | the C-39 case |
| M-12 | Removal of a rule with `exempts` classified UNDECIDABLE | the C-33 case |
| M-13 | C-40 records not emitted | the C-16 FX-001 case; the C-18 CASH-001 case |
| M-14 | `derive_combinations` ignores market layer files | the combinations test |
| M-15 | `assert_authorisation_current` takes the in-force reference from a directory argument or the candidate, instead of the store adapter (X2D-1) | the in-force anchor test (B passes v1's directory); the no-adapter test |
| M-16 | Signature verification skipped | the signatures test (wrong digest) |
| M-17 | `CONFIG_KEY_DIRECTIONS` restored to v0.2's `turnover.*` glob | `t_config_keys_are_exact`; the C-39 two-step case |
| M-18 | Expiry check removed, or moved after the anchor, or measured on the process clock instead of `database_time` | the expiry tests |
| M-19 | Approver keys compared as PEM bytes instead of raw keys | the signatures test (LF/CRLF PEM) |
| M-20 | `APPROVAL_DIGEST_TAG` dropped from the preimage | the signatures test (untagged digest) |
| M-21 | C-40's indirect triggers (3) and (4) removed | the C-40 indirect-trigger cases |
| M-22 | `src/config/policy_diff.py` installs a default (`IN_FORCE_STORE = …`, or `VAULT_RESOLVER = …`, after its declaration), with an adapter that returns one row | `t_store_adapter_assigned_only_by_store_module`; `t_defaults_are_none` |
| M-23 | The (m, None) anchor applied to any combination with no stored row, not only one with a `LAYER_ADDED` record | the first-env-layer test (no `LAYER_ADDED` record) |
| M-24 | The `requested_at` real-time check removed | the Models test |
| M-25 | `assert_authorisation_current` calls `conn.execute` itself instead of going through the adapter | `t_conn_reaches_only_the_store_adapter` |
| M-26 | The `request_used` check removed | the replay test |
| M-27 | The re-derivation at step 7 removed | the stripped-authorisation test (records blanked) |
| M-28 | The `raw_key_sha256` comparison removed | the signatures test (key differs from its pin) |
| M-29 | C-42 removed from `rule_action_direction` | the C-42 case |
| M-30 | The used-request check moved after expiry | the late-replay test |

---

## 8. Error paths

| Condition | Exception / outcome | Fail-closed behaviour |
|---|---|---|
| Old or new effective document fails `PolicyDocument` validation, or the loader raises any `PolicyError` | `PolicyDiffError` | No change list; nothing authorised |
| A document uses `HALT_ENTRIES` before `RuleAction` has it | `PolicyDiffError` (validation) | As above |
| A market layer for a market not in `MARKETS`, or an invalid env layer name | `PolicyDiffError` | Nothing authorised |
| `changes` or `diffs` out of canonical order, or duplicated; a `requested_at` that is not a real time | Model validation error → `PolicyDiffError` | Nothing authorised |
| **Any other exception during derivation or classification** (for example a `TypeError` from an unexpected value shape) | `PolicyDiffError`, chained to the original | Nothing authorised |
| An action value missing from `ACTION_LADDER` | UNDECIDABLE (C-10) | Two-person; CI already fails by `t_every_action_is_ranked` |
| A scope value missing from the scope table | UNDECIDABLE (C-13) | Two-person |
| A bound is a token on one side and a number on the other | UNDECIDABLE (C-05) | Two-person |
| A set-valued key is not a list on one side; a numeric key turns non-numeric or `null`; an unlisted key | UNDECIDABLE (C-39) | Two-person |
| A `PolicyChange` whose `basis` is not a row of this spec | Model validation error → `PolicyDiffError` | Nothing authorised |
| A `Rule` field with no row | Impossible at runtime: `t_every_rule_field_is_classified` fails CI first | — |
| An approval by an identity not listed in the in-force `governance.signature.approver_key_refs`, a reference that does not resolve (including "no Vault client yet"), a non-Ed25519 key, or a signature that does not verify | `PolicyGovernanceError` | Change refused |
| No B6 in-force store adapter installed (today, under `[DEFAULT-B6]`), or the store has no rows at all | `InForceAnchorError` (a `StaleAuthorisationError`) | Nothing applied |
| `requested_at` older than `APPROVAL_TTL_HOURS` by the database clock | `ApprovalExpiredError`, `reason` `EXPIRED` (a `StaleAuthorisationError`) | Request denied; `APPROVAL_EXPIRED` written and committed, nothing else; nothing applied |
| `requested_at` ahead of the database clock | `ApprovalExpiredError`, `reason` `FUTURE` (a `StaleAuthorisationError`) | Nothing written; the request may be retried |
| `auth.request_id` already used by an in-force row (X2F-1) | `StaleAuthorisationError` | Nothing written; a new request is needed |
| A digest mismatch, a candidate that no longer loads, or an authorisation that does not re-derive to itself (X2F-3) | `StaleAuthorisationError` | Nothing written; re-diff and re-approve |
| Fewer distinct approvers (identity and key) than the version in force requires, with any gated change | `PolicyGovernanceError` | Change refused |
| At apply time, the **stored** in-force hash or the candidate hash of any combination differs from the authorisation (a combination new in the change compares through its (m, None) row), a row is missing for a combination the in-force files derive, or the combination set differs | `StaleAuthorisationError` | No `config_version` row, in-force row or `CONFIG_CHANGED` written; re-diff and re-approve against the version in force |
| Every change TIGHTENS or NEUTRAL, with no C-36/C-40/C-41 record | `PolicyAuthorisation` with `required_approvals = "0"` | Caller writes `CONFIG_CHANGED` before the version takes effect (`[CONST-5]`) |
| Audit write of the authorisation fails | — (caller) | The version does not take effect (`[CONST-5]`) |

---

## 9. Upstream defects — required output

| # | Defect | Evidence | Consequence | Owner | Status |
|---|---|---|---|---|---|
| **F-1** | `threshold_ref` is never validated; UNIV-001, UNIV-002 and UNIV-003 do not resolve to any key | v0.1 §7; the P1.3 v0.2 plan | P2.9 behaviour on an unresolvable ref is unspecified. Keys are classified directly (§3.7) | SPEC-P1.3 v0.2 | Carried |
| **F-2** | Rule constants duplicated in non-rule config | v0.1 §7 | Two copies can diverge in one signed version. The diff governs both | SPEC-P1.3 v0.2 | Carried |
| **F-3** | `PolicyGate` grants exemptions whatever the grantor's `mode` | v0.1 §7; re-measured in step 2 (monitor grantor → ALLOW at 25% drawdown) | C-35 no longer claims an added monitor ALLOW "cannot bind"; C-36 fires in any mode | SPEC-P1.3 v0.2 | Carried |
| **F-4** | The signature covers the merged document; the override deny-list covers only `rules.`, `governance.`, `kill_switch.`; market and environment layers have no deny-list at all and may carry a whole `rules:` list (measured in step 2) | v0.1 §7; X2S-2 | One signature per combination. Every layer is now covered by derived combinations and C-41 | SPEC-P1.3 v0.2; Q-P1.3.1-2 | Carried |
| **F-5** | No field says whether a rule applies to exits | `Rule` schema | Ruling 13a needs it in P2.9 (Q-P1.3.1-11) | SPEC-P1.3 v0.2, P2.9 | Carried |
| **F-6** | `assert_change_authorised()` still trusts a caller-supplied change list and is still exported | loader.py §8 | Guarded by `t_v1_authorisation_not_on_the_approval_path` | SPEC-P1.3 v0.2 | Carried |
| **F-8** | KILL-002 is `eq` with no comparand; the validator accepts it | `Rule._coherent` | KILL-002's predicate is unstated | SPEC-P1.3 v0.2, P2.9 | Carried; Q-P1.3.1-7 |
| **F-9** | An added ALLOW rule can exempt KILL rules | Measured 2026-10-21, twice | Closed in the diff by C-36 `[DEFAULT-B3]`, at test time by §7.2(c) | This spec; SPEC-P1.3 v0.2 (B3 option d) | Mitigated |
| **F-10** | Ruling 12 reads `scope` as coverage; the schema uses it as an aggregation cell | §3.3 | B4 | Owner; SPEC-P1.3 v0.2 | Carried |
| **F-11** | Every chain written (#6 comments 6221094775, 6222485680; #37 comment 6221220445; #17 comment 6221174702) gives `KILL > HALT_ENTRIES > DENY`. The prose of #16 comment 6221092946 (the ratified full text), DECISIONS.md and #17 comment 6221093871 says "between MODIFY and DENY". #17 comment 6221174702 has both in one sentence | §1 B2 | The ladder needed a ruling | Owner | **Answered 2026-10-31: the chain.** That amends Rulings 12 and 14 as ratified, and DECISIONS.md must record it before the freeze (§10 item 12) |
| **F-12** | `trading.config_version.approval_id` is a single `uuid` | SPEC-P1.2 §6.9 | A two-person approval cannot be recorded on the row it authorises | P1.2 / P1.4 / P6.4 | Carried; Q-P1.3.1-6 |
| **F-13** | d8067b6 recorded condition 12 CLOSED prematurely | d8067b6; reopened in **4397c4f**, which records it OPEN, re-running per #6 | Closure criteria in §10 | Owner | Corrected upstream in 4397c4f |
| **F-14** | **New.** On the unedited policy, a LOSS-003 and LOSS-004 co-breach yields **KILL, LOSS-003, POOL**: the lowest-id KILL binds with its own scope | Measured in step 2 and again for this revision | Contradicts SPEC-P1.3 §10 ("consolidated drawdown 10% → GLOBAL KILL") and ADR-15 §4 ("stricter binds") | SPEC-P1.3 v0.2 (B5 option d) | New |
| **F-15** | **New.** A KILL produced by `on_missing_input: KILL` on a non-KILL rule carries `kill_scope = None`, and no spec says what P2.10 does with a scopeless kill | `_combine` reads `rule.kill_scope`; FX-001 edit measured KILL/None | Undefined kill scope at the most safety-critical boundary | SPEC-P1.3 v0.2 (B5 option d treats None as GLOBAL); P2.10 | New |

| **F-16** | **New (X2D-1).** No frozen spec records which `config_hash` is in force for a (market, environment) combination. `trading.config_version` has no combination column and no in-force marker | SPEC-P1.2 §6.9; SPEC-P1.3 §5.4 | A compare-and-swap has nothing authoritative to compare against | P1.2 / P6.4; B6; Q-P1.3.1-13 | New; fails closed under `[DEFAULT-B6]` |
| **F-17** | **New (X2E-3).** No approver is listed anywhere: `governance.signature` is `{algorithm, public_key_ref, required}`, with no `approver_key_refs` | Measured on `config/policy.yaml`, 2026-10-31 | No approval can be counted, and none can be enrolled through the approval path | Owner via B7; Q-P1.3.1-1, Q-P1.3.1-14 | New; fails closed |
| **F-18** | **New (X2F-2).** Nothing ties what runs to the in-force store. `config_version` has no trigger, `app_rw` may insert into it, `run_context.config_hash` references only it, and `run_context` has no environment column | `0001_initial.sql` l. 760, 866, 1161; SPEC-P1.3 §5.4 item 3 | Until B6's clause (5) lands, a version can run without passing the approval path | P1.2 / P6.4; Q-P1.3.1-13 | New; §6 amends SPEC-P1.3 §5.4 item 3 |

(F-7 of v0.1 was withdrawn in v0.2; it is B1.)

---

## 10. STAGE-1-GAP-AUDIT §10 — condition 12

**Current state (4397c4f):** OPEN, "in progress, re-running per #6's execution sequence", with a
"Condition 12 — reopened 2026-10-21" note. That record is correct and this spec proposes no edit to
it now.

**The condition text itself is stale** (X2S-17). It still reads "Pin `action`, `mode`, `comparison`
and `scope` of the constitutional rules; define loosening for a non-threshold change (X5R-G2)".
When the condition is closed, the row should read:

| # | Condition | Gates | Severity | State |
|---|---|---|---|---|
| **12** | Pin all five attributes (`threshold`, `action`, `mode`, `comparison`, `scope`) of every constitutional rule and `scope` and `mode` of every rule; classify every policy change by Owner Ruling 12, with UNDECIDABLE failing closed to the two-person rule (X5R-G2, X5R-G9) | P2.9; any policy change | HIGH | **CLOSED** by SPEC-P1.3.1-POLICY-DIFF (FROZEN), with the evidence below |

**Closure criteria.** The row may read CLOSED only when the closing record quotes, from one commit,
all of the following:

1. SPEC-P1.3.1 at status FROZEN, after an X2 of the spec (delta re-reviews of v0.3, v0.3.1 and
   v0.3.2, and the narrow pass of v0.3.3; steps 2 to 2e) in a separate conversation with its BLOCKER findings cleared, and **B1 to B7** each answered by the
   Owner or its default ratified.
2. `src/config/policy_diff.py` generated by X1 citing only the frozen spec, with an X2 of the code
   in a separate conversation.
3. `py -3.11 tests/verify_p13_policy_diff.py` and `py -3.11 -O tests/verify_p13_policy_diff.py`
   both exit 0, and the same on Python 3.12+ in CI (or condition 15 named as carried).
4. `py -3.11 tests/mutate_x5r_g9.py --must-fail tests/verify_p13_policy_diff.py --must-pass
   tests/verify_p13_config.py` exits 0 with five `[KILLED]` lines, **each attributed to the pin in
   §7.3**; and the same command with `--negative-control` exits 0 with five `[SURVIVED]` lines.
5. `py -3.11 tests/mutate_x5r_g9.py --sweep --must-fail tests/verify_p13_policy_diff.py` exits 0
   with every loadable mutation KILLED by attribution, the loadable count equal to §7.5's for the
   policy file at that commit; and with `--negative-control`, every one SURVIVED.
6. `py -3.11 tests/mutate_policy_diff_code.py` exits 0, every M-1 to M-30 caught by its named test
   in both modes, and its negative control passes.
7. `t_no_bare_assert` passes, and `verify_p13_config.py` and `verify_p11_x5_conditions.py` still
   pass in both modes.
8. SPEC-P1.3 §5.3 and §5.4 item 3 carry the §6 text, by a logged re-open to v0.1.1 with a change-log
   entry (Q-P1.3.1-9, answered).
9. If B5's default (a) was ratified rather than option (d) landed, F-14 and F-15 are carried in
   writing against SPEC-P1.3 v0.2 and P2.10.
10. The in-force anchor (B6) is either defined in a frozen P1.2 / P6.4 spec and wired as the store
    adapter, or, if B6's default was ratified, Q-P1.3.1-13 (F-16) is carried in writing as a
    prerequisite of the first policy change after go-live, with F-18. B7's answer (no bootstrap,
    reopened when a second approver exists) and Q-P1.3.1-14 are carried the same way, as a
    prerequisite of the first gated change. Condition 12 is about classifying and gating changes. It can close while
    applying them still waits on B6, provided that wait fails closed (§5.3, §8), which it does.
11. Q-P1.3.1-11 is carried in writing to P2.9 (#16) as a requirement, because B1's answer is the one
    that is not fail-closed for exits.
12. **Done at the freeze:** `DECISIONS.md` records the Owner's answer to B2 as an amendment of Rulings 12
    and 14, corrects "between `MODIFY` and `DENY`", and records B1 and B7 with it.
13. Q-P1.3.1-15 is carried in writing to P2.10 (#17).

---

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | Direction is decided by Ruling 12's rows; where it has none, by its permitted-set principle when provable; otherwise UNDECIDABLE | The ruling is binding and adds one principle; this spec adds none | No — it is the ruling | **Critical** |
| 2 | Any `comparison` change is UNDECIDABLE, and so is every predicate field changed with it | Ruling 12 `comparison` row | No — ruling | High |
| 3 | Ladder `KILL > HALT_ENTRIES > DENY > MODIFY > ALLOW` | The Owner's answer to B2; every written chain | Yes — one constant | **High if the pin in §7.2(f) is dropped:** `DENY → HALT_ENTRIES` is free, and on any rule but LOSS-001 and LOSS-002 it stops that rule denying exits (X2F-4) |
| 4 | Scope narrowness = evaluation-set containment: 2 ordered pairs, 19 UNDECIDABLE with reasons | Ordering by cell size gives opposite answers | Yes — B4 option (c) | Low |
| 5 | `severity` is NEUTRAL alone and follows the action otherwise | Ruling 12 `severity` row | No — ruling | Low |
| 6 | Rule addition is TIGHTENS or NEUTRAL; effects on other rules are derived records (C-36 LOOSENS, C-40 UNDECIDABLE) | Keeps every ruled record intact while closing the measured zero-approval paths (F-9, X2S-1) | Yes — B3, B5 | **Critical** if reversed: the kill switch can be switched off (B3) or narrowed to POOL (B5) at zero approvals |
| 7 | No exit-path overlay | Ruling-conformant (B1); its real blast radius — TURN-002, its config key, `holding.min_sessions`, added DENY rules, at zero approvals — is stated, and exit protection is put to P2.9 as an explicit requirement | Yes — B1 options (B), (C) | High if wrong: a protective stop-out can be denied after a free tightening |
| 8 | Pins: five attributes on 20 constitutional rules; `scope` and `mode` on all 47; plus the KILL-002 exemption pin and the kill-rule set pin | Ruling 12 "Required tests"; §7.2(d) is the test-time half of B5 | No — ruling | Medium |
| 9 | Rule removal is LOOSENS for every rule | Ruling 12 | No | Low |
| 10 | `enforce → monitor` is LOOSENS on every rule | Ruling 12 | No | Low |
| 11 | `kill_scope` / `modify` appearing with an action change take the action's direction | Consequences the loader enforces | Yes | Low — C-40 covers the kill-scope effect independently |
| 12 | Monitor rules are classified as if they bound | Blocks loosen-then-promote | Yes | High |
| 13 | **The combination set is derived from the two policy directories**; a layer file appearing or disappearing is UNDECIDABLE | A caller-supplied set let a market-layer loosening pass with zero approvals (X2S-2); a fixed key match made new combinations unapprovable (X2S-9) | Yes | High |
| 14 | The approval count comes from the version in force at approval | A version must not approve itself | No | High |
| 15 | **An authorisation is applied only by compare-and-swap** against the **stored** in-force hash per combination, read by this module on the writer's transaction, and the candidate hash; until a frozen spec defines the store, nothing is applied (`[DEFAULT-B6]`) | Stale bases undo approved changes (X2S-3); a caller-supplied reference reopens that (X2D-1) | Yes — B6 | High |
| 16 | **Approvals are Ed25519 signatures by identities listed, with key references, in the in-force policy (`governance.signature.approver_key_refs`) over a domain-tagged diff digest**; keys compared raw; distinct identities and keys | Plain strings let one person supply two names (X2S-10); a caller-supplied key lookup does the same (X2D-2) (X2S-10); SPEC-P1.3 §5.2 already chose Ed25519 for attribution | Yes | High |
| 17 | Config keys get a direction only by exact name; unlisted keys are UNDECIDABLE | Globs gave future keys a direction (X2S-11) | Yes | Medium — friction at team size 1 |
| 18 | `authority` stays UNDECIDABLE | It keys the pinned constitutional set | Yes | Low |
| 19 | Every record carries a `basis` row id; the classifier helpers return theirs | Traceability; makes basis coverage testable (X2S-8) | Yes | Low |
| 20 | Evidence counts a kill only when a named pin or test fails with the expected message, in both modes, with a negative control | A suite exit code passed with every pin removed (X2S-4) | Yes | **Critical** for the evidence: otherwise step 5 proves nothing |
| 21 | Removing an `InstrumentType` from `tradeable` stays TIGHTENS, a recorded departure from ADR-09 row 7 | Every applied version carries the Owner's policy signature at team size 1; a role-based approval layer is not justified for one key | Yes | Low — revisit when a non-Owner signer is enrolled |
| 22 | `required_approvals` and every other authorisation field are strings | `jcs-nonum-1` bans JSON numbers (X2S-6) | Yes | Medium — otherwise no change can be recorded |
| 23 | **Approvals expire 24 h after `requested_at`**, measured on the database clock after the lock is held; `requested_at` and `request_id` are inside the signed digest | ADR-09 row 2 (FROZEN): 24 h SLA, "request denied" on expiry. Applied to every authorisation, not only limit increases: simpler, and a stale request is re-diffed anyway (X2D-3) | Yes | Low — an expired request is re-requested |
| 24 | **The approval digest is domain-separated** by `APPROVAL_DIGEST_TAG` | An approval and a policy signature may use the same Owner key; a fixed tag makes their preimages disjoint by construction (X2D-5) | Yes | Low — hygiene; no replay was found without it |
| 25 | **C-40 also fires on indirect paths:** any non-NEUTRAL config record when R uses a `*_ref`, and a C-26 shrink that removes R | A kill-capable rule can fire in more states without a record on itself (X2D-4); failing closed on any config change is simpler than resolving templated refs (F-1) | Yes | Low — both paths are also pinned today |
| 26 | **A combination new in a change is anchored by its (m, None) row**, only when its diff carries the `LAYER_ADDED` record for that env file | Without it the first env layer could never be applied (X2E-1); the two have one effective document, so the anchor is exact | Yes | Low — fails closed on any other missing row |
| 27 | **The store enforces the compare-and-swap itself** (B6's required shape): `previous_config_hash`, a store-side check, closing rows, and a genesis outside the approval path that lists no approver | A Python check can be skipped (X2E-2); a retired combination and the first insert need a defined state; a map must not enter at genesis | Yes — B6 | Medium — the shape binds the P1.2 / P6.4 author |
| 28 | **Clock tolerance is zero**; `requested_at` comes from the database when the request opens | The simplest rule that fails closed; a refused request is retried (X2E-6) | Yes | Low |
| 29 | **An approval is single-use**, in §5.3 and in the store | A revert returns the hashes an old approval was given against (X2F-1) | Yes | High |
| 30 | **§5.3 re-derives the authorisation from a verified `old_dir`** | The digest covers hashes, not the records or the count, and the object travels as data for up to 24 h (X2F-3). The anchor still comes only from the store, so X2D-1 stays closed | Yes | High |
| 31 | **Map entries pin the raw key's hash** | The policy hash excludes referenced values (X2F-7) | Yes | Medium — dormant while the map is empty, but the format freezes now |
| 32 | **The `HALT_ENTRIES` set is both pinned and gated (C-42)** | A pin is a test: it never meets a candidate directory outside the repository. C-42 refuses the same move at governance, and Ruling 14's own change stays C-09 | Yes | Medium — if it is wrong, one more change needs two approvers |
| 33 | **The used-request check runs before expiry** | A late replay must not write a denial of a request that was applied (X2G-2) | Yes | Low |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|---|---|---|---|
| 1 | `[DEFAULT-B1]` Exit protection belongs in P2.9, as an explicit requirement that a computed exposure-reducing order is never denied by TURN-002, TURN-001 or HOLD-001 | No ruling covers it; 13a covers missing, stale or ambiguous inputs only | Owner answer to B1; P2.9 spec | Until P2.9 meets Q-P1.3.1-11, a free tightening of TURN-002 can deny a stop-out |
| 2 | Withdrawn: the Owner answered B2 on 2026-10-31 (§1) | — | — | — |
| 3 | `[DEFAULT-B3]` An exemption is a narrowing of the exempted rule's scope | Ruling 12's addition row read with its scope row | Owner answer to B3 | If the addition row governs every effect of an addition, the hole is closed only by the pin and option (d) |
| 4 | `[DEFAULT-B4]` `scope` is an aggregation cell in P2.9 | Schema and `policy.yaml` usage | Owner answer to B4; P2.9 | Some UNDECIDABLE outcomes are unnecessary friction |
| 5 | `[DEFAULT-B5]` A displaced GLOBAL kill is an UNDECIDABLE effect on the GLOBAL rule | SPEC-P1.3 §4.2's lowest-id binding plus C-17 | Owner answer to B5; SPEC-P1.3 v0.2 option (d) | If the Owner accepts option (c), a GLOBAL kill can be narrowed to POOL at zero approvals |
| 6 | P2.9's evaluator implements `passed = observed <comparison> threshold` | P2.9 is unwritten; SPEC-P1.3 §3.2 implies it | P2.9, against C-01/C-02 tests | Every threshold classification inverts |
| 7 | `PolicyGate` applies exemptions and kill scope as loader.py §10 does today | Read and measured | SPEC-P1.3 v0.2 | If option (d) lands, C-40 becomes unnecessary (removed by revision) |
| 8 | `HALT_ENTRIES` will be spelled exactly `"HALT_ENTRIES"` | Ruling 14 and #6 spell it so | #17's code | `t_every_action_is_ranked` fails CI |
| 9 | Every combination that will run is `({None} ∪ MARKETS) × ({None} ∪ env files present)` | The loader takes `market` and `environment` only; `TRADING_ENV` names an env file | P6.4 deployment manifest | A run with an environment that has no file loads base plus market layer, which is the (m, None) combination already diffed |
| 10 | `[DEFAULT-B6]` P1.2 / P6.4 will define an authoritative in-force `config_hash` for every combination the in-force files derive, in the shape B6 states, readable by this module on the writer's transaction | No frozen spec defines it (F-16); SPEC-P1.2 §6.9 defines `config_version`, not the in-force record or the writer | Owner answer to B6; Q-P1.3.1-13 | Until it exists, no policy change can be applied by this path (fail-closed). Without the lock, two concurrent applies could both pass the compare-and-swap |
| 11 | Approver keys are named in the in-force policy's `governance.signature.approver_key_refs` and readable through `VAULT_RESOLVER` at approval time | The frozen loader accepts the map (measured); approver enrolment is Q-P1.3.1-1; the Vault client is P6.2 | P6.2; SPEC-P1.3 v0.2 (Q-P1.3.1-14) | No approval can be counted, so every gated change is refused: fail-closed |
| 12 | At team size 1 the only enrolled policy signer is the Owner | ADR-09 `[DEFAULT-3]` of P0.1 | Q-P1.3.1-1 | A non-Owner signer could remove an `InstrumentType` without the Owner (DECISION 21) |
| 13 | `EffectiveConfig.redacted` equals the hashed merged mapping | loader.py `_redact` only renders `Decimal` as string and lists for tuples; YAML yields neither difference | The redaction test in §7.4 | The diff would compare something other than what was signed |
| 14 | `CONFIG_KEY_DIRECTIONS` directions are as tabulated | Carried from v0.1; the PDT floor is unverified (condition 16) | Broker PDT documentation | One key misclassified |
| 15 | Python 3.12+ behaves as 3.11 for this code | Only `py -3.11` has the dependencies locally | Condition 15, CI | Evidence must be re-run |
| 16 | `[DEFAULT-B7]` Without an Owner-ruled bootstrap, `approver_key_refs` can neither be created nor grow: zero identities are listed today (F-17), and adding one is gated | Adding an approver widens who can approve, so it is gated | Owner answer to B7 | No LOOSENS or UNDECIDABLE change is ever approvable until the Owner rules |
| 17 | The database clock is a trustworthy UTC clock for expiry | P1.1 forbids naive datetimes and keeps clocks out of the domain; the writer's connection is the one shared clock at apply time | P6.4 (NTP on the DB host) | A skewed DB clock expires requests early (fail-closed) or late |
| 18 | P6.2's approver tooling can read the database clock when it opens a request | The check runs on that clock, and a tooling clock ahead of it is refused (X2E-6) | P6.2 | Valid requests are refused at apply time and retried: fail-closed friction only |

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|---|---|---|---|
| **Q-P1.3.1-1** | Who is the second approver, and how is each approver's Ed25519 key enrolled in Vault and listed in `governance.signature.approver_key_refs`? (carries Q-P1.3-1; bootstrap is B7) | Owner; P6.2 | Enrol a second identity in Vault | Every gated change |
| **Q-P1.3.1-2** | One signature per (market, env, override) combination, or sign the base and hash layers separately? Should market and env layers get a deny-list like the override layer? (F-4) | Owner + P6.4 | SPEC-P1.3 §5.2 vs §6 | P6.4 |
| **Q-P1.3.1-3** | How does P2.9 treat an unresolvable `threshold_ref`? (F-1) | P2.9 author | UNIV-001/002/003 refs | P2.9 |
| **Q-P1.3.1-4** | Add `applies_to` to `Rule`? (F-5) | SPEC-P1.3 v0.2; Owner via B1 | `Rule` schema; Ruling 13a | P2.9 |
| **Q-P1.3.1-5** | Does kill-switch liquidation go through `PolicyGate` at all? | P2.10 | P2.10 liquidation design | P2.10 |
| **Q-P1.3.1-6** | Where is a two-person approval stored, given `config_version.approval_id` holds one id? (F-12) | P1.2 / P1.4 / P6.4 | SPEC-P1.2 §6.9; SPEC-P1.4 §3 | The first policy change after go-live |
| **Q-P1.3.1-7** | What does KILL-002's `eq` compare against? (F-8) | SPEC-P1.3 v0.2; P2.9 | `Rule._coherent`; KILL-002 | P2.9 |
| **Q-P1.3.1-9** | Is the §5.3 amendment a re-freeze event for SPEC-P1.3? d8067b6 left it at v0.1 FROZEN. **Answered by the Owner, 2026-10-31: a logged re-open at closure of condition 12.** SPEC-P1.3 goes to v0.1.1, which avoids the separate P1.3 v0.2 plan, with a change-log entry, because STAGE-0-FREEZE §8 says a re-opening with no entry has not happened | Owner | SPEC-P1.3 header; STAGE-0-FREEZE §7 to §9 | Closure of condition 12 (§10 item 8) |
| **Q-P1.3.1-10** | Who owns the next SPEC-P1.3.1 revision? The P1.3 v0.2 plan also proposes one, for `applies_to` | Owner | `AI-Trading-Agent-stage1-fresh-reviews/P1.3-v0.2/PLAN.md` §8 | Versioning of this spec |
| **Q-P1.3.1-11** | **New.** Under B1 (A), P2.9 must guarantee that an order the risk engine computes as exposure-reducing (Ruling 13a's definition) is never denied by TURN-001, TURN-002 or HOLD-001, and must state which other rules bind against such an order | P2.9 author | Ruling 13a; TURN-002 inputs (`intended_notional`) | **P2.9** |
| **Q-P1.3.1-12** | **New.** Take B5 option (d) in SPEC-P1.3 v0.2: a KILL verdict is GLOBAL if any binding KILL outcome's rule is GLOBAL or has no `kill_scope`? (F-14, F-15) | SPEC-P1.3 v0.2; Owner | SPEC-P1.3 §4.2; loader.py `_combine` | P2.10; removal of C-40 |
| **Q-P1.3.1-13** | **New (X2D-1, X2E-1, X2E-2, F-16).** Define the authoritative in-force `config_hash` for every combination the in-force files derive, in the shape B6 states: closing rows for retired combinations, `previous_config_hash` with a store-side check and a `CONFIG_CHANGED` citing the same `request_id`, a genesis outside the approval path, written only in the transaction that inserts `config_version`, under the policy-change lock, append-only; read by `assert_authorisation_current` on that transaction. It also covers clause (5), reused versions, the genesis rule, and the policy-writer role. The store's own suite proves it: an out-of-sequence insert, an insert with no `CONFIG_CHANGED`, a used `request_id`, a `config_version` insert with no in-force row, a non-backtest run on another hash, an insert by `app_rw`, and any update, delete or truncate are refused, and of two concurrent applies one commits. Also decide whether an audit job or process start re-verifies each in-force row's signatures from its `CONFIG_CHANGED` payload, the only defence against a forged event | P1.2 / P6.4 author; Owner via B6 | SPEC-P1.2 §6.9; SPEC-P1.3 §5.4 | **Applying any policy change** (the first after go-live) |
| **Q-P1.3.1-15** | **New (X2F-5).** A `HALT_ENTRIES` outcome must decide entries only. For an exit, the gate resolves the binding set with `HALT_ENTRIES` outcomes removed, or a halt displaces a DENY: with LOSS-001 and KILL-001 both failing, an ordinary exit could go out while the kill switch is tripped. Test: kill switch TRIPPED, LOSS-001 breached, a non-liquidation exit → DENY by KILL-001 | #17 / P2.10 | `_combine`; SPEC-P1.3 §4.1 | **P2.10** |
| **Q-P1.3.1-14** | **New (X2D-2).** Document `governance.signature.approver_key_refs` in SPEC-P1.3 (§3 schema, §5.2), or move it to a typed `Governance` field in SPEC-P1.3 v0.2; deliver the client `VAULT_RESOLVER` wraps; and, if B7 (b) is chosen, specify the bootstrap rule with the B6 store | SPEC-P1.3 v0.2; P6.2 | `Governance.signature: Mapping[str, Any]` in loader.py §5 | Counting any approval |
| Q15 *(carried)* | Suites on Python 3.12+ | CI | `python3.12 -O tests/verify_p13_policy_diff.py` | All |

(Q-P1.3.1-8 of v0.2, "reopen condition 12?", is withdrawn: 4397c4f reopened it.)

## CONTRACTS EXPORTED

| Name | Kind | Signature or schema | Consumers |
|---|---|---|---|
| `derive_combinations` | function | `(old_dir: Path, new_dir: Path) -> tuple[tuple[str \| None, str \| None], ...]`; raises `PolicyDiffError` | P6.4, tests |
| `diff_policies` | function | `(old_raw: Mapping, new_raw: Mapping, *, market=None, environment=None, old_layers=frozenset(), new_layers=frozenset()) -> PolicyDiff`; raises `PolicyDiffError` | tests, `diff_policy_dirs` |
| `diff_policy_dirs` | function | `(old_dir: Path, new_dir: Path) -> tuple[PolicyDiff, ...]` | P6.2, P6.4 |
| `authorisation_digest` | function | `(diffs: Sequence[PolicyDiff], request_id: str, requested_at: str) -> str` (64 hex), preimage prefixed by `APPROVAL_DIGEST_TAG` | Approver tooling (P6.2), P1.4 |
| `assert_policy_change_authorised` | function | `(old_dir: Path, new_dir: Path, approvals: Sequence[ApprovalSignature], *, request_id: str, requested_at: str) -> PolicyAuthorisation`; no key parameter; keys from the in-force `governance.signature.approver_key_refs`; raises `PolicyGovernanceError`, `ApprovalExpiredError`, `PolicyDiffError` | **P6.2, P6.4 — the only approval path** |
| `assert_authorisation_current` | function, **precondition** | `(auth: PolicyAuthorisation, conn, old_dir: Path, candidate_dir: Path) -> None`. Reads the in-force anchor, the clock and the used-request check itself on `conn` through the module-level B6 store adapter; no hash or time parameter, and `old_dir` is verified against the store before it is read. Raises `InForceAnchorError` (always, until the B6 store exists), `StaleAuthorisationError`, `ApprovalExpiredError`. Must be called in the transaction that records the new in-force version, under the policy-change lock | **P1.2, P1.4, P6.4** — the config writer and the B6 store (Q-P1.3.1-13) |
| `action_direction` | function | `(old: str, new: str) -> tuple[Direction, str]` | Tests; #17 |
| `rule_action_direction` | function | `(rule_id: str, old: str, new: str) -> tuple[Direction, str]`; C-42, otherwise `action_direction` | `diff_policies`, tests; #17 |
| `scope_direction` | function | `(old: str, new: str) -> tuple[Direction, str, str]` | Tests |
| `key_direction` | function | `(path: str) -> KeyDirection` | P6.2; any phase adding a config key |
| `PolicyChange`, `PolicyDiff`, `ApprovalSignature`, `PolicyAuthorisation` | models | §4; all-string, `jcs-nonum-1`-safe | P1.4 (`CONFIG_CHANGED` payload), P6.2, P6.4 |
| `PolicyDiffError` | exception | subclass of `PolicyError` | P6.2 |
| `StaleAuthorisationError` | exception | subclass of `PolicyGovernanceError` | P6.4 |
| `InForceAnchorError` | exception | subclass of `StaleAuthorisationError`: no authoritative in-force record is available | P6.4 |
| `ApprovalExpiredError` | exception | subclass of `StaleAuthorisationError`, with attributes `reason` (`EXPIRED` or `FUTURE`) and `request_id`: `requested_at` older than `APPROVAL_TTL_HOURS`, or in the future. Catch it before `StaleAuthorisationError` | P6.4, P1.4 (`APPROVAL_EXPIRED`) |
| `Direction`, `ChangeKind`, `KeyDirection` | enums | §4 | P6.2, P1.4 |
| `MARKETS`, `ACTION_LADDER`, `HALT_ENTRIES_RULES`, `SCOPE_NARROWER_THAN`, `APPROVAL_DIGEST_TAG`, `APPROVAL_TTL_HOURS` | constants | §4 | #17, P6.2, tests |
| `InForceStore`, `IN_FORCE_STORE` | protocol, module variable | §4; `None` until the B6 store exists; assigned only by its module and tests | P1.2, P6.4, tests |
| `VAULT_RESOLVER` | module variable | `Callable[[str], bytes] \| None`; `None` until P6.2; assigned only by P6.2's module and tests | P6.2, tests |
| `CONFIG_KEY_DIRECTIONS` | constant | ordered `(exact key, KeyDirection)`; last entry `("**", UNDECIDABLE)` | P6.2; any phase adding a config key |
| `RULE_FIELDS` | constant | equals `set(Rule.model_fields)` | CI |
| `CLASSIFICATION_BASES` | constant | `{"C-01", …, "C-42"}` | CI, P1.4 |
| `tests/verify_p13_policy_diff.py` | test suite | §7.2, §7.4, §7.6; `require()` only; `FAILED <name>: <RULE-ID>.<field> …` lines | **CI**, with and without `-O` |
| `tests/mutate_x5r_g9.py` | harness | `[--sweep] [--negative-control] --must-fail SUITE [--must-pass SUITE …]` → exit 0 iff every loadable mutation is KILLED by attribution (or, under `--negative-control`, every one SURVIVED) | CI, gap audits |
| `tests/mutate_policy_diff_code.py` | harness | M-1 to M-30, attributed to named tests, with a negative control | X2 of the code, step 5 |
| AMENDMENT SPEC-P1.3 §5.3 | spec text | §6 | SPEC-P1.3, #6 step 3 |
| ~~`LIQUIDATION_PATH_RULES`~~ | ~~constant~~ | Removed in v0.2 (`[DEFAULT-B1]`); restored only under B1 option (B) | — |

**END OF SPEC-P1.3.1-POLICY-DIFF v0.3.4 (FROZEN)**
