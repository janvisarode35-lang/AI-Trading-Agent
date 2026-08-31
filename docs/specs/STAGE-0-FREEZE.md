---
id: STAGE-0-FREEZE
version: 1.1
status: ACTIVE
phase: Stage 0 — DECIDE, closure
depends_on: [SPEC-P0.1-DECISIONS v0.3, SPEC-P0.2-PROVIDERS v0.5, SPEC-P0.3-BUDGET v0.5, master-research-summary.md]
produces: [STAGE-0-FREEZE-RECORD, FREEZE-PROCEDURE, CARRIED-FORWARD-REGISTER]
---

# STAGE 0 FREEZE RECORD

**Frozen at:** 2026-08-25
**Frozen by:** JS — Project Owner, acting as Head of Architecture and Risk Owner
**Authority:** ADR-09 row 12 (Owner), the only role that may take or re-take an architectural decision
**Git HEAD at freeze:** `dd0bdb09b6912c93db2fcdd07570a8f39a656d46` (2026-08-21T15:35:52+05:30)

> The prompt pack defines no freeze procedure. This document **is** the procedure, kept as small
> as the job allows: an artifact list with hashes, the decisions frozen, the items carried
> forward, and the conditions under which a frozen decision may be re-opened.

---

## 1. What "frozen" means, and what it does not

**Frozen means:**
- The **architectural decisions** in ADR-01 through ADR-15 and AD-1 through AD-5 are fixed.
- **No silent change is permitted.** A change requires a documented trigger from §7, the authority
  in §8, and a version bump on the affected spec.
- Downstream stages may build against these decisions without asking whether they will move.

**Frozen does NOT mean:**
- That every research question is closed. **Eleven items are carried forward in §6**, one of them
  gating.
- That the specs are immutable. They are amendable **through a recorded procedure**, not by
  editing in place.
- That measurement-by-design questions have been answered. Three of them (Q13, Q14, Q15) are
  answerable only by running the system and must never be converted into pre-implementation
  decisions.

---

## 2. Frozen artifact list, with versions and hashes

SHA-256 over the exact file bytes at the moment of freeze. Any later byte-level change to a frozen
artifact **must** be accompanied by a version bump and an entry in §9.

| Artifact | Version | Status | Bytes | SHA-256 |
|---|---|---|---|---|
| `master-research-summary.md` | 1.0 | source of truth | 63,677 | `195e8575bd8846a02489af923161baee0e64e81ac4f6e7d223dd09f25257cb53` |
| `docs/PROMPT-PACK.md` | — | process, not frozen | 83,391 | `ff3c791fd81332c8e95163a491b54db8722de985eeefacedb994efaedf42cdbf` |
| `docs/specs/SPEC-P0.1-DECISIONS.md` | **0.3** | **FROZEN** | 175,620 | `3ca6ed70ce9476c4171ec01cdad541e993d55514b41efdd4f9eaee927439f974` |
| `docs/specs/SPEC-P0.2-PROVIDERS.md` | **0.5** | **FROZEN** | 157,682 | `f332af022e634db09d9d2cb39f0f8f5019d430bf849278cd6d9e012703fb7faf` |
| `docs/specs/SPEC-P0.3-BUDGET.md` | **0.5** | **FROZEN** | 138,580 | `667b002d70b3a9ad43b5dff0fc6bf6387ff2d8e90b402e803f75168e7ff3f47f` |

**Verification command** — a reviewer or a CI step can confirm the freeze has not been broken:

```bash
sha256sum master-research-summary.md docs/PROMPT-PACK.md docs/specs/SPEC-P0.*.md
```

`PROMPT-PACK.md` is hashed but **not frozen**: it is process, not architecture, and it carries two
outstanding defects (P0.3 amendments A-16 and A-17) that should be corrected in it rather than
worked around.

---

## 3. Decisions explicitly frozen

**Twenty architectural decisions.** Fifteen ADRs from P0.1 v0.1, unchanged, plus five Owner
decisions taken at closure.

| Ref | Decision | Source |
|---|---|---|
| ADR-01 | Grafana + FastAPI + Telegram; no custom frontend before live capital | P0.1 §3 |
| ADR-02 | systemd timers → `docker compose run`, plus one long-lived monitor unit | P0.1 §3 |
| ADR-03 | No Kubernetes before three named metrics hold simultaneously | P0.1 §3 |
| ADR-04 | EDGAR + FRED + one news API + broker corporate actions; social media excluded permanently | P0.1 §3 |
| ADR-05 | Equities only; ETFs read-only in v1; futures and options never | P0.1 §3 |
| ADR-06 | Vector DB killed; pgvector inside existing Postgres is the only escape hatch | P0.1 §3 |
| ADR-07 | Quarterly expanding-window retrain + 5 enumerated out-of-cycle triggers | P0.1 §3 |
| ADR-08 | Promotion proven on walk-forward OOS; live shadow detects harm only | P0.1 §3 |
| ADR-09 | 12 enumerated HITL actions; **risk DENY is never overridable** | P0.1 §3 |
| ADR-10 | RPO 0 state; RTO-safe 30 min; RTO-operational 4 h; 5-part recovery definition | P0.1 §3 |
| ADR-11 | Dual-market by contract, US-first by capital | P0.1 §3 |
| ADR-12 | Long-only, cash account, no margin, through v2 | P0.1 §3 |
| **ADR-13** | **Swing: median 15 trading days, band 3–40, hard max 120. Treat as irreversible** | P0.1 §3 |
| ADR-14 | 1,500 US names, weekly reconstitution with 1,300/1,700 hysteresis, one decision per session | P0.1 §3 |
| ADR-15 | USD base, segregated pools, **no system-initiated FX conversion ever**, dual limit enforcement | P0.1 §3 |
| **AD-1** | Assumption A14 replaced: ≈$129/mo paper, ≈$228/mo live verified; VM and backup unpriced; **total operating cost INCOMPLETE** | P0.1 §0.5.1 |
| **AD-2** | Walk-forward rolls **3 months**, 1.5-year initial train; 20-year/+$120-mo alternative rejected | P0.1 §0.5.1 |
| **AD-3** | US backup broker is **MANUAL-ONLY**, excluded from every RTO claim | P0.1 §0.5.1 |
| **AD-4** | Zerodha primary · Upstox automated monitoring backup · IBKR manual-only emergency | P0.1 §0.5.1 |
| **AD-5** | OpenAI `gpt-5.6-luna` primary, DeepSeek `deepseek-v4-flash` fallback — **CONDITIONAL on M-7** | P0.1 §0.5.1 |

**Ten invariants** (P0.1 §10.3 I1–I10) and **fifteen provider correctness rules** (P0.2 §10.5
N1–N15) and **twelve budget rules** (P0.3 §15 B1–B12) are frozen with them.

### 3.1 Constitutional amendment carried by this freeze

**AD-5 changes the `[CONST]` FIXED STACK line.** It currently reads
"DeepSeek (primary LLM) + GPT-4o-mini (fallback)". Both halves are now wrong: the ordering is
reversed, and `gpt-4o-mini` is not in OpenAI's catalogue (P0.2 F-8, `[V]`). It must read:

> **OpenAI `gpt-5.6-luna` (primary LLM) + DeepSeek `deepseek-v4-flash` (fallback)**

This is recorded here as a constitutional amendment rather than buried inside an ADR, because
Block A's FIXED STACK is higher precedence than any spec and a silent divergence between the
Constitution and the frozen specs is exactly the drift this freeze exists to prevent.

---

## 4. Amendment disposition — all twenty

| # | Source | Disposition | Where |
|---|---|---|---|
| A-1 | P0.2 | **APPLIED** via AD-5 | P0.1 §0.5.1 |
| A-2 | P0.2 | **APPLIED** — model ids in config, DeepSeek now fallback | P0.2 §6, §10.4 |
| A-3 | P0.2 | **APPLIED** (cosmetic) — Polygon → Massive | P0.1 §9.1 |
| A-4 | P0.2 | **APPLIED — AD-4** | P0.1 ADR-11 |
| A-5 | P0.2 | **NO CHANGE NEEDED** | — |
| A-6 | P0.2 | **APPLIED — AD-1** | P0.1 §8 |
| A-7 | P0.2 | **APPLIED** (additive) — rules N1, N2 | P0.1 ADR-04 |
| A-8 | P0.2 | **APPLIED** (additive) — rule N3 | P0.1 ADR-04 |
| A-9 | P0.2 | **APPLIED — AD-3** | P0.1 ADR-10 |
| A-10 | P0.2 | **APPLIED — AD-5**, conditional on M-7 | P0.1 §0.5.1 |
| A-11 | P0.2 | **APPLIED** (additive) — tick size date-versioned | P0.1 §6 |
| A-12 | P0.2 | **APPLIED** (additive) — rule N11 | P0.1 §0.4 |
| A-13 | P0.3 | **APPLIED — AD-2** | P0.1 ADR-08 |
| **A-14** | P0.3 | **NOT APPLIED — CARRIED FORWARD** (§6) | P0.3 §6.3 |
| A-15 | P0.3 | **APPLIED — AD-1** | P0.1 §8 |
| A-16 | P0.3 | **APPLIED** (cosmetic) — prompt-pack defect recorded | §2 note |
| A-17 | P0.3 | **APPLIED** (cosmetic) — gate width stays 15 | P0.3 §5.3 |
| A-18 | P0.3 | **APPLIED** — closed by AD-5 | P0.1 §0.5.1 |
| A-19 | P0.3 | **APPLIED** (additive) — Chain B row-width premise stated | P0.1 ADR-13 Chain B |
| A-20 | P0.3 | **APPLIED** (additive) — Chain B bitemporality | P0.1 ADR-13 Chain B |

**Nineteen applied. One (A-14) deliberately not** — it is an unresolved `[CONST-1]` / `[CONST-6]`
question and was not among the five decisions taken. Deciding it silently to tidy the queue would
be precisely the failure this freeze prevents.

---

## 5. The five authority decisions, with rationale

| Ref | Decision | Rationale | Conditional? |
|---|---|---|---|
| **AD-1** | A14 replaced. ≈$129/mo paper, ≈$228/mo live **verified**; VM and off-VM backup **unpriced**; total operating cost marked **INCOMPLETE** | Conflating verified recurring cost with full operating cost is how an infrastructure line vanishes from a budget. No VM or backup price is invented; the difference stays visible | Until P0.3 Q-1 and Q-2 resolve |
| **AD-2** | Walk-forward rolls = **3 months**, 1.5-year initial train | 34 windows are unreachable at 6-month rolls from 10 years of purchased history (~16 result). 3-month rolls reach 34 from history already bought, at ~100 closed trades per window. The 20-year alternative costs **+$120/mo** and is not required by the architecture | No |
| **AD-3** | US backup broker **MANUAL-ONLY**, excluded from all RTO claims | IBKR needs a browser login on the gateway machine, idles out in ~6 min, hard-resets every 24 h (P0.2 F-12 `[V]`). It cannot authenticate itself unattended at the moment it is needed. **Neither RTO number changes** — both were always primary-broker and VM-rebuild derived | No |
| **AD-4** | Zerodha primary · Upstox automated monitoring backup · IBKR manual-only emergency | `[CONST-10]` names Zerodha. Upstox's `extended_token` removes daily re-auth from the **read-only** path only; the order path still re-auths daily. Authentication convenience is not grounds to promote a broker | Upstox → primary would need a `[CONST-10]` amendment |
| **AD-5** | OpenAI `gpt-5.6-luna` primary, DeepSeek `deepseek-v4-flash` fallback | OpenAI publishes that API data is not used for training absent opt-in, and that abuse logs are retained 30 days `[V]`. DeepSeek's terms could not be retrieved at all | **YES — conditional on M-7.** The entire margin is criterion C5, resting on an *absence of evidence* about DeepSeek, not evidence against it |

---

## 6. Items explicitly carried forward across the freeze

**Freezing does not close these.** Full detail in P0.1 §9.

### 6.1 FORMERLY GATING — all three retrieved and resolved on 2026-08-26

**Stage 1 now has no remaining documentary gate.** None of the three changed an architectural
decision. Two confirmed an existing decision was already right; one produced an additive rule.

| # | Item | Verified answer, with source | Decision effect |
|---|---|---|---|
| **Q4 / M-5** | Is the news archive point-in-time? | **NO** `[V]`. Both vendors expose a post-publication revision timestamp and **neither offers any version, revision or as-of-content parameter**, so a historical query returns the article as currently stored. `massive.com/docs/rest/partners/benzinga/news`; `docs.alpaca.markets/reference/news-3` | **ADR-04 UNCHANGED** — every candidate vendor shares the property, so it is a characteristic of financial news, not a defect of one supplier. **Rule N4 moves from precautionary to evidence-based**; **new rule N16** makes our own store the point-in-time record. Residual materiality → **M-12**, not gating |
| **M-2** | Is price history retained for delisted names? | **YES** `[V]`. “our market data includes companies that have been delisted from the exchanges and is stored as it occurred on that date.” `massive.com/knowledge-base/article/what-does-massive-do-with-delisted-tickers` | **ADR-14 and invariant I7 UNCHANGED**, and no longer at risk — the never-delete rule is now vendor-supportable |
| **M-3** | WebSocket reconnect / replay semantics | **No mechanism is documented** `[V]`. Two Alpaca streaming pages retrieved in full; both silent on reconnect, replay, sequence numbers and gap recovery. They do document the 1-connection limit and that “slow clients may get disconnected if their buffer becomes full” | **Rule N5 UNCHANGED and confirmed correct.** An undocumented replay could only be an optimisation, never a correctness dependency — so it cannot gate |

### 6.2 OPEN — carried, not gating

`Q7/M-6` settlement and good-faith rules · `Q8` India tax schedule · `Q9` LRS/TCS ·
`Q10` record-retention minima · `Q12` RBI FX endpoint · **`M-7` DeepSeek data-retention terms
(AD-5 depends on it)** · `M-9` broker detail gaps · `M-10` OpenAI Batch turnaround ·
**`M-11b` OpenAI Terms of Service on automated access, redistribution and storage (new
2026-08-26; the auth half M-11a is closed)** · **`M-12` materiality of Benzinga post-publication
edits (new 2026-08-26, residual of M-5)** · `M-3` residual: the same replay semantics for
Massive, Zerodha and Upstox · **`A-14` does `[CONST-6]` DENY apply to exposure-reducing
actions** · `P0.3 Q-1/Q-2` VM and backup pricing · `P0.3 Q-11` heading convention ·
`P0.3 Q-12` zero-trade bar behaviour.

### 6.3 PARTIAL

`Q1` Alpaca idempotency-key **charset** undocumented → M-1 · `Q5` EDGAR **propagation latency**
unpublished → M-8.

### 6.4 MEASUREMENT-BY-DESIGN — never to be converted into pre-implementation decisions

| # | Quantity | Default in force | Measured by |
|---|---|---|---|
| **Q13** | Round-trip transaction cost | 25 bps US / 90 bps India | P5.3, after ≥200 **live** fills (paper excluded, rule N11) |
| **Q14** | Tokens per thesis | 6,000 in / 1,500 out | P4.3, first 50 live gate calls |
| **Q15** | Audit-event rate and row width | 15,000/session, ~1 KB | P1.2 / P6.1, after 20 live sessions |

---

## 7. Conditions that permit re-opening a frozen decision

A frozen decision may be re-opened **only** on a documented trigger. Five categories, and nothing
else:

| # | Trigger | Example |
|---|---|---|
| **T1** | **A revisit condition named in the ADR itself fires** | ADR-14: NAV crosses ~$100,000, so the ADDV floor's scaling term begins to bind |
| **T2** | **A carried-forward item resolves and contradicts the decision** | **M-7 resolves and DeepSeek's terms are comparable → AD-5 is re-scored.** This is a live, expected trigger, not a hypothetical |
| **T3** | **A verified external fact changes** | A vendor discontinues a tier; SEBI amends the circular; the November 2027 tick regime is deferred again |
| **T4** | **Measurement contradicts an assumption the decision rests on** | Measured audit volume exceeds ~150,000 events/session, breaking P0.3's 250 GB disk sizing |
| **T5** | **A downstream phase proves the decision unimplementable** | P2.9 demonstrates that a deterministic risk check cannot meet its 60 s budget |

**Not triggers:** a losing trade, a losing week, a drawdown, developer preference, or a desire to
simplify. ADR-07 and `[CONST-8]` already forbid the first three from changing a model; this freeze
extends the same prohibition to architecture.

---

## 8. Authority for re-opening

| Action | Authority | Record required |
|---|---|---|
| Re-open any ADR or AD | **Owner** (ADR-09 row 12) | New amendment id, version bump on the affected spec, entry in §9 |
| Amend `[CONST]` FIXED STACK or a numbered invariant | **Owner** | Explicit constitutional amendment, as §3.1 |
| Apply an additive rule that changes no decision | Phase author | Version bump, entry in §9 |
| **Override a risk DENY** | **Nobody. No code path exists** | ADR-09; `hitl.risk_deny_override_permitted = false`, immutable |

A re-opening that does not produce a §9 entry has not happened. That is the whole mechanism.

---

## 9. Change log against the freeze

| Date | Artifact | From → To | Trigger | Authority | Summary |
|---|---|---|---|---|---|
| 2026-08-25 | SPEC-P0.1-DECISIONS | v0.1 → **v0.2** | Stage 0 closure | Owner | 20 amendments dispositioned; AD-1…AD-5 taken; open-item register rebuilt; **FROZEN** |
| 2026-08-25 | SPEC-P0.2-PROVIDERS | v0.2 → **v0.3** | AD-3, AD-4, AD-5 | Owner | LLM roles swapped; Batch-tier claim corrected (M-10); amendment dispositions recorded. **No fact sheet, price or verified limit changed**; **FROZEN** |
| 2026-08-26 | SPEC-P0.1-DECISIONS | v0.2 → **v0.3** | **T3** — verified external facts (4 retrievals) | Phase author (§8, changes no decision) | ADR-04 records the news point-in-time finding and rule N16; §9.3 reclassified from GATING to resolved. **No ADR or AD changed** |
| 2026-08-26 | SPEC-P0.2-PROVIDERS | v0.4 → **v0.5** | **T3** — verified external facts (4 retrievals) | Phase author (§8, changes no decision) | M-2 closed; M-3 downgraded from gating; M-5 answered (**not** point-in-time) with new rule **N16**; M-11 split, auth closed; **M-12** and **M-11b** opened. Register 10 → 9 items. **No ADR or AD changed** |
| 2026-08-26 | SPEC-P0.3-BUDGET | v0.4 → **v0.5** | **T3** — rule N16 | Phase author (§8, changes no decision) | News storage line carries a revision factor; quantified as immaterial (news is 1.3% of compressed storage). **No VM, latency, LLM or sensitivity figure changed** |
| 2026-08-26 | SPEC-P0.2-PROVIDERS | v0.3 → **v0.4** | Defect in the 2026-08-25 freeze: three sites still asserted the pre-AD-5 LLM ordering | Phase author (§8, changes no decision) | §3.11/§3.12 headings and DECISIONS row 7 aligned with AD-5; **M-11** added for OpenAI auth/legal. **No fact, price, limit or decision changed** |
| 2026-08-25 | SPEC-P0.3-BUDGET | v0.3 → **v0.4** | AD-2, AD-5 | Owner | LLM cost model recomputed on the new primary; RULE-B8 made provider-conditional; Q-9 closed by AD-2. **No storage, latency or VM figure changed**; **FROZEN** |

---

## 10. Downstream stages that may now proceed

| Stage | Phases | Status | Precondition carried |
|---|---|---|---|
| **Stage 1 — SPECIFY** | **P1.1 → P1.2 → P1.3 → P1.4** | **CLEARED TO PROCEED — no remaining documentary gate (2026-08-26)** | All three former gates are resolved (§6.1). **Two design requirements now bind P1.2 and P2.1 that were previously contingent**: rule **N16** (news revisions stored as new rows; our store is the point-in-time record, the vendor's is not) and rule **N5** (gap-is-lost, reconcile from REST). Both are cheap now and expensive to retrofit after the schema freezes |
| Stage 2 — CORE | P2.1 → P2.10 | Blocked on Stage 1 | **A-14 must be ratified before P2.9** — P0.3 §6.2 stage 4 and §13 row 27 are not implementable without it |
| Stage 3 — EXECUTE | P3.1 → P3.4 | Blocked | Hard rule: **P2.9 and P2.10 must be FROZEN and tested** before any code can reach a broker |
| Stage 4 — INTELLIGENCE | P4.1 → P4.4 | Blocked on P2.7 | P4.3 must implement AD-5's Standard-tier constraint until M-10 closes |
| Stage 5 — VALIDATE | P5.1 → P5.5 | Blocked | P5.2 implements AD-2's 3-month rolls |
| Stage 6 — OPERATE | P6.1 → P6.6 | Blocked | P6.4 resolves Q-1 and Q-2, completing AD-1's cost model |

**Specific instruction to P1.1, the next phase:** it consumes SPEC-P0.1-DECISIONS **v0.2** — not
v0.1 — and must import the enumerations and configuration keys from its §10, including the twelve
keys added by AD-1 through AD-5.

---

## 11. Cross-document consistency report

Verified programmatically at freeze time across P0.1 v0.2, P0.2 v0.3, P0.3 v0.4 and
`master-research-summary.md`.

| Check | Result | Evidence |
|---|---|---|
| No contradictory broker hierarchy | **PASS** | Zerodha primary / Upstox monitoring / IBKR manual-only stated identically in P0.1 ADR-11, P0.1 §10.2 and this record. P0.2's fact sheets describe capabilities, not selection. **Three stale P0.2 rows were found by the STEP 7 validator and fixed**: §6 A-4 still recommended "consider Upstox as India primary", §6 A-6 still proposed a flat $130–230 band that AD-1 rejected, and §7 row 15 still read "escalated" after the escalation was answered |
| No contradictory authentication assumptions | **PASS** | IBKR browser-login and 6-min idle timeout stated in P0.1 ADR-10 (AD-3) and P0.2 F-12; Zerodha 06:00 IST expiry in P0.1 ADR-11 and P0.2 F-4; Upstox `extended_token` read-only-only in both |
| No stale cost assumption | **PASS** | No spec *asserts* the old band. A14 is superseded in place; ADR-13 option B and Chain A carry the verified figures and the INCOMPLETE marker. `$30–200/mo` still appears **five times as a quoted historical value** — P0.1 §0.5.1 (recording what AD-1 replaced), P0.2 §2, §4.3 and §6 A-6 (recording what was found low), and this row. That is deliberate: deleting the superseded figure would destroy the record of what was believed and why it changed. **An earlier draft of this row claimed the string appeared nowhere; that claim was false and was caught by the STEP 7 validator.** |
| No stale walk-forward calculation | **PASS** | Every `34 windows` reference now names 3-month rolls: P0.1 one-page row 13, ADR-08 conclusion, ADR-08 Stage 1, ADR-13 evidence table, ADR-04. P0.3 §7.2 and §14.4 updated; Q-9 struck |
| No unsupported automated-failover claim | **PASS** | P0.1 ADR-10 states the backup is excluded from every RTO claim and requires a human login. RTO-safe 30 min and RTO-operational 4 h are unchanged and independently derived |
| No stale LLM decision | **PASS as of 2026-08-26** | AD-5 applied in P0.1 §0.5.1/§10.2, P0.2 §4.3/§6/§10.4, P0.3 §0/§1/§5/§7/§8/§9.2/§13/§14.4/§15.1/§16. `gpt-4o-mini` survives only where it is explicitly named as non-existent. **This row read PASS on 2026-08-25 and was overstated**: the STEP 7 validator checked §4.3, §10.4 and the config keys but not section headings or the DECISIONS table, so P0.2 §3.11, §3.12 and DECISIONS row 7 still asserted DeepSeek-primary for one day. Found by the P0.2 re-run audit and fixed in P0.2 v0.4; the validator now checks role labels |
| No accidental closure of Q4 | **PASS** | Q4/M-5 appears as **OPEN AND GATING** in P0.1 §9.3, in P0.2 §5.2 M-5, and in §6.1 above. No document marks it closed |
| No missing amendment | **PASS** | All 20 dispositioned in §4; 19 applied, A-14 explicitly carried |
| No undocumented architecture change | **PASS** | Every change traces to AD-1…AD-5 or to an additive amendment; §9 records all three version bumps |
| Contract models still execute | **PASS** | P0.3's four Python blocks concatenate, import, and pass **21/21** validator assertions after the AD-5 price change |
| LLM arithmetic recomputed | **PASS** | Independently recomputed: $0.00300/call, $0.95/mo at gate 15, $113.40/replay, 66,667 calls to reach $200/mo = 2.12× universe. Every §5 conclusion survives |

| Retrieval-driven amendment (2026-08-26) | **PASS** | Four facts retrieved from primary vendor documentation and applied under §7 trigger T3. **Zero ADR or AD-level decisions changed** — M-2 and M-3 confirmed existing decisions correct, M-5 produced additive rule N16, M-11a confirmed the Vault line. Every retrieval is recorded with its exact fact, source URL and retrieval date in P0.2 §5.2 and P0.1 §9.3 |

**Two residual inconsistencies, declared rather than silently fixed:**

1. **`master-research-summary.md` is not amended.** It is the immutable research input, not a
   decision record. Where it conflicts with a frozen decision — the "$200–500/month" LLM figure
   (§6 Phase 5), "Polygon.io" (§8/§10), the 6-month walk-forward rolls (§13) — **the frozen spec
   wins**, per P0.1 §0.1's precedence order. Editing the research summary to match its own
   conclusions would destroy the audit trail of what was originally believed.
2. **`docs/PROMPT-PACK.md` retains defects A-16 and A-17.** P0.3's phase prompt asks for an
   open-burst ingest analysis ADR-13 forecloses, and `scripts/create-issues.sh` carries an
   acceptance criterion ("the gate width from this phase is the number P4.2 implements") that is
   unsatisfiable on cost grounds. Both are process defects for the prompt-pack maintainer, and
   neither affects a frozen decision.

---

# STAGE 0 FROZEN

**2026-08-25 · SPEC-P0.1 v0.2 · SPEC-P0.2 v0.3 · SPEC-P0.3 v0.4 · Owner: JS**

Twenty architectural decisions frozen. Nineteen amendments applied, one carried. Eleven items
carried forward, three of them gating Stage 1 sign-off. **Stage 1 is cleared to proceed.**
